import os
import sys
import subprocess
import time

def launch_app():
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Current directory: {current_dir}")
        
        # Path to the main application
        app_path = os.path.join(current_dir, "screen_app_fixed.pyw")
        print(f"App path: {app_path}")
        
        # Check if the app exists
        if not os.path.exists(app_path):
            print(f"Error: Could not find {app_path}")
            return False
            
        # Launch the application using pythonw.exe
        pythonw_path = os.path.join(current_dir, "venv", "Scripts", "pythonw.exe")
        if not os.path.exists(pythonw_path):
            print(f"Error: Could not find Python executable at {pythonw_path}")
            return False
            
        print("Launching application...")
        subprocess.Popen([pythonw_path, app_path])
        print("Application launched successfully!")
        return True
        
    except Exception as e:
        print(f"Error launching application: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Screen Split App...")
    if launch_app():
        print("Application launched successfully!")
    else:
        print("Failed to launch application.")
    time.sleep(2)  # Keep the window open for 2 seconds 