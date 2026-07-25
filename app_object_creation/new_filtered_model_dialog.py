from typing import List, Dict, Any
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QDialogButtonBox, QWidget
from ui.error_dialogs import ErrorHandler

class NewFilteredModelDialog(QDialog):
    """
    Dialog to select a base PLTS model and a compatible Twist Filter 
    to create a new independent FilteredModel.
    """
    def __init__(self, model_names: List[str], twist_filters_map: Dict[str, Any], parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Filtered Model")
        self.resize(400, 250)
        
        self.model_names = model_names
        self.twist_filters_map = twist_filters_map

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select Base PLTS Model:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(model_names)
        self.combo_model.currentIndexChanged.connect(self.update_filter_options)
        layout.addWidget(self.combo_model)

        layout.addWidget(QLabel("Select Twist Filter:"))
        self.combo_filter = QComboBox()
        layout.addWidget(self.combo_filter)

        layout.addWidget(QLabel("Filtered Model Name:"))
        self.input_name = QLineEdit()
        layout.addWidget(self.input_name)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.update_filter_options()

    def update_filter_options(self) -> None:
        self.combo_filter.clear()
        selected_model_name = self.combo_model.currentText()
        if not selected_model_name:
            return

        from services import JSONHandler
        from config import PATHS
        base_model = JSONHandler.load_model_from_json(PATHS["models"], selected_model_name)
        if not base_model or not base_model.twist_structure:
            return

        ts_name = base_model.twist_structure.name
        compatible_filters = [fname for fname, tf in self.twist_filters_map.items() if tf.twist_name == ts_name]
        
        self.combo_filter.addItems(compatible_filters)
        
        if compatible_filters:
            self.input_name.setText(f"{selected_model_name}_filtered_{compatible_filters[0]}")

    def validate_and_accept(self) -> None:
        if not self.combo_model.currentText():
            ErrorHandler.show_warning("Validation Error", "Please select a base model.", self)
            return
        if not self.combo_filter.currentText():
            ErrorHandler.show_warning("Validation Error", "Please select a twist filter.", self)
            return
        if not self.input_name.text().strip():
            ErrorHandler.show_warning("Validation Error", "Filtered model name cannot be empty.", self)
            return
        self.accept()

    def get_data(self) -> tuple:
        return (
            self.combo_model.currentText(),
            self.combo_filter.currentText(),
            self.input_name.text().strip()
        )