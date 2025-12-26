# WebSite to Android & iOS App

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.8%2B-green" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Android-APK-brightgreen" alt="Android">
  <img src="https://img.shields.io/badge/iOS-Xcode%20Project-lightgrey" alt="iOS">
</p>

A professional desktop application that transforms any website URL or local HTML files into fully functional **Android APKs** and **iOS Xcode Projects** — without requiring the full Android SDK or Xcode installed on your development machine.

---

## ✨ Features

### 🤖 Android APK Generation
- **SDK-less Build Pipeline**: No need to install the full Android SDK. The tool automatically downloads and manages `aapt2`, `d8`, `zipalign`, and `apksigner`.
- **Zero AndroidX Dependencies**: Generates pure, lightweight APKs without AppCompat or other external libraries.
- **Debug & Release Variants**: Choose between Debug (auto-signed) or Release (custom keystore) builds.
- **Auto-generated Assets**: If no icon is provided, a default professional icon is generated automatically.
- **OneDrive Compatible**: Robust file handling that works seamlessly in cloud-synced folders.

### 🍎 iOS Project Export
- **Complete Xcode Project**: Generates a ready-to-build `.xcodeproj` folder structure.
- **Swift & SwiftUI**: Modern Swift source code with WKWebView integration.
- **Asset Catalog Generation**: Automatically creates `AppIcon.appiconset` with all required icon sizes.
- **Info.plist Configuration**: Bundle ID, version, and display name are templated automatically.

### ⚙️ Advanced Configuration
- **Web Content Modes**: Load content from a remote URL, a local folder, or a single HTML file.
- **WebView Options**: Enable/disable JavaScript, DOM Storage, Zoom, File Access, and more.
- **Custom User Agent & Headers**: Inject custom HTTP headers for authenticated or specialized content.
- **Permissions**: Request Camera, Microphone, Geolocation, and other Android permissions.
- **Splash Screen**: Configure a splash image with customizable duration.

### 🛠️ Development Tools
- **ADB Integration**: Detect connected devices and install APKs directly with one click.
- **APK Analyzer**: Inspect the built APK's manifest, permissions, and package info.
- **Build History**: Track all your builds with timestamps and configurations.
- **Project Save/Load**: Save your configuration to `.w2apk` project files and reload them anytime.

---

## 📸 Screenshots

*(Coming Soon)*

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- **Java JDK 8, 11, or 17** (must be in your system PATH or discoverable)
- **Windows OS** (primary support; macOS/Linux may require minor adjustments)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/z1000biker/website2app.git
    cd website2app
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python main.py
    ```

### First Run
On the first run, the application will automatically download the required Android build tools (`aapt2`, `d8`, `zipalign`, `apksigner`) to the `bin/` directory. This is a one-time operation.

---

## 📖 Usage Guide

### Building an Android APK
1.  Launch the application.
2.  Fill in **Project Metadata**: App Name, Package Name (e.g., `com.yourcompany.app`), Version.
3.  Select **Web Content** mode:
    - **URL (Remote)**: Enter the website URL.
    - **Local Folder**: Select a directory containing `index.html`.
    - **Single HTML File**: Select a standalone `.html` file.
4.  (Optional) Configure an **App Icon** and **Splash Screen**.
5.  Navigate to the **Android Settings** tab.
6.  Enable any desired **Extras** (Zoom, Downloads, Geolocation, etc.).
7.  Choose **Build Variant**: `Debug` or `Release`.
8.  Click **BUILD ANDROID APK**.
9.  The output APK will be saved to your specified **Output Directory**.

### Exporting an iOS Project
1.  Configure your project metadata as above.
2.  Navigate to the **iOS Settings** tab.
3.  Set the **Bundle ID** and **Display Name**.
4.  Click **EXPORT iOS PROJECT**.
5.  The tool will create a `WebApp_iOS/` folder in your output directory.
6.  Transfer this folder to a Mac with Xcode.
7.  Open `WebApp.xcodeproj` and click **Run** to build for a simulator or device.

### Installing to Android Device
1.  Connect your Android device via USB (ensure USB Debugging is enabled).
2.  Click the **🔄 (Refresh)** button next to the device dropdown to detect devices.
3.  Select your device from the list.
4.  Click **Install to Device**.

---

## 📁 Project Structure

```
website2app/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── bin/                    # Auto-downloaded Android build tools
│   ├── aapt2.exe
│   ├── d8.jar
│   ├── zipalign.exe
│   ├── apksigner.jar
│   └── android.jar
├── assets/
│   ├── template/           # Android Java/XML templates (Jinja2)
│   │   ├── MainActivity.java
│   │   ├── AndroidManifest.xml
│   │   └── build.gradle
│   └── template_ios/       # iOS Swift/Xcode templates (Jinja2)
│       ├── WebApp/
│       │   ├── WebAppApp.swift
│       │   ├── ContentView.swift
│       │   ├── AppDelegate.swift
│       │   └── Info.plist
│       └── WebApp.xcodeproj/
│           └── project.pbxproj
├── builder/
│   ├── engine.py           # Core build logic (compile, dex, sign)
│   ├── generator.py        # Android project generator
│   ├── generator_ios.py    # iOS project generator
│   ├── downloader.py       # Tool auto-downloader
│   └── project_manager.py  # Save/Load/History logic
└── gui/
    ├── main_window.py      # Main PyQt6 window
    ├── widgets.py          # Custom UI widgets (FilePicker, etc.)
    └── styles.qss          # Stylesheet for premium UI
