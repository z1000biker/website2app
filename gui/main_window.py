import sys
import os
import threading
import json
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTabWidget, QFormLayout, QLineEdit, 
                             QComboBox, QSpinBox, QCheckBox, QTextEdit, 
                             QPushButton, QGridLayout, QGroupBox, QScrollArea, 
                             QMessageBox, QFileDialog, QProgressBar, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from gui.widgets import FilePicker
from builder.generator import ProjectGenerator
from builder.engine import BuildEngine
from builder.project_manager import ProjectManager, HistoryManager

class Signaller(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)
    status = pyqtSignal(str)
    progress = pyqtSignal(int)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebSite to Android & iOS App")
        self.resize(1100, 850)
        
        self.project_manager = ProjectManager(self)
        self.history_manager = HistoryManager(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Load Stylesheet
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.signaller = Signaller()
        self.signaller.log.connect(self.log)
        self.signaller.finished.connect(self.post_build)
        self.signaller.status.connect(self.update_status)
        self.signaller.progress.connect(self.update_progress)

        self.setup_menu()
        self.setup_header()
        self.setup_body()
        self.setup_output_section()
        self.setup_status_bar()

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        
        new_act = file_menu.addAction('New')
        new_act.triggered.connect(self.reset_fields)
        
        open_act = file_menu.addAction('Open Project')
        open_act.triggered.connect(self.load_project_ui)
        
        save_act = file_menu.addAction('Save Project')
        save_act.triggered.connect(self.save_project_ui)
        
        file_menu.addSeparator()
        exit_act = file_menu.addAction('Exit')
        exit_act.triggered.connect(self.close)

        history_menu = menubar.addMenu('&History')
        view_history_act = history_menu.addAction('View Build History')
        view_history_act.triggered.connect(self.show_history)

        build_menu = menubar.addMenu('&Build')
        validate_act = build_menu.addAction('Validate')
        validate_act.triggered.connect(self.validate_project)
        build_act = build_menu.addAction('Build APK')
        build_act.triggered.connect(self.start_build_thread)

    def setup_header(self):
        header = QWidget()
        header.setFixedHeight(80)
        layout = QHBoxLayout(header)
        
        # Logo Placeholder
        logo_label = QLabel("W2APK")
        logo_label.setFixedSize(60, 60)
        logo_label.setStyleSheet("background-color: #e74c3c; border-radius: 30px; color: white; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_container = QWidget()
        t_layout = QVBoxLayout(title_container)
        title = QLabel("WebSite to Android & iOS App")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Transform your site into a mobile app (Android & iOS)")
        subtitle.setObjectName("headerSubtitle")
        t_layout.addWidget(title)
        t_layout.addWidget(subtitle)
        
        layout.addWidget(logo_label)
        layout.addWidget(title_container)
        layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        icons = ["📄", "🔄", "ℹ️"]
        callbacks = [self.show_docs, self.check_deps_action, self.show_about]
        for icon_text, callback in zip(icons, callbacks):
            btn = QPushButton(icon_text)
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("background: #f8f9fa; border: 1px solid #ccc; border-radius: 20px; font-size: 18px;")
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        self.main_layout.addWidget(header)

    def setup_body(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # 2. Project Metadata
        meta_group = QGroupBox("Project Metadata")
        meta_layout = QGridLayout()
        
        meta_layout.addWidget(QLabel("App Name:"), 0, 0)
        self.app_title = QLineEdit("My Android App")
        meta_layout.addWidget(self.app_title, 0, 1, 1, 3)
        
        meta_layout.addWidget(QLabel("Package Name:"), 1, 0)
        self.pkg_input = QLineEdit("com.kontopoulos.app")
        meta_layout.addWidget(self.pkg_input, 1, 1, 1, 3)
        
        meta_layout.addWidget(QLabel("Version Name:"), 2, 0)
        self.ver_name = QLineEdit("1.0.0")
        meta_layout.addWidget(self.ver_name, 2, 1)
        
        meta_layout.addWidget(QLabel("Version Code:"), 2, 2)
        self.ver_code = QSpinBox()
        self.ver_code.setRange(1, 100000)
        self.ver_code.setValue(1)
        meta_layout.addWidget(self.ver_code, 2, 3)
        
        docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
        self.out_dir = FilePicker("Output Directory", mode='dir')
        self.out_dir.set_path(docs_dir)
        meta_layout.addWidget(self.out_dir, 3, 0, 1, 4)
        
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)
        
        # 3. Web Content
        web_group = QGroupBox("Web Content")
        web_layout = QFormLayout()
        
        self.web_mode = QComboBox()
        self.web_mode.addItems(["URL (Remote)", "Local Folder", "Single HTML File"])
        self.web_mode.currentIndexChanged.connect(self.on_web_mode_change)
        web_layout.addRow("Input Method:", self.web_mode)
        
        self.web_path = FilePicker("Content Path", mode='dir')
        self.web_path.set_path(docs_dir)
        web_layout.addRow(self.web_path)
        
        self.url_input = QLineEdit("https://www.google.com")
        web_layout.addRow("URL:", self.url_input)
        
        self.start_page = QLineEdit("index.html")
        web_layout.addRow("Start Page:", self.start_page)
        
        web_group.setLayout(web_layout)
        layout.addWidget(web_group)
        
        layout.addWidget(web_group)
        
        # Tabs for Platform Specific Settings
        self.tabs = QTabWidget()
        
        # --- Android Tab ---
        android_tab = QWidget()
        android_layout = QVBoxLayout(android_tab)
        
        # 4. App Configuration
        conf_group = QGroupBox("App Configuration")
        conf_layout = QGridLayout()
        
        self.icon_path = FilePicker("App Icon (PNG/JPEG)", mode='file')
        conf_layout.addWidget(self.icon_path, 0, 0, 1, 2)
        
        self.splash_path = FilePicker("Splash Image", mode='file')
        conf_layout.addWidget(self.splash_path, 1, 0, 1, 1)
        self.splash_duration = QSpinBox()
        self.splash_duration.setSuffix(" ms")
        self.splash_duration.setRange(500, 10000)
        self.splash_duration.setValue(2000)
        conf_layout.addWidget(QLabel("Duration:"), 1, 1)
        conf_layout.addWidget(self.splash_duration, 1, 2)
        
        self.orientation = QComboBox()
        self.orientation.addItems(["Auto Rotate", "Portrait", "Landscape"])
        conf_layout.addWidget(QLabel("Orientation:"), 2, 0)
        conf_layout.addWidget(self.orientation, 2, 1)
        
        self.show_status_bar = QCheckBox("Show Status Bar")
        self.show_status_bar.setChecked(True)
        self.show_nav_bar = QCheckBox("Show Navigation Bar")
        self.show_nav_bar.setChecked(True)
        
        self.enable_js = QCheckBox("Enable JavaScript")
        self.enable_js.setChecked(True)
        self.enable_dom = QCheckBox("Enable DOM Storage")
        self.enable_dom.setChecked(True)
        self.enable_file_access = QCheckBox("Enable File Access")
        
        conf_layout.addWidget(self.show_status_bar, 3, 0)
        conf_layout.addWidget(self.show_nav_bar, 3, 1)
        conf_layout.addWidget(self.enable_js, 4, 0)
        conf_layout.addWidget(self.enable_dom, 4, 1)
        conf_layout.addWidget(self.enable_file_access, 4, 2)
        
        # Advanced WebView Config
        conf_layout.addWidget(QLabel("User Agent:"), 5, 0)
        self.user_agent = QLineEdit()
        self.user_agent.setPlaceholderText("Default")
        conf_layout.addWidget(self.user_agent, 5, 1, 1, 2)
        
        conf_layout.addWidget(QLabel("Addl Headers (JSON):"), 6, 0)
        self.headers = QLineEdit()
        self.headers.setPlaceholderText('e.g. {"X-App": "W2APK"}')
        conf_layout.addWidget(self.headers, 6, 1, 1, 2)
        
        conf_group.setLayout(conf_layout)
        android_layout.addWidget(conf_group)
        
        # 5. Extras
        extras_group = QGroupBox("Extras")
        extras_layout = QGridLayout()
        self.extra_checks = {}
        extras = ["Exit on Back", "Show Progress Bar", "Enable Zoom", "Multiple Windows", 
                  "Enable Downloads", "Geolocation", "Camera Access", "Microphone", 
                  "AdMob Integration", "Pull to Refresh", "Swipe Navigation"]
        
        cols = 3
        for i, e in enumerate(extras):
            cb = QCheckBox(e)
            extras_layout.addWidget(cb, i // cols, i % cols)
            self.extra_checks[e] = cb
            
        extras_group.setLayout(extras_layout)
        android_layout.addWidget(extras_group)
        
        # 6. APK Signing
        sign_group = QGroupBox("APK Signing")
        sign_layout = QVBoxLayout()
        self.auto_sign = QCheckBox("Auto-generate Keystore (Debug)")
        self.auto_sign.setChecked(True)
        sign_layout.addWidget(self.auto_sign)
        
        self.custom_ks_group = QGroupBox("Custom Keystore")
        self.custom_ks_group.setEnabled(False)
        self.auto_sign.toggled.connect(lambda checked: self.custom_ks_group.setEnabled(not checked))
        ks_layout = QFormLayout()
        self.ks_path = FilePicker("", mode='file')
        ks_layout.addRow("Path:", self.ks_path)
        self.ks_pass = QLineEdit()
        self.ks_pass.setEchoMode(QLineEdit.EchoMode.Password)
        ks_layout.addRow("Password:", self.ks_pass)
        self.ks_alias = QLineEdit()
        ks_layout.addRow("Alias:", self.ks_alias)
        self.ks_key_pass = QLineEdit()
        self.ks_key_pass.setEchoMode(QLineEdit.EchoMode.Password)
        ks_layout.addRow("Key Pass:", self.ks_key_pass)
        self.custom_ks_group.setLayout(ks_layout)
        sign_layout.addWidget(self.custom_ks_group)
        sign_group.setLayout(sign_layout)
        android_layout.addWidget(sign_group)
        
        # Android Build Button
        self.build_btn = QPushButton("BUILD ANDROID APK")
        self.build_btn.setFixedHeight(50)
        self.build_btn.setStyleSheet("background-color: #27ae60; font-size: 16px; color: white;")
        android_layout.addWidget(self.build_btn)
        
        self.tabs.addTab(android_tab, "Android Settings")
        
        # --- iOS Tab ---
        ios_tab = QWidget()
        ios_layout = QVBoxLayout(ios_tab)
        
        ios_conf = QGroupBox("iOS Configuration")
        ios_c_layout = QFormLayout()
        self.ios_bundle_id = QLineEdit("com.kontopoulos.app")
        self.ios_display_name = QLineEdit("My App")
        self.ios_build_num = QSpinBox()
        self.ios_build_num.setRange(1, 1000)
        self.ios_build_num.setValue(1)
        
        ios_c_layout.addRow("Bundle ID:", self.ios_bundle_id)
        ios_c_layout.addRow("Display Name:", self.ios_display_name)
        ios_c_layout.addRow("Build Number:", self.ios_build_num)
        ios_conf.setLayout(ios_c_layout)
        ios_layout.addWidget(ios_conf)
        
        ios_info = QLabel("iOS Project Export will generate a complete Xcode Project.\nYou can then open it on a Mac to compile the final .app file.")
        ios_info.setWordWrap(True)
        ios_info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        ios_layout.addWidget(ios_info)
        
        self.ios_export_btn = QPushButton("EXPORT iOS PROJECT")
        self.ios_export_btn.setFixedHeight(50)
        self.ios_export_btn.setStyleSheet("background-color: #2980b9; font-size: 16px; color: white;")
        ios_layout.addWidget(self.ios_export_btn)
        ios_layout.addStretch()
        
        self.tabs.addTab(ios_tab, "iOS Settings")
        
        layout.addWidget(self.tabs)
        
        # 7. Common Build Controls (Bottom)
        ctrl_group = QGroupBox("Global Controls")
        ctrl_layout = QHBoxLayout()
        self.validate_btn = QPushButton("Validate")
        
        self.build_variant = QComboBox()
        self.build_variant.addItems(["Debug", "Release"])
        
        self.reset_btn = QPushButton("Reset Fields")
        self.save_cfg_btn = QPushButton("Save Project")
        
        ctrl_layout.addWidget(QLabel("Variant:"))
        ctrl_layout.addWidget(self.build_variant)
        ctrl_layout.addWidget(self.validate_btn)
        ctrl_layout.addWidget(self.reset_btn)
        ctrl_layout.addWidget(self.save_cfg_btn)
        
        # ADB / Analysis Row (Android Only Info really, but let's keep it here for now)
        self.analyze_btn = QPushButton("Analyze APK")
        self.install_btn = QPushButton("Install to Device")
        self.device_list = QComboBox()
        self.refresh_devices_btn = QPushButton("🔄")
        self.refresh_devices_btn.setFixedSize(30, 30)
        
        adb_layout = QHBoxLayout()
        adb_layout.addWidget(self.analyze_btn)
        adb_layout.addWidget(QLabel("Device:"))
        adb_layout.addWidget(self.device_list)
        adb_layout.addWidget(self.refresh_devices_btn)
        adb_layout.addWidget(self.install_btn)
        
        layout.addWidget(ctrl_group)
        layout.addLayout(adb_layout)
        ctrl_group.setLayout(ctrl_layout)
        
        # Connect Buttons
        self.validate_btn.clicked.connect(self.validate_project)
        self.build_btn.clicked.connect(self.start_build_thread)
        self.reset_btn.clicked.connect(self.reset_fields)
        self.save_cfg_btn.clicked.connect(self.save_project_ui)
        self.analyze_btn.clicked.connect(self.analyze_apk_action)
        self.install_btn.clicked.connect(self.install_apk_action)
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)
        self.ios_export_btn.clicked.connect(self.start_ios_export_thread)

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def setup_output_section(self):
        output_group = QGroupBox("Build Output")
        layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        self.console = QTextEdit()
        self.console.setObjectName("consoleOutput")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(150)
        layout.addWidget(self.console)
        
        output_group.setLayout(layout)
        self.main_layout.addWidget(output_group)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    # GUI Actions
    def log(self, text):
        self.console.append(text)
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_status(self, text):
        self.status_label.setText(f"Status: {text}")
        self.status_bar.showMessage(text)

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def validate_project(self, silent=False):
        pkg = self.pkg_input.text().strip()
        # Auto-sanitize: replace spaces with underscores
        if " " in pkg:
            pkg = pkg.replace(" ", "_")
            self.pkg_input.setText(pkg)
            self.log(f"Auto-sanitized package name: {pkg}")

        import re
        # Android package name rules: segments must start with letter, only alphanumeric or underscores
        pkg_pattern = r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'
        if not re.match(pkg_pattern, pkg, re.IGNORECASE):
            if not silent:
                QMessageBox.warning(self, "Validation Error", 
                    "Invalid package name. \nRules:\n- Must contain at least one dot\n- No spaces or special characters\n- Each segment must start with a letter\n- Example: com.example.myapp")
            return False

        if not self.app_title.text():
            if not silent: QMessageBox.warning(self, "Validation Error", "App name is required.")
            return False
        if self.web_mode.currentText() == "URL (Remote)" and not self.url_input.text().startswith("http"):
            if not silent: QMessageBox.warning(self, "Validation Error", "Please enter a valid URL.")
            return False
        
        if not silent:
            QMessageBox.information(self, "Validation Success", "Project configuration is valid.")
        return True

    def reset_fields(self):
        self.app_title.setText("My Android App")
        self.pkg_input.setText("com.kontopoulos.app")
        self.url_input.setText("https://www.google.com")
        self.ver_name.setText("1.0.0")
        self.ver_code.setValue(1)
        # Add more resets as needed
        self.log("Fields reset.")

    def save_project_ui(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.w2apk)")
        if path:
            success, msg = self.project_manager.save_project(path)
            if success:
                QMessageBox.information(self, "Save", msg)
            else:
                QMessageBox.critical(self, "Save Error", msg)

    def load_project_ui(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.w2apk)")
        if path:
            success, msg = self.project_manager.load_project(path)
            if success:
                QMessageBox.information(self, "Load", msg)
            else:
                QMessageBox.critical(self, "Load Error", msg)

    def on_web_mode_change(self, index):
        # 0 = URL, 1 = Local Folder, 2 = Single HTML
        if index == 0:  # URL
            self.web_path.setVisible(False)
            self.url_input.setVisible(True)
        elif index == 1:  # Local Folder
            self.web_path.set_mode('dir')
            self.web_path.label.setText("Content Folder")
            self.web_path.setVisible(True)
            self.url_input.setVisible(False)
        else:  # Single HTML
            self.web_path.set_mode('file')
            self.web_path.label.setText("HTML File")
            self.web_path.setVisible(True)
            self.url_input.setVisible(False)

    # Config Serialization
    def get_config(self):
        return {
            "app_title": self.app_title.text(),
            "package_name": self.pkg_input.text(),
            "version_name": self.ver_name.text(),
            "version_code": self.ver_code.value(),
            "output_dir": self.out_dir.input_field.text(),
            "web_mode": self.web_mode.currentText(),
            "web_path": self.web_path.input_field.text(),
            "url": self.url_input.text(),
            "start_page": self.start_page.text(),
            "icon_path": self.icon_path.input_field.text(),
            "splash_path": self.splash_path.input_field.text(),
            "splash_duration": self.splash_duration.value(),
            "orientation": self.orientation.currentText(),
            "show_status_bar": self.show_status_bar.isChecked(),
            "show_nav_bar": self.show_nav_bar.isChecked(),
            "enable_js": self.enable_js.isChecked(),
            "enable_dom": self.enable_dom.isChecked(),
            "enable_file_access": self.enable_file_access.isChecked(),
            "user_agent": self.user_agent.text(),
            "headers": self.headers.text(),
            "extras": {e: cb.isChecked() for e, cb in self.extra_checks.items()},
            "build_variant": self.build_variant.currentText(),
            "auto_sign": self.auto_sign.isChecked(),
            "custom_ks": {
                "path": self.ks_path.input_field.text(),
                "pass": self.ks_pass.text(),
                "alias": self.ks_alias.text(),
                "key_pass": self.ks_key_pass.text()
            },
            "ios": {
                "bundle_id": self.ios_bundle_id.text(),
                "display_name": self.ios_display_name.text(),
                "build_num": self.ios_build_num.value()
            }
        }

    def set_config(self, cfg):
        self.app_title.setText(cfg.get("app_title", ""))
        self.pkg_input.setText(cfg.get("package_name", ""))
        self.ver_name.setText(cfg.get("version_name", "1.0.0"))
        self.ver_code.setValue(cfg.get("version_code", 1))
        self.out_dir.set_path(cfg.get("output_dir", ""))
        self.web_mode.setCurrentText(cfg.get("web_mode", "URL (Remote)"))
        self.web_path.set_path(cfg.get("web_path", ""))
        self.url_input.setText(cfg.get("url", ""))
        self.start_page.setText(cfg.get("start_page", "index.html"))
        self.icon_path.set_path(cfg.get("icon_path", ""))
        self.splash_path.set_path(cfg.get("splash_path", ""))
        self.splash_duration.setValue(cfg.get("splash_duration", 2000))
        self.orientation.setCurrentText(cfg.get("orientation", "Auto Rotate"))
        self.show_status_bar.setChecked(cfg.get("show_status_bar", True))
        self.show_nav_bar.setChecked(cfg.get("show_nav_bar", True))
        self.enable_js.setChecked(cfg.get("enable_js", True))
        self.enable_dom.setChecked(cfg.get("enable_dom", True))
        self.enable_file_access.setChecked(cfg.get("enable_file_access", False))
        self.user_agent.setText(cfg.get("user_agent", ""))
        self.headers.setText(cfg.get("headers", ""))
        self.build_variant.setCurrentText(cfg.get("build_variant", "Debug"))
        
        extras = cfg.get("extras", {})
        for e, cb in self.extra_checks.items():
            cb.setChecked(extras.get(e, False))
            
        self.auto_sign.setChecked(cfg.get("auto_sign", True))
        ks = cfg.get("custom_ks", {})
        self.ks_path.set_path(ks.get("path", ""))
        self.ks_pass.setText(ks.get("pass", ""))
        self.ks_alias.setText(ks.get("alias", ""))
        self.ks_key_pass.setText(ks.get("key_pass", ""))
        
        ios = cfg.get("ios", {})
        self.ios_bundle_id.setText(ios.get("bundle_id", "com.kontopoulos.app"))
        self.ios_display_name.setText(ios.get("display_name", "My App"))
        self.ios_build_num.setValue(ios.get("build_num", 1))

    def start_build_thread(self):
        if not self.validate_project(silent=True):
            QMessageBox.warning(self, "Validation Error", "Please fix the project configuration errors before building. Check the package name for spaces or invalid characters.")
            return
        self.build_btn.setEnabled(False)
        self.console.clear()
        self.progress_bar.setValue(0)
        self.log("Starting build process...")
        t = threading.Thread(target=self.run_build)
        t.start()

    def run_build(self):
        try:
            config = self.get_config()
            output_dir = config['output_dir']
            
            if not output_dir or not os.path.exists(output_dir):
                self.signaller.log.emit("Error: Valid output directory required.")
                self.signaller.finished.emit(False)
                return

            # 2. Check Deps
            self.signaller.status.emit("Checking dependencies...")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            signing_config = {
                "auto_sign": config.get("auto_sign", True),
                "custom_ks": config.get("custom_ks", {})
            }
            engine = BuildEngine(base_dir, logger_callback=self.signaller.log.emit, signing_config=signing_config)
            ok, msg = engine.check_dependencies()
            if not ok:
                self.signaller.log.emit(f"Dependency Error: {msg}")
                self.signaller.finished.emit(False)
                return

            self.signaller.progress.emit(20)
            
            # 3. Generate Project
            self.signaller.status.emit("Generating project...")
            template_dir = os.path.join(base_dir, "assets", "template")
            gen = ProjectGenerator(template_dir)
            gen.generate(config, output_dir)
            
            self.signaller.progress.emit(40)
            
            # 4. Build
            variant = config.get("build_variant", "Debug")
            self.signaller.status.emit(f"Building APK ({variant} variant)...")
            success = engine.build(output_dir, variant=variant)
            
            self.signaller.progress.emit(100)
            self.signaller.finished.emit(success)

        except Exception as e:
            self.signaller.log.emit(f"Critical Error: {str(e)}")
            import traceback
            self.signaller.log.emit(traceback.format_exc())
            self.signaller.finished.emit(False)

    def start_ios_export_thread(self):
        self.ios_export_btn.setEnabled(False)
        self.console.clear()
        self.progress_bar.setValue(0)
        self.log("Starting iOS Project Export...")
        t = threading.Thread(target=self.run_ios_export)
        t.start()

    def run_ios_export(self):
        try:
            config = self.get_config()
            output_dir = config['output_dir']
            
            if not output_dir or not os.path.exists(output_dir):
                self.signaller.log.emit("Error: Valid output directory required.")
                self.signaller.finished.emit(False)
                return

            self.signaller.status.emit("Generating iOS Project...")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_dir, "assets", "template_ios")
            
            from builder.generator_ios import IOSProjectGenerator
            gen = IOSProjectGenerator(template_dir)
            gen.generate(config, output_dir)
            
            self.signaller.progress.emit(100)
            self.signaller.finished.emit(True)

        except Exception as e:
            self.signaller.log.emit(f"iOS Export Error: {str(e)}")
            import traceback
            self.signaller.log.emit(traceback.format_exc())
            self.signaller.finished.emit(False)

    def post_build(self, success):
        self.build_btn.setEnabled(True)
        self.ios_export_btn.setEnabled(True)
        self.signaller.status.emit("Ready")
        if success:
            config = self.get_config()
            self.history_manager.add_entry(config)
            QMessageBox.information(self, "Build Complete", "APK generated successfully!")
        else:
            QMessageBox.warning(self, "Build Failed", "Check the console log for details.")

    def show_history(self):
        history = self.history_manager.get_history()
        if not history:
            QMessageBox.information(self, "History", "No build history found.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Build History")
        msg.setText("Last 50 Builds:")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        
        for entry in history:
            text = f"[{entry['timestamp']}] {entry['app_title']} ({entry['package_name']})\nPath: {entry['output_dir']}"
            item = QLabel(text)
            item.setStyleSheet("border-bottom: 1px solid #ccc; padding: 5px;")
            vbox.addWidget(item)
        
        scroll.setWidget(container)
        scroll.setFixedSize(600, 400)
        
        msg.layout().addWidget(scroll, 1, 0, 1, msg.layout().columnCount())
        msg.exec()

    def show_about(self):
        QMessageBox.information(self, "About", "WebSite to Android & iOS App\nPython Edition v2.0\nA professional tool for creating mobile apps from websites.")

    def show_docs(self):
        QMessageBox.information(self, "Help", "Documentation can be found in the project walkthrough.md file.")

    def check_deps_action(self):
        self.console.clear()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = BuildEngine(base_dir, logger_callback=self.log)
        ok, msg = engine.check_dependencies()
        if ok:
            QMessageBox.information(self, "Dependencies", "All dependencies found!")
            self.refresh_devices()
        else:
            QMessageBox.warning(self, "Dependencies", f"Issues found: {msg}")

    def refresh_devices(self):
        from builder.engine import ADBManager
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        adb = ADBManager(os.path.join(base_dir, "bin"), logger=self.log)
        devices = adb.list_devices()
        self.device_list.clear()
        self.device_list.addItems(devices)
        if devices:
            self.log(f"Found {len(devices)} device(s).")
        else:
            self.log("No ADB devices found.")

    def install_apk_action(self):
        device = self.device_list.currentText()
        if not device:
            QMessageBox.warning(self, "ADB", "No device selected.")
            return
        
        config = self.get_config()
        variant = config.get('build_variant', 'Debug').lower()
        apk_name = f"output_{variant}.apk"
        apk_path = os.path.join(config['output_dir'], apk_name)
        
        from builder.engine import ADBManager
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        adb = ADBManager(os.path.join(base_dir, "bin"), logger=self.log)
        
        success, msg = adb.install_apk(device, apk_path)
        if success:
            QMessageBox.information(self, "ADB", "Installation successful!")
        else:
            QMessageBox.critical(self, "ADB", f"Installation failed:\n{msg}")

    def analyze_apk_action(self):
        config = self.get_config()
        variant = config.get('build_variant', 'Debug').lower()
        apk_path = os.path.join(config['output_dir'], f"output_{variant}.apk")
        
        from builder.engine import APKAnalyzer
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        aapt2 = os.path.join(base_dir, "bin", "aapt2.exe")
        analyzer = APKAnalyzer(aapt2)
        
        info = analyzer.get_info(apk_path)
        
        # Show in a scrollable dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("APK Analysis")
        msg.setText("APK Badging Metadata:")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(info)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll.setWidget(content)
        scroll.setFixedSize(600, 400)
        
        msg.layout().addWidget(scroll, 1, 0, 1, msg.layout().columnCount())
        msg.exec()
