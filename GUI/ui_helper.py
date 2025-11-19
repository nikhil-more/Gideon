from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def create_colored_frame(color, min_height=50):
	frame = QFrame()
	frame.setAutoFillBackground(True)
	palette = frame.palette()
	palette.setColor(QPalette.ColorRole.Window, QColor(color))
	frame.setPalette(palette)
	frame.setMinimumHeight(min_height)
	return frame

def update_to_colored_frame(frame:QFrame, color, min_height=50):
	frame.setAutoFillBackground(True)
	palette = frame.palette()
	palette.setColor(QPalette.ColorRole.Window, QColor(color))
	frame.setPalette(palette)
	frame.setMinimumHeight(min_height)

def create_circle_widget(label_text, initial_value):
	layout = QVBoxLayout()
	circle = QLabel(initial_value)
	circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
	circle.setFixedSize(60, 60)
	circle.setStyleSheet("""
	    background-color: #f7b2f0;
	    border-radius: 30px;
	    font-weight: bold;
	    color: #333;
	    border: 3px solid white;
	""")
	label = QLabel(label_text)
	label.setAlignment(Qt.AlignmentFlag.AlignCenter)
	label.setStyleSheet("color: white; font-size: 12px;")

	layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)
	layout.addWidget(label)

	return circle, layout
