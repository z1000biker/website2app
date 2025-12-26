import subprocess
import os
import shutil
import glob
from builder.downloader import MinimalToolsDownloader

class BuildEngine:
    def __init__(self, base_dir, logger_callback=None, signing_config=None):
        self.base_dir = base_dir
        self.tools_dir = os.path.join(base_dir, "bin")
        self.logger = logger_callback
        self.signing_config = signing_config
        self.downloader = MinimalToolsDownloader(base_dir, logger=self.log)
        self.jdk_tools = {} # Cache paths for java, javac, keytool

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def check_dependencies(self):
        """Checks for Java and Minimal Tools."""
        self.log("Checking System Dependencies...")
        
        java = shutil.which("java")
        javac = shutil.which("javac")
        keytool = shutil.which("keytool")
        
        # If keytool is missing from PATH, try to find it near javac
        if javac and not keytool:
            jdk_bin = os.path.dirname(javac)
            keytool_alt = os.path.join(jdk_bin, "keytool.exe" if os.name == 'nt' else "keytool")
            if os.path.exists(keytool_alt):
                keytool = keytool_alt
                
        # More aggressive search for keytool on Windows
        if not keytool and os.name == 'nt':
            search_paths = [
                "C:\\Program Files\\Java",
                "C:\\Program Files (x86)\\Java"
            ]
            for sp in search_paths:
                if os.path.exists(sp):
                    for root, dirs, files in os.walk(sp):
                        if "keytool.exe" in files:
                            keytool = os.path.join(root, "keytool.exe")
                            break
                if keytool: break
        
        self.jdk_tools['java'] = java
        self.jdk_tools['javac'] = javac
        self.jdk_tools['keytool'] = keytool
        
        self.log(f"Java: {'Found' if java else 'MISSING'}")
        self.log(f"Javac: {'Found' if javac else 'MISSING'}")
        self.log(f"Keytool: {'Found' if keytool else 'MISSING'}")
        
        if not java or not javac:
            return False, "Java JDK is missing. Please install Java JDK 8 or 11/17."
        
        if not keytool:
            self.log("Warning: keytool not found. Signing (Step 7) might fail.")

        # Check if minimal tools are already downloaded
        if not self.downloader.is_installed():
            self.log("Minimal tools not found. Starting auto-download...")
            if not self.downloader.download_and_setup():
                return False, "Failed to download minimal build tools."
        
        return True, "Minimal tools and Java are ready."

    def build(self, project_path, variant="Debug"):
        """
        SDK-less build pipeline:
        1. Compile Resources (aapt2 compile)
        2. Link Resources (aapt2 link) -> creates R.java and base APK
        3. Compile Java source to .class (javac)
        4. Dex classes to classes.dex (d8)
        5. Add classes.dex to APK
        6. Align (zipalign)
        7. Sign (apksigner)
        """
        try:
            # Setup paths
            bin_dir = self.tools_dir
            aapt2 = os.path.join(bin_dir, "aapt2.exe")
            zipalign = os.path.join(bin_dir, "zipalign.exe")
            android_jar = os.path.join(bin_dir, "android.jar")
            
            # Find d8 and apksigner (might be jars or bat/exe)
            d8 = self._find_tool("d8")
            apksigner = self._find_tool("apksigner")

            # Project paths
            app_dir = os.path.join(project_path, "app")
            src_main = os.path.join(app_dir, "src", "main")
            res_dir = os.path.join(src_main, "res")
            manifest = os.path.join(src_main, "AndroidManifest.xml")
            java_src = os.path.join(src_main, "java")
            
            build_work_dir = os.path.join(app_dir, "build_manual")
            os.makedirs(build_work_dir, exist_ok=True)
            
            self.log("Step 1: Compiling resources...")
            compiled_res = os.path.join(build_work_dir, "compiled_res.zip")
            cmd = [aapt2, "compile", "--dir", res_dir, "-o", compiled_res]
            self._run_cmd(cmd)

            self.log("Step 2: Linking resources and generating R.java...")
            gen_java_dir = os.path.join(build_work_dir, "gen")
            os.makedirs(gen_java_dir, exist_ok=True)
            unsigned_apk = os.path.join(build_work_dir, "unsigned.apk")
            cmd = [
                aapt2, "link", "-I", android_jar, 
                "--manifest", manifest,
                compiled_res,
                "-o", unsigned_apk,
                "--java", gen_java_dir,
                "--auto-add-overlay"
            ]
            self._run_cmd(cmd)

            self.log("Step 3: Compiling Java source...")
            obj_dir = os.path.join(build_work_dir, "obj")
            os.makedirs(obj_dir, exist_ok=True)
            
            # Find all java files
            java_files = glob.glob(os.path.join(java_src, "**", "*.java"), recursive=True)
            java_files += glob.glob(os.path.join(gen_java_dir, "**", "*.java"), recursive=True)
            
            # Enforce Java 8 compatibility to ensure d8 can process the class files
            javac_cmd = self.jdk_tools.get('javac', 'javac')
            cmd = [javac_cmd, "-source", "1.8", "-target", "1.8", "-d", obj_dir, "-cp", android_jar] + java_files
            self._run_cmd(cmd)

            self.log("Step 4: Dexing class files...")
            dex_file = os.path.join(build_work_dir, "classes.dex")
            class_files = glob.glob(os.path.join(obj_dir, "**", "*.class"), recursive=True)
            
            if d8.endswith(".jar"):
                cmd = ["java", "-Xmx1024M", "-cp", d8, "com.android.tools.r8.D8"]
            else:
                cmd = [d8]
            
            # Explicitly set min-api to 21 to avoid some D8/R8 NPEs with modern bytecode
            cmd += ["--min-api", "21", "--lib", android_jar, "--output", build_work_dir] + class_files
            self._run_cmd(cmd)

            self.log("Step 5: Injecting classes.dex into APK...")
            # We can use aapt2 or just a zip tool. aapt2 'add' isn't standard, usually we use jar or zip.
            # But aapt2 link can take --java as input? No. 
            # We'll use a zip library or just 'jar' if available.
            self._add_to_zip(unsigned_apk, dex_file, "classes.dex")

            self.log("Step 6: Aligning APK...")
            aligned_apk = os.path.join(build_work_dir, "aligned.apk")
            cmd = [zipalign, "-f", "4", unsigned_apk, aligned_apk]
            self._run_cmd(cmd)

            # Step 7: Sign APK
            final_apk = os.path.join(project_path, f"output_{variant.lower()}.apk")
            
            # Prioritize custom keystore if Variant is Release OR if auto_sign is disabled
            use_custom = False
            if self.signing_config:
                if variant == "Release" or not self.signing_config.get('auto_sign', True):
                    use_custom = True

            if use_custom:
                ks = self.signing_config.get('custom_ks', {})
                ks_path = ks.get('path')
                ks_pass = ks.get('pass')
                ks_alias = ks.get('alias')
                ks_key_pass = ks.get('key_pass')
                
                if ks_path and os.path.exists(ks_path) and ks_alias:
                    self.log(f"Step 7: Signing APK (Release/Custom)...")
                    if apksigner.endswith(".jar"):
                        cmd = ["java", "-Xmx1024M", "-jar", apksigner]
                    else:
                        cmd = [apksigner]
                    cmd += [
                        "sign", 
                        "--ks", ks_path, 
                        "--ks-pass", f"pass:{ks_pass}",
                        "--ks-key-alias", ks_alias,
                        "--key-pass", f"pass:{ks_key_pass}",
                        "--out", final_apk, aligned_apk
                    ]
                    self._run_cmd(cmd)
                    self.log(f"RELEASE BUILD SUCCESSFUL! APK at: {final_apk}")
                    return True
                else:
                    self.log("Warning: Custom keystore info incomplete. Falling back to debug.")
            
            # Fallback to debug keystore if specifically Debug variant OR if release info is missing
            self.log(f"Step 7: Signing APK ({variant})...")
            if variant == "Release" and (not self.signing_config or self.signing_config.get('auto_sign', True)):
                 self.log("Warning: Release variant requested but no custom keystore provided. Using debug keystore.")
            
            debug_keystore = os.path.join(self.base_dir, "debug.keystore")
            if not os.path.exists(debug_keystore):
                self._gen_debug_keystore(debug_keystore)

            if apksigner.endswith(".jar"):
                cmd = ["java", "-Xmx1024M", "-jar", apksigner]
            else:
                cmd = [apksigner]
                
            cmd += ["sign", "--ks", debug_keystore, "--ks-pass", "pass:android", "--out", final_apk, aligned_apk]
            self._run_cmd(cmd)

            self.log(f"DEBUG BUILD SUCCESSFUL! APK at: {final_apk}")
            return True

        except Exception as e:
            self.log(f"BUILD FAILED: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return False

    def _run_cmd(self, cmd):
        # Normalize all paths in the command to avoid issues with mixed slashes or non-ASCII
        # Note: We only normalize strings that look like paths (contain / or \)
        safe_cmd = []
        for arg in cmd:
            if isinstance(arg, str) and (os.sep in arg or '/' in arg or '\\' in arg):
                # Only normalize if the path exists or looks like one we just created
                safe_cmd.append(os.path.normpath(arg))
            else:
                safe_cmd.append(str(arg))

        self.log(f"Executing: {' '.join(['\"'+a+'\"' if ' ' in a else a for a in safe_cmd])}")
        
        # Use a more robust way to handle non-ASCII paths on Windows
        try:
            res = subprocess.run(safe_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
            if res.returncode != 0:
                error_msg = res.stderr.strip() if res.stderr else "Unknown error (empty stderr)"
                raise Exception(f"Command failed with exit code {res.returncode}: {error_msg}")
        except Exception as e:
            if "Command failed" in str(e):
                raise e
            raise Exception(f"Failed to execute command: {str(e)}")

    def _find_tool(self, name):
        """Finds tool in bin dir, supports .jar, .exe, .bat."""
        # Prioritize .jar so we can control JVM args directly
        for ext in [".jar", ".exe", ".bat", ""]:
            path = os.path.join(self.tools_dir, name + ext)
            if os.path.exists(path):
                return path
        raise Exception(f"Tool {name} not found in {self.tools_dir}")

    def _add_to_zip(self, zip_path, file_to_add, arcname):
        import zipfile
        with zipfile.ZipFile(zip_path, 'a') as z:
            z.write(file_to_add, arcname)

    def _gen_debug_keystore(self, path):
        self.log("Generating debug keystore...")
        keytool = self.jdk_tools.get('keytool', 'keytool')
        cmd = [
            keytool, "-genkey", "-v", "-keystore", path, 
            "-storepass", "android", "-alias", "androiddebugkey", 
            "-keypass", "android", "-keyalg", "RSA", "-keysize", "2048", 
            "-validity", "10000", "-dname", "CN=Android Debug,O=Android,C=US"
        ]
        self._run_cmd(cmd)

class ADBManager:
    def __init__(self, tools_dir, logger=None):
        self.adb = os.path.join(tools_dir, "adb.exe")
        self.logger = logger

    def log(self, msg):
        if self.logger: self.logger(msg)

    def list_devices(self):
        try:
            res = subprocess.run([self.adb, "devices"], capture_output=True, text=True, shell=True)
            lines = res.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
            return devices
        except:
            return []

    def install_apk(self, device_id, apk_path):
        if not os.path.exists(apk_path):
            return False, "APK file not found."
        
        self.log(f"Installing to {device_id}...")
        cmd = [self.adb, "-s", device_id, "install", "-r", apk_path]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            self.log("Install Successful!")
            return True, "Success"
        else:
            self.log(f"Install Failed: {res.stderr}")
            return False, res.stderr

class APKAnalyzer:
    def __init__(self, aapt2_path):
        self.aapt2 = aapt2_path

    def get_info(self, apk_path):
        if not os.path.exists(apk_path):
            return "APK file not found."
        try:
            # aapt2 dump badging is the standard way to get APK info
            cmd = [self.aapt2, "dump", "badging", apk_path]
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if res.returncode == 0:
                return res.stdout
            else:
                return f"Analysis failed: {res.stderr}"
        except Exception as e:
            return f"Error during analysis: {str(e)}"
