from PyQt6.QtWidgets import QMessageBox
import functools

def handle_ui_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            instance = args[0]
            QMessageBox.critical(instance, "Error", str(e))
    return wrapper