import os
import subprocess
import shutil
from pathlib import Path
import uuid
import json

def create_version_info():
    """Create Windows version info file"""
    version_info = """VSVersionInfo(
      ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
      ),
      kids=[
        StringFileInfo([
          StringTable(
            u'040904B0',
            [StringStruct(u'CompanyName', u'Your Company'),
             StringStruct(u'FileDescription', u'Screen Split Application'),
             StringStruct(u'FileVersion', u'1.0.0'),
             StringStruct(u'InternalName', u'screen_split'),
             StringStruct(u'LegalCopyright', u'© 2024 Your Company. All rights reserved.'),
             StringStruct(u'OriginalFilename', u'Screen Split.exe'),
             StringStruct(u'ProductName', u'Screen Split'),
             StringStruct(u'ProductVersion', u'1.0.0')])
        ])
      ]
    )"""
    
    with open('file_version_info.txt', 'w') as f:
        f.write(version_info)

def ensure_assets():
    """Ensure assets directory exists"""
    os.makedirs('assets', exist_ok=True)
    # Copy your icon file to assets/icon.ico
    # TODO: Add your icon file here

def build_executable():
    """Build executable with PyInstaller"""
    print("Creating version info...")
    create_version_info()
    
    print("Ensuring assets...")
    ensure_assets()
    
    print("Building executable with PyInstaller...")
    pyinstaller_path = os.path.join('venv', 'Scripts', 'pyinstaller.exe')
    subprocess.run([pyinstaller_path, 'screen_split.spec'], check=True)
    print("Executable built successfully!")

def create_installer():
    """Create installer with Inno Setup"""
    print("Creating installer with Inno Setup...")
    
    # Generate a unique app ID if not exists
    app_id = str(uuid.uuid4())
    
    # Create the Inno Setup script
    iss_content = f"""#define MyAppName "Screen Split"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://your-website.com"
#define MyAppExeName "Screen Split.exe"

[Setup]
AppId={{{app_id}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=ScreenSplit-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardImageFile=assets/wizard.bmp
WizardSmallImageFile=assets/wizard-small.bmp
SetupIconFile=assets/icon.ico
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}

; Sign the installer if you have a code signing certificate
; SignTool=signtool sign /f "$f" /t http://timestamp.digicert.com $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\\Screen Split\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "dist\\Screen Split\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\Uninstall {{#MyAppName}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}"

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{#SetupSetting("AppId")}}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) and (IsUpgrade()) then
    UnInstallOldVersion();
end;
"""
    
    # Write the Inno Setup script
    with open('installer.iss', 'w') as f:
        f.write(iss_content)
    
    # Run Inno Setup compiler
    subprocess.run(['iscc', 'installer.iss'], check=True)
    print("Installer created successfully!")

def main():
    """Main build process"""
    try:
        # Create necessary directories
        os.makedirs('installer', exist_ok=True)
        os.makedirs('assets', exist_ok=True)
        
        # Build the executable
        build_executable()
        
        # Create the installer
        create_installer()
        
        print("\nInstallation package created successfully!")
        print("You can find the installer in the 'installer' directory.")
        
        # Create version info for GitHub release
        version_info = {
            "version": "1.0.0",
            "release_notes": "Initial release of Screen Split Application",
            "installer_url": "https://your-website.com/downloads/ScreenSplit-Setup.exe"
        }
        
        with open('installer/release_info.json', 'w') as f:
            json.dump(version_info, f, indent=2)
            
    except Exception as e:
        print(f"Error creating installer: {str(e)}")
        raise

if __name__ == '__main__':
    main() 