from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QScrollArea
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class ConversationWindow(QFrame):
	def __init__(self):
		super().__init__()
		self.setup()

	def setup(self):
		scroll_palette = self.palette()
		scroll_palette.setColor(QPalette.ColorRole.Window, QColor("#ffd60a"))
		self.setPalette(scroll_palette)

		self.chat_layout = QVBoxLayout()
		self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		# Example chat
		example_chats = [
				("Gideon", "Hi sir. How can I help you", "#003f88"),
				("User", "Help me with information about Nicola Tesla", "#4d00b4"),
				("Gideon", """Nikola Tesla<sup>[a]</sup> (10 July 1856 – 7 January 1943) was a Serbian-American engineer, <b>futurist</b>, and inventor. 
		He is known for his contributions to the design of the modern <i>alternating current</i> (AC) <a href='#'>electricity supply system</a>.""",
				 "#003f88"),
				("User", "What is 2 * 3", "#4d00b4"),
				("", "Generating answer for you .............................................", "#f20089"),
		]

		for sender, msg, color in example_chats:
			label = QLabel()
			label.setWordWrap(True)
			if sender:
				label.setText(
					f"<b><span style='color:{color}'>{sender}:</span></b> <span style='color:#024'> {msg}</span>")
			else:
				label.setText(f"<span style='color:{color}'>{msg}</span>")
			self.chat_layout.addWidget(label)

		# Scroll Area
		scroll_area_widget = QWidget()
		scroll_area_widget.setLayout(self.chat_layout)

		scroll_area = QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_area.setWidget(scroll_area_widget)

		scroll_frame_layout = QVBoxLayout(self)
		scroll_frame_layout.addWidget(scroll_area)