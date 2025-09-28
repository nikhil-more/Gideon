from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from .ui_helper import update_to_colored_frame, create_circle_widget

class SystemVitalsWindow(QFrame):
	def __init__(self):
		super().__init__()
		self.setup()

		# === Timers for Real-Time Updates ===
		# self.stats_timer = QTimer()
		# self.stats_timer.timeout.connect(self.update_system_stats)
		# self.stats_timer.start(1000)  # every 1 second

	def setup(self):
		update_to_colored_frame(self, "#003f88", 120)
		sys_layout = QHBoxLayout(self)

		# CPU, RAM, GPU
		left_stats_layout = QVBoxLayout()
		self.cpu_circle, cpu_widget = create_circle_widget("CPU", "0%")
		self.ram_circle, ram_widget = create_circle_widget("RAM", "0%")
		self.gpu_circle, gpu_widget = create_circle_widget("GPU", "0%")

		left_stats_layout.addLayout(cpu_widget)
		left_stats_layout.addLayout(ram_widget)
		left_stats_layout.addLayout(gpu_widget)

		# Temperature & Fan Speed
		right_stats_layout = QVBoxLayout()
		self.temp_label = QLabel("Temp : <b>--</b>")
		self.fan_label = QLabel("Fan Speed : <b>--</b>")

		for label in [self.temp_label, self.fan_label]:
			label.setStyleSheet("color: white; font-size: 14px;")
			right_stats_layout.addWidget(label)

		sys_layout.addLayout(left_stats_layout)
		sys_layout.addStretch()
		sys_layout.addLayout(right_stats_layout)



	def update_system_stats(self):
		self.cpu_circle.setText(f"{psutil.cpu_percent()}%")
		self.ram_circle.setText(f"{psutil.virtual_memory().percent}%")

		# Try GPU (optional)
		try:
			gpus = GPUtil.getGPUs()
			if gpus:
				self.gpu_circle.setText(f"{int(gpus[0].load * 100)}%")
			else:
				self.gpu_circle.setText("N/A")
		except Exception:
			self.gpu_circle.setText("N/A")

		# Temperature and fan speed
		try:
			temps = psutil.sensors_temperatures()
			fans = psutil.sensors_fans()

			# Temperature
			found_temp = False
			for name, entries in temps.items():
				for entry in entries:
					if hasattr(entry, 'current'):
						self.temp_label.setText(f"Temp : <b>{int(entry.current)}°C</b>")
						found_temp = True
						break
				if found_temp:
					break
			if not found_temp:
				self.temp_label.setText("Temp : <b>N/A</b>")

			# Fan Speed
			found_fan = False
			for fan_group in fans.values():
				for fan in fan_group:
					if hasattr(fan, 'current') and fan.current is not None:
						self.fan_label.setText(f"Fan Speed : <b>{int(fan.current)}</b>")
						found_fan = True
						break
				if found_fan:
					break
			if not found_fan:
				self.fan_label.setText("Fan Speed : <b>N/A</b>")

		except Exception:
			self.temp_label.setText("Temp : <b>Error</b>")
			self.fan_label.setText("Fan Speed : <b>Error</b>")
