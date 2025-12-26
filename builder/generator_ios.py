import os
import shutil
from jinja2 import Environment, FileSystemLoader

class IOSProjectGenerator:
    def __init__(self, template_dir):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_dir = template_dir

    def generate(self, config, output_dir):
        """
        Generates the iOS Xcode project structure.
        """
        project_name = "WebApp"
        ios_dir = os.path.join(output_dir, "WebApp_iOS")
        
        # Clean old export
        if os.path.exists(ios_dir):
            shutil.rmtree(ios_dir, ignore_errors=True)
        
        os.makedirs(ios_dir, exist_ok=True)
        
        # 1. Copy common web content to assets directory
        assets_dest = os.path.join(ios_dir, project_name, "www")
        os.makedirs(assets_dest, exist_ok=True)
        self._process_web_content(config, assets_dest)
        
        # 2. Render Swift source and Plist
        template_config = config.copy()
        # Merge iOS specific config into root for easier template access
        if 'ios' in config:
            template_config.update(config['ios'])
            
        render_files = [
            ("WebApp/AppDelegate.swift", f"{project_name}/AppDelegate.swift"),
            ("WebApp/ContentView.swift", f"{project_name}/ContentView.swift"),
            ("WebApp/WebAppApp.swift", f"{project_name}/WebAppApp.swift"),
            ("WebApp/Info.plist", f"{project_name}/Info.plist"),
            ("WebApp.xcodeproj/project.pbxproj", f"{project_name}.xcodeproj/project.pbxproj")
        ]
        
        for t_path, o_path in render_files:
            target_out = os.path.join(ios_dir, o_path)
            os.makedirs(os.path.dirname(target_out), exist_ok=True)
            self._render_to_file(t_path, template_config, target_out)

        # 3. Process Icons for iOS
        self._process_ios_icons(config.get('icon_path'), os.path.join(ios_dir, project_name, "Assets.xcassets"))

    def _process_web_content(self, config, assets_dir):
        from builder.generator import ProjectGenerator
        # Reuse the existing web content processing logic if possible, 
        # but let's just implement it simply here to avoid tight coupling.
        mode = config.get('web_mode')
        path = config.get('web_path')
        
        if mode == "Local Folder" and path and os.path.exists(path):
            shutil.copytree(path, assets_dir, dirs_exist_ok=True)
        elif mode == "Single HTML File" and path and os.path.exists(path):
            shutil.copy2(path, os.path.join(assets_dir, "index.html"))

    def _render_to_file(self, template_name, context, output_path):
        template = self.env.get_template(template_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template.render(context))

    def _process_ios_icons(self, icon_path, xcassets_dir):
        icon_set_dir = os.path.join(xcassets_dir, "AppIcon.appiconset")
        os.makedirs(icon_set_dir, exist_ok=True)
        
        # Basic Contents.json for Xcode
        contents_json = """{
  "images" : [
    { "size" : "20x20", "idiom" : "iphone", "filename" : "icon-20@2x.png", "scale" : "2x" },
    { "size" : "20x20", "idiom" : "iphone", "filename" : "icon-20@3x.png", "scale" : "3x" },
    { "size" : "29x29", "idiom" : "iphone", "filename" : "icon-29@2x.png", "scale" : "2x" },
    { "size" : "29x29", "idiom" : "iphone", "filename" : "icon-29@3x.png", "scale" : "3x" },
    { "size" : "40x40", "idiom" : "iphone", "filename" : "icon-40@2x.png", "scale" : "2x" },
    { "size" : "40x40", "idiom" : "iphone", "filename" : "icon-40@3x.png", "scale" : "3x" },
    { "size" : "60x60", "idiom" : "iphone", "filename" : "icon-60@2x.png", "scale" : "2x" },
    { "size" : "60x60", "idiom" : "iphone", "filename" : "icon-60@3x.png", "scale" : "3x" },
    { "size" : "1024x1024", "idiom" : "ios-marketing", "filename" : "icon-1024.png", "scale" : "1x" }
  ],
  "info" : { "version" : 1, "author" : "xcode" }
}"""
        with open(os.path.join(icon_set_dir, "Contents.json"), "w") as f:
            f.write(contents_json)
            
        if icon_path and os.path.exists(icon_path):
            try:
                from PIL import Image
                img = Image.open(icon_path)
                sizes = [40, 60, 58, 87, 80, 120, 120, 180, 1024]
                filenames = ["icon-20@2x.png", "icon-20@3x.png", "icon-29@2x.png", "icon-29@3x.png", 
                             "icon-40@2x.png", "icon-40@3x.png", "icon-60@2x.png", "icon-60@3x.png", "icon-1024.png"]
                for size, fname in zip(sizes, filenames):
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized.save(os.path.join(icon_set_dir, fname))
            except:
                pass # Fallback if Pillow fails
