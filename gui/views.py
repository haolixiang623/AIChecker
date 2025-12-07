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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["类型", "文本", "链接地址", "验证状态", "状态描述", "响应时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.btn_refresh = QPushButton("刷新最近数据")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)
        
        self.storage = StorageManager()
        
    def load_data(self):
        from utils.status_codes import get_status_description, get_status_color
        
        # Load last session for demo
        sessions = self.storage.get_recent_sessions(1)
        if not sessions:
            return
            
        session = sessions[0]
        elements = self.storage.get_elements_by_session(session.id)
        
        self.table.setRowCount(len(elements))
        for i, el in enumerate(elements):
            # 类型
            self.table.setItem(i, 0, QTableWidgetItem(el.type))
            
            # 文本（截断显示）
            text_display = el.text[:30] + "..." if el.text and len(el.text) > 30 else (el.text or "")
            text_item = QTableWidgetItem(text_display)
            if el.text and len(el.text) > 30:
                text_item.setToolTip(el.text)  # 完整文本作为提示
            self.table.setItem(i, 1, text_item)
            
            # 链接地址（完整显示）
            if el.href:
                href_item = QTableWidgetItem(el.href)
                href_item.setToolTip(el.href)
                self.table.setItem(i, 2, href_item)
            else:
                self.table.setItem(i, 2, QTableWidgetItem("-"))
            
            # 验证状态
            if el.validated:
                status_text = "✅ 已验证"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(Qt.darkGreen)
            else:
                status_text = "⚪ 未验证"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(Qt.gray)
            self.table.setItem(i, 3, status_item)
            
            # 状态描述（使用新的工具函数）
            if el.type == 'a' and el.status_code is not None:
                status_desc = get_status_description(el.status_code)
                status_item = QTableWidgetItem(status_desc)
                status_item.setForeground(get_status_color(el.status_code))
                if el.validation_error:
                    status_item.setToolTip(f"错误: {el.validation_error}")
                self.table.setItem(i, 4, status_item)
            elif el.clickable is not None:
                clickable_text = "✅ 可点击" if el.clickable else "❌ 不可点击"
                clickable_item = QTableWidgetItem(clickable_text)
                clickable_item.setForeground(Qt.darkGreen if el.clickable else Qt.red)
                if el.validation_error:
                    clickable_item.setToolTip(f"错误: {el.validation_error}")
                self.table.setItem(i, 4, clickable_item)
            else:
                self.table.setItem(i, 4, QTableWidgetItem("-"))
            
            # 响应时间
            if el.response_time is not None:
                time_text = f"{el.response_time:.2f}s"
                self.table.setItem(i, 5, QTableWidgetItem(time_text))
            else:
                self.table.setItem(i, 5, QTableWidgetItem("-"))
            
            # 操作按钮
            btn_analyze = QPushButton("AI 分析")
            btn_analyze.clicked.connect(lambda checked, e=el: self.analyze_element(e))
            self.table.setCellWidget(i, 6, btn_analyze)

            
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


class ScanHistoryView(QWidget):
    """扫描历史记录视图 - 显示最近50次扫描"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>扫描历史</h2>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "目标URL", "开始时间", "持续时间", "状态", "元素数", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # 按钮行
        from PySide6.QtWidgets import QHBoxLayout
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.clicked.connect(self.load_history)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.storage = StorageManager()
        self.load_history()
        
    def load_history(self):
        """加载最近50次扫描记录"""
        sessions = self.storage.get_recent_sessions(50)
        
        self.table.setRowCount(len(sessions))
        for i, session in enumerate(sessions):
            # ID
            self.table.setItem(i, 0, QTableWidgetItem(str(session.id)))
            
            # URL
            url_item = QTableWidgetItem(session.url)
            url_item.setToolTip(session.url)
            self.table.setItem(i, 1, url_item)
            
            # 开始时间（相对时间）
            time_str = self._format_relative_time(session.start_time)
            self.table.setItem(i, 2, QTableWidgetItem(time_str))
            
            # 持续时间
            duration = session.get_duration()
            if duration:
                duration_str = f"{duration:.1f}秒"
            else:
                duration_str = "进行中" if session.status == 'pending' else "-"
            self.table.setItem(i, 3, QTableWidgetItem(duration_str))
            
            # 状态
            status_item = QTableWidgetItem(session.status)
            if session.status == 'completed':
                status_item.setForeground(Qt.darkGreen)
            elif session.status == 'failed':
                status_item.setForeground(Qt.red)
            else:
                status_item.setForeground(QColor(200, 150, 0))
            self.table.setItem(i, 4, status_item)
            
            # 元素数
            element_count = session.get_element_count()
            self.table.setItem(i, 5, QTableWidgetItem(str(element_count)))
            
            # 操作按钮
            btn_view = QPushButton("查看详情")
            btn_view.clicked.connect(lambda checked, sid=session.id: self.view_session_details(sid))
            self.table.setCellWidget(i, 6, btn_view)
    
    def _format_relative_time(self, dt):
        """格式化相对时间"""
        import datetime
        now = datetime.datetime.now()
        delta = now - dt
        
        if delta.days > 7:
            return dt.strftime("%Y-%m-%d %H:%M")
        elif delta.days > 1:
            return f"{delta.days}天前"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours}小时前"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
    
    def view_session_details(self, session_id):
        """查看会话详情"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        # 获取会话摘要
        summary = self.storage.get_session_summary(session_id)
        
        # 创建对话框显示详情
        dialog = QDialog(self)
        dialog.setWindowTitle(f"扫描会话 #{session_id} 详情")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        duration_text = f"{summary['duration']:.2f}秒" if summary['duration'] else '未完成'
        
        details = f"""
扫描会话详情
{'='*50}

URL: {summary['url']}
开始时间: {summary['start_time']}
结束时间: {summary['end_time'] or '未完成'}
状态: {summary['status']}
持续时间: {duration_text}

元素统计
{'='*50}
总元素数: {summary['total_elements']}
已验证元素: {summary['validated_elements']}

链接统计
{'-'*50}
链接总数: {summary['link_total']}
正常链接 (2xx): {summary['link_ok']}
错误链接 (4xx/5xx): {summary['link_error']}

按钮统计
{'-'*50}
按钮总数: {summary['button_total']}
可点击按钮: {summary['button_clickable']}
"""

        text_edit.setPlainText(details)
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec()


class AIAnalysisWorker(QThread):
    """AI批量分析工作线程"""
    finished = Signal(str)
    progress = Signal(int, str)
    error = Signal(str)
    
    def __init__(self, session_id, storage):
        super().__init__()
        self.session_id = session_id
        self.storage = storage
    
    def run(self):
        try:
            from ai.client import AIClient
            
            # 获取会话数据
            summary = self.storage.get_session_summary(self.session_id)
            elements = self.storage.get_elements_by_session(self.session_id)
            
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
            
            # 调用AI分析
            client = AIClient()
            if not client.client:
                self.error.emit("AI客户端未初始化，请设置OPENAI_API_KEY环境变量")
                return
            
            report = client.analyze_session(summary, elements_data, self.progress.emit)
            
            # 保存报告
            self.storage.save_report(report, session_id=self.session_id)
            
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(f"分析过程出错: {str(e)}")


class AIAnalysisView(QWidget):
    """AI批量分析视图"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>AI 批量分析</h2>"))
        
        # 会话选择区
        from PySide6.QtWidgets import QHBoxLayout, QComboBox
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("选择扫描会话:"))
        
        self.session_combo = QComboBox()
        selection_layout.addWidget(self.session_combo)
        
        self.btn_analyze = QPushButton("开始分析")
        self.btn_analyze.clicked.connect(self.start_analysis)
        selection_layout.addWidget(self.btn_analyze)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)
        
        # 报告显示区
        layout.addWidget(QLabel("<h3>分析报告</h3>"))
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
        
        # 导出按钮
        self.btn_export = QPushButton("导出报告")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        layout.addWidget(self.btn_export)
        
        self.storage = StorageManager()
        self.current_report = ""
        self.load_sessions()
    
    def load_sessions(self):
        """加载最近的扫描会话到下拉列表"""
        sessions = self.storage.get_recent_sessions(20)
        self.session_combo.clear()
        
        for session in sessions:
            display_text = f"#{session.id} - {session.url[:50]} - {session.start_time.strftime('%Y-%m-%d %H:%M')}"
            self.session_combo.addItem(display_text, session.id)
    
    def start_analysis(self):
        """开始批量分析"""
        if self.session_combo.currentIndex() < 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先选择一个扫描会话")
            return
        
        session_id = self.session_combo.currentData()
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备分析...")
        self.btn_analyze.setEnabled(False)
        self.report_text.clear()
        
        # 启动工作线程
        self.worker = AIAnalysisWorker(session_id, self.storage)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.error.connect(self.analysis_error)
        self.worker.start()
    
    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def analysis_finished(self, report):
        """分析完成"""
        self.current_report = report
        self.report_text.setMarkdown(report)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("分析完成!")
        self.btn_analyze.setEnabled(True)
        self.btn_export.setEnabled(True)
    
    def analysis_error(self, error_msg):
        """分析出错"""
        from PySide6.QtWidgets import QMessageBox
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.btn_analyze.setEnabled(True)
        QMessageBox.critical(self, "错误", error_msg)
    
    def export_report(self):
        """导出报告"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存AI分析报告",
            "",
            "Markdown文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_report)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "成功", f"报告已导出到: {file_path}")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

