import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from services.object_manager import ObjectManager
from services.theme_service import ThemeService
from services.logging_service import setup_logging

def handle_exception(exc_type, exc_value, exc_traceback):
    logging.critical("Unhandled exception occurred", exc_info=(exc_type, exc_value, exc_traceback))
    
    if QApplication.instance():
        QMessageBox.critical(
            None, 
            "Critical Error", 
            "An unexpected error occurred and the application must close.\n\n"
            "Please check the log files in the 'logs/' directory for details."
        )
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def main():
    setup_logging()
    sys.excepthook = handle_exception
    
    app = QApplication(sys.argv)
    
    manager = ObjectManager()
    theme_service = ThemeService()
    window = MainWindow(manager, theme_service)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()