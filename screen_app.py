import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import win32gui
import win32con
from PIL import ImageGrab

class ScreenSplitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Split Application")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Left side - Windows application display
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Window selection dropdown
        self.window_combo = QComboBox()
        self.refresh_windows()
        left_layout.addWidget(self.window_combo)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Windows")
        refresh_btn.clicked.connect(self.refresh_windows)
        left_layout.addWidget(refresh_btn)
        
        # Application display area
        self.app_display = QLabel()
        self.app_display.setMinimumSize(600, 600)
        self.app_display.setStyleSheet("border: 2px solid black;")
        left_layout.addWidget(self.app_display)
        
        # Right side - Camera and logo
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Camera display
        self.camera_display = QLabel()
        self.camera_display.setMinimumSize(500, 400)
        self.camera_display.setStyleSheet("border: 2px solid black;")
        right_layout.addWidget(self.camera_display)
        
        # Logo display
        self.logo_display = QLabel()
        self.logo_display.setMinimumSize(500, 150)
        self.logo_display.setStyleSheet("border: 2px solid black;")
        right_layout.addWidget(self.logo_display)
        
        # Add widgets to main layout
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Error: Could not open camera")
            return
            
        # Setup timers
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera)
        self.camera_timer.start(30)  # 30ms = ~33fps
        
        self.app_timer = QTimer()
        self.app_timer.timeout.connect(self.update_app_display)
        self.app_timer.start(100)  # 100ms = 10fps
        
        # Load logo (you'll need to add your logo file)
        self.load_logo()
        
    def refresh_windows(self):
        self.window_combo.clear()
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    self.window_combo.addItem(title, hwnd)
        
        win32gui.EnumWindows(winEnumHandler, None)
        
    def update_camera(self):
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.camera_display.setPixmap(QPixmap.fromImage(qt_image))
            
    def update_app_display(self):
        hwnd = self.window_combo.currentData()
        if hwnd:
            try:
                # Get window position and size
                rect = win32gui.GetWindowRect(hwnd)
                x, y, width, height = rect
                
                # Capture the window
                screenshot = ImageGrab.grab(bbox=(x, y, width, height))
                screenshot = screenshot.convert('RGB')
                
                # Convert to QImage
                img_data = screenshot.tobytes("raw", "RGB")
                qim = QImage(img_data, screenshot.size[0], screenshot.size[1], QImage.Format.Format_RGB888)
                
                # Scale to fit display
                pixmap = QPixmap.fromImage(qim)
                scaled_pixmap = pixmap.scaled(self.app_display.size(), Qt.AspectRatioMode.KeepAspectRatio)
                self.app_display.setPixmap(scaled_pixmap)
            except Exception as e:
                print(f"Error capturing window: {e}")
                
    def load_logo(self):
        # TODO: Add your logo file and update this method
        # For now, we'll just display a placeholder text
        self.logo_display.setText("LOGO PLACEHOLDER")
        self.logo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def closeEvent(self, event):
        self.camera.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScreenSplitApp()
    window.show()
    sys.exit(app.exec()) 