```

---

## ⚙️ Configuration Options

### Android WebView Settings
| Option                | Description                                      |
|-----------------------|--------------------------------------------------|
| Enable JavaScript     | Allow JS execution in the WebView                |
| Enable DOM Storage    | Allow local/session storage                      |
| Enable File Access    | Allow `file://` protocol access                  |
| Enable Zoom           | Allow pinch-to-zoom                              |
| Show Progress Bar     | Display loading indicator                        |
| Exit on Back          | Close app when back is pressed at root           |
| Custom User Agent     | Override the default WebView user agent          |
| Additional Headers    | Inject custom HTTP headers (JSON format)         |

### Android Permissions
- `INTERNET` (always included)
- `CAMERA`
- `MICROPHONE`
- `ACCESS_FINE_LOCATION` (Geolocation)
- `WRITE_EXTERNAL_STORAGE` (Downloads)

### iOS App Transport Security
The generated iOS project includes `NSAllowsArbitraryLoads = true` in `Info.plist` to allow loading mixed content. For production, you should configure App Transport Security exceptions properly.

---

## 🔐 APK Signing

### Debug Signing (Default)
- A debug keystore is generated automatically in the `bin/` directory.
- The APK is signed with alias `androiddebugkey` and password `android`.

### Release Signing
1.  Uncheck **Auto-generate Keystore (Debug)**.
2.  Provide your custom keystore path, password, alias, and key password.
3.  Select **Release** from the Build Variant dropdown.
4.  The APK will be signed with your custom keystore.

---

## 🧰 Troubleshooting

### "Java not found" or "javac not recognized"
- Ensure Java JDK (8, 11, or 17) is installed and `JAVA_HOME` is set, or the `java` and `javac` executables are in your system PATH.

### "Unsupported class file major version"
- This means your Java version is too new. The tool enforces `-source 1.8 -target 1.8` for compatibility, but ensure you have a compatible JDK.

### "keytool not recognized"
- The application attempts to locate `keytool` in standard JDK paths. If it fails, add your JDK's `bin` directory to PATH.

### APK installation fails on device
- **Uninstall previous versions** of the app on the device if you've rebuilt with a different signing key.
- Ensure **USB Debugging** is enabled on the device.
- Check that the device's Android version is 5.0 (API 21) or higher.

### iOS project doesn't build in Xcode
- Ensure you have Xcode 13+ installed on your Mac.
- Open the `.xcodeproj` file, select your team for signing, and try building again.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **PyQt6** for the cross-platform GUI framework.
- **Jinja2** for powerful templating.
- **Pillow** for image processing.
- The Android Open Source Project for `aapt2`, `d8`, and related tools.

---

## 📬 Contact

Created by **Nikos Kontopoulos** — feel free to reach out!

- **GitHub**: [@z1000biker](https://github.com/z1000biker)
- **Email**: sv1eex@hotmail.com

---

<p align="center">
  <b>Happy Building! 🚀</b>
</p>
