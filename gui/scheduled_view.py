"""
定时扫描视图 - 添加到 views.py 末尾
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
                               QLineEdit, QRadioButton, QButtonGroup, QCheckBox, QSpinBox,
                               QMessageBox, QFormLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from data.models import ScheduledTask
from data.storage import StorageManager
import datetime


class ScheduledScanView(QWidget):
    """定时扫描视图"""
    
    def __init__(self, scheduler=None):
        super().__init__()
        self.scheduler = scheduler
        self.storage = StorageManager()
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>定时扫描</h2>"))
        
        # 任务列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "任务名称", "URL", "定时配置", "状态", "下次执行", "最后执行", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加任务")
        self.btn_add.clicked.connect(self.add_task)
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.clicked.connect(self.load_tasks)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.load_tasks()
    
    def load_tasks(self):
        """加载所有定时任务"""
        tasks = ScheduledTask.select().order_by(ScheduledTask.created_at.desc())
        
        self.table.setRowCount(len(tasks))
        for i, task in enumerate(tasks):
            # ID
            self.table.setItem(i, 0, QTableWidgetItem(str(task.id)))
            
            # 任务名称
            self.table.setItem(i, 1, QTableWidgetItem(task.name))
            
            # URL
            url_item = QTableWidgetItem(task.url[:50] + "..." if len(task.url) > 50 else task.url)
            url_item.setToolTip(task.url)
            self.table.setItem(i, 2, url_item)
            
            # 定时配置
            if task.schedule_type == 'interval':
                schedule_text = f"每 {task.interval_minutes} 分钟"
            else:
                schedule_text = f"Cron: {task.cron_expression}"
            self.table.setItem(i, 3, QTableWidgetItem(schedule_text))
            
            # 状态
            status_item = QTableWidgetItem("✅ 启用" if task.enabled else "⚪ 禁用")
            status_item.setForeground(Qt.darkGreen if task.enabled else Qt.gray)
            self.table.setItem(i, 4, status_item)
            
            # 下次执行
            if task.next_run_time:
                next_time = task.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                next_time = "-"
            self.table.setItem(i, 5, QTableWidgetItem(next_time))
            
            # 最后执行
            if task.last_run_time:
                last_time = task.last_run_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_time = "未执行"
            self.table.setItem(i, 6, QTableWidgetItem(last_time))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("编辑")
            btn_edit.clicked.connect(lambda checked, tid=task.id: self.edit_task(tid))
            btn_layout.addWidget(btn_edit)
            
            btn_toggle = QPushButton("禁用" if task.enabled else "启用")
            btn_toggle.clicked.connect(lambda checked, tid=task.id: self.toggle_task(tid))
            btn_layout.addWidget(btn_toggle)
            
            btn_run = QPushButton("立即执行")
            btn_run.clicked.connect(lambda checked, tid=task.id: self.run_task_now(tid))
            btn_layout.addWidget(btn_run)
            
            btn_delete = QPushButton("删除")
            btn_delete.clicked.connect(lambda checked, tid=task.id: self.delete_task(tid))
            btn_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(i, 7, btn_widget)
    
    def add_task(self):
        """添加新任务"""
        dialog = TaskEditDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            task = ScheduledTask.create(**task_data)
            
            # 添加到调度器
            if self.scheduler and task.enabled:
                self.scheduler.add_task(task.id)
            
            self.load_tasks()
            QMessageBox.information(self, "成功", f"任务 '{task.name}' 已创建")
    
    def edit_task(self, task_id):
        """编辑任务"""
        task = ScheduledTask.get_by_id(task_id)
        dialog = TaskEditDialog(self, task)
        if dialog.exec():
            task_data = dialog.get_task_data()
            for key, value in task_data.items():
                setattr(task, key, value)
            task.save()
            
            # 更新调度器
            if self.scheduler:
                self.scheduler.remove_task(task_id)
                if task.enabled:
                    self.scheduler.add_task(task_id)
            
            self.load_tasks()
            QMessageBox.information(self, "成功", f"任务 '{task.name}' 已更新")
    
    def toggle_task(self, task_id):
        """启用/禁用任务"""
        task = ScheduledTask.get_by_id(task_id)
        task.enabled = not task.enabled
        task.save()
        
        # 更新调度器
        if self.scheduler:
            if task.enabled:
                self.scheduler.add_task(task_id)
            else:
                self.scheduler.remove_task(task_id)
        
        self.load_tasks()
        status = "启用" if task.enabled else "禁用"
        QMessageBox.information(self, "成功", f"任务 '{task.name}' 已{status}")
    
    def run_task_now(self, task_id):
        """立即执行任务"""
        if self.scheduler:
            reply = QMessageBox.question(
                self, "确认", "确定要立即执行此任务吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 在后台线程执行
                import threading
                thread = threading.Thread(target=self.scheduler.execute_task, args=(task_id,))
                thread.start()
                QMessageBox.information(self, "提示", "任务已开始执行，请稍后查看扫描历史")
        else:
            QMessageBox.warning(self, "错误", "调度器未初始化")
    
    def delete_task(self, task_id):
        """删除任务"""
        task = ScheduledTask.get_by_id(task_id)
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除任务 '{task.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 从调度器移除
            if self.scheduler:
                self.scheduler.remove_task(task_id)
            
            task.delete_instance()
            self.load_tasks()
            QMessageBox.information(self, "成功", "任务已删除")


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("编辑任务" if task else "添加任务")
        self.resize(500, 400)
        
        layout = QFormLayout(self)
        
        # 任务名称
        self.name_input = QLineEdit()
        if task:
            self.name_input.setText(task.name)
        layout.addRow("任务名称:", self.name_input)
        
        # URL
        self.url_input = QLineEdit()
        if task:
            self.url_input.setText(task.url)
        layout.addRow("扫描URL:", self.url_input)
        
        # 定时类型
        schedule_group = QWidget()
        schedule_layout = QVBoxLayout(schedule_group)
        
        self.schedule_group = QButtonGroup()
        self.radio_interval = QRadioButton("间隔时间")
        self.radio_cron = QRadioButton("Cron表达式")
        self.schedule_group.addButton(self.radio_interval, 1)
        self.schedule_group.addButton(self.radio_cron, 2)
        
        schedule_layout.addWidget(self.radio_interval)
        
        # 间隔时间输入
        interval_widget = QWidget()
        interval_layout = QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(20, 0, 0, 0)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 10080)  # 1分钟到1周
        self.interval_input.setValue(60)
        interval_layout.addWidget(QLabel("每"))
        interval_layout.addWidget(self.interval_input)
        interval_layout.addWidget(QLabel("分钟"))
        interval_layout.addStretch()
        schedule_layout.addWidget(interval_widget)
        
        schedule_layout.addWidget(self.radio_cron)
        
        # Cron表达式输入
        cron_widget = QWidget()
        cron_layout = QHBoxLayout(cron_widget)
        cron_layout.setContentsMargins(20, 0, 0, 0)
        self.cron_input = QLineEdit()
        self.cron_input.setPlaceholderText("例如: 0 9 * * * (每天9点)")
        cron_layout.addWidget(self.cron_input)
        schedule_layout.addWidget(cron_widget)
        
        layout.addRow("定时配置:", schedule_group)
        
        # 扫描选项
        options_group = QWidget()
        options_layout = QVBoxLayout(options_group)
        self.check_validation = QCheckBox("启用元素验证")
        self.check_ai_report = QCheckBox("自动生成AI报告")
        options_layout.addWidget(self.check_validation)
        options_layout.addWidget(self.check_ai_report)
        layout.addRow("扫描选项:", options_group)
        
        # 如果是编辑模式，填充数据
        if task:
            if task.schedule_type == 'interval':
                self.radio_interval.setChecked(True)
                self.interval_input.setValue(task.interval_minutes)
            else:
                self.radio_cron.setChecked(True)
                self.cron_input.setText(task.cron_expression)
            
            self.check_validation.setChecked(task.enable_validation)
            self.check_ai_report.setChecked(task.generate_ai_report)
        else:
            self.radio_interval.setChecked(True)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow("", btn_layout)
    
    def get_task_data(self):
        """获取任务数据"""
        data = {
            'name': self.name_input.text(),
            'url': self.url_input.text(),
            'enable_validation': self.check_validation.isChecked(),
            'generate_ai_report': self.check_ai_report.isChecked(),
        }
        
        if self.radio_interval.isChecked():
            data['schedule_type'] = 'interval'
            data['interval_minutes'] = self.interval_input.value()
            data['cron_expression'] = None
        else:
            data['schedule_type'] = 'cron'
            data['interval_minutes'] = None
            data['cron_expression'] = self.cron_input.text()
        
        return data
