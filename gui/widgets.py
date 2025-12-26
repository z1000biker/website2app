from PyQt6.QtWidgets import QLineEdit, QFileDialog, QWidget, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

class FilePicker(QWidget):
    pathChanged = pyqtSignal(str)

    def __init__(self, label_text, mode='file', parent=None):
        super().__init__(parent)
        self.mode = mode
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        
        h_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Path to file or folder...")
        h_layout.addWidget(self.input_field)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("secondaryBtn")
        self.browse_btn.clicked.connect(self.browse)
        h_layout.addWidget(self.browse_btn)
        
        layout.addLayout(h_layout)
        self.setLayout(layout)

    def browse(self):
        if self.mode == 'file':
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if path:
            self.input_field.setText(path)
            self.pathChanged.emit(path)

    def set_path(self, path):
        self.input_field.setText(path)
    
    def get_path(self):
        return self.input_field.text()
    
    def set_mode(self, mode):
        self.mode = mode

class ToggleSwitch(QWidget):
    # Placeholder for a custom toggle switch if needed, 
    # for now we can use CheckBox in main window or implement a simple one here
    pass
