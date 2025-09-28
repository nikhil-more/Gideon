import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QHBoxLayout

what = ["what is", "what's", "whats", "wht"]
DEFAULT = "~/Documents/workspace/"
gideon = ['gideon', 'didion', 'vdo', 'video']


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		print("\nVirtual Assistant Initialized")
		print("\n...............................\n")
		self.processed = False

	def setup(self):
		window = QWidget(self)
		self.setCentralWidget(window)
		window.setStyleSheet('background-color : rgb(0, 0, 0)')
		self.setGeometry(100, 50, 1680, 900)
		self.setWindowTitle("Gideon-Virtual Assistant")
		# self.setWindowIcon(QIcon("img/gideon_icon.jpg"))
		self.setMinimumWidth(1000)
		hbox = QHBoxLayout()
		self.create_sections()
		hbox.addWidget(self.first_section)
		hbox.addWidget(self.second_section)
		hbox.addWidget(self.third_section)
		window.setLayout(hbox)
		self.initialize_helpers()
		print("Initialization Complete")
		print("\n................................\n")

	def create_sections(self):
		self.first_section = QWidget(self)
		self.first_section.setStyleSheet('background-color : rgb(175,175,175)')
		self.first_section.setMaximumWidth(350)
		self.second_section = QWidget()
		self.second_section.setStyleSheet('background-color : rgb(128, 255, 170)')
		self.third_section = QWidget()
		self.third_section.setStyleSheet('background-color : rgb(255, 255, 128)')
		self.third_section.setMaximumWidth(350)
		self.third_section.setMinimumWidth(350)

	def initialize_helpers(self):
		pass


if __name__ == "__main__":
	app = QApplication(sys.argv)

	mainWindow = MainWindow()
	mainWindow.setup()
	mainWindow.show()

	app.exec()