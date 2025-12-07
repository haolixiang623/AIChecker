from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from gui.views import DashboardView, ScanView, ResultsView, ScanHistoryView, AIAnalysisView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIChecker - 智能网页巡检")
        self.resize(1200, 800)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #f0f0f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        
        self.btn_dashboard = QPushButton("仪表盘")
        self.btn_scan = QPushButton("新建扫描")
        self.btn_results = QPushButton("扫描结果")
        self.btn_history = QPushButton("扫描历史")
        self.btn_ai_analysis = QPushButton("AI 分析")
        
        for btn in [self.btn_dashboard, self.btn_scan, self.btn_results, 
                    self.btn_history, self.btn_ai_analysis]:
            btn.setFixedHeight(40)
            sidebar_layout.addWidget(btn)
            
        main_layout.addWidget(sidebar)
        
        # Content Area
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Views
        self.dashboard_view = DashboardView()
        self.scan_view = ScanView()
        self.results_view = ResultsView()
        self.history_view = ScanHistoryView()
        self.ai_analysis_view = AIAnalysisView()
        
        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.scan_view)
        self.stack.addWidget(self.results_view)
        self.stack.addWidget(self.history_view)
        self.stack.addWidget(self.ai_analysis_view)
        
        # Signals
        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.btn_scan.clicked.connect(lambda: self.stack.setCurrentWidget(self.scan_view))
        self.btn_results.clicked.connect(lambda: self.stack.setCurrentWidget(self.results_view))
        self.btn_history.clicked.connect(lambda: self._show_history())
        self.btn_ai_analysis.clicked.connect(lambda: self._show_ai_analysis())
        
        # 连接扫描完成信号
        self.scan_view.scan_completed.connect(self._on_scan_completed)

        
        # Style
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def _show_history(self):
        """显示扫描历史并刷新数据"""
        self.history_view.load_history()
        self.stack.setCurrentWidget(self.history_view)
    
    def _show_ai_analysis(self):
        """显示AI分析并刷新会话列表"""
        self.ai_analysis_view.load_sessions()
        self.stack.setCurrentWidget(self.ai_analysis_view)
    
    def _on_scan_completed(self, session_id):
        """扫描完成后自动切换到历史视图"""
        self._show_history()

