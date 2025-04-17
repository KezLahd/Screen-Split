import sys
import cv2
import traceback
import logging
import logging.handlers
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox,
                           QProgressBar, QSplashScreen, QSizePolicy, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QIcon
import win32gui
import win32con
import win32ui
import win32api
import win32api as wapi
import time
import numpy
from mss import mss
import threading
from queue import Queue
import concurrent.futures
import os
import ctypes
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation

def setup_logging():
    # Remove all existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, 'app_debug.log')
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    return root_logger

# Set up logging
logger = setup_logging()
logger.info("=== Application Starting ===")
logger.info(f"Log file location: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_debug.log')}")
logger.info(f"Current working directory: {os.getcwd()}")

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.camera = None
        self._lock = threading.Lock()
        
    def run(self):
        try:
            self.status_updated.emit("Initializing camera...")
            logger.info("Starting camera initialization")
            
            # Try different camera indices if 0 doesn't work
            camera_opened = False
            for camera_index in range(2):  # Try first two camera indices
                logger.info(f"Attempting to open camera index {camera_index}")
                self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    camera_opened = True
                    logger.info(f"Successfully opened camera at index {camera_index}")
                    break
                else:
                    logger.warning(f"Failed to open camera at index {camera_index}")
            
            if not camera_opened:
                error_msg = "Could not open camera on any available index"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
                
            # Set camera properties
            logger.info("Setting camera properties")
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Verify camera settings
            actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera settings - Width: {actual_width}, Height: {actual_height}, FPS: {actual_fps}")
            self.status_updated.emit(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            # Warm up the camera
            logger.info("Warming up camera")
            for i in range(5):
                ret, frame = self.camera.read()
                if not ret:
                    error_msg = f"Failed to read initial camera frame (attempt {i+1})"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return
                logger.debug(f"Successfully read frame {i+1}")
                time.sleep(0.1)  # Give camera time to stabilize
                
            self.status_updated.emit("Camera ready")
            logger.info("Camera initialization complete")
            self.running = True
            last_frame_time = 0
            frame_interval = 1.0 / 30  # 30 FPS
            
            while self.running:
                current_time = time.time()
                if current_time - last_frame_time >= frame_interval:
                    ret, frame = self.camera.read()
                    if ret:
                        # Flip the frame horizontally for selfie view
                        frame = cv2.flip(frame, 1)
                        # Convert to RGB and create QImage
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_frame.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        self.frame_ready.emit(qt_image)
                        last_frame_time = current_time
                    else:
                        error_msg = "Failed to read camera frame"
                        logger.error(error_msg)
                        self.error_occurred.emit(error_msg)
                        break
                else:
                    # Sleep for a short time to prevent high CPU usage
                    time.sleep(0.001)
                    
        except Exception as e:
            error_msg = f"Camera error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.error_occurred.emit(error_msg)
        finally:
            with self._lock:
                if self.camera:
                    logger.info("Releasing camera")
                    self.camera.release()
                
    def stop(self):
        logger.info("Stopping camera thread")
        self.running = False

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        # Create a base pixmap with dark background
        pixmap = QPixmap(400, 200)
        pixmap.fill(QColor("#2b2b2b"))
        self.setPixmap(pixmap)
        
        # Create layout for splash content
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title = QLabel("Screen Split App")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add subtitle
        subtitle = QLabel("Loading application...")
        subtitle.setStyleSheet("color: #cccccc; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Add progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)
        
        # Create a widget to hold the layout
        widget = QWidget(self)
        widget.setLayout(layout)
        
    def updateProgress(self, value, message=""):
        self.progress.setValue(value)
        if message:
            self.showMessage(message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, QColor("white"))

class ScreenSplitApp(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            logger.info("Initializing ScreenSplitApp")
            self.setWindowTitle("Screen Split Application")
            
            # Initialize variables
            self.camera_thread = None
            self.camera_enabled = False
            self.selected_window = None
            self.window_handles = {}
            
            # Get display information
            self.enumerate_displays()
            
            # Set window attributes
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #000000;
                }
                QWidget {
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #333333;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #444444;
                }
                QComboBox {
                    background-color: #333333;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                    color: white;
                }
                QComboBox:hover {
                    background-color: #444444;
                }
                QComboBox QAbstractItemView {
                    background-color: #333333;
                    color: white;
                    selection-background-color: #555555;
                }
            """)
            
            # Remove frameless window flag to show title bar
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
            
            self.setup_ui()
            
        except Exception as e:
            logger.error(f"Error in __init__: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
    def enumerate_displays(self):
        try:
            logger.info("Enumerating displays")
            self.displays = []
            
            def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitor_info = win32api.GetMonitorInfo(hMonitor)
                self.displays.append({
                    'handle': hMonitor,
                    'info': monitor_info,
                    'rect': lprcMonitor
                })
                return True
            
            win32api.EnumDisplayMonitors(None, None, callback)
            logger.info(f"Found {len(self.displays)} displays")
            
        except Exception as e:
            logger.error(f"Error enumerating displays: {str(e)}")
            logger.error(traceback.format_exc())
            
    def setup_ui(self):
        try:
            logger.info("Setting up UI")
            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            
            # Create horizontal splitter
            self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
            main_layout = QHBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self.main_splitter)
            
            # Left side - Window container frame
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(0)
            
            # Window selection controls
            controls_widget = QWidget()
            controls_widget.setMaximumHeight(50)
            controls_widget.setStyleSheet("""
                QWidget {
                    background-color: #000000;
                    padding: 5px;
                }
            """)
            controls_layout = QHBoxLayout(controls_widget)
            controls_layout.setContentsMargins(5, 5, 5, 5)
            
            # Window selection combo box
            self.window_selector = QComboBox()
            self.window_selector.addItem("Select a window...")
            self.window_selector.currentIndexChanged.connect(self.on_window_selected)
            controls_layout.addWidget(self.window_selector)
            
            # Refresh windows button
            refresh_button = QPushButton("Refresh Windows")
            refresh_button.clicked.connect(self.enumerate_windows)
            controls_layout.addWidget(refresh_button)
            
            left_layout.addWidget(controls_widget)
            
            # Window container frame
            self.window_container = QWidget()
            self.window_container.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            self.window_container.setStyleSheet("""
                QWidget {
                    background-color: #000000;
                    border: 2px solid #333333;
                    border-radius: 5px;
                }
            """)
            left_layout.addWidget(self.window_container, stretch=1)
            
            # Right side - Camera and logo
            right_widget = QWidget()
            right_widget.setStyleSheet("background-color: #000000;")
            
            # Calculate minimum and maximum widths based on aspect ratios
            base_height = 400  # Base height for camera view
            min_width = int((9 * base_height) / 16)  # Minimum width for 16:9
            max_width = int((4 * base_height) / 3)   # Maximum width for 4:3
            
            right_widget.setMinimumWidth(min_width)
            right_widget.setMaximumWidth(max_width)
            
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(5, 0, 5, 5)
            
            # Camera controls
            camera_controls = QHBoxLayout()
            self.camera_toggle = QPushButton("Enable Camera")
            self.camera_toggle.clicked.connect(self.toggle_camera)
            camera_controls.addWidget(self.camera_toggle)
            right_layout.addLayout(camera_controls)
            
            # Create a widget to hold both camera and logo with equal heights
            display_widget = QWidget()
            display_layout = QVBoxLayout(display_widget)
            display_layout.setSpacing(5)
            
            # Camera display
            self.camera_display = QLabel()
            self.camera_display.setMinimumHeight(base_height)
            self.camera_display.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )
            self.camera_display.setStyleSheet("""
                QLabel {
                    border: 2px solid #333333;
                    background-color: #1a1a1a;
                    color: #CCCCCC;
                }
            """)
            self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.camera_display.setText("Camera disabled")
            display_layout.addWidget(self.camera_display)
            
            # Logo display
            self.logo_display = QLabel()
            self.logo_display.setMinimumHeight(base_height)
            self.logo_display.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )
            self.logo_display.setStyleSheet("""
                QLabel {
                    border: 2px solid #333333;
                    background-color: #1a1a1a;
                    color: #CCCCCC;
                }
            """)
            self.logo_display.setText("BRAND LOGO")
            self.logo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            display_layout.addWidget(self.logo_display)
            
            right_layout.addWidget(display_widget, stretch=1)
            
            # Add widgets to splitter
            self.main_splitter.addWidget(left_widget)
            self.main_splitter.addWidget(right_widget)
            
            # Set initial splitter sizes (2:1 ratio)
            self.main_splitter.setStretchFactor(0, 2)
            self.main_splitter.setStretchFactor(1, 1)
            
            # Style the splitter
            self.main_splitter.setStyleSheet("""
                QSplitter::handle {
                    background-color: #333333;
                    width: 2px;
                }
                QSplitter::handle:hover {
                    background-color: #555555;
                }
            """)
            
            logger.info("UI setup complete")
            
            # Start window enumeration
            self.enumerate_windows()
            
        except Exception as e:
            logger.error(f"Error in setup_ui: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def enumerate_windows(self):
        try:
            self.window_handles.clear()
            self.window_selector.clear()
            self.window_selector.addItem("Select a window...")
            
            def enum_windows_callback(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and title != "Screen Split Application" and title != "":
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            if width > 50 and height > 50:
                                self.window_handles[title] = hwnd
                                self.window_selector.addItem(title)
                        except:
                            pass
                return True
            
            win32gui.EnumWindows(enum_windows_callback, None)
            
        except Exception as e:
            logger.error(f"Error enumerating windows: {str(e)}")
            
    def on_window_selected(self, index):
        if index > 0:
            title = self.window_selector.currentText()
            hwnd = self.window_handles.get(title)
            if hwnd and win32gui.IsWindow(hwnd):
                try:
                    logger.info(f"Moving window: {title}")
                    
                    # Store original window info
                    self.original_styles = {}
                    self.original_styles[hwnd] = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    self.original_rect = win32gui.GetWindowRect(hwnd)
                    
                    # Set window style to enable moving and keyboard input
                    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    new_style = (style | win32con.WS_VISIBLE | win32con.WS_CHILD |
                               win32con.WS_TABSTOP | win32con.WS_MAXIMIZEBOX) & ~win32con.WS_MINIMIZEBOX
                    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
                    
                    # Store window info for maximize/restore
                    self.window_states = {}
                    self.window_states[hwnd] = {
                        'maximized': False,
                        'restore_rect': self.original_rect
                    }
                    
                    # Move window to container
                    win32gui.SetParent(hwnd, int(self.window_container.winId()))
                    
                    # Center the window in the container
                    container_rect = self.window_container.geometry()
                    window_rect = win32gui.GetWindowRect(hwnd)
                    window_width = window_rect[2] - window_rect[0]
                    window_height = window_rect[3] - window_rect[1]
                    
                    x = max(0, (container_rect.width() - window_width) // 2)
                    y = max(0, (container_rect.height() - window_height) // 2)
                    
                    win32gui.MoveWindow(hwnd, x, y, window_width, window_height, True)
                    
                    # Store the window handle
                    self.selected_window = hwnd
                    
                    # Set up timer to periodically check and constrain window position
                    self.constraint_timer = QTimer(self)
                    self.constraint_timer.timeout.connect(lambda: self.check_window_bounds(hwnd))
                    self.constraint_timer.start(16)  # 60 FPS check rate
                    
                    # Set focus to the window to enable keyboard input
                    win32gui.SetFocus(hwnd)
                    
                    logger.info(f"Window moved successfully")
                    
                except Exception as e:
                    logger.error(f"Error moving window: {str(e)}")
                    logger.error(traceback.format_exc())
                    QMessageBox.warning(self, "Error", f"Failed to move window: {str(e)}")
                    
    def check_window_bounds(self, hwnd):
        try:
            if not win32gui.IsWindow(hwnd):
                self.constraint_timer.stop()
                return
                
            # Get current window position and size
            window_rect = win32gui.GetWindowRect(hwnd)
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]
            
            # Get container bounds
            container_rect = self.window_container.geometry()
            container_pos = self.window_container.mapToGlobal(container_rect.topLeft())
            
            # Convert window position to container coordinates
            window_pos = win32gui.ScreenToClient(int(self.window_container.winId()), (window_rect[0], window_rect[1]))
            
            # Only constrain if the window is trying to go outside the container
            needs_constraint = False
            new_x = window_pos[0]
            new_y = window_pos[1]
            
            # Check left boundary
            if window_pos[0] < -window_width + 20:  # Allow 20px to grab
                new_x = -window_width + 20
                needs_constraint = True
                
            # Check right boundary
            if window_pos[0] > container_rect.width() - 20:  # Allow 20px to grab
                new_x = container_rect.width() - 20
                needs_constraint = True
                
            # Check top boundary
            if window_pos[1] < -window_height + 20:  # Allow 20px to grab
                new_y = -window_height + 20
                needs_constraint = True
                
            # Check bottom boundary
            if window_pos[1] > container_rect.height() - 20:  # Allow 20px to grab
                new_y = container_rect.height() - 20
                needs_constraint = True
            
            # Only move the window if it needs to be constrained
            if needs_constraint:
                win32gui.MoveWindow(hwnd, new_x, new_y, window_width, window_height, True)
                
        except Exception as e:
            logger.error(f"Error in check_window_bounds: {str(e)}")
            logger.error(traceback.format_exc())
            self.constraint_timer.stop()
            
    def toggle_camera(self):
        if not self.camera_enabled:
            try:
                logger.info("Starting camera thread")
                self.camera_thread = CameraThread()
                self.camera_thread.frame_ready.connect(self.update_camera_frame)
                self.camera_thread.error_occurred.connect(self.handle_camera_error)
                self.camera_thread.status_updated.connect(self.update_camera_status)
                self.camera_thread.start()
                self.camera_enabled = True
                self.camera_toggle.setText("Disable Camera")
                logger.info("Camera thread started successfully")
            except Exception as e:
                logger.error(f"Error starting camera: {str(e)}")
                logger.error(traceback.format_exc())
                self.handle_camera_error(f"Failed to start camera: {str(e)}")
        else:
            try:
                logger.info("Stopping camera thread")
                if self.camera_thread:
                    self.camera_thread.stop()
                    self.camera_thread.wait()
                self.camera_enabled = False
                self.camera_toggle.setText("Enable Camera")
                self.camera_display.setText("Camera disabled")
                logger.info("Camera thread stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping camera: {str(e)}")
                logger.error(traceback.format_exc())
                
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
        
    def handle_camera_error(self, error_msg):
        QMessageBox.warning(self, "Camera Error", error_msg)
        self.camera_enabled = False
        self.camera_toggle.setText("Enable Camera")
        self.camera_display.setText("Camera error")
        
    def closeEvent(self, event):
        try:
            logger.info("Application closing")
            
            # Stop the constraint timer if running
            if hasattr(self, 'constraint_timer'):
                self.constraint_timer.stop()
            
            # Restore selected window if any
            if self.selected_window and win32gui.IsWindow(self.selected_window):
                try:
                    # Restore original window procedure
                    if hasattr(self, 'old_win_proc'):
                        win32gui.SetWindowLong(self.selected_window, win32con.GWL_WNDPROC, self.old_win_proc)
                    
                    # Reset window style and parent
                    if hasattr(self, 'original_styles'):
                        original_style = self.original_styles.get(self.selected_window)
                        if original_style is not None:
                            win32gui.SetWindowLong(self.selected_window, win32con.GWL_STYLE, original_style)
                    
                    # Remove from container
                    win32gui.SetParent(self.selected_window, None)
                    
                    # Restore original position and size
                    if hasattr(self, 'original_rect'):
                        left, top, right, bottom = self.original_rect
                        width = right - left
                        height = bottom - top
                        win32gui.MoveWindow(self.selected_window, left, top, width, height, True)
                        
                except Exception as e:
                    logger.error(f"Error restoring window: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Stop camera if running
            if self.camera_thread:
                self.camera_thread.stop()
                self.camera_thread.wait()
                
        except Exception as e:
            logger.error(f"Error in closeEvent: {str(e)}")
            logger.error(traceback.format_exc())
        event.accept()

if __name__ == '__main__':
    try:
        print("Creating QApplication instance...")
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        print("QApplication created successfully")
        
        # Show splash screen
        print("Creating splash screen...")
        splash = SplashScreen()
        splash.show()
        print("Splash screen created and shown")
        app.processEvents()
        
        # Initialize main window
        print("Creating main window...")
        window = ScreenSplitApp()
        print("Main window created")
        
        # Show main window
        print("Showing main window...")
        window.show()
        window.raise_()
        window.activateWindow()
        print("Main window shown and activated")
        app.processEvents()
        
        # Close splash screen
        print("Closing splash screen...")
        splash.finish(window)
        print("Splash screen closed")
        
        print("Starting Qt event loop...")
        app.exec()
        print("Qt event loop finished")
        
    except Exception as e:
        print(f"ERROR: Application failed to start")
        print(f"Error details: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1) 