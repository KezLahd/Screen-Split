from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

def main():
    try:
        print("Creating application...")
        app = QApplication([])
        print("Created QApplication")
        
        window = QMainWindow()
        print("Created QMainWindow")
        
        label = QLabel("Testing PyQt6")
        print("Created QLabel")
        
        window.setCentralWidget(label)
        window.setWindowTitle("PyQt6 Test")
        window.resize(400, 200)
        window.show()
        print("Window shown")
        
        app.exec()
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 