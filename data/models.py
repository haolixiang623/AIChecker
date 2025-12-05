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

def init_db():
    db.connect()
    db.create_tables([ScanSession, PageElement, AIReport])
