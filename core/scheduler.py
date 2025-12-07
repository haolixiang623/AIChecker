"""
定时任务调度器模块

使用 APScheduler 实现定时扫描任务的调度和执行
"""

import asyncio
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from data.models import ScheduledTask, db
from data.storage import StorageManager
from core.scanner import PageScanner
from core.detector import ElementDetector
from core.validator import ElementValidator
from ai.client import AIClient


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.storage = StorageManager()
        self.running_tasks = set()  # 跟踪正在运行的任务
    
    def start(self):
        """启动调度器并加载所有启用的任务"""
        self.scheduler.start()
        self._load_tasks()
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
    
    def _load_tasks(self):
        """从数据库加载所有启用的任务"""
        tasks = ScheduledTask.select().where(ScheduledTask.enabled == True)
        for task in tasks:
            self.add_task(task.id)
    
    def add_task(self, task_id):
        """添加定时任务到调度器"""
        try:
            task = ScheduledTask.get_by_id(task_id)
            
            # 移除已存在的任务（如果有）
            job_id = f"task_{task_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 根据类型创建触发器
            if task.schedule_type == 'interval':
                trigger = IntervalTrigger(minutes=task.interval_minutes)
            elif task.schedule_type == 'cron':
                # 解析cron表达式
                parts = task.cron_expression.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4]
                    )
                else:
                    print(f"Invalid cron expression for task {task_id}: {task.cron_expression}")
                    return
            else:
                print(f"Unknown schedule type for task {task_id}: {task.schedule_type}")
                return
            
            # 添加任务到调度器
            self.scheduler.add_job(
                self.execute_task,
                trigger=trigger,
                id=job_id,
                args=[task_id],
                name=task.name
            )
            
            # 更新下次执行时间
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                task.next_run_time = job.next_run_time
                task.save()
            
            print(f"Added scheduled task: {task.name} (ID: {task_id})")
        except Exception as e:
            print(f"Error adding task {task_id}: {e}")
    
    def remove_task(self, task_id):
        """从调度器移除任务"""
        job_id = f"task_{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            print(f"Removed scheduled task ID: {task_id}")
    
    def execute_task(self, task_id):
        """执行扫描任务"""
        # 防止同一任务重复执行
        if task_id in self.running_tasks:
            print(f"Task {task_id} is already running, skipping...")
            return
        
        self.running_tasks.add(task_id)
        
        try:
            task = ScheduledTask.get_by_id(task_id)
            print(f"Executing scheduled task: {task.name} (ID: {task_id})")
            
            # 更新最后执行时间
            task.last_run_time = datetime.datetime.now()
            task.save()
            
            # 在新的事件循环中执行异步扫描
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            session_id = loop.run_until_complete(
                self._run_scan(task)
            )
            loop.close()
            
            # 更新最后扫描会话ID
            if session_id:
                task.last_session_id = session_id
                task.save()
                
                # 如果启用了AI报告生成
                if task.generate_ai_report:
                    self._generate_ai_report(session_id)
            
            # 更新下次执行时间
            job = self.scheduler.get_job(f"task_{task_id}")
            if job and job.next_run_time:
                task.next_run_time = job.next_run_time
                task.save()
            
            print(f"Task {task_id} completed successfully. Session ID: {session_id}")
        except Exception as e:
            print(f"Error executing task {task_id}: {e}")
        finally:
            self.running_tasks.discard(task_id)
    
    async def _run_scan(self, task):
        """执行扫描（异步）"""
        scanner = PageScanner()
        detector = ElementDetector()
        
        await scanner.start()
        page = await scanner.scan(task.url)
        
        if not page:
            await scanner.stop()
            return None
        
        elements = await detector.detect(page)
        
        # 保存到数据库
        session = self.storage.create_session(task.url)
        self.storage.save_elements(session.id, elements)
        
        # 如果启用验证
        if task.enable_validation:
            await self._validate_elements(page, session.id)
        
        self.storage.complete_session(session.id)
        await scanner.stop()
        
        return session.id
    
    async def _validate_elements(self, page, session_id):
        """验证元素（异步）"""
        elements = self.storage.get_elements_by_session(session_id)
        current_url = page.url
        
        async with ElementValidator() as validator:
            # 验证链接
            links = [el for el in elements if el.type == 'a' and el.href]
            for link in links:
                result = await validator.validate_link(link.href, current_url)
                self.storage.update_element_validation(link.id, {
                    'status_code': result['status_code'],
                    'response_time': result['response_time'],
                    'error': result['error']
                })
            
            # 验证按钮
            buttons = [el for el in elements if el.type in ['button', 'input']]
            for btn in buttons:
                try:
                    handle = page.locator(btn.selector).first
                    result = await validator.validate_button(page, handle)
                    self.storage.update_element_validation(btn.id, {
                        'clickable': result['clickable'],
                        'enabled': result['enabled'],
                        'error': result.get('error')
                    })
                except Exception as e:
                    self.storage.update_element_validation(btn.id, {
                        'clickable': False,
                        'enabled': False,
                        'error': str(e)
                    })
    
    def _generate_ai_report(self, session_id):
        """生成AI报告"""
        try:
            client = AIClient()
            if not client.client:
                print(f"AI client not initialized, skipping report generation for session {session_id}")
                return
            
            summary = self.storage.get_session_summary(session_id)
            elements = self.storage.get_elements_by_session(session_id)
            
            # 转换元素为字典列表
            elements_data = []
            for el in elements:
                elements_data.append({
                    'type': el.type,
                    'text': el.text,
                    'href': el.href,
                    'status_code': el.status_code,
                    'clickable': el.clickable,
                    'validated': el.validated,
                    'validation_error': el.validation_error,
                    'response_time': el.response_time,
                })
            
            report = client.analyze_session(summary, elements_data)
            self.storage.save_report(report, session_id=session_id)
            
            print(f"AI report generated for session {session_id}")
        except Exception as e:
            print(f"Error generating AI report for session {session_id}: {e}")
    
    def get_next_run_time(self, task_id):
        """获取任务的下次执行时间"""
        job_id = f"task_{task_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
