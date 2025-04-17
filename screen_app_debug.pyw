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
                            rect = win32gui.GetWindowRect(hwnd)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            if width > 50 and height > 50:
                                window_handles[title] = hwnd
                                window_titles.append(title)
                        except Exception:
                            pass
                return True
            
            win32gui.EnumWindows(winEnumHandler, None)
            self.windows_ready.emit(window_handles, window_titles)
        except Exception as e:
            print(f"Error enumerating windows: {str(e)}") 

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