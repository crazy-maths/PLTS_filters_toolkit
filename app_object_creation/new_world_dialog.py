"""
New World Dialog Module.
"""

from typing import Dict, Set, Tuple, Optional, Any, List
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, 
    QGroupBox, QVBoxLayout, QWidget, QMessageBox, QLabel, QScrollArea, QListWidget, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt
from services.logging_service import get_logger
from ui.error_dialogs import ErrorHandler

logger = get_logger("NewWorldDialog")

class NewWorldDialog(QDialog):
    def __init__(
        self, 
        twist_structures: Dict[str, Any], 
        props: Set[str], 
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create New States")
        self.resize(900, 600)
        
        self.twist_structures = twist_structures
        self.props = sorted(list(props))
        self.assignment_widgets: Dict[str, QComboBox] = {}
        
        self.queue_data: List[Tuple[str, str, str, Dict[str, str]]] = []
        
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        info_group = QGroupBox("State Definition")
        form_layout = QFormLayout()
        
        self.long_name_input = QLineEdit()
        self.long_name_input.setPlaceholderText("Unique ID (e.g. State_1)")
        
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Graph Label (e.g. s1). Optional if length long name <= 5.")
        
        self.combo_ts = QComboBox()
        self.combo_ts.setPlaceholderText("Select Twist Structure")
        if self.twist_structures:
            self.combo_ts.addItems(sorted(list(self.twist_structures.keys())))
        
        self.combo_ts.currentTextChanged.connect(self.update_assignment_options)
        
        form_layout.addRow("Long Name:", self.long_name_input)
        form_layout.addRow("Short Name:", self.short_name_input)
        form_layout.addRow("Twist Structure:", self.combo_ts)
        info_group.setLayout(form_layout)
        left_layout.addWidget(info_group)
        
        self.assignments_group = QGroupBox("Proposition Valuations")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.assignments_layout = QFormLayout(scroll_content)
        
        if not self.props:
            self.assignments_layout.addRow(QWidget(), QLabel("No propositions defined."))
        else:
            for p in self.props:
                combo = QComboBox()
                self.assignment_widgets[p] = combo
                self.assignments_layout.addRow(f"Value for '{p}':", combo)
            
        scroll.setWidget(scroll_content)
        group_layout = QVBoxLayout(self.assignments_group)
        group_layout.addWidget(scroll)
        left_layout.addWidget(self.assignments_group)

        self.btn_add = QPushButton("Add to Queue >>")
        self.btn_add.setStyleSheet("font-weight: bold; padding: 8px;")
        self.btn_add.clicked.connect(self.add_to_queue)
        left_layout.addWidget(self.btn_add)
        
        if self.combo_ts.count() > 0:
            self.update_assignment_options(self.combo_ts.currentText())

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("<b>States to Create:</b>"))
        self.list_queue = QListWidget()
        right_layout.addWidget(self.list_queue)
        
        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self.remove_from_queue)
        right_layout.addWidget(btn_remove)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 400])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_final)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def update_assignment_options(self, ts_name: str) -> None:
        """Populates value dropdowns with elements from selected Twist Structure."""
        if ts_name not in self.twist_structures: return

        ts = self.twist_structures[ts_name]
        sorted_elems = ts.toposort_twist_elements()
        
        for combo in self.assignment_widgets.values():
            prev_text = combo.currentText()
            
            combo.blockSignals(True)
            combo.clear()
            
            for e in sorted_elems:
                real_str = str(e)
                display_str = real_str.replace("'", "")
                combo.addItem(display_str, real_str)
            
            idx = combo.findText(prev_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                
            combo.blockSignals(False)

    def add_to_queue(self) -> None:
        try:
            l_name = self.long_name_input.text().strip()
            s_name = self.short_name_input.text().strip()
            ts_name = self.combo_ts.currentText()
            
            if not l_name:
                ErrorHandler.show_warning("Validation Error", "Long Name is required.")
                return
            if not ts_name:
                ErrorHandler.show_warning("Validation Error", "Twist Structure required.")
                return
            
            if len(s_name) > 5:
                ErrorHandler.show_warning("Validation Error", "Short name must be 5 chars or less.")
                return

            if not s_name:
                if len(l_name) <= 5:
                    s_name = l_name
                else:
                    ErrorHandler.show_warning("Validation Error", "Short Name required for long names (>5 chars).")
                    return
            
            for item in self.queue_data:
                if item[0] == l_name:
                    ErrorHandler.show_warning("Duplicate Error", f"Long Name '{l_name}' already in queue.")
                    return
                if item[1] == s_name:
                    ErrorHandler.show_warning("Duplicate Error", f"Short Name '{s_name}' already in queue.")
                    return

            assignments = {p: (combo.currentData() or combo.currentText()) 
                           for p, combo in self.assignment_widgets.items()}
            
            self.queue_data.append((l_name, s_name, ts_name, assignments))
            
            self.list_queue.addItem(f"{s_name} ({l_name}) - [{ts_name}]")
            self.long_name_input.clear()
            self.short_name_input.clear()
            self.long_name_input.setFocus()
            
            for combo in self.assignment_widgets.values():
                if combo.count() > 0: combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error adding world to queue: {str(e)}")
            ErrorHandler.show_error("System Error", "An error occurred while adding the state to the queue.")

    def remove_from_queue(self) -> None:
        row = self.list_queue.currentRow()
        if row >= 0:
            self.list_queue.takeItem(row)
            self.queue_data.pop(row)

    def validate_final(self) -> None:
        try:
            if not self.queue_data:
                if self.long_name_input.text().strip() and self.short_name_input.text().strip():
                    if ErrorHandler.ask_yes_no("Add current?", "Queue is empty. Add current state and finish?"):
                        self.add_to_queue()
                        if self.queue_data: self.accept()
                        return
                
                ErrorHandler.show_warning("Validation Error", "No states in the queue to create.")
                return
                
            self.accept()
        except Exception as e:
            logger.error(f"Error during final validation: {str(e)}")
            ErrorHandler.show_error("System Error", "An error occurred during final submission.")

    def get_data(self) -> List[Tuple[str, str, str, Dict[str, str]]]:
        try:
            return self.queue_data
        except Exception as e:
            logger.error(f"Error retrieving world queue data: {str(e)}")
            ErrorHandler.show_error("Data Error", "An error occurred while retrieving state data.")
            raise