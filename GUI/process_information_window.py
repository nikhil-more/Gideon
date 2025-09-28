from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt


from .ui_helper import update_to_colored_frame, create_colored_frame

class ProcessInformationWindow(QFrame):
	def __init__(self):
		super().__init__()
		self.setup()

	def setup(self):
		update_to_colored_frame(self, "#60d6e6")
		cyan_layout = QVBoxLayout(self)

		green_dot = QLabel()
		green_dot.setFixedSize(15, 15)
		green_dot.setStyleSheet("background-color: #06d6a0; border-radius: 7px;")
		cyan_layout.addWidget(green_dot, alignment=Qt.AlignmentFlag.AlignRight)

		orange_panel = create_colored_frame("#faae4b")
		status_layout = QVBoxLayout(orange_panel)
		statuses = [
				"Listening to command ...",
				"Analyzing the task ....",
				"Opening YouTube for you ....",
				"Playing the required video for you ....."
		]
		for text in statuses:
			label = QLabel(f"> {text}")
			label.setStyleSheet("color: white; font-size: 13px;")
			status_layout.addWidget(label)

		cyan_layout.addWidget(orange_panel)