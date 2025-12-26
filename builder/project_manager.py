import json
import os

class ProjectManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def save_project(self, file_path):
        """Serializes current GUI state to a JSON file."""
        config = self.main_window.get_config()
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True, "Project saved successfully."
        except Exception as e:
            return False, f"Failed to save project: {str(e)}"

    def load_project(self, file_path):
        """Deserializes JSON file and updates GUI state."""
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist."
            
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            self.main_window.set_config(config)
            return True, "Project loaded successfully."
        except Exception as e:
            return False, f"Failed to load project: {str(e)}"

class HistoryManager:
    def __init__(self, base_dir):
        self.history_file = os.path.join(base_dir, "build_history.json")

    def add_entry(self, config):
        import datetime
        history = self.get_history()
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "app_title": config.get("app_title"),
            "package_name": config.get("package_name"),
            "output_dir": config.get("output_dir")
        }
        history.insert(0, entry)
        history = history[:50] # Keep last 50
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)

    def get_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []
