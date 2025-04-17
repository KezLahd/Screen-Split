from PyQt6.QtWidgets import QApplication
import screen_app_debug
import sys

def create_window():
    print("Creating application window...")
    window = screen_app_debug.ScreenSplitApp()
    print("Showing application window...")
    window.show()
    window.raise_()
    window.activateWindow()
    print("Window should now be visible")
    return window

def run_app():
    app = QApplication(sys.argv)
    window = create_window()
    return app.exec()

if __name__ == "__main__":
    sys.exit(run_app()) 