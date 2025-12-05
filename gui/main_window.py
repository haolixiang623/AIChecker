from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from gui.views import DashboardView, ScanView, ResultsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIChecker - 智能网页巡检")
        self.resize(1000, 700)
        
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
        
        for btn in [self.btn_dashboard, self.btn_scan, self.btn_results]:
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
        
        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.scan_view)
        self.stack.addWidget(self.results_view)
        
        # Signals
        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.btn_scan.clicked.connect(lambda: self.stack.setCurrentWidget(self.scan_view))
        self.btn_results.clicked.connect(lambda: self.stack.setCurrentWidget(self.results_view))
        
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
