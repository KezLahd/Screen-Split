import sys
import cv2
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox,
                           QProgressBar, QSplashScreen, QScrollArea, QSplitter, QSizePolicy,
                           QFileDialog, QFrame, QMenu)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QIcon, QCursor
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
import win32ui
from win32com.shell import shell, shellcon
import pythoncom
import subprocess
import os

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

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True  # Set to True at initialization
        self.camera = None
        self._lock = threading.Lock()
        
    def run(self):
        try:
            self.status_updated.emit("Initializing camera...")
            
            # Pre-initialize camera settings
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend
            if not self.camera.isOpened():
                self.error_occurred.emit("Could not open camera")
                return
                
            # Set higher resolution for better quality when zoomed
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Warm up the camera
            for _ in range(5):
                self.camera.read()
                
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
                        self.error_occurred.emit("Failed to read camera frame")
                        break
                else:
                    # Sleep for a short time to prevent high CPU usage
                    time.sleep(0.001)
                    
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
        self.running = True  # Start as True to begin capture immediately
        self.monitor_index = 0
        self.sct = None
        self._lock = threading.Lock()
        
    def run(self):
        try:
            # Create mss instance
            self.sct = mss()
            
            # Get monitor info
            monitors = self.sct.monitors
            
            # Skip first monitor (combined display)
            if self.monitor_index + 1 >= len(monitors):
                self.error_occurred.emit(f"Invalid monitor index: {self.monitor_index}")
                return
            
            # Get the target monitor
            monitor = monitors[self.monitor_index + 1]  # Add 1 to skip combined display
            
            # Create monitor settings once
            monitor_settings = {
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height'] - 58  # Adjust for taskbar
            }
            
            last_capture_time = 0
            frame_interval = 1.0 / 30  # Target 30 FPS
            
            while self.running:
                current_time = time.time()
                
                # Only capture if enough time has passed
                if current_time - last_capture_time >= frame_interval:
                    try:
                        # Capture screen
                        screenshot = self.sct.grab(monitor_settings)
                        
                        # Convert to QImage
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
                            time.sleep(0.1)  # Brief pause on error
                else:
                    # Small sleep to prevent CPU overuse
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

class WindowEnumerator(QThread):
    windows_ready = pyqtSignal(dict, list)
    
    def run(self):
        try:
            window_handles = {}
            window_titles = ["Select a window..."]
            
            def winEnumHandler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and title != "Screen Split Application" and title != "":
                        try:
                            # Get window size to filter out tiny/invalid windows
                            rect = win32gui.GetWindowRect(hwnd)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            if width > 50 and height > 50:  # Filter out very small windows
                                window_handles[title] = hwnd
                                window_titles.append(title)
                        except Exception:
                            pass
            
            win32gui.EnumWindows(winEnumHandler, None)
            self.windows_ready.emit(window_handles, window_titles)
        except Exception as e:
            print(f"Error enumerating windows: {str(e)}")

class CustomScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set smooth scrolling properties
        self.scroll_speed = 120
        self.scroll_animation_timer = QTimer()
        self.scroll_animation_timer.timeout.connect(self.animate_scroll)
        self.target_scroll_pos = 0
        self.current_scroll_pos = 0
        self.scroll_step = 0
        self.is_portrait = False
        
        # Add threshold for scrollbar visibility
        self.scrollbar_threshold = 5  # pixels
        
        # Set scrollbar policies
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Start with scrollbars off
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Add resize timer for smoother updates
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_scrollbar_visibility)
        
        # Add a flag to track if we're currently resizing
        self.is_resizing = False
        
        # Style the scroll area
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:horizontal {
                height: 6px;
                background: transparent;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: rgba(102, 102, 102, 0.7);
                min-width: 50px;
                min-height: 50px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:horizontal:pressed, QScrollBar::handle:vertical:pressed {
                background: rgba(153, 153, 153, 0.9);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                width: 0px;
                height: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
    
    def resizeEvent(self, event):
        """Handle resize events to update scrollbar visibility smoothly"""
        super().resizeEvent(event)
        self.is_resizing = True
        # Restart the timer on each resize
        self.resize_timer.start(50)  # 50ms delay
    
    def update_scrollbar_visibility(self):
        """Update scrollbar visibility based on current dimensions"""
        if not self.widget():
            return
            
        viewport_size = self.viewport().size()
        widget_size = self.widget().size()
        
        # Check if scrollbars are needed with threshold
        needs_horizontal = widget_size.width() > (viewport_size.width() + self.scrollbar_threshold)
        needs_vertical = widget_size.height() > (viewport_size.height() + self.scrollbar_threshold)
        
        # During resize, only show horizontal scrollbar if content is significantly larger
        if self.is_resizing:
            needs_horizontal = widget_size.width() > (viewport_size.width() + 20)  # Increased threshold during resize
        
        # Update horizontal scrollbar
        if self.is_portrait:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded if needs_horizontal
                else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        
        # Update vertical scrollbar
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded if needs_vertical
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        
        self.is_resizing = False
    
    def set_orientation(self, is_portrait):
        """Set the scroll orientation based on screen dimensions"""
        self.is_portrait = is_portrait
        self.update_scrollbar_visibility()
    
    def is_scrollbar_needed(self, orientation):
        """Check if a scrollbar is needed in the given orientation"""
        if not self.widget():
            return False
            
        viewport_size = self.viewport().size()
        widget_size = self.widget().size()
        
        if orientation == Qt.Orientation.Horizontal:
            return widget_size.width() > viewport_size.width()
        else:
            return widget_size.height() > viewport_size.height()
    
    def wheelEvent(self, event):
        if self.hasFocus() or self.underMouse():  # Check if we have focus or mouse is over
            if event.angleDelta().y() != 0:  # Vertical wheel movement
                # Calculate the number of pixels to scroll
                delta = event.angleDelta().y()
                
                # Prioritize vertical scrollbar if it's visible and has a range
                vertical_scrollbar = self.verticalScrollBar()
                horizontal_scrollbar = self.horizontalScrollBar()
                
                if vertical_scrollbar.isVisible() and vertical_scrollbar.maximum() > 0:
                    scrollbar = vertical_scrollbar
                elif horizontal_scrollbar.isVisible() and horizontal_scrollbar.maximum() > 0:
                    scrollbar = horizontal_scrollbar
                else:
                    return
                
                self.current_scroll_pos = scrollbar.value()
                
                # Calculate target position
                scroll_amount = int(-delta / 120.0 * self.scroll_speed)
                self.target_scroll_pos = max(0, min(
                    self.current_scroll_pos + scroll_amount,
                    scrollbar.maximum()
                ))
                
                # Calculate steps for smooth animation
                self.scroll_step = (self.target_scroll_pos - self.current_scroll_pos) / 10
                
                # Start animation if not already running
                if not self.scroll_animation_timer.isActive():
                    self.scroll_animation_timer.start(16)  # ~60 FPS
                
                event.accept()
            return
        super().wheelEvent(event)
    
    def animate_scroll(self):
        if abs(self.target_scroll_pos - self.current_scroll_pos) < 1:
            self.scroll_animation_timer.stop()
            # Use vertical scrollbar if it's visible and has range, otherwise horizontal
            vertical_scrollbar = self.verticalScrollBar()
            horizontal_scrollbar = self.horizontalScrollBar()
            
            if vertical_scrollbar.isVisible() and vertical_scrollbar.maximum() > 0:
                scrollbar = vertical_scrollbar
            else:
                scrollbar = horizontal_scrollbar
                
            scrollbar.setValue(int(self.target_scroll_pos))
            return
            
        self.current_scroll_pos += self.scroll_step
        # Use vertical scrollbar if it's visible and has range, otherwise horizontal
        vertical_scrollbar = self.verticalScrollBar()
        horizontal_scrollbar = self.horizontalScrollBar()
        
        if vertical_scrollbar.isVisible() and vertical_scrollbar.maximum() > 0:
            scrollbar = vertical_scrollbar
        else:
            scrollbar = horizontal_scrollbar
            
        scrollbar.setValue(int(self.current_scroll_pos))
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Make sure scrolling works immediately when focused
        self.setFocus()
    
    def enterEvent(self, event):
        super().enterEvent(event)
        # Set focus when mouse enters
        self.setFocus()

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        
    def set_file_path(self, path):
        self.file_path = path
        
    def run(self):
        try:
            if not self.file_path:
                return
                
            # Load the image
            pixmap = QPixmap(self.file_path)
            if pixmap.isNull():
                self.error_occurred.emit("Failed to load the selected image.")
                return
            
            # Scale the image
            scaled_pixmap = pixmap.scaled(
                200,  # Fixed width
                150,  # Fixed height
                Qt.AspectRatioMode.KeepAspectFit,
                Qt.TransformationMode.FastTransformation
            )
            
            self.image_loaded.emit(scaled_pixmap)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class FilePickerThread(QThread):
    file_selected = pyqtSignal(str)
    
    def run(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create and hide the root window
            root = tk.Tk()
            root.withdraw()
            
            # Show the file dialog
            file_path = filedialog.askopenfilename(
                title="Select Brand Logo",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg"),
                    ("All files", "*.*")
                ]
            )
            
            # Destroy the root window
            root.destroy()
            
            if file_path:
                self.file_selected.emit(file_path)
                
        except Exception as e:
            print(f"Error in file picker thread: {str(e)}")

class ScreenSplitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Split Application")
        
        # Add update checking
        self.current_version = "1.0.0"
        self.update_url = "https://raw.githubusercontent.com/yourusername/screen-split-app/main/version.txt"
        self.update_check_timer = QTimer()
        self.update_check_timer.timeout.connect(self.check_for_updates)
        self.update_check_timer.start(24 * 60 * 60 * 1000)  # Check daily
        
        # Set frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Enable resizing for frameless window
        self.setMouseTracking(True)
        self.resize_edge = None
        self.resize_start_pos = None
        self.start_geometry = None
        self.resize_border = 8  # Increased border width for easier resizing
        self.corner_size = 16   # Larger corner area for easier diagonal resizing
        
        # Store window state
        self.normal_geometry = None  # Store the normal window geometry
        self.is_maximized = False    # Track maximized state
        
        # Add window border styling
        self.setStyleSheet("""
            QMainWindow {
                border: 1px solid #333333;
            }
        """)
        
        # Initialize UI elements that will be referenced
        self.screen_display = None
        self.scroll_area = None
        self.camera_display = None
        self.logo_display = None
        self.camera_toggle = None
        self.display_combo = None
        self.toolbar = None
        self.drag_position = None
        
        # Add resize debounce timer
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.delayed_resize)
        
        # Add toolbar fade timer with longer initial delay
        self.toolbar_fade_timer = QTimer()
        self.toolbar_fade_timer.setSingleShot(True)
        self.toolbar_fade_timer.timeout.connect(self.fade_toolbar)
        
        # Get all available screens
        self.screens = QApplication.screens()
        
        # Store exact monitor dimensions
        self.taskbar_height = 58
        
        # Initialize thread variables
        self.screen_thread = None
        self.camera_thread = None
        self.camera_enabled = False
        
        # Set window size constraints
        primary_screen = self.screens[0].geometry()
        self.min_width = int(primary_screen.width() * 0.3)  # 30% of screen width
        self.min_height = 400  # Minimum height in pixels
        
        # Initialize zoom variables
        self.zoom_factor = 1.0
        self.original_pixmap = None
        self.original_size = None
        self.user_zoomed = False
        self.initial_height = None
        
        # Set minimum and maximum zoom levels
        self.min_zoom = 1.0
        self.max_zoom = 2.0
        
        # Set initial window size
        self.setMinimumSize(self.min_width, self.min_height)
        
        # Set dark theme colors
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1084D9;
            }
            QPushButton:pressed {
                background-color: #006CBE;
            }
            QLabel {
                color: #ffffff;
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox:on {
                border: 2px solid #0078D4;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0078D4;
            }
            #titleBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #333333;
            }
            #titleBar QPushButton {
                padding: 4px 12px;
                border-radius: 0;
                font-size: 16px;
            }
            #minimizeBtn {
                background-color: transparent;
                color: #ffffff;
            }
            #minimizeBtn:hover {
                background-color: #404040;
            }
            #maximizeBtn {
                background-color: transparent;
                color: #ffffff;
            }
            #maximizeBtn:hover {
                background-color: #404040;
            }
            #closeBtn {
                background-color: transparent;
                color: #ffffff;
            }
            #closeBtn:hover {
                background-color: #c42b1c;
            }
        """)
        
        # Set up the UI first
        self.setup_ui()
        
        # Initialize with primary screen dimensions
        self.update_monitor_dimensions(0)  # Default to primary screen
        
        # Calculate window size (80% of screen width)
        primary_screen = self.screens[0].geometry()
        self.screen_width = primary_screen.width()
        self.screen_height = primary_screen.height()
        window_width = int(self.screen_width * 0.8)
        window_height = int((window_width * (self.screen_height - self.taskbar_height)) / self.screen_width)
        
        # Set window size and position
        self.setGeometry(
            (self.screen_width - window_width) // 2,
            (self.screen_height - window_height) // 2,
            window_width,
            window_height
        )
        
        # Start threads after UI is set up
        self.setup_threads()
        
        # Initialize image loader thread
        self.image_loader = ImageLoaderThread(self)
        self.image_loader.image_loaded.connect(self.on_image_loaded)
        self.image_loader.error_occurred.connect(self.on_image_error)

        # Force initial size update before showing the window
        self.force_initial_size_update()

        # Add camera zoom tracking
        self.camera_zoom_factor = 1.0
        self.camera_original_size = None

    def force_initial_size_update(self):
        """Force an initial size update to ensure proper layout"""
        try:
            # Get the current width of the right panel
            right_panel_width = int(self.width() * 0.3)  # Start with 30% of window width
            
            # Calculate available height for camera and logo
            available_height = self.height() - 50  # Adjust margin allowance to 50 for better spacing
            
            # Calculate minimum and maximum right panel widths based on height
            min_right_width = int(available_height * 0.3)  # Minimum 30% of height
            max_right_width = int(self.width() * 0.5)  # Maximum 50% of window width
            
            # Constrain the right panel width
            if right_panel_width < min_right_width:
                right_panel_width = min_right_width
            elif right_panel_width > max_right_width:
                right_panel_width = max_right_width
            
            # Calculate target camera container height (50% of available height)
            target_camera_height = int(available_height * 0.5)
            
            # Calculate maximum width based on target height and 16:9 ratio
            max_width_16_9 = int(target_camera_height * (16/9))
            
            # Calculate minimum width based on target height and 9:16 ratio
            min_width_9_16 = int(target_camera_height * (9/16))
            
            # Calculate camera width based on available space
            camera_width = min(right_panel_width - 40, max_width_16_9)
            
            # If width becomes less than minimum 9:16 width, adjust height to maintain ratio
            if camera_width < min_width_9_16:
                camera_height = int(camera_width * (16/9))  # Maintain 9:16 ratio
            else:
                camera_height = target_camera_height
            
            # Calculate remaining height for logo
            toolbar_height = 40  # Height of camera toolbar
            remaining_height = available_height - camera_height - toolbar_height - 15  # Adjust spacing to 15
            
            # Update camera display if it exists
            if hasattr(self, 'camera_display') and self.camera_display:
                self.camera_display.setFixedSize(camera_width, camera_height)
                self.camera_display.setContentsMargins(0, 0, 0, 0)
            
            # Update camera toolbar width to match camera width
            if hasattr(self, 'camera_toggle') and self.camera_toggle:
                self.camera_toggle.parentWidget().setFixedWidth(camera_width)
            
            # Update logo container size if it exists
            if hasattr(self, 'logo_container') and self.logo_container:
                self.logo_container.setFixedWidth(camera_width)
                self.logo_container.setMinimumHeight(remaining_height)
                
                # Only update image size if we have an image loaded and not manually zoomed
                if hasattr(self, 'current_image_label') and self.current_image_label and not self.user_zoomed:
                    self.update_image_size()
            
            # Update splitter sizes with the calculated right panel width
            self.splitter.setSizes([self.width() - right_panel_width, right_panel_width])
            
            # Update scroll area orientation
            if self.scroll_area:
                self.scroll_area.set_orientation(self.monitor_height > self.monitor_width)
            
            # Force layout updates
            self.updateGeometry()
            self.layout().activate()
            
            # Process any pending events
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in force_initial_size_update: {str(e)}")

    def showEvent(self, event):
        """Handle window show event to ensure proper initial layout"""
        super().showEvent(event)
        # Force one final update after window is shown
        QTimer.singleShot(0, self.force_initial_size_update)

    def update_monitor_dimensions(self, screen_index):
        """Update monitor dimensions based on selected screen"""
        try:
            if screen_index < 0 or screen_index >= len(self.screens):
                raise ValueError(f"Invalid screen index: {screen_index}")
                
            screen = self.screens[screen_index].geometry()
            self.screen_width = screen.width()
            self.screen_height = screen.height()
            
            # Only subtract taskbar height for primary display (index 0)
            if screen_index == 0:
                self.monitor_height = self.screen_height - self.taskbar_height
            else:
                self.monitor_height = self.screen_height
                
            self.monitor_width = self.screen_width
            
            # Update scroll area orientation based on new dimensions
            is_portrait = self.monitor_height > self.monitor_width
            self.scroll_area.set_orientation(is_portrait)
            
        except Exception as e:
            error_msg = f"Error updating monitor dimensions: {str(e)}"
            self.handle_screen_error(error_msg)
            raise

    def setup_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add custom title bar
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(32)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        title_bar_layout.setSpacing(0)
        
        # Add menu buttons
        file_btn = QPushButton("File")
        file_btn.setObjectName("menuBtn")
        file_btn.setFixedSize(45, 32)
        file_btn.setStyleSheet("font-size: 12px; text-align: center; padding: 0 8px;")
        file_btn.clicked.connect(lambda: self.show_menu(file_btn, "File"))
        
        view_btn = QPushButton("View")
        view_btn.setObjectName("menuBtn")
        view_btn.setFixedSize(45, 32)
        view_btn.setStyleSheet("font-size: 12px; text-align: center; padding: 0 8px;")
        view_btn.clicked.connect(lambda: self.show_menu(view_btn, "View"))
        
        title_bar_layout.addWidget(file_btn)
        title_bar_layout.addWidget(view_btn)
        title_bar_layout.addSpacing(10)  # Reduced spacing to match Cursor
        
        # Add title label (centered)
        title_label = QLabel("Screen Split Application")
        title_label.setStyleSheet("background: transparent; border: none; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar_layout.addWidget(title_label, 1)  # Add stretch factor to center
        
        # Add window controls
        minimize_btn = QPushButton("−")
        minimize_btn.setObjectName("minimizeBtn")
        minimize_btn.setFixedSize(46, 32)
        minimize_btn.clicked.connect(self.showMinimized)
        
        maximize_btn = QPushButton("□")
        maximize_btn.setObjectName("maximizeBtn")
        maximize_btn.setFixedSize(46, 32)
        maximize_btn.clicked.connect(self.toggle_maximize)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(46, 32)
        close_btn.clicked.connect(self.close)
        
        title_bar_layout.addWidget(minimize_btn)
        title_bar_layout.addWidget(maximize_btn)
        title_bar_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # Update stylesheet to include menu button styling
        self.setStyleSheet(self.styleSheet() + """
            #menuBtn {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 0;
                font-size: 12px;
            }
            #menuBtn:hover {
                background-color: #404040;
            }
            #menuBtn:pressed {
                background-color: #505050;
            }
        """)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - Screen capture display
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #1e1e1e;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create custom scroll area for screen display
        self.scroll_area = CustomScrollArea()
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QWidget#scrollAreaWidgetContents {
                background-color: #1e1e1e;
            }
            QScrollBar:horizontal {
                height: 6px;
                background: transparent;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: rgba(102, 102, 102, 0.7);
                min-width: 50px;
                min-height: 50px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:horizontal:pressed, QScrollBar::handle:vertical:pressed {
                background: rgba(153, 153, 153, 0.9);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                width: 0px;
                height: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # Screen display area
        self.screen_display = QLabel()
        self.screen_display.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.screen_display.setText("Starting screen capture...")
        self.screen_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.screen_display.customContextMenuRequested.connect(self.show_display_menu)
        self.screen_display.setStyleSheet("background-color: #1e1e1e;")
        
        # Add screen display to scroll area
        self.scroll_area.setWidget(self.screen_display)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.addWidget(self.scroll_area)
        
        # Right side - Camera and logo
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #1e1e1e;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(0, 8, 8, 8)  # Reduced right margin
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create camera container widget
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setSpacing(0)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the container contents
        
        # Camera display
        self.camera_display = QLabel()
        self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_display.setText("Camera disabled")
        self.camera_display.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-bottom: none;
                color: #cccccc;  /* Fixed text color */
            }
        """)
        camera_layout.addWidget(self.camera_display, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Camera toolbar
        camera_toolbar = QWidget()
        camera_toolbar.setFixedHeight(40)
        camera_toolbar.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #333333;
                border-top: none;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
                border-radius: 4px;
                margin: 0;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        toolbar_layout = QHBoxLayout(camera_toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        toolbar_layout.setSpacing(20)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        # Create zoom out icon
        zoom_out_icon = QPixmap(30, 30)
        zoom_out_icon.fill(Qt.GlobalColor.transparent)
        painter = QPainter(zoom_out_icon)
        painter.setPen(QColor("#cccccc"))
        painter.setBrush(QColor("#cccccc"))
        
        # Draw minus sign
        painter.drawRect(8, 13, 14, 4)
        painter.end()

        # Create zoom in icon
        zoom_in_icon = QPixmap(30, 30)
        zoom_in_icon.fill(Qt.GlobalColor.transparent)
        painter = QPainter(zoom_in_icon)
        painter.setPen(QColor("#cccccc"))
        painter.setBrush(QColor("#cccccc"))
        
        # Draw plus sign
        painter.drawRect(8, 13, 14, 4)  # Horizontal line
        painter.drawRect(13, 8, 4, 14)  # Vertical line
        painter.end()

        # Add stretch before first button
        toolbar_layout.addStretch(1)

        # Zoom out button (left side)
        zoom_out_btn = QPushButton()
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.setIcon(QIcon(zoom_out_icon))
        zoom_out_btn.setIconSize(QSize(20, 20))
        zoom_out_btn.clicked.connect(self.zoom_camera_out)
        toolbar_layout.addWidget(zoom_out_btn)
        
        # Camera toggle button in toolbar with icon
        self.camera_toggle = QPushButton()
        self.camera_toggle.setFixedSize(30, 30)
        self.camera_toggle.setIcon(QIcon(camera_icon))
        self.camera_toggle.setIconSize(QSize(20, 20))
        self.camera_toggle.clicked.connect(self.toggle_camera)
        toolbar_layout.addWidget(self.camera_toggle, 0, Qt.AlignmentFlag.AlignCenter)

        # Zoom in button (right side)
        zoom_in_btn = QPushButton()
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.setIcon(QIcon(zoom_in_icon))
        zoom_in_btn.setIconSize(QSize(20, 20))
        zoom_in_btn.clicked.connect(self.zoom_camera_in)
        toolbar_layout.addWidget(zoom_in_btn)

        # Add stretch after last button
        toolbar_layout.addStretch(1)
        
        # Add toolbar to camera container with center alignment
        camera_layout.addWidget(camera_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add camera container to right layout
        right_layout.addWidget(camera_container)
        
        # Create logo container
        self.logo_container = QFrame()
        self.logo_container.setObjectName("logoContainer")
        self.logo_container.mousePressEvent = self.logo_container_clicked
        self.logo_container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Initialize the logo container
        self.reset_logo_container()
        
        # Add logo container to right layout
        right_layout.addWidget(self.logo_container, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Create splitter for resizing
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setHandleWidth(8)
        self.splitter.setStyleSheet("""
            QSplitter {
                background-color: #1e1e1e;
            }
            QSplitter::handle {
                background-color: #333333;
                margin: 0px;
                padding: 0px;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #444444;
            }
            QSplitter::handle:pressed {
                background-color: #555555;
            }
        """)
        
        # Set initial sizes (70% left, 30% right)
        self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])
        
        # Set splitter constraints
        self.splitter.setMinimumWidth(int(self.width() * 0.5))
        self.splitter.setMaximumWidth(int(self.width() * 0.85))
        
        # Connect splitter moved signal with error handling
        self.splitter.splitterMoved.connect(self.safe_splitter_moved)
        
        # Add splitter to main layout
        content_layout.addWidget(self.splitter)
        main_layout.addLayout(content_layout)
        
    def safe_splitter_moved(self, pos, index):
        """Handle splitter movement with error handling"""
        try:
            # Get current sizes
            left_size, right_size = self.splitter.sizes()
            total_size = left_size + right_size
            
            # Calculate minimum and maximum right panel sizes
            min_right_size = int(total_size * 0.15)  # 15% minimum
            max_right_size = int(total_size * 0.5)   # 50% maximum
            
            # Constrain the right panel size
            if right_size < min_right_size:
                self.splitter.setSizes([total_size - min_right_size, min_right_size])
            elif right_size > max_right_size:
                self.splitter.setSizes([total_size - max_right_size, max_right_size])
            
            # Update layouts immediately for smoother movement
            self.update_right_panel_sizes()
            
            # Update scrollbar visibility after a short delay to ensure sizes are stable
            QTimer.singleShot(100, lambda: self.scroll_area.set_orientation(self.monitor_height > self.monitor_width))
            
        except Exception as e:
            print(f"Error in safe_splitter_moved: {str(e)}")
            # Reset cursor if there's an error
            QApplication.restoreOverrideCursor()

    def update_right_panel_sizes(self):
        """Update right panel widget sizes based on available space and aspect ratio constraints"""
        try:
            # Get the current width of the right panel
            right_panel_width = self.splitter.sizes()[1]
            
            # Calculate available height for camera and logo
            available_height = self.height() - 50  # Adjust margin allowance to 50 for better spacing
            
            # Calculate minimum and maximum right panel widths based on height
            min_right_width = int(available_height * 0.3)  # Minimum 30% of height
            max_right_width = int(self.width() * 0.5)  # Maximum 50% of window width
            
            # Constrain the right panel width
            if right_panel_width < min_right_width:
                # Adjust splitter sizes to maintain minimum width
                left_size = self.splitter.sizes()[0]
                self.splitter.setSizes([left_size - (min_right_width - right_panel_width), min_right_width])
                right_panel_width = min_right_width
            elif right_panel_width > max_right_width:
                # Adjust splitter sizes to maintain maximum width
                left_size = self.splitter.sizes()[0]
                self.splitter.setSizes([left_size + (right_panel_width - max_right_width), max_right_width])
                right_panel_width = max_right_width
            
            # Calculate target camera container height (50% of available height)
            target_camera_height = int(available_height * 0.5)
            
            # Calculate maximum width based on target height and 16:9 ratio
            max_width_16_9 = int(target_camera_height * (16/9))
            
            # Calculate minimum width based on target height and 9:16 ratio
            min_width_9_16 = int(target_camera_height * (9/16))
            
            # Calculate camera width based on available space, accounting for margins
            camera_width = min(right_panel_width - 40, max_width_16_9)
            
            # If width becomes less than minimum 9:16 width, adjust height to maintain ratio
            if camera_width < min_width_9_16:
                camera_height = int(camera_width * (16/9))  # Maintain 9:16 ratio
            else:
                camera_height = target_camera_height
            
            # Calculate remaining height for logo
            toolbar_height = 40  # Height of camera toolbar
            remaining_height = available_height - camera_height - toolbar_height - 15  # Adjust spacing to 15
            
            # Update camera display if it exists
            if hasattr(self, 'camera_display') and self.camera_display:
                self.camera_display.setFixedSize(camera_width, camera_height)
                self.camera_display.setContentsMargins(0, 0, 0, 0)
            
            # Update camera toolbar width to match camera width
            if hasattr(self, 'camera_toggle') and self.camera_toggle:
                toolbar = self.camera_toggle.parentWidget()
                toolbar.setFixedWidth(camera_width)
                toolbar.setContentsMargins(10, 0, 10, 0)  # Maintain horizontal margins
            
            # Update logo container size if it exists
            if hasattr(self, 'logo_container') and self.logo_container:
                self.logo_container.setFixedWidth(camera_width)
                self.logo_container.setMinimumHeight(remaining_height)
                self.logo_container.setContentsMargins(0, 8, 8, 8)  # Maintain margins
                
                # Only update image size if we have an image loaded and not manually zoomed
                if hasattr(self, 'current_image_label') and self.current_image_label and not self.user_zoomed:
                    self.update_image_size()
            
            # Force layout updates
            self.updateGeometry()
            self.layout().activate()
            
            # Process any pending events
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in update_right_panel_sizes: {str(e)}")

    def initial_size_update(self):
        """Perform initial size calculations after window is shown"""
        self.update_right_panel_sizes()
        # Force an immediate update of the splitter sizes
        self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])

    def setup_threads(self):
        """Initialize and start the screen capture thread"""
        self.start_screen_capture()
        
    def start_screen_capture(self, index=0):
        """Start screen capture with specified monitor index"""
        try:
            # Create new thread first
            new_thread = ScreenCaptureThread()
            new_thread.monitor_index = index
            
            # Update monitor dimensions before starting capture
            self.update_monitor_dimensions(index)
            
            # Connect signals
            new_thread.frame_ready.connect(self.update_screen_frame)
            new_thread.error_occurred.connect(self.handle_screen_error)
            new_thread.status_updated.connect(self.update_screen_status)
            
            # Keep reference to old thread
            old_thread = self.screen_thread
            
            # Update reference and start new thread
            self.screen_thread = new_thread
            self.screen_thread.start()
            
            # Stop old thread after new one is running
            if old_thread:
                QTimer.singleShot(100, lambda: self.cleanup_old_thread(old_thread))
            
        except Exception as e:
            error_msg = f"Error starting screen capture: {str(e)}"
            self.handle_screen_error(error_msg)
            self.screen_thread = None

    def cleanup_old_thread(self, thread):
        """Cleanup old thread safely"""
        if thread:
            thread.stop()
            thread.wait(100)  # Wait briefly for cleanup
            thread.deleteLater()

    def update_screen_frame(self, qt_image):
        """Update the screen frame with new image"""
        try:
            if not self.screen_display or not self.scroll_area:
                return

            pixmap = QPixmap.fromImage(qt_image)
            if pixmap.isNull():
                return
            
            # Get the available display width and height
            available_width = self.scroll_area.viewport().width()
            available_height = self.scroll_area.viewport().height()
            
            if available_width <= 0 or available_height <= 0:
                return  # Skip invalid dimensions
            
            # Check if screen is in portrait mode (height > width)
            is_portrait = self.monitor_height > self.monitor_width
            self.scroll_area.set_orientation(is_portrait)
            
            try:
                if is_portrait:
                    # For portrait, fit to available width
                    display_width = available_width
                    display_height = int((display_width * pixmap.height()) / pixmap.width())
                else:
                    # For landscape, fit to available height
                    display_height = available_height
                    display_width = int((display_height * pixmap.width()) / pixmap.height())
                    
                    # Ensure width is at least the viewport width
                    if display_width < available_width:
                        display_width = available_width
                        display_height = int((display_width * pixmap.height()) / pixmap.width())
                
                # Scale the pixmap
                scaled_pixmap = pixmap.scaled(
                    display_width,
                    display_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                if not scaled_pixmap.isNull():
                    self.screen_display.setPixmap(scaled_pixmap)
                    self.screen_display.setFixedSize(display_width, display_height)
                    
                    # Ensure the background color is set
                    self.screen_display.setStyleSheet("background-color: #1e1e1e;")
                    
            except ZeroDivisionError:
                # Handle potential division by zero
                pass
                
        except Exception as e:
            # Log error but don't crash
            print(f"Error updating screen frame: {str(e)}")
            
    def update_screen_status(self, status):
        self.screen_display.setText(status)
        
    def handle_screen_error(self, error_msg):
        print(f"Screen capture error: {error_msg}")
        self.screen_display.setText(f"Error: {error_msg}")
        QMessageBox.warning(self, "Screen Capture Error", error_msg)
        
    def show_display_menu(self, pos):
        """Handle right-click on the display area"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 4px 20px;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #3d3d3d;
                margin: 4px 0px;
            }
            QMenu::indicator {
                width: 0px;
            }
            QMenu::right-arrow {
                image: none;
                width: 0px;
            }
        """)
        display_menu = menu.addMenu("Select Display")
        
        # Add display options
        for i, screen in enumerate(self.screens):
            name = screen.name()
            geometry = screen.geometry()
            action = display_menu.addAction(f"Display {i+1}: {name} ({geometry.width()}x{geometry.height()})")
            action.triggered.connect(lambda checked, idx=i: self.on_display_changed(idx))
            
        menu.exec(self.scroll_area.mapToGlobal(pos))

    def on_display_changed(self, index):
        """Handle display selection change"""
        try:
            # Update dimensions first
            self.update_monitor_dimensions(index)
            
            # Start new capture thread immediately
            self.start_screen_capture(index)
            
            # Show a brief notification
            self.screen_display.setText(f"Switching to Display {index + 1}...")
            QTimer.singleShot(2000, lambda: self.screen_display.clear() if self.screen_display.text() == f"Switching to Display {index + 1}..." else None)
            
        except Exception as e:
            error_msg = f"Error changing display: {str(e)}"
            self.handle_screen_error(error_msg)
        
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
            # Update UI first
            self.camera_enabled = False
            self.camera_toggle.setStyleSheet("")
            self.camera_display.clear()
            self.camera_display.setText("Camera disabled")
            
            # Stop any running countdown
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                self.countdown_timer.stop()
            
            # Stop the thread immediately
            if self.camera_thread:
                self.camera_thread.running = False
                self.camera_thread = None
            
    def update_camera_frame(self, qt_image):
        """Update camera frame with center zoom and height fitting"""
        try:
            if not self.camera_display:
                return

            # Get the container dimensions
            container_width = self.camera_display.width()
            container_height = self.camera_display.height()
            
            # Convert QImage to QPixmap
            original_pixmap = QPixmap.fromImage(qt_image)
            
            # Store original size if not set
            if self.camera_original_size is None:
                self.camera_original_size = (container_width, container_height)
            
            # Calculate scaling to fit height
            scale_factor = container_height / original_pixmap.height()
            
            # Calculate new dimensions maintaining aspect ratio
            new_width = int(original_pixmap.width() * scale_factor)
            new_height = container_height
            
            # Scale the image
            scaled_pixmap = original_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Apply zoom factor
            if self.camera_zoom_factor != 1.0:
                zoomed_width = int(scaled_pixmap.width() * self.camera_zoom_factor)
                zoomed_height = int(scaled_pixmap.height() * self.camera_zoom_factor)
                scaled_pixmap = scaled_pixmap.scaled(
                    zoomed_width,
                    zoomed_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            # If the scaled width is larger than the container, crop the center portion
            if scaled_pixmap.width() > container_width:
                # Calculate the center crop
                x_offset = (scaled_pixmap.width() - container_width) // 2
                crop_rect = QRect(x_offset, 0, container_width, container_height)
                cropped_pixmap = scaled_pixmap.copy(crop_rect)
                self.camera_display.setPixmap(cropped_pixmap)
            else:
                # If the scaled image is smaller or equal to container width, use it as is
                self.camera_display.setPixmap(scaled_pixmap)
                
        except Exception as e:
            print(f"Error updating camera frame: {str(e)}")

    def update_camera_status(self, status):
        # Only process status updates if camera is still enabled
        if not self.camera_enabled:
            return
            
        if status == "Initializing camera...":
            # Start countdown animation
            self.countdown_value = 3
            self.countdown_timer = QTimer()
            self.countdown_timer.timeout.connect(self.update_countdown)
            self.countdown_timer.start(1000)  # Update every second
            self.camera_display.setText(f"Camera starting in {self.countdown_value}...")
        else:
            self.camera_display.setText(status)
        
    def update_countdown(self):
        # Only update countdown if camera is still enabled
        if not self.camera_enabled:
            self.countdown_timer.stop()
            return
            
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.camera_display.setText(f"Camera starting in {self.countdown_value}...")
        else:
            self.countdown_timer.stop()
            self.camera_display.clear()  # Just clear the text instead of showing "Camera ready"
        
    def handle_camera_error(self, error_msg):
        QMessageBox.warning(self, "Camera Error", error_msg)
        self.camera_enabled = False
        self.camera_toggle.setStyleSheet("")
        self.camera_display.setText("Camera error")
        
    def closeEvent(self, event):
        # Update UI first
        self.camera_enabled = False
        if self.camera_display:
            self.camera_display.clear()
            self.camera_display.setText("Camera disabled")
            
        # Simply stop the thread
        if self.camera_thread:
            self.camera_thread.running = False
            self.camera_thread = None
            
        event.accept()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Update sizes immediately during resize
        self.update_right_panel_sizes()

    def delayed_resize(self):
        """Apply resize changes after debounce delay"""
        try:
            if not self.scroll_area or not self.screen_display:
                return

            # Get available dimensions from scroll area viewport
            available_width = self.scroll_area.viewport().width()
            available_height = self.scroll_area.viewport().height()
            
            if available_width <= 0 or available_height <= 0:
                return  # Skip invalid dimensions
            
            # Check orientation
            is_portrait = self.monitor_height > self.monitor_width
            
            # Calculate new dimensions
            try:
                if is_portrait:
                    # For portrait, fit to width
                    display_width = available_width
                    display_height = int((display_width * self.monitor_height) / self.monitor_width)
                else:
                    # For landscape, fit to height
                    display_height = available_height
                    display_width = int((display_height * self.monitor_width) / self.monitor_height)
                    
                    # Ensure width is at least the viewport width
                    if display_width < available_width:
                        display_width = available_width
                        display_height = int((display_width * self.monitor_height) / self.monitor_width)
                
                # Update screen display size
                self.screen_display.setFixedSize(display_width, display_height)
                
                # Update camera and logo sizes
                camera_width = max(200, int(self.width() * 0.25))  # Minimum width of 200px
                camera_height = int(camera_width * 0.75)
                
                # Update sizes only if widgets exist
                if self.camera_display:
                    self.camera_display.setFixedSize(camera_width, camera_height)
                if self.logo_display:
                    self.logo_display.setFixedSize(camera_width, int(camera_width * 0.3))
                    
            except ZeroDivisionError:
                # Handle potential division by zero
                pass
                
        except Exception as e:
            # Log error but don't crash
            print(f"Error in delayed resize: {str(e)}")

    def fade_toolbar(self):
        """Fade out the toolbar"""
        try:
            if self.toolbar:
                effect = QGraphicsOpacityEffect(self.toolbar)
                self.toolbar.setGraphicsEffect(effect)
                
                animation = QPropertyAnimation(effect, b"opacity")
                animation.setDuration(500)
                animation.setStartValue(1.0)
                animation.setEndValue(0.1)
                animation.start()
                
        except Exception as e:
            print(f"Error fading toolbar: {str(e)}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we're on a resize edge
            edge = self.get_resize_edge(event.position())
            if edge:
                self.resize_edge = edge
                self.resize_start_pos = event.globalPosition().toPoint()
                self.start_geometry = self.geometry()
                return
                
            # Check if the click is in the title bar area for dragging
            if event.position().y() <= 32:  # Title bar height
                self.drag_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        try:
            # Handle resizing
            if self.resize_edge and event.buttons() & Qt.MouseButton.LeftButton:
                delta = event.globalPosition().toPoint() - self.resize_start_pos
                self.handle_resize(delta)
                return

            # Check if we're over the splitter handle first
            if self.is_over_splitter_handle(event.pos()):
                self.setCursor(Qt.CursorShape.SplitHCursor)
                return

            # Only update cursor if not over splitter handle
            edge = self.get_resize_edge(event.position())
            if edge:
                self.update_cursor(edge)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Handle window dragging
            if self.drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
                delta = event.globalPosition().toPoint() - self.drag_position
                self.move(self.pos() + delta)
                self.drag_position = event.globalPosition().toPoint()
                
        except Exception as e:
            print(f"Error in mouse move event: {str(e)}")
            # Reset cursor if there's an error
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            was_resizing = self.resize_edge is not None
            self.resize_edge = None
            self.resize_start_pos = None
            self.start_geometry = None
            self.drag_position = None
            
            # Always reset cursor after resizing or dragging
            self.setCursor(Qt.CursorShape.ArrowCursor)
                    
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Handle mouse entering window"""
        super().enterEvent(event)
        # Check if we're over the splitter handle first
        if self.is_over_splitter_handle(event.position().toPoint()):
            self.setCursor(Qt.CursorShape.SplitHCursor)
            return
            
        # Only update cursor if not over splitter handle
        edge = self.get_resize_edge(event.position())
        self.update_cursor(edge)

    def leaveEvent(self, event):
        """Reset cursor when mouse leaves the window"""
        super().leaveEvent(event)
        # Always reset cursor when leaving window
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def get_resize_edge(self, pos):
        """Determine if the position is on a resize edge"""
        try:
            if self.isMaximized():
                return None
                
            x = pos.x()
            y = pos.y()
            width = self.width()
            height = self.height()
            border = self.resize_border
            corner = self.corner_size
            
            # Check corners first (using larger corner area)
            if x <= corner and y <= corner:
                return 'top_left'
            if x >= width - corner and y <= corner:
                return 'top_right'
            if x <= corner and y >= height - corner:
                return 'bottom_left'
            if x >= width - corner and y >= height - corner:
                return 'bottom_right'
                
            # Then check edges
            if x <= border:
                return 'left'
            if x >= width - border:
                return 'right'
            if y <= border:
                return 'top'
            if y >= height - border:
                return 'bottom'
                
            return None
        except Exception as e:
            print(f"Error in get_resize_edge: {str(e)}")
            return None

    def update_cursor(self, edge):
        """Update the cursor based on the resize edge"""
        try:
            if edge is None:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return
                
            cursor_map = {
                'top': Qt.CursorShape.SizeVerCursor,
                'bottom': Qt.CursorShape.SizeVerCursor,
                'left': Qt.CursorShape.SizeHorCursor,
                'right': Qt.CursorShape.SizeHorCursor,
                'top_left': Qt.CursorShape.SizeFDiagCursor,
                'bottom_right': Qt.CursorShape.SizeFDiagCursor,
                'top_right': Qt.CursorShape.SizeBDiagCursor,
                'bottom_left': Qt.CursorShape.SizeBDiagCursor
            }
            
            cursor = cursor_map.get(edge)
            if cursor:
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                
        except Exception as e:
            print(f"Error updating cursor: {str(e)}")
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def handle_resize(self, delta):
        """Handle window resizing"""
        try:
            if not self.resize_edge or not self.start_geometry:
                return
                
            new_geometry = QRect(self.start_geometry)
            
            # Calculate new dimensions while respecting minimum sizes
            if self.resize_edge in ['left', 'top_left', 'bottom_left']:
                new_left = new_geometry.left() + delta.x()
                new_width = new_geometry.right() - new_left
                if new_width >= self.min_width:
                    new_geometry.setLeft(new_left)
                else:
                    # Stop resizing if we hit minimum width
                    new_geometry.setLeft(new_geometry.right() - self.min_width)
            
            if self.resize_edge in ['right', 'top_right', 'bottom_right']:
                new_width = new_geometry.width() + delta.x()
                if new_width >= self.min_width:
                    new_geometry.setRight(new_geometry.left() + new_width)
                else:
                    # Stop resizing if we hit minimum width
                    new_geometry.setRight(new_geometry.left() + self.min_width)
            
            if self.resize_edge in ['top', 'top_left', 'top_right']:
                new_top = new_geometry.top() + delta.y()
                new_height = new_geometry.bottom() - new_top
                if new_height >= self.min_height:
                    new_geometry.setTop(new_top)
                else:
                    # Stop resizing if we hit minimum height
                    new_geometry.setTop(new_geometry.bottom() - self.min_height)
            
            if self.resize_edge in ['bottom', 'bottom_left', 'bottom_right']:
                new_height = new_geometry.height() + delta.y()
                if new_height >= self.min_height:
                    new_geometry.setBottom(new_geometry.top() + new_height)
                else:
                    # Stop resizing if we hit minimum height
                    new_geometry.setBottom(new_geometry.top() + self.min_height)
            
            # Apply the new geometry if valid
            if (new_geometry.width() >= self.min_width and 
                new_geometry.height() >= self.min_height):
                self.setGeometry(new_geometry)
                # Update internal layouts
                self.update_right_panel_sizes()
                
        except Exception as e:
            print(f"Error in handle_resize: {str(e)}")

    def toggle_maximize(self):
        """Toggle between normal and fullscreen mode"""
        try:
            if self.is_maximized:
                # Restore to normal size
                if self.normal_geometry:
                    self.setGeometry(self.normal_geometry)
                    # Force a complete size update to restore initial state with proper margins
                    QTimer.singleShot(0, lambda: [
                        self.force_initial_size_update(),
                        self.update_right_panel_sizes(),
                        self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)]),
                        # Ensure margins are applied to right panel objects
                        self.camera_display.setContentsMargins(0, 0, 0, 0),
                        self.camera_toggle.parentWidget().setContentsMargins(10, 0, 10, 0),
                        self.logo_container.setContentsMargins(0, 8, 8, 8),
                        # Force layout updates
                        self.updateGeometry(),
                        self.layout().activate(),
                        QApplication.processEvents()
                    ])
                self.is_maximized = False
            else:
                # Store current geometry before maximizing
                self.normal_geometry = self.geometry()
                
                # Get the screen that contains the window
                screen = self.screen()
                if not screen:
                    screen = QApplication.primaryScreen()
                
                # Get screen geometry, accounting for taskbar
                screen_geometry = screen.availableGeometry()  # This excludes taskbar
                
                # Set window to available screen dimensions (excluding taskbar)
                self.setGeometry(screen_geometry)
                self.is_maximized = True
                
                # Force an immediate size update with proper right panel sizing and margins
                QTimer.singleShot(0, lambda: [
                    self.force_initial_size_update(),
                    self.update_right_panel_sizes(),
                    self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)]),
                    # Ensure margins are applied to right panel objects
                    self.camera_display.setContentsMargins(0, 0, 0, 0),
                    self.camera_toggle.parentWidget().setContentsMargins(10, 0, 10, 0),
                    self.logo_container.setContentsMargins(0, 8, 8, 8),
                    # Force layout updates
                    self.updateGeometry(),
                    self.layout().activate(),
                    QApplication.processEvents()
                ])
                
        except Exception as e:
            print(f"Error in toggle_maximize: {str(e)}")
            # Fallback to standard maximize
            if self.isMaximized():
                self.showNormal()
                self.is_maximized = False
                # Force a complete size update to restore initial state with proper margins
                QTimer.singleShot(0, lambda: [
                    self.force_initial_size_update(),
                    self.update_right_panel_sizes(),
                    self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)]),
                    # Ensure margins are applied to right panel objects
                    self.camera_display.setContentsMargins(0, 0, 0, 0),
                    self.camera_toggle.parentWidget().setContentsMargins(10, 0, 10, 0),
                    self.logo_container.setContentsMargins(0, 8, 8, 8),
                    # Force layout updates
                    self.updateGeometry(),
                    self.layout().activate(),
                    QApplication.processEvents()
                ])
            else:
                self.showMaximized()
                self.is_maximized = True
                # Force an immediate size update with proper right panel sizing and margins
                QTimer.singleShot(0, lambda: [
                    self.force_initial_size_update(),
                    self.update_right_panel_sizes(),
                    self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)]),
                    # Ensure margins are applied to right panel objects
                    self.camera_display.setContentsMargins(0, 0, 0, 0),
                    self.camera_toggle.parentWidget().setContentsMargins(10, 0, 10, 0),
                    self.logo_container.setContentsMargins(0, 8, 8, 8),
                    # Force layout updates
                    self.updateGeometry(),
                    self.layout().activate(),
                    QApplication.processEvents()
                ])

    def select_logo(self):
        """Handle logo image selection using tkinter file dialog"""
        try:
            # Check if camera is initializing
            if hasattr(self, 'camera_display') and self.camera_display and self.camera_display.text().startswith("Camera starting in"):
                QMessageBox.warning(self, "Camera Initializing", "Please wait for the camera to finish initializing before adding a brand logo.")
                return
                
            # Create and start file picker thread
            self.file_picker_thread = FilePickerThread()
            self.file_picker_thread.file_selected.connect(self.handle_selected_file)
            self.file_picker_thread.start()
            
        except Exception as e:
            print(f"Error starting file picker: {str(e)}")
            self.reset_logo_container()

    def logo_container_clicked(self, event):
        """Handle click events on the logo container"""
        # Check if camera is initializing
        if hasattr(self, 'camera_display') and self.camera_display and self.camera_display.text().startswith("Camera starting in"):
            return
            
        if not hasattr(self, 'current_image_label') or not self.current_image_label:
            # If no image is loaded, allow left click to select image
            if event.button() == Qt.MouseButton.LeftButton:
                self.select_logo()
        event.accept()

    def reset_logo_container(self):
        """Reset the logo container to its default state"""
        try:
            # Clear existing layout
            if self.logo_container.layout():
                QWidget().setLayout(self.logo_container.layout())

            # Create plus icon
            plus_label = QLabel(self.logo_container)
            plus_icon = QPixmap(30, 30)
            plus_icon.fill(Qt.GlobalColor.transparent)
            painter = QPainter(plus_icon)
            painter.setPen(QColor("#cccccc"))
            painter.setBrush(QColor("#cccccc"))
            painter.drawRect(13, 8, 4, 14)  # Vertical line
            painter.drawRect(8, 13, 14, 4)  # Horizontal line
            painter.end()
            plus_label.setPixmap(plus_icon)
            plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            plus_label.setStyleSheet("background: transparent;")

            # Create text label
            text_label = QLabel("Add Brand Logo", self.logo_container)
            text_label.setStyleSheet("color: #ffffff; background: transparent;")
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Create and set new layout
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            layout.addStretch(1)
            layout.addWidget(plus_label, 0, Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(text_label, 0, Qt.AlignmentFlag.AlignCenter)
            layout.addStretch(1)

            # Set the layout
            self.logo_container.setLayout(layout)

            # Store references to prevent garbage collection
            self.current_layout = layout
            self.plus_label = plus_label
            self.text_label = text_label

            # Update container style
            self.logo_container.setStyleSheet("""
                QFrame#logoContainer {
                    background-color: #2d2d2d;
                    border: 2px solid #333333;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 0;
                }
                QFrame#logoContainer:hover {
                    background-color: #3d3d3d;
                    border: 2px solid #444444;
                }
            """)

            # Clear any stored image references
            self.current_image_label = None
            self.current_pixmap = None
            self.current_image_path = None

            self.logo_container.update()

        except Exception as e:
            print(f"Error in reset_logo_container: {str(e)}")

    def show_menu(self, button, menu_type):
        """Show the appropriate menu for the clicked button"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 4px 20px;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #666666;
            }
            QMenu::separator {
                height: 1px;
                background: #3d3d3d;
                margin: 4px 0px;
            }
            QMenu::indicator {
                width: 0px;
            }
            QMenu::right-arrow {
                image: none;
                width: 0px;
            }
            QMenu[mini="true"] {
                background-color: #252526;
            }
        """)
        
        if menu_type == "File":
            # Add Brand Logo section
            brand_logo_menu = QMenu("Brand Logo", self)
            brand_logo_menu.setProperty("mini", True)
            brand_logo_menu.setStyleSheet(menu.styleSheet())
            
            # Check if a logo is currently displayed
            has_logo = hasattr(self, 'current_image_label') and self.current_image_label and self.current_image_label.pixmap() is not None
            
            if has_logo:
                # Only show change and remove options if logo exists
                change_logo_action = brand_logo_menu.addAction("Change Brand Logo")
                change_logo_action.triggered.connect(self.handle_change_logo)
                
                remove_logo_action = brand_logo_menu.addAction("Remove Brand Logo")
                remove_logo_action.triggered.connect(self.reset_logo_container)
            else:
                # Only show add option if no logo exists
                add_logo_action = brand_logo_menu.addAction("Add Brand Logo")
                add_logo_action.triggered.connect(self.select_logo)
            
            menu.addMenu(brand_logo_menu)
            menu.addSeparator()
            
            # Add Check for Updates option
            update_action = menu.addAction("Check for Updates")
            update_action.triggered.connect(self.check_for_updates)
            menu.addSeparator()
            
            # Add Exit option
            menu.addAction("Exit", self.close)
            
        elif menu_type == "View":
            # Add Camera submenu
            camera_menu = QMenu("Camera", self)
            camera_menu.setProperty("mini", True)
            camera_menu.setStyleSheet(menu.styleSheet())
            
            # Add toggle camera action
            toggle_action = camera_menu.addAction("Toggle Camera")
            toggle_action.triggered.connect(self.toggle_camera)
            toggle_action.setEnabled(True)  # Always enabled
            
            camera_menu.addSeparator()
            
            # Add zoom actions
            zoom_in_action = camera_menu.addAction("Zoom In")
            zoom_in_action.triggered.connect(self.zoom_camera_in)
            zoom_in_action.setEnabled(self.camera_enabled)  # Only enabled when camera is on
            
            zoom_out_action = camera_menu.addAction("Zoom Out")
            zoom_out_action.triggered.connect(self.zoom_camera_out)
            zoom_out_action.setEnabled(self.camera_enabled and self.camera_zoom_factor > 1.0)  # Only enabled when camera is on and zoomed in
            
            menu.addMenu(camera_menu)
            
            # Add display selection menu
            display_menu = QMenu("Select Display", self)
            display_menu.setProperty("mini", True)
            display_menu.setStyleSheet(menu.styleSheet())
            
            for i, screen in enumerate(self.screens):
                name = screen.name()
                geometry = screen.geometry()
                action = display_menu.addAction(f"Display {i+1}: {name} ({geometry.width()}x{geometry.height()})")
                action.triggered.connect(lambda checked, idx=i: self.on_display_changed(idx))
                
            menu.addMenu(display_menu)
        
        # Show menu below the button
        pos = button.mapToGlobal(QPoint(0, button.height()))
        menu.exec(pos)

    def handle_change_logo(self):
        """Handle changing the brand logo"""
        try:
            # Check if camera is initializing
            if hasattr(self, 'camera_display') and self.camera_display and self.camera_display.text().startswith("Camera starting in"):
                QMessageBox.warning(self, "Camera Initializing", "Please wait for the camera to finish initializing before changing the brand logo.")
                return
                
            # First reset the logo container to ensure clean state
            self.reset_logo_container()
            
            # Create and start file picker thread
            self.file_picker_thread = FilePickerThread()
            self.file_picker_thread.file_selected.connect(self.handle_selected_file)
            self.file_picker_thread.start()
            
        except Exception as e:
            print(f"Error changing logo: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to change brand logo: {str(e)}")
            self.reset_logo_container()

    def contextMenuEvent(self, event):
        """Handle right-click context menu events"""
        if hasattr(self, 'logo_container') and hasattr(self, 'current_image_label') and self.current_image_label:
            container_pos = self.logo_container.mapFromGlobal(event.globalPos())
            if self.logo_container.rect().contains(container_pos):
                self.show_context_menu(event.globalPos())
                event.accept()
                return
        
        super().contextMenuEvent(event)

    def show_context_menu(self, position):
        """Show the context menu at the specified position"""
        if not hasattr(self, 'logo_container') or not hasattr(self, 'current_image_label') or not self.current_image_label:
            return
            
        self.context_menu = QMenu(self)
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 4px 20px;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #666666;
            }
            QMenu::separator {
                height: 1px;
                background: #3d3d3d;
                margin: 4px 0px;
            }
            QMenu::indicator {
                width: 0px;
            }
            QMenu::right-arrow {
                image: none;
                width: 0px;
            }
        """)
        
        change_action = self.context_menu.addAction("Change Brand Logo")
        change_action.triggered.connect(lambda: self.handle_menu_action('change'))
        
        self.context_menu.addSeparator()
        
        zoom_in_action = self.context_menu.addAction("Zoom In")
        zoom_in_action.triggered.connect(lambda: self.handle_menu_action('zoom_in'))
        
        zoom_out_action = self.context_menu.addAction("Zoom Out")
        zoom_out_action.triggered.connect(lambda: self.handle_menu_action('zoom_out'))
        zoom_out_action.setEnabled(self.zoom_factor > 1.0)
        
        # Store the position for future use
        self.menu_position = position
        
        # Show menu immediately at the position
        self.context_menu.popup(position)

    def handle_menu_action(self, action):
        """Handle context menu actions"""
        if action == 'zoom_in':
            self.zoom_in()
            # Create and show new menu immediately
            self.show_context_menu(self.menu_position)
        elif action == 'zoom_out':
            self.zoom_out()
            # Create and show new menu immediately
            self.show_context_menu(self.menu_position)
        elif action == 'change':
            if hasattr(self, 'context_menu'):
                self.context_menu.close()
            self.select_logo()

    def zoom_in(self):
        """Increase image size by 10% of initial height"""
        if not hasattr(self, 'current_image_label') or not self.current_image_label:
            return
        if not hasattr(self, 'current_pixmap') or not self.current_pixmap:
            return

        try:
            # Calculate new height as 10% larger than current
            current_height = self.current_image_label.pixmap().height()
            new_height = int(current_height * 1.1)
            
            # Calculate new width maintaining aspect ratio
            aspect_ratio = self.current_pixmap.width() / self.current_pixmap.height()
            new_width = int(new_height * aspect_ratio)
            
            # Scale the image
            scaled_pixmap = self.current_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Update the label
            self.current_image_label.setPixmap(scaled_pixmap)
            self.current_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Update zoom factor and set user zoomed flag
            self.zoom_factor = new_height / self.initial_height
            self.user_zoomed = True
            print(f"Zoomed in to {self.zoom_factor:.2f}x")
            
        except Exception as e:
            print(f"Error zooming in: {str(e)}")

    def zoom_out(self):
        """Decrease image size by 10% of initial height"""
        if not hasattr(self, 'current_image_label') or not self.current_image_label:
            return
        if not hasattr(self, 'current_pixmap') or not self.current_pixmap:
            return

        try:
            # Calculate new height as 10% smaller than current
            current_height = self.current_image_label.pixmap().height()
            new_height = int(current_height * 0.9)
            
            # Don't allow zooming below initial size
            if new_height < self.initial_height:
                new_height = self.initial_height
            
            # Calculate new width maintaining aspect ratio
            aspect_ratio = self.current_pixmap.width() / self.current_pixmap.height()
            new_width = int(new_height * aspect_ratio)
            
            # Scale the image
            scaled_pixmap = self.current_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Update the label
            self.current_image_label.setPixmap(scaled_pixmap)
            self.current_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Calculate the new zoom factor
            self.zoom_factor = new_height / self.initial_height
            print(f"Zoomed out to {self.zoom_factor:.2f}x")
            
            # Check if we're back to the initial size (within 1%)
            if abs(self.zoom_factor - 1.0) < 0.01:
                self.zoom_factor = 1.0
                self.user_zoomed = False
                # Force an immediate resize to ensure proper scaling
                self.update_image_size(force_resize=True)
                print("Reset to initial size - auto-resize enabled")
            
        except Exception as e:
            print(f"Error zooming out: {str(e)}")

    def update_image_size(self, force_resize=False):
        """Update the image size to fit the container height while maintaining aspect ratio"""
        print("\nStarting update_image_size...")
        if not hasattr(self, 'current_image_label') or not self.current_image_label:
            print("No image label found")
            return
        if not hasattr(self, 'current_pixmap') or not self.current_pixmap:
            print("No pixmap found")
            return

        try:
            # Get container size
            container_size = self.logo_container.size()
            container_height = container_size.height()
            container_width = container_size.width()
            print(f"Container dimensions: {container_width}x{container_height}")
            print(f"Current zoom factor: {self.zoom_factor}")

            # Always resize if forcing or if we're at zoom factor 1.0
            if force_resize or abs(self.zoom_factor - 1.0) < 0.01:
                # Reset zoom state
                self.zoom_factor = 1.0
                self.user_zoomed = False
                print("Reset zoom state to 1.0")

                # Calculate aspect ratio
                aspect_ratio = self.current_pixmap.width() / self.current_pixmap.height()
                
                # Calculate new dimensions to fit container height
                new_height = container_height
                new_width = int(new_height * aspect_ratio)
                print(f"Calculated new dimensions: {new_width}x{new_height}")

                print("Scaling image...")
                # Scale the image
                scaled_pixmap = self.current_pixmap.scaled(
                    new_width,
                    new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                print(f"Scaled pixmap size: {scaled_pixmap.width()}x{scaled_pixmap.height()}")

                print("Updating label...")
                # Update the label to fill container width but maintain scaled height
                self.current_image_label.setFixedSize(container_width, container_height)
                
                # Ensure the scaled pixmap is valid
                if not scaled_pixmap.isNull():
                    self.current_image_label.setPixmap(scaled_pixmap)
                    # Center the image horizontally
                    self.current_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    print("Image update complete")
                    
                    # Update initial height
                    self.initial_height = new_height
                    print(f"Updated initial height to: {self.initial_height}")
                else:
                    print("Error: Scaled pixmap is null")
            else:
                print("Skipping auto-resize as user has manually zoomed")
                # Just update the container size without changing the image size
                self.current_image_label.setFixedSize(container_width, container_height)

        except Exception as e:
            print(f"Error updating image size: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            # Try to recover by resetting the container
            self.reset_logo_container()

    def on_image_loaded(self, pixmap):
        """Handle successful image loading"""
        try:
            self.logo_display.setText("")
            self.logo_display.setPixmap(pixmap)
            self.logo_button.setText("Click to change image")
            self.logo_button.setEnabled(True)
        except Exception as e:
            print(f"Error setting image: {str(e)}")
            self.on_image_error("Failed to display image")
            
    def on_image_error(self, error_msg):
        """Handle image loading error"""
        print(f"Image loading error: {error_msg}")
        self.logo_display.setText("Add Brand Logo")
        self.logo_button.setText("Click to select image")
        self.logo_button.setEnabled(True)

    def update_logo_display(self, has_image=False):
        """Update the logo display text and button based on whether an image is loaded"""
        try:
            if not has_image:
                self.logo_display.clear()
                self.logo_display.setText("Add Brand Logo")
                self.logo_button.setText("Click to select image")
            else:
                self.logo_button.setText("Click to change image")
        except Exception as e:
            print(f"Error updating logo display: {str(e)}")  # Debug print

    def handle_selected_file(self, file_path):
        """Handle the selected file from the file dialog"""
        print(f"\nHandling selected file: {file_path}")
        try:
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return

            # Store the file path for reference
            self.current_image_path = file_path

            print("Loading image...")
            # Try to load image with different formats
            self.current_pixmap = QPixmap()
            success = False

            try:
                # First try direct loading
                if self.current_pixmap.load(file_path):
                    success = True
                else:
                    # If direct loading fails, try loading with QImage first
                    image = QImage(file_path)
                    if not image.isNull():
                        self.current_pixmap = QPixmap.fromImage(image)
                        success = True
            except Exception as e:
                print(f"Error in image loading: {str(e)}")

            if not success or self.current_pixmap.isNull():
                print("Failed to load image")
                QMessageBox.warning(self, "Error", "Failed to load the selected image.")
                return

            print(f"Image loaded successfully, original size: {self.current_pixmap.width()}x{self.current_pixmap.height()}")

            # Get container size
            container_size = self.logo_container.size()
            print(f"Container size: {container_size.width()}x{container_size.height()}")

            try:
                # Clear existing layout and widgets
                print("Clearing existing layout...")
                if self.logo_container.layout():
                    # Store old layout
                    old_layout = self.logo_container.layout()
                    
                    # Remove all widgets from the layout
                    while old_layout.count():
                        item = old_layout.takeAt(0)
                        if item.widget():
                            widget = item.widget()
                            widget.setParent(None)  # Remove parent first
                            widget.deleteLater()  # Schedule for deletion
                    
                    # Clear the layout
                    QWidget().setLayout(old_layout)
                    
                    # Process events to ensure cleanup
                    QApplication.processEvents()
                
                print("Layout cleared")

                # Create new label for image that fills the entire container
                print("Creating image label...")
                self.current_image_label = QLabel(self.logo_container)
                self.current_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Make the label fill the entire container
                self.current_image_label.setMinimumSize(container_size)
                self.current_image_label.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
                print("Label created")

                # Reset zoom state
                self.zoom_factor = 1.0
                self.user_zoomed = False
                print("Reset zoom state")

                # Scale image to fit container height
                print("Scaling image...")
                self.update_image_size(force_resize=True)
                print("Image scaled")

                # Create and set new layout that fills the container
                print("Creating new layout...")
                layout = QVBoxLayout(self.logo_container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                layout.addWidget(self.current_image_label)
                print("Layout created")
                
                # Set the new layout
                print("Setting layout...")
                self.logo_container.setLayout(layout)
                print("Layout set")

                # Update container style
                print("Updating container style...")
                self.logo_container.setStyleSheet("""
                    QFrame#logoContainer {
                        background-color: transparent;
                        border: 2px solid #333333;
                        border-radius: 4px;
                        padding: 0px;
                        margin: 0px;
                    }
                    QFrame#logoContainer:hover {
                        border-color: #444444;
                    }
                """)
                # Set cursor separately using setCursor
                self.logo_container.setCursor(Qt.CursorShape.PointingHandCursor)

                # Store reference to layout and ensure widgets stay alive
                self.current_layout = layout
                self.current_image_label.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

                # Force immediate updates
                print("Forcing updates...")
                QApplication.processEvents()
                layout.activate()
                self.logo_container.updateGeometry()
                self.logo_container.update()
                
                print("Image display complete")

            except Exception as e:
                print(f"Error in layout handling: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                QMessageBox.warning(self, "Error", f"Failed to update logo display: {str(e)}")
                self.reset_logo_container()

        except Exception as e:
            print(f"Error in handle_selected_file: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Error", f"Failed to handle selected file: {str(e)}")
            self.reset_logo_container()

    def is_over_splitter_handle(self, pos):
        """Check if the mouse is over the splitter handle"""
        try:
            if not hasattr(self, 'splitter'):
                return False
                
            # Get splitter handle geometry
            handle = self.splitter.handle(1)  # Get first handle
            if not handle:
                return False
                
            # Convert position to splitter coordinates
            splitter_pos = self.splitter.mapFromGlobal(self.mapToGlobal(pos))
            return handle.geometry().contains(splitter_pos)
            
        except Exception as e:
            print(f"Error checking splitter handle: {str(e)}")
            return False

    def zoom_camera_in(self):
        """Increase camera zoom by 10%"""
        if not self.camera_display or not self.camera_display.pixmap():
            return

        try:
            # Get current pixmap
            current_pixmap = self.camera_display.pixmap()
            if current_pixmap.isNull():
                return

            # Calculate new dimensions (10% larger)
            self.camera_zoom_factor *= 1.1
            new_width = int(current_pixmap.width() * 1.1)
            new_height = int(current_pixmap.height() * 1.1)

            # Scale the pixmap
            scaled_pixmap = current_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Update the display
            self.camera_display.setPixmap(scaled_pixmap)
            self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        except Exception as e:
            print(f"Error zooming camera in: {str(e)}")

    def zoom_camera_out(self):
        """Decrease camera zoom by 10%"""
        if not self.camera_display or not self.camera_display.pixmap():
            return

        try:
            # Get current pixmap
            current_pixmap = self.camera_display.pixmap()
            if current_pixmap.isNull():
                return

            # Calculate new dimensions (10% smaller)
            new_zoom = self.camera_zoom_factor * 0.9
            
            # Don't allow zooming below original size
            if new_zoom < 1.0:
                new_zoom = 1.0
                self.camera_zoom_factor = 1.0
                return
            
            self.camera_zoom_factor = new_zoom
            new_width = int(current_pixmap.width() * 0.9)
            new_height = int(current_pixmap.height() * 0.9)

            # Scale the pixmap
            scaled_pixmap = current_pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Update the display
            self.camera_display.setPixmap(scaled_pixmap)
            self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        except Exception as e:
            print(f"Error zooming camera out: {str(e)}")

    def mouseDoubleClickEvent(self, event):
        """Handle double click on title bar to maximize/restore"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is in title bar area (first 32 pixels)
            if event.position().y() <= 32:
                self.toggle_maximize()
                event.accept()
            else:
                super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def check_for_updates(self):
        """Check for application updates"""
        try:
            import urllib.request
            import json
            
            # Get latest version from GitHub
            with urllib.request.urlopen(self.update_url) as response:
                latest_version = response.read().decode().strip()
                
            if latest_version > self.current_version:
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    f"A new version ({latest_version}) is available. Would you like to update now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.download_update(latest_version)
                    
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")
            
    def download_update(self, version):
        """Download and install the update"""
        try:
            import urllib.request
            import tempfile
            import shutil
            import os
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Download update package
            update_url = f"https://github.com/yourusername/screen-split-app/releases/download/v{version}/screen-split-app-{version}.zip"
            update_file = os.path.join(temp_dir, f"update-{version}.zip")
            
            with urllib.request.urlopen(update_url) as response:
                with open(update_file, 'wb') as f:
                    f.write(response.read())
                    
            # Extract and install update
            import zipfile
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Run update script
            update_script = os.path.join(temp_dir, "update.bat")
            if os.path.exists(update_script):
                subprocess.Popen([update_script])
                self.close()  # Close current instance
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Update Error",
                f"Failed to download update: {str(e)}\nPlease try updating manually."
            )

def main():
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("QApplication created")
        window = ScreenSplitApp()
        print("Window created")
        window.show()
        print("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        print("Full error traceback:")
        traceback.print_exc()
        QMessageBox.critical(None, "Error", f"Failed to start application: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()