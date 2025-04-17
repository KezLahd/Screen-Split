# Screen Split App

A professional screen splitting application that allows you to view your screen and camera simultaneously, with support for adding a brand logo.

## Features

- Screen capture from any display
- Camera feed with zoom controls
- Brand logo support with zoom functionality
- Modern dark theme UI
- Resizable window with smooth animations
- Customizable layout

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10 or higher

### Method 1: Using pip (Recommended)
1. Open Command Prompt as Administrator
2. Run the following commands:
```bash
pip install screen-split-app
```

### Method 2: Manual Installation
1. Download the latest release from the [releases page](https://github.com/KezLahd/Screen-Split/releases)
2. Extract the zip file
3. Open Command Prompt in the extracted folder
4. Run:
```bash
pip install -r requirements.txt
python setup.py install
```

## Usage

1. Launch the application by running:
```bash
screen-split
```

2. Or use the desktop shortcut created during installation

### Controls
- **Camera Controls**:
  - Click the camera icon to toggle camera
  - Use zoom buttons to adjust camera zoom
  - Right-click for additional options

- **Logo Controls**:
  - Click the logo area to add/change logo
  - Right-click for zoom controls
  - Drag to resize window

- **Display Selection**:
  - Right-click on the screen area
  - Select "Select Display" to choose which screen to capture

## Updates

The application will automatically check for updates when launched. You can also manually check for updates by:
1. Right-clicking on the title bar
2. Selecting "Check for Updates"

## Troubleshooting

If you encounter any issues:
1. Check the error log in `%APPDATA%\Screen Split App\logs`
2. Make sure all dependencies are installed correctly
3. Ensure your camera drivers are up to date
4. Try running the application as administrator

## Support

For support, please:
1. Check the [documentation](https://github.com/KezLahd/Screen-Split/wiki)
2. Open an issue on GitHub
3. Contact support@example.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.