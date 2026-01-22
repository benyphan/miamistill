import sys
import subprocess
import time
import math

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotline Miami Menu")
        self.setGeometry(100, 100, 1024, 640)
        self.setStyleSheet("background-color: rgb(30,0,60);")

        self.title = QLabel("HOTLINE MIAMI", self)
        self.title.setFont(QFont("Arial", 48))
        self.title.setStyleSheet("color: orange;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setGeometry(0, 50, 1024, 100)

        self.start_btn = QPushButton("START GAME", self)
        self.start_btn.setGeometry(362, 250, 300, 60)
        self.start_btn.setFont(QFont("Arial", 24))
        self.start_btn.setStyleSheet(self.button_style(normal=True))
        self.start_btn.clicked.connect(self.start_game)

        self.exit_btn = QPushButton("EXIT", self)
        self.exit_btn.setGeometry(362, 350, 300, 60)
        self.exit_btn.setFont(QFont("Arial", 24))
        self.exit_btn.setStyleSheet(self.button_style(normal=True))
        self.exit_btn.clicked.connect(self.close)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_hover)
        self.timer.start(16)

    def button_style(self, normal=True, alpha=255):
        if normal:
            return "background-color: rgb(255,105,180); color: white; border: none;"
        else:
            return f"background-color: rgba(255,20,147,{alpha}); color: white; border: none;"

    def update_hover(self):
        t = time.time()
        for btn in [self.start_btn, self.exit_btn]:
            if btn.underMouse():
                alpha = int((math.sin(t * 6) + 1) / 2 * 255)
                btn.setStyleSheet(self.button_style(normal=False, alpha=alpha))
            else:
                btn.setStyleSheet(self.button_style(normal=True))

    def start_game(self):
        self.close()
        # запускаем игру отдельным процессом
        subprocess.Popen([sys.executable, "main.py"])

    def run(self):
        app = QApplication(sys.argv)
        self.show()
        sys.exit(app.exec())
