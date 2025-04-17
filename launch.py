import sys
import os
import traceback
from pathlib import Path

def main():
    try:
        # Redirect stdout to a file
        sys.stdout = open('app_output.log', 'w')
        sys.stderr = sys.stdout
        
        print("Starting application...")
        print(f"Working directory: {os.getcwd()}")
        
        # Verify the virtual environment is active
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            raise RuntimeError("Virtual environment is not active. Please run 'setup.bat' first.")
        
        print("Verifying imports...")
        # Import required modules
        import PyQt6
        import cv2
        import win32gui
        import win32con
        import win32ui
        import win32api
        import mss
        import numpy
        print("All imports successful")
        
        print("Launching main application...")
        # Import and run the main application
        import screen_app_debug
        return 0
        
    except ImportError as e:
        print(f"Error: Missing required package - {str(e)}")
        print("Please run setup.bat to install all required packages.")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return 1
    finally:
        # Restore stdout/stderr
        if sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__
        if sys.stderr != sys.__stderr__:
            sys.stderr = sys.__stderr__

if __name__ == "__main__":
    sys.exit(main()) 