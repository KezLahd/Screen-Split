import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("PyQt6 Test")
    window.setGeometry(100, 100, 300, 200)
    
    label = QLabel("PyQt6 is working!", window)
    label.setGeometry(50, 80, 200, 30)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 