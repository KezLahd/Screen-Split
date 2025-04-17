import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QSplitter)
from PyQt6.QtCore import Qt

class SimpleScreenSplitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Screen Split")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_label = QLabel("Left Panel")
        left_layout.addWidget(left_label)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_label = QLabel("Right Panel")
        right_layout.addWidget(right_label)
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        
        # Set up main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.splitter)

if __name__ == '__main__':
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("QApplication created")
        window = SimpleScreenSplitApp()
        print("Window created")
        window.show()
        print("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1) 