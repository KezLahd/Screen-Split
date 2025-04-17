import sys
import cv2
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox,
                           QProgressBar, QSplashScreen, QScrollArea, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QIcon
import win32gui
import win32con
import time
import numpy
from mss import mss
import threading
from queue import Queue
import concurrent.futures
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.camera = None
        self._lock = threading.Lock()
        
    def run(self):
        try:
            self.status_updated.emit("Initializing camera...")
            
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.camera.isOpened():
                self.error_occurred.emit("Could not open camera")
                return
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            for _ in range(5):
                self.camera.read()
            
            while self.running:
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(qt_image)
                else:
                    self.error_occurred.emit("Failed to read camera frame")
                    break
                    
        except Exception as e:
            self.error_occurred.emit(f"Camera error: {str(e)}")
        finally:
            with self._lock:
                if self.camera:
                    self.camera.release()
                    self.camera = None
                    
    def stop(self):
        self.running = False
        with self._lock:
            if self.camera:
                self.camera.release()
                self.camera = None

class ScreenCaptureThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.monitor_index = 0
        self.sct = None
        self._lock = threading.Lock()
        
    def run(self):
        try:
            self.sct = mss()
            monitors = self.sct.monitors
            
            if self.monitor_index + 1 >= len(monitors):
                self.error_occurred.emit(f"Invalid monitor index: {self.monitor_index}")
                return
            
            monitor = monitors[self.monitor_index + 1]
            
            monitor_settings = {
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height'] - 58
            }
            
            last_capture_time = 0
            frame_interval = 1.0 / 30
            
            while self.running:
                current_time = time.time()
                if current_time - last_capture_time >= frame_interval:
                    try:
                        screenshot = self.sct.grab(monitor_settings)
                        frame = numpy.array(screenshot)
                        height, width = frame.shape[:2]
                        bytes_per_line = width * 4
                        
                        qt_image = QImage(
                            frame.data,
                            width,
                            height,
                            bytes_per_line,
                            QImage.Format.Format_ARGB32
                        )
                        
                        if self.running:
                            self.frame_ready.emit(qt_image)
                            last_capture_time = current_time
                    except Exception as e:
                        if self.running:
                            self.error_occurred.emit(f"Frame capture error: {str(e)}")
                            time.sleep(0.1)
                else:
                    time.sleep(0.001)
        except Exception as e:
            if self.running:
                self.error_occurred.emit(f"Screen capture error: {str(e)}")
        finally:
            if self.sct:
                try:
                    self.sct.close()
                except:
                    pass
                self.sct = None
            self.running = False
            
    def stop(self):
        self.running = False
        if self.sct:
            try:
                self.sct.close()
            except:
                pass
            self.sct = None

class ScreenSplitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Split Application")
        self.setup_ui()
        
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Screen capture display
        self.screen_display = QLabel()
        self.screen_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_display.setText("Screen capture disabled")
        left_layout.addWidget(self.screen_display)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # Camera container
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setSpacing(2)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        
        # Camera display
        self.camera_display = QLabel()
        self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_display.setText("Camera disabled")
        camera_layout.addWidget(self.camera_display)
        
        # Camera toolbar
        camera_toolbar = QWidget()
        camera_toolbar.setFixedHeight(40)
        camera_toolbar.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        toolbar_layout = QHBoxLayout(camera_toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(0)
        
        # Create camera icon
        camera_icon = QPixmap(30, 30)
        camera_icon.fill(Qt.GlobalColor.transparent)
        painter = QPainter(camera_icon)
        painter.setPen(QColor("#cccccc"))
        painter.setBrush(QColor("#cccccc"))
        
        # Draw camera body
        painter.drawRect(5, 8, 20, 14)
        # Draw camera lens
        painter.drawEllipse(10, 11, 8, 8)
        # Draw camera top
        points = [
            QPoint(8, 8),
            QPoint(12, 4),
            QPoint(18, 4),
            QPoint(22, 8)
        ]
        painter.drawPolygon(points)
        painter.end()
        
        # Camera toggle button
        self.camera_toggle = QPushButton()
        self.camera_toggle.setFixedSize(30, 30)
        self.camera_toggle.setIcon(QIcon(camera_icon))
        self.camera_toggle.setIconSize(QSize(20, 20))
        self.camera_toggle.clicked.connect(self.toggle_camera)
        toolbar_layout.addWidget(self.camera_toggle, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add toolbar to camera container
        camera_layout.addWidget(camera_toolbar)
        
        # Add camera container to right layout
        right_layout.addWidget(camera_container)
        
        # Logo display
        self.logo_display = QLabel()
        self.logo_display.setText("BRAND LOGO")
        self.logo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_display.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.logo_display, 1)
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        
        # Set up main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.splitter)
        
        # Initialize other variables
        self.camera_thread = None
        self.camera_enabled = False
        
    def toggle_camera(self):
        if not self.camera_enabled:
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self.update_camera_frame)
            self.camera_thread.error_occurred.connect(self.handle_camera_error)
            self.camera_thread.status_updated.connect(self.update_camera_status)
            self.camera_thread.start()
            self.camera_enabled = True
            self.camera_toggle.setStyleSheet("background-color: #0078D4;")
        else:
            self.camera_enabled = False
            self.camera_toggle.setStyleSheet("")
            self.camera_display.clear()
            self.camera_display.setText("Camera disabled")
            if self.camera_thread:
                self.camera_thread.running = False
                self.camera_thread = None
                
    def update_camera_frame(self, qt_image):
        """Update camera frame with center zoom and height fitting"""
        try:
            if not self.camera_display:
                return

            container_width = self.camera_display.width()
            container_height = self.camera_display.height()
            
            original_pixmap = QPixmap.fromImage(qt_image)
            scale_factor = container_height / original_pixmap.height()
            
            new_width = int(original_pixmap.width() * scale_factor)
            new_height = container_height
            
            scaled_pixmap = original_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            if scaled_pixmap.width() > container_width:
                x_offset = (scaled_pixmap.width() - container_width) // 2
                crop_rect = QRect(x_offset, 0, container_width, container_height)
                cropped_pixmap = scaled_pixmap.copy(crop_rect)
                self.camera_display.setPixmap(cropped_pixmap)
            else:
                self.camera_display.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error updating camera frame: {str(e)}")

    def handle_camera_error(self, error_msg):
        QMessageBox.warning(self, "Camera Error", error_msg)
        self.camera_enabled = False
        self.camera_toggle.setStyleSheet("")
        self.camera_display.setText("Camera error")
        
    def update_camera_status(self, status):
        if not self.camera_enabled:
            return
            
        if status == "Initializing camera...":
            self.countdown_value = 3
            self.countdown_timer = QTimer()
            self.countdown_timer.timeout.connect(self.update_countdown)
            self.countdown_timer.start(1000)
            self.camera_display.setText(f"Camera starting in {self.countdown_value}...")
        else:
            self.camera_display.setText(status)

if __name__ == '__main__':
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("Created QApplication")
        window = ScreenSplitApp()
        print("Created window")
        window.show()
        print("Showed window")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        print("Full error traceback:")
        traceback.print_exc()
        sys.exit(1) 