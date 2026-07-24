"""
View Logs Dialog.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QWidget, QLabel
)
from PyQt6.QtGui import QFont
from services.logging_service import get_logger
from ui.error_dialogs import ErrorHandler

logger = get_logger("ViewLogsDialog")


class ViewLogsDialog(QDialog):
    def __init__(self, log_file_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.log_file_path = log_file_path
        
        self.setWindowTitle("Application Logs")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        self.label_info = QLabel(f"Showing log file: {self.log_file_path.name}")
        layout.addWidget(self.label_info)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()

        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.clicked.connect(self.handle_clear_logs)
        btn_layout.addWidget(self.btn_clear)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_logs)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        self.load_logs()

    def handle_clear_logs(self) -> None:
        """Clears the application logs and updates the text area."""
        try:
            if ErrorHandler.ask_confirmation("Clear Logs", "Are you sure you want to clear all logs?", self):
                from services.logging_service import clear_logs
                clear_logs()
                self.load_logs()
        except Exception as e:
            logger.error(f"Failed to clear logs from UI: {str(e)}")
            ErrorHandler.show_error("Log Error", "Unable to clear the log file.", self)

    def load_logs(self) -> None:
        """Reads the log file and loads its content into the text area."""
        try:
            if not self.log_file_path.exists():
                self.text_edit.setPlainText("Log file does not exist yet.")
                return

            with open(self.log_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.text_edit.setPlainText(content if content else "Log file is empty.")
            
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            logger.debug("Log file content successfully reloaded in UI.")
        except Exception as e:
            logger.error(f"Failed to read log file at {self.log_file_path}: {str(e)}")
            ErrorHandler.show_error("Log Error", "Unable to read the log file.")