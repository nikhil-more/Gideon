from PyQt6.QtWidgets import QApplication, QWidget, QApplication, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPalette, QColor
from datetime import datetime
import sys

class TitleWindow(QFrame):
	def __init__(self):
		super().__init__()
		self.setup()

	def setup(self):
		self.setAutoFillBackground(True)
		palette = self.palette()
		palette.setColor(QPalette.ColorRole.Window, QColor("#9b5de5"))
		self.setPalette(palette)
		self.setFixedHeight(60)

		top_layout = QHBoxLayout(self)
		gideon_label = QLabel("GIDEON")
		gideon_label.setStyleSheet(
			"background-color: #003f88; color: white; padding: 10px; font-weight: bold; font-size: 18px;")
		gideon_label.setFixedWidth(200)
		gideon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.date_label = QLabel()
		self.date_label.setStyleSheet("background-color: #003f88; color: white; padding: 10px;")
		self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.update_date()

		top_layout.addWidget(gideon_label)
		top_layout.addStretch()
		top_layout.addWidget(self.date_label)

	def update_date(self):
		now = datetime.now()
		self.date_label.setText(now.strftime("%A, %d-%m-%Y"))

if __name__=="__main__":
	app = QApplication(sys.argv)
	title = TitleWindow()
	title.show()
	app.exec()