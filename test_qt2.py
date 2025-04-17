import sys
from PyQt6.QtWidgets import *

def main():
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("Created QApplication")
        
        window = QWidget()
        print("Created QWidget")
        
        window.setWindowTitle("PyQt6 Test")
        window.resize(300, 200)
        print("Set window properties")
        
        layout = QVBoxLayout()
        label = QLabel("Testing PyQt6")
        layout.addWidget(label)
        window.setLayout(layout)
        print("Added layout and label")
        
        window.show()
        print("Showed window")
        
        return app.exec()
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 