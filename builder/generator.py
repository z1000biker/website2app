import os
import shutil
from jinja2 import Environment, FileSystemLoader

class ProjectGenerator:
    def __init__(self, template_dir):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_dir = template_dir

    def generate(self, config, output_dir):
        """
        Generates the Android project structure.
        """
        # Define paths
        app_dir = os.path.join(output_dir, "app")
        
        # CLEAN OLD OUTPUT to prevent stale files from breaking the build
        if os.name == 'nt':
            if os.path.exists(app_dir):
                import time
                shutil.rmtree(app_dir, ignore_errors=True)
                # Brief wait to let OneDrive release any locks
                time.sleep(0.5)
        elif os.path.exists(app_dir):
            shutil.rmtree(app_dir)
        
        src_main = os.path.join(app_dir, "src", "main")
        assets_dir = os.path.join(src_main, "assets")
        java_dir = os.path.join(src_main, "java")
        res_dir = os.path.join(src_main, "res")
        
        # Create directories
        package_path = config['package_name'].replace('.', os.sep)
        final_java_path = os.path.join(java_dir, package_path)
        
        os.makedirs(final_java_path, exist_ok=True)
        os.makedirs(os.path.join(res_dir, "layout"), exist_ok=True)
        os.makedirs(os.path.join(res_dir, "values"), exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)
        
        # Handle Web Content
        self._process_web_content(config, assets_dir)
        
        # Process Icons (Use default if not provided)
        if config.get('icon_path') and os.path.exists(config['icon_path']):
            self._process_icons(config['icon_path'], res_dir)
        else:
            self._generate_default_icon(res_dir)
            
        # Process Splash if provided
        if config.get('splash_path') and os.path.exists(config['splash_path']):
            self._process_splash(config['splash_path'], res_dir)

        # Prepare config for template
        template_config = config.copy()
        if config.get('headers'):
            try:
                import json
                template_config['headers_dict'] = json.loads(config['headers'])
            except:
                template_config['headers_dict'] = {}
        else:
            template_config['headers_dict'] = {}

        # Render and write files
        self._render_to_file('build.gradle', template_config, os.path.join(app_dir, "build.gradle"))
        self._render_to_file('AndroidManifest.xml', template_config, os.path.join(src_main, "AndroidManifest.xml"))
        self._render_to_file('MainActivity.java', template_config, os.path.join(final_java_path, "MainActivity.java"))
        
        # Resources
        self._create_strings_xml(config['app_title'], os.path.join(res_dir, "values", "strings.xml"))
        self._create_layout_xml(config, os.path.join(res_dir, "layout", "activity_main.xml"))
        
        # Root level build.gradle and settings.gradle
        self._create_root_gradle(output_dir)

    def _process_web_content(self, config, assets_dir):
        mode = config.get('web_mode')
        path = config.get('web_path')
        
        if mode == "Local Folder" and path and os.path.exists(path):
            # Copy entire folder to assets
            for item in os.listdir(path):
                s = os.path.join(path, item)
                d = os.path.join(assets_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        elif mode == "Single HTML File" and path and os.path.exists(path):
            shutil.copy2(path, os.path.join(assets_dir, "index.html"))

    def _process_icons(self, icon_path, res_dir):
        try:
            from PIL import Image
            img = Image.open(icon_path)
            densities = {
                "mipmap-mdpi": 48,
                "mipmap-hdpi": 72,
                "mipmap-xhdpi": 96,
                "mipmap-xxhdpi": 144,
                "mipmap-xxxhdpi": 192
            }
            for name, size in densities.items():
                target_dir = os.path.join(res_dir, name)
                os.makedirs(target_dir, exist_ok=True)
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(os.path.join(target_dir, "ic_launcher.png"))
        except Exception as e:
            print(f"Icon processing failed: {e}")

    def _generate_default_icon(self, res_dir):
        try:
            from PIL import Image, ImageDraw
            # Create a simple blue icon with a white square
            size = 512
            img = Image.new('RGB', (size, size), color=(33, 150, 243))
            draw = ImageDraw.Draw(img)
            draw.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill=(255, 255, 255))
            
            densities = {
                "mipmap-mdpi": 48,
                "mipmap-hdpi": 72,
                "mipmap-xhdpi": 96,
                "mipmap-xxhdpi": 144,
                "mipmap-xxxhdpi": 192
            }
            for name, target_size in densities.items():
                target_dir = os.path.join(res_dir, name)
                os.makedirs(target_dir, exist_ok=True)
                resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                resized.save(os.path.join(target_dir, "ic_launcher.png"))
        except Exception as e:
            print(f"Default icon generation failed: {e}")

    def _process_splash(self, splash_path, res_dir):
        try:
            from PIL import Image
            img = Image.open(splash_path)
            # Create a drawable folder for splash
            target_dir = os.path.join(res_dir, "drawable")
            os.makedirs(target_dir, exist_ok=True)
            # Just copy the splash as is or resize to a standard large size
            img.save(os.path.join(target_dir, "splash.png"))
        except Exception as e:
            print(f"Splash processing failed: {e}")

    def _render_to_file(self, template_name, context, output_path):
        template = self.env.get_template(template_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template.render(context))

    def _create_strings_xml(self, app_name, path):
        content = f'''<resources>
    <string name="app_name">{app_name}</string>
</resources>'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_layout_xml(self, config, path):
        # Simple FrameLayout that works without AndroidX
        template_content = '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</FrameLayout>
'''
        # Create a dummy Jinja2 environment for this specific string template
        # This allows us to use Jinja2 logic directly within the Python string
        env = Environment(loader=FileSystemLoader('.')) # Loader doesn't matter as we use from_string
        template = env.from_string(template_content)
        content = template.render(config)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_root_gradle(self, output_dir):
        settings = "rootProject.name = 'My Application'\ninclude ':app'"
        with open(os.path.join(output_dir, "settings.gradle"), "w", encoding='utf-8') as f:
            f.write(settings)
            
        build_gradle = """// Top-level build file where you can add configuration options common to all sub-projects/modules.
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.4.2'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}"""
        with open(os.path.join(output_dir, "build.gradle"), "w", encoding='utf-8') as f:
            f.write(build_gradle)
