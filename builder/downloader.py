import os
import zipfile
import urllib.request
import shutil

class MinimalToolsDownloader:
    # Google Repository Links
    BUILD_TOOLS_URL = "https://dl.google.com/android/repository/build-tools_r33.0.1-windows.zip"
    PLATFORM_URL = "https://dl.google.com/android/repository/platform-33_r02.zip"
    PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

    def __init__(self, base_dir, logger=None):
        self.base_dir = base_dir
        self.tools_dir = os.path.join(base_dir, "bin")
        self.logger = logger or print

    def log(self, msg):
        self.logger(msg)

    def is_installed(self):
        """Checks if essential tools exist."""
        essentials = [
            os.path.join(self.tools_dir, "aapt2.exe"),
            os.path.join(self.tools_dir, "zipalign.exe"),
            os.path.join(self.tools_dir, "android.jar")
        ]
        return all(os.path.exists(f) for f in essentials)

    def download_and_setup(self):
        if self.is_installed():
            self.log("Minimal tools already installed.")
            return True

        os.makedirs(self.tools_dir, exist_ok=True)
        temp_dir = os.path.join(self.base_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 1. Download Build Tools
            bt_zip = os.path.join(temp_dir, "build-tools.zip")
            self.log("Downloading Build Tools (~50MB)...")
            urllib.request.urlretrieve(self.BUILD_TOOLS_URL, bt_zip)
            
            self.log("Extracting essential build binaries...")
            with zipfile.ZipFile(bt_zip, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    # We only need a few things
                    if any(x in file for x in ["aapt2.exe", "zipalign.exe", "apksigner", "d8"]):
                        filename = os.path.basename(file)
                        if filename:
                            with zip_ref.open(file) as source, open(os.path.join(self.tools_dir, filename), "wb") as target:
                                shutil.copyfileobj(source, target)
            
            # 2. Download Platform (for android.jar)
            p_zip = os.path.join(temp_dir, "platform.zip")
            self.log("Downloading Android Platform jar (~70MB)...")
            urllib.request.urlretrieve(self.PLATFORM_URL, p_zip)
            
            self.log("Extracting android.jar...")
            with zipfile.ZipFile(p_zip, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith("android.jar"):
                        with zip_ref.open(file) as source, open(os.path.join(self.tools_dir, "android.jar"), "wb") as target:
                            shutil.copyfileobj(source, target)
                            break
            
            # 3. Download Platform Tools (ADB)
            pt_zip = os.path.join(temp_dir, "platform-tools.zip")
            self.log("Downloading Platform Tools (ADB) (~5MB)...")
            urllib.request.urlretrieve(self.PLATFORM_TOOLS_URL, pt_zip)
            
            self.log("Extracting ADB...")
            with zipfile.ZipFile(pt_zip, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith("adb.exe") or file.endswith("AdbWinApi.dll") or file.endswith("AdbWinUsbApi.dll"):
                        filename = os.path.basename(file)
                        with zip_ref.open(file) as source, open(os.path.join(self.tools_dir, filename), "wb") as target:
                            shutil.copyfileobj(source, target)

            self.log("Minimal SDK setup complete (including ADB).")
            return True

        except Exception as e:
            self.log(f"Setup failed: {str(e)}")
            return False
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
