"""
Error handling and messaging utility module.
Provides centralized UI dialog displays integrated with logger logging.
"""

from PyQt6.QtWidgets import QMessageBox
from services.logging_service import get_logger

logger = get_logger("ErrorHandler")


class ErrorHandler:
    @staticmethod
    def show_error(title: str, message: str, parent=None):
        """Displays a critical error dialog and logs the error."""
        logger.error(f"{title}: {message}")
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """Displays a warning dialog and logs the warning."""
        logger.warning(f"{title}: {message}")
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_info(title: str, message: str, parent=None):
        """Displays an informational message dialog."""
        logger.info(f"{title}: {message}")
        QMessageBox.information(parent, title, message)

    @staticmethod
    def ask_confirmation(title: str, message: str, parent=None) -> bool:
        """
        Displays a binary confirmation dialog (Yes/No).
        Returns True if the user clicks Yes, False otherwise.
        """
        logger.info(f"Prompting user confirmation - {title}: {message}")
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes