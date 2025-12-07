from peewee import *
import datetime

db = SqliteDatabase('aichecker.db')

class BaseModel(Model):
    class Meta:
        database = db

class ScanSession(BaseModel):
    url = CharField()
    start_time = DateTimeField(default=datetime.datetime.now)
    end_time = DateTimeField(null=True)
    status = CharField(default='pending') # pending, completed, failed
    
    def get_element_count(self):
        """获取此会话的元素总数"""
        return self.elements.count()
    
    def get_validation_summary(self):
        """获取验证结果摘要"""
        total = self.elements.count()
        validated = self.elements.where(PageElement.validated == True).count()
        
        # 统计链接状态
        links = self.elements.where(PageElement.type == 'a')
        link_total = links.count()
        link_ok = links.where(
            (PageElement.status_code >= 200) & 
            (PageElement.status_code < 300)
        ).count()
        link_error = links.where(
            (PageElement.status_code >= 400)
        ).count()
        
        # 统计按钮状态
        buttons = self.elements.where(PageElement.type.in_(['button', 'input']))
        button_total = buttons.count()
        button_clickable = buttons.where(PageElement.clickable == True).count()
        
        return {
            'total_elements': total,
            'validated_elements': validated,
            'link_total': link_total,
            'link_ok': link_ok,
            'link_error': link_error,
            'button_total': button_total,
            'button_clickable': button_clickable,
        }
    
    def get_duration(self):
        """获取扫描持续时间（秒）"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds()
        return None


class PageElement(BaseModel):
    session = ForeignKeyField(ScanSession, backref='elements')
    type = CharField() # a, button, etc.
    text = TextField(null=True)
    href = TextField(null=True)
    element_id = CharField(null=True)
    class_name = CharField(null=True)
    selector = CharField()
    visible = BooleanField(default=True)
    screenshot_path = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    
    # 验证结果字段
    validated = BooleanField(default=False)  # 是否已验证
    validation_time = DateTimeField(null=True)  # 验证时间
    
    # 链接验证结果
    status_code = IntegerField(null=True)  # HTTP 状态码
    response_time = FloatField(null=True)  # 响应时间（秒）
    validation_error = TextField(null=True)  # 验证错误信息
    
    # 按钮验证结果
    clickable = BooleanField(null=True)  # 是否可点击
    enabled = BooleanField(null=True)  # 是否启用

class AIReport(BaseModel):
    session = ForeignKeyField(ScanSession, backref='reports', null=True)
    element = ForeignKeyField(PageElement, backref='reports', null=True)
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)

class ScheduledTask(BaseModel):
    """定时扫描任务模型"""
    name = CharField()  # 任务名称
    url = TextField()  # 扫描URL
    enabled = BooleanField(default=True)  # 是否启用
    
    # 定时配置
    schedule_type = CharField()  # 'interval' 或 'cron'
    interval_minutes = IntegerField(null=True)  # 间隔分钟数
    cron_expression = CharField(null=True)  # cron表达式
    
    # 扫描选项
    enable_validation = BooleanField(default=False)  # 是否启用验证
    generate_ai_report = BooleanField(default=False)  # 是否生成AI报告
    
    # 执行记录
    last_run_time = DateTimeField(null=True)  # 最后执行时间
    next_run_time = DateTimeField(null=True)  # 下次执行时间
    last_session_id = IntegerField(null=True)  # 最后扫描会话ID
    
    created_at = DateTimeField(default=datetime.datetime.now)

def init_db():
    # 检查数据库是否已连接，避免重复连接
    if not db.is_closed():
        # 数据库已连接，只需确保表存在
        db.create_tables([ScanSession, PageElement, AIReport, ScheduledTask], safe=True)
    else:
        # 数据库未连接，先连接再创建表
        db.connect()
        db.create_tables([ScanSession, PageElement, AIReport, ScheduledTask], safe=True)


