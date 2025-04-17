import sys
import os
import traceback

def main():
    print("=== Screen Split App Launcher ===")
    print(f"Current directory: {os.getcwd()}")
    print("Python executable:", sys.executable)
    print("Python version:", sys.version)
    print("\nAttempting to start application...")

    try:
        print("\nChecking imports...")
        from PyQt6.QtWidgets import QApplication
        print("PyQt6 ✓")
        import cv2
        print("OpenCV ✓")
        import win32gui
        import win32con
        import win32ui
        import win32api
        print("Win32 modules ✓")
        import mss
        print("MSS ✓")
        import numpy
        print("NumPy ✓")
        
        print("\nStarting application...")
        import app_window
        return app_window.run_app()
        
    except ImportError as e:
        print(f"\nERROR: Failed to import required package")
        print(f"Details: {str(e)}")
        print("\nPlease run setup.bat to install all required packages")
        return 1
        
    except Exception as e:
        print(f"\nERROR: Unexpected error occurred")
        print(f"Details: {str(e)}")
        print("\nFull error trace:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\nApplication exited with code: {exit_code}")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        traceback.print_exc()
        exit_code = 1
    input("\nPress Enter to exit...") 