"""
Object Loading Dialog Module.

This module provides a reusable dialog for selecting multiple items from a list.
It is used for loading multiple objects (Lattices, Twist Structures, Worlds, Models)
from JSON files into the main application workspace.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QAbstractItemView,
    QWidget
)
from services.logging_service import get_logger
from ui.error_dialogs import ErrorHandler

logger = get_logger("MultiSelectDialog")


class MultiSelectDialog(QDialog):
    """
    A generic dialog that presents a list of items and allows the user to select one or more.
    Useful for batch loading operations.

    Attributes:
        selected_items (List[str]): Stores the text of the items selected by the user
                                    after the dialog is accepted.
    """

    def __init__(self, title: str, items: List[str], parent: Optional[QWidget] = None):
        """
        Initializes the MultiSelectDialog.

        Args:
            title (str): The title to display on the dialog window.
            items (List[str]): A list of strings to populate the selection widget.
            parent (Optional[QWidget]): The parent widget (MainWindow).
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        self.selected_items: List[str] = []

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select objects to load (Hold Ctrl/Shift to select multiple):"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.addItems(items)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        """
        Handles the OK button click.
        Captures the currently selected items before closing the dialog.
        """
        try:
            items = self.list_widget.selectedItems()
            if not items:
                ErrorHandler.show_warning("Selection Error", "Please select at least one item.")
                return
            
            self.selected_items = [item.text() for item in items]
            super().accept()
        except Exception as e:
            logger.error(f"Error capturing selected items: {str(e)}")
            ErrorHandler.show_error("System Error", "An error occurred while processing your selection.")

    def get_selected_items(self) -> List[str]:
        """
        Retrieves the list of items selected by the user.

        Returns:
            List[str]: A list of strings corresponding to the selected rows.
        """
        try:
            return self.selected_items
        except Exception as e:
            logger.error(f"Error retrieving selected items: {str(e)}")
            ErrorHandler.show_error("Data Error", "An error occurred while retrieving selection data.")
            raise