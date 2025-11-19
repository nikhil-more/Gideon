from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
from .title_window import TitleWindow
from .conversation_window import ConversationWindow
from .process_information_window import ProcessInformationWindow
from .system_vitals_window import SystemVitalsWindow

class MainWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Gideon Enhanced UI")
		self.setGeometry(60, 60, 1300, 700)

		main_layout = QHBoxLayout(self)

		# ========== LEFT SECTION ==========
		left_layout = QVBoxLayout()

		# Top bar with name and date
		title_window = TitleWindow()

		# Scrollable yellow chat area
		conversation_window = ConversationWindow()

		left_layout.addWidget(title_window)
		left_layout.addWidget(conversation_window)

		# ========== RIGHT SECTION ==========
		right_layout = QVBoxLayout()

		# Cyan Panel (Status + Green Dot)
		process_information_window = ProcessInformationWindow()

		# System Panel
		system_vitals_window = SystemVitalsWindow()

		right_layout.addWidget(process_information_window, 3)
		right_layout.addWidget(system_vitals_window, 1)
		# === Final Assembly ===
		main_layout.addLayout(left_layout, 3)
		main_layout.addLayout(right_layout, 1)