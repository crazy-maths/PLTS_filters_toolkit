"""
New Model Dialog Module.
"""

from collections import defaultdict
from typing import List, Set, Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, 
    QComboBox, QListWidget, QAbstractItemView, QTabWidget, QWidget, 
    QTableWidget, QLabel, QMessageBox, QHBoxLayout, QTextEdit
)
from ast import literal_eval
from services.logging_service import get_logger
from ui.error_dialogs import ErrorHandler

logger = get_logger("NewModelDialog")

class NewModelDialog(QDialog):
    def __init__(
        self,
        twist_structures_dict: Dict[str, Any],
        worlds_dict: Dict[str, Any],
        props: Set[str],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create New PLTS")
        self.resize(850, 700)
        
        self.twist_structures = twist_structures_dict
        self.worlds_dict = worlds_dict
        self.ts_names = sorted(list(twist_structures_dict.keys()))
        self.props = props
        
        self.relations_data: Dict[str, Dict[str, Dict[str, Tuple[str, str]]]] = defaultdict(lambda: defaultdict(dict))
        
        self.current_action_context: Optional[str] = None
        
        self.ts_elements_data: List[Tuple[str, Optional[str]]] = []
        
        self.no_connection_str = "(No Connection)"
        
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.main_layout.addWidget(self.tabs)

        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "1. General & States")

        self.tab_relations = QWidget()
        self.setup_relations_tab()
        self.tabs.addTab(self.tab_relations, "2. Action Relations (Weights)")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(buttons)

    def setup_general_tab(self) -> None:
        layout = QVBoxLayout(self.tab_general)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("PLTS Name")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional description of the model...")
        self.desc_input.setMaximumHeight(1000)
        
        self.combo_ts = QComboBox()
        self.combo_ts.addItems(self.ts_names)
        self.combo_ts.currentIndexChanged.connect(self.on_ts_changed)
        
        self.actions_input = QLineEdit()
        self.actions_input.setPlaceholderText("e.g: knows, believes, a")
        self.actions_input.editingFinished.connect(self.parse_actions)

        form.addRow("Name:", self.name_input)
        form.addRow("Description:", self.desc_input)
        form.addRow("Twist Structure:", self.combo_ts)
        form.addRow("Actions:", self.actions_input)
        layout.addLayout(form)

        layout.addWidget(QLabel("Select States (Filtered by Twist Structure):"))
        self.list_worlds = QListWidget()
        
        self.list_worlds.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_worlds)
        
        if self.ts_names: self.on_ts_changed(0)

    def setup_relations_tab(self) -> None:
        layout = QVBoxLayout(self.tab_relations)
        
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Edit Relations for Action:"))
        self.combo_current_action = QComboBox()
        self.combo_current_action.currentTextChanged.connect(self.switch_action_context)
        action_layout.addWidget(self.combo_current_action)
        layout.addLayout(action_layout)
        
        layout.addWidget(QLabel("Assign weights (Row → Col)."))
        self.table_relations = QTableWidget()
        layout.addWidget(self.table_relations)

    def on_ts_changed(self, index: int):
        name = self.combo_ts.currentText()

        if name in self.twist_structures:
            ts = self.twist_structures[name]

            sorted_elems = ts.toposort_twist_elements()

            bottom_elem = sorted_elems[0]

            self.ts_elements_data = []
            self.ts_bottom = bottom_elem

            for e in sorted_elems:
                real_str = str(e)
                display_str = real_str.replace("'", "")
                self.ts_elements_data.append((display_str, real_str))

        self.filter_worlds_by_ts(name)

    def filter_worlds_by_ts(self, ts_name: str) -> None:
        """Only show worlds that are associated with the selected Twist Structure."""
        self.list_worlds.clear()
        
        compatible_worlds = []
        for w_name, world_obj in self.worlds_dict.items():
            if world_obj.twist_structure.name == ts_name:
                compatible_worlds.append(w_name)
        
        self.list_worlds.addItems(sorted(compatible_worlds))
        
        if not compatible_worlds and self.worlds_dict:
            self.list_worlds.setToolTip("No states found for this Twist Structure.")
        else:
            self.list_worlds.setToolTip("")

    def parse_actions(self) -> List[str]:
        return [x.strip() for x in self.actions_input.text().split(',') if x.strip()]

    def on_tab_changed(self, index: int) -> None:
        if index == 1: self.prepare_relations_tab()

    def prepare_relations_tab(self) -> None:
        try:
            actions = self.parse_actions()
            if not actions:
                logger.warning("Attempted to access Relations tab without defining actions.")
                ErrorHandler.show_warning("Action Required", "Please define at least one action in the General tab first.")
                self.tabs.setCurrentIndex(0)
                return
            
            curr = self.combo_current_action.currentText()
            self.combo_current_action.blockSignals(True)
            self.combo_current_action.clear()
            self.combo_current_action.addItems(actions)
            if curr in actions:
                self.combo_current_action.setCurrentText(curr)
            self.combo_current_action.blockSignals(False)

            selected_worlds = [item.text() for item in self.list_worlds.selectedItems()]
            n = len(selected_worlds)
            self.table_relations.setRowCount(n)
            self.table_relations.setColumnCount(n)
            self.table_relations.setHorizontalHeaderLabels(selected_worlds)
            self.table_relations.setVerticalHeaderLabels(selected_worlds)
            
            if self.combo_current_action.count() > 0:
                self.switch_action_context(self.combo_current_action.currentText())
        except Exception as e:
            logger.error(f"Failed to prepare relations tab: {str(e)}")
            ErrorHandler.show_error("Display Error", "An error occurred while preparing the relations table.")

    def switch_action_context(self, new_action: str) -> None:
        if not new_action: return
        if self.current_action_context:
            self.save_current_table_to_data(self.current_action_context)
        self.current_action_context = new_action
        self.load_data_to_table(new_action)

    def save_current_table_to_data(self, action: str) -> None:
        try:
            rows = self.table_relations.rowCount()
            cols = self.table_relations.columnCount()
            
            if action not in self.relations_data:
                self.relations_data[action] = defaultdict(dict)
                
            for r in range(rows):
                src_item = self.table_relations.verticalHeaderItem(r)
                src = src_item.text() if src_item else str(r)
                
                for c in range(cols):
                    tgt_item = self.table_relations.horizontalHeaderItem(c)
                    tgt = tgt_item.text() if tgt_item else str(c)
                    
                    combo = self.table_relations.cellWidget(r, c)
                    
                    if isinstance(combo, QComboBox):
                        val_data = combo.currentData()
                        if val_data is None:
                            if tgt in self.relations_data[action][src]:
                                del self.relations_data[action][src][tgt]
                        else:
                            try:
                                # Ensure val_data is a string before evaluating
                                val_tuple = literal_eval(str(val_data))
                                self.relations_data[action][src][tgt] = val_tuple
                            except (ValueError, SyntaxError) as e:
                                logger.error(f"Failed to parse weight data '{val_data}' for action '{action}': {str(e)}")
        except Exception as e:
            logger.error(f"Critical error saving table data for action '{action}': {str(e)}")
    
    def load_data_to_table(self, action: str) -> None:
        try:
            rows = self.table_relations.rowCount()
            cols = self.table_relations.columnCount()
            data = self.relations_data.get(action, {})
            
            for r in range(rows):
                src_item = self.table_relations.verticalHeaderItem(r)
                src = src_item.text() if src_item else str(r)
                row_data = data.get(src, {})
                
                for c in range(cols):
                    tgt_item = self.table_relations.horizontalHeaderItem(c)
                    tgt = tgt_item.text() if tgt_item else str(c)
                    
                    combo = QComboBox()
                    for display_text, user_data in self.ts_elements_data:
                        combo.addItem(display_text, user_data)
                    
                    saved_val = row_data.get(tgt, None)

                    if saved_val is None:
                        idx = combo.findData(str(self.ts_bottom))
                        combo.setCurrentIndex(idx if idx >= 0 else 0)
                    else:
                        saved_str = str(saved_val)
                        idx = combo.findData(saved_str)
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
                        else:
                            logger.warning(f"Saved value '{saved_str}' not found in current Twist Structure for ({src}, {tgt}).")
                            combo.setCurrentIndex(0)
                    
                    self.table_relations.setCellWidget(r, c, combo)
        except Exception as e:
            logger.error(f"Failed to load relation data into table for action '{action}': {str(e)}")
            ErrorHandler.show_error("Display Error", "An error occurred while loading relationship data.")

    def validate_and_accept(self) -> None:
        try:
            if not self.name_input.text().strip():
                ErrorHandler.show_warning("Validation Error", "PLTS Name is required.")
                return
            if not self.combo_ts.currentText():
                ErrorHandler.show_warning("Validation Error", "Twist Structure is required.")
                return
            if not self.list_worlds.selectedItems():
                ErrorHandler.show_warning("Validation Error", "Please select at least one State.")
                return
            if not self.parse_actions():
                ErrorHandler.show_warning("Validation Error", "Please define at least one action.")
                return
            
            if self.current_action_context:
                self.save_current_table_to_data(self.current_action_context)
            
            self.accept()
        except Exception as e:
            logger.error(f"Error during model validation: {str(e)}")
            ErrorHandler.show_error("System Error", "An unexpected error occurred during validation.")

    def get_data(self) -> Tuple[str, str, List[str], Set[str], Dict, str]:
        try:
            name = self.name_input.text().strip()
            description = self.desc_input.toPlainText().strip()
            ts_name = self.combo_ts.currentText()
            selected_items = self.list_worlds.selectedItems()
            world_names = [item.text() for item in selected_items]
            
            if self.current_action_context:
                self.save_current_table_to_data(self.current_action_context)

            return name, ts_name, world_names, self.props, self.relations_data, description
        except Exception as e:
            logger.error(f"Error retrieving model data: {str(e)}")
            ErrorHandler.show_error("Data Error", "An error occurred while preparing the model data for creation.")
            raise