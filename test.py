from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
import sys

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Test Window")
window.setGeometry(100, 100, 400, 300)

label = QLabel("Test successful!", window)
label.setGeometry(150, 120, 200, 50)

window.show()
sys.exit(app.exec()) 