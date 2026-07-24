import os
from config.config import PATHS

class ThemeService:
    def __init__(self):
        self.is_dark_mode = False
        self.colors = {
            "dark": {
                "header": "#5dade2", "accent": "#2a82da", "warn": "#f39c12",
                "info": "#3498db", "error": "#e74c3c", "text": "#ffffff", "subtle": "#888888"
            },
            "light": {
                "header": "#2980b9", "accent": "#2980b9", "warn": "#d35400",
                "info": "#2980b9", "error": "#c0392b", "text": "#000000", "subtle": "#777777"
            }
        }

    def toggle(self):
        self.is_dark_mode = not self.is_dark_mode

    def get_stylesheet(self) -> str:
        filename = "dark.qss" if self.is_dark_mode else "light.qss"
        filepath = os.path.join(PATHS["assets"], filename)
        
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read()
        return ""

    def get_color(self, role: str) -> str:
        mode = "dark" if self.is_dark_mode else "light"
        return self.colors[mode].get(role, "#000000")