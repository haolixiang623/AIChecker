from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
import asyncio
from core.scanner import PageScanner
from core.detector import ElementDetector
from data.storage import StorageManager
from ai.client import AIClient

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>欢迎使用 AIChecker</h2>"))
        layout.addWidget(QLabel("最近的扫描记录将显示在这里..."))
        layout.addStretch()

class ScanWorker(QThread):
    finished = Signal(object)
    log = Signal(str)

    def __init__(self, url, enable_validation=False):
        super().__init__()
        self.url = url
        self.enable_validation = enable_validation

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self._scan())
        self.finished.emit(results)
        loop.close()

    async def _scan(self):
        from core.validator import ElementValidator
        
        self.log.emit(f"正在启动扫描器: {self.url}")
        scanner = PageScanner()
        detector = ElementDetector()
        storage = StorageManager()
        
        await scanner.start()
        page = await scanner.scan(self.url)
        
        if not page:
            self.log.emit("页面加载失败")
            await scanner.stop()
            return None
            
        self.log.emit("页面加载成功，正在检测元素...")
        elements = await detector.detect(page)
        self.log.emit(f"检测到 {len(elements)} 个元素")
        
        # Save to DB
        session = storage.create_session(self.url)
        storage.save_elements(session.id, elements)
        
        # 验证元素（如果启用）
        if self.enable_validation:
            self.log.emit("\n开始验证元素...")
            await self._validate_elements(page, session.id, storage)
        
        storage.complete_session(session.id)
        await scanner.stop()
        return session.id
    
    async def _validate_elements(self, page, session_id, storage):
        """验证元素的可用性"""
        from core.validator import ElementValidator
        
        # 获取数据库中的元素
        elements = storage.get_elements_by_session(session_id)
        current_url = page.url
        
        async with ElementValidator() as validator:
            # 验证链接
            links = [el for el in elements if el.type == 'a' and el.href]
            if links:
                self.log.emit(f"验证 {len(links)} 个链接...")
                for i, link in enumerate(links):
                    result = await validator.validate_link(link.href, current_url)
                    storage.update_element_validation(link.id, {
                        'status_code': result['status_code'],
                        'response_time': result['response_time'],
                        'error': result['error']
                    })
                    if (i + 1) % 50 == 0:
                        self.log.emit(f"  已验证 {i + 1}/{len(links)} 个链接")
            
            # 验证按钮
            buttons = [el for el in elements if el.type in ['button', 'input']]
            if buttons:
                self.log.emit(f"验证 {len(buttons)} 个按钮...")
                for i, btn in enumerate(buttons):
                    try:
                        # 重新定位元素
                        handle = page.locator(btn.selector).first
                        result = await validator.validate_button(page, handle)
                        storage.update_element_validation(btn.id, {
                            'clickable': result['clickable'],
                            'enabled': result['enabled'],
                            'error': result.get('error')
                        })
                    except Exception as e:
                        storage.update_element_validation(btn.id, {
                            'clickable': False,
                            'enabled': False,
                            'error': str(e)
                        })
                    if (i + 1) % 50 == 0:
                        self.log.emit(f"  已验证 {i + 1}/{len(buttons)} 个按钮")
        
        self.log.emit("验证完成!")

class ScanView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入目标网址 (例如: https://example.com)")
        layout.addWidget(QLabel("目标网址:"))
        layout.addWidget(self.url_input)
        
        # 验证选项
        from PySide6.QtWidgets import QCheckBox
        self.validate_checkbox = QCheckBox("启用元素验证（检查链接状态码和按钮可点击性）")
        self.validate_checkbox.setChecked(False)
        layout.addWidget(self.validate_checkbox)
        
        self.btn_start = QPushButton("开始扫描")
        self.btn_start.clicked.connect(self.start_scan)
        layout.addWidget(self.btn_start)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(QLabel("扫描日志:"))
        layout.addWidget(self.log_area)
        
    def start_scan(self):
        url = self.url_input.text()
        if not url:
            self.log_area.append("请输入有效的 URL")
            return
            
        self.log_area.clear()
        self.btn_start.setEnabled(False)
        
        enable_validation = self.validate_checkbox.isChecked()
        self.worker = ScanWorker(url, enable_validation)
        self.worker.log.connect(self.log_area.append)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()
        
    def scan_finished(self, session_id):
        self.btn_start.setEnabled(True)
        if session_id:
            self.log_area.append(f"扫描完成! 会话 ID: {session_id}")
        else:
            self.log_area.append("扫描失败")

class ResultsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>扫描结果</h2>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["类型", "文本", "验证状态", "状态码/可点击", "响应时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.btn_refresh = QPushButton("刷新最近数据")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)
        
        self.storage = StorageManager()
        
    def load_data(self):
        # Load last session for demo
        sessions = self.storage.get_recent_sessions(1)
        if not sessions:
            return
            
        session = sessions[0]
        elements = self.storage.get_elements_by_session(session.id)
        
        self.table.setRowCount(len(elements))
        for i, el in enumerate(elements):
            self.table.setItem(i, 0, QTableWidgetItem(el.type))
            self.table.setItem(i, 1, QTableWidgetItem(el.text[:30] + "..." if el.text and len(el.text) > 30 else (el.text or "")))
            
            # 验证状态
            if el.validated:
                status_text = "✅ 已验证"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(Qt.darkGreen)
            else:
                status_text = "⚪ 未验证"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(Qt.gray)
            self.table.setItem(i, 2, status_item)
            
            # 状态码或可点击性
            if el.type == 'a' and el.status_code is not None:
                status_code_item = QTableWidgetItem(str(el.status_code))
                if 200 <= el.status_code < 300:
                    status_code_item.setForeground(Qt.darkGreen)
                elif 300 <= el.status_code < 400:
                    status_code_item.setForeground(Qt.darkYellow)
                else:
                    status_code_item.setForeground(Qt.red)
                self.table.setItem(i, 3, status_code_item)
            elif el.clickable is not None:
                clickable_text = "✅ 可点击" if el.clickable else "❌ 不可点击"
                clickable_item = QTableWidgetItem(clickable_text)
                clickable_item.setForeground(Qt.darkGreen if el.clickable else Qt.red)
                self.table.setItem(i, 3, clickable_item)
            else:
                self.table.setItem(i, 3, QTableWidgetItem("-"))
            
            # 响应时间
            if el.response_time is not None:
                time_text = f"{el.response_time:.2f}s"
                self.table.setItem(i, 4, QTableWidgetItem(time_text))
            else:
                self.table.setItem(i, 4, QTableWidgetItem("-"))
            
            # 操作按钮
            btn_analyze = QPushButton("AI 分析")
            btn_analyze.clicked.connect(lambda checked, e=el: self.analyze_element(e))
            self.table.setCellWidget(i, 5, btn_analyze)
            
    def analyze_element(self, element):
        from PySide6.QtWidgets import QMessageBox
        
        # In a real app, you'd want to get the key from settings or a dialog
        # For now, we assume it's in env or we prompt/warn
        client = AIClient() 
        if not client.client:
            QMessageBox.warning(self, "缺少 API Key", "请设置 OPENAI_API_KEY 环境变量或在代码中配置。")
            return

        self.btn_refresh.setEnabled(False)
        # Use a thread or async to avoid freezing UI, but for simple demo:
        QMessageBox.information(self, "分析中", "正在请求 AI 分析，请稍候...")
        
        report = client.analyze_element({
            "type": element.type,
            "text": element.text,
            "href": element.href,
            "selector": element.selector
        })
        
        # Save report to DB
        self.storage.save_report(report, session_id=element.session.id, element_id=element.id)
        
        QMessageBox.information(self, "分析报告", report)
        self.btn_refresh.setEnabled(True)
