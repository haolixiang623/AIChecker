from data.models import db, ScanSession, PageElement, AIReport, init_db
import datetime

class StorageManager:
    def __init__(self):
        init_db()

    def create_session(self, url):
        return ScanSession.create(url=url)

    def complete_session(self, session_id, status='completed'):
        session = ScanSession.get_by_id(session_id)
        session.end_time = datetime.datetime.now()
        session.status = status
        session.save()
        return session

    def save_elements(self, session_id, elements_data):
        """
        Bulk save detected elements.
        elements_data: list of dicts from ElementDetector
        """
        with db.atomic():
            for el_data in elements_data:
                PageElement.create(
                    session_id=session_id,
                    type=el_data.get('type'),
                    text=el_data.get('text'),
                    href=el_data.get('href'),
                    element_id=el_data.get('id'),
                    class_name=el_data.get('class'),
                    selector=el_data.get('selector'),
                    visible=el_data.get('visible', True),
                    screenshot_path=el_data.get('screenshot_path')
                )

    def get_recent_sessions(self, limit=10):
        return ScanSession.select().order_by(ScanSession.start_time.desc()).limit(limit)

    def get_elements_by_session(self, session_id):
        return PageElement.select().where(PageElement.session == session_id)
    
    def save_report(self, content, session_id=None, element_id=None):
        return AIReport.create(
            content=content,
            session_id=session_id,
            element_id=element_id
        )
    
    def update_element_validation(self, element_id, validation_data):
        """
        更新单个元素的验证结果
        
        Args:
            element_id: 元素 ID
            validation_data: 验证结果字典
        """
        element = PageElement.get_by_id(element_id)
        element.validated = True
        element.validation_time = datetime.datetime.now()
        
        # 链接验证结果
        if 'status_code' in validation_data:
            element.status_code = validation_data['status_code']
        if 'response_time' in validation_data:
            element.response_time = validation_data['response_time']
        if 'error' in validation_data:
            element.validation_error = validation_data['error']
        
        # 按钮验证结果
        if 'clickable' in validation_data:
            element.clickable = validation_data['clickable']
        if 'enabled' in validation_data:
            element.enabled = validation_data['enabled']
        
        element.save()
        return element
    
    def batch_update_validations(self, validations):
        """
        批量更新验证结果
        
        Args:
            validations: [(element_id, validation_data), ...]
        """
        with db.atomic():
            for element_id, validation_data in validations:
                self.update_element_validation(element_id, validation_data)
    
    def get_session_summary(self, session_id):
        """
        获取会话的详细摘要信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            dict: 包含会话信息和统计数据的字典
        """
        session = ScanSession.get_by_id(session_id)
        summary = session.get_validation_summary()
        
        return {
            'session': session,
            'url': session.url,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'duration': session.get_duration(),
            'status': session.status,
            **summary
        }
    
    def get_session_ai_reports(self, session_id):
        """
        获取会话的所有AI分析报告
        
        Args:
            session_id: 会话 ID
            
        Returns:
            list: AIReport 对象列表
        """
        return AIReport.select().where(AIReport.session == session_id).order_by(AIReport.created_at.desc())
    
    def get_element_ai_reports(self, element_id):
        """
        获取元素的所有AI分析报告
        
        Args:
            element_id: 元素 ID
            
        Returns:
            list: AIReport 对象列表
        """
        return AIReport.select().where(AIReport.element == element_id).order_by(AIReport.created_at.desc())


