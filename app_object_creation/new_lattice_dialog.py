"""
New Lattice Dialog Module.

Creates a Lattice with elements, order relations, and an Implication Map.
"""

import itertools
import logging
from typing import Tuple, Set, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, 
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QTableWidget, QHeaderView, QComboBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from ui.error_dialogs import ErrorHandler

logger = logging.getLogger("NewLatticeDialog")


class NewLatticeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Lattice")
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # TAB 1: Structure
        self.tab_struct = QWidget()
        self.setup_struct_tab()
        self.tabs.addTab(self.tab_struct, "1. Elements & Order")
        
        # TAB 2: Implication
        self.tab_imp = QWidget()
        self.setup_imp_tab()
        self.tabs.addTab(self.tab_imp, "2. Implication")
        
        self.tabs.currentChanged.connect(self.on_tab_changed)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def setup_struct_tab(self):
        layout = QVBoxLayout(self.tab_struct)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.elements_input = QLineEdit()
        self.elements_input.setPlaceholderText("separated by comma, e.g., 0,1,a,b")
        self.elements_input.returnPressed.connect(self.populate_lists)
        form.addRow("Name:", self.name_input)
        form.addRow("Elements:", self.elements_input)
        layout.addLayout(form)

        self.gen_btn = QPushButton("Define an order")
        self.gen_btn.clicked.connect(self.populate_lists)
        layout.addWidget(self.gen_btn)
        
        layout.addWidget(QLabel("Relations (a ≤ b):"))
        self.rel_list = QListWidget()
        self.rel_list.itemChanged.connect(self.on_relation_changed)
        layout.addWidget(self.rel_list)

    def setup_imp_tab(self):
        layout = QVBoxLayout(self.tab_imp)
        layout.addWidget(QLabel("Define Implication (Row → Col):"))
        self.table_imp = QTableWidget()
        layout.addWidget(self.table_imp)

    def populate_lists(self):
        try:
            elements = [e.strip() for e in self.elements_input.text().split(',') if e.strip()]
            if not elements:
                return

            self.rel_list.clear()
            for p in itertools.product(elements, repeat=2):
                item = QListWidgetItem(f"({p[0]}, {p[1]})")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if p[0] == p[1] else Qt.CheckState.Unchecked)
                self.rel_list.addItem(item)
        except Exception as e:
            logger.error(f"Failed to populate relation list: {str(e)}")
            ErrorHandler.show_error("Generation Error", "An error occurred while generating the relations list.")

    def on_tab_changed(self, index):
        if index == 1: self.populate_imp_table()

    def populate_imp_table(self):
        try:
            elements = sorted([e.strip() for e in self.elements_input.text().split(',') if e.strip()])
            if not elements:
                logger.warning("Attempted to populate implication table with no elements.")
                return
            
            n = len(elements)
            self.table_imp.setRowCount(n)
            self.table_imp.setColumnCount(n)
            self.table_imp.setHorizontalHeaderLabels(elements)
            self.table_imp.setVerticalHeaderLabels(elements)
            self.table_imp.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            for r in range(n):
                for c in range(n):
                    combo = QComboBox()
                    combo.addItems(elements)
                    self.table_imp.setCellWidget(r, c, combo)
        except Exception as e:
            logger.error(f"Failed to populate implication table: {str(e)}")
            ErrorHandler.show_error("Display Error", "An error occurred while building the implication table.")
    
    def on_relation_changed(self, item: QListWidgetItem):
        try:
            clean = item.text().replace('(', '').replace(')', '').replace("'", "")
            parts = [x.strip() for x in clean.split(',')]
            
            if len(parts) != 2:
                return

            a, b = parts
            if a == b:
                return

            opposite = None
            for i in range(self.rel_list.count()):
                other = self.rel_list.item(i)
                clean_other = other.text().replace('(', '').replace(')', '').replace("'", "")
                other_parts = [v.strip() for v in clean_other.split(',')]
                
                if len(other_parts) == 2 and other_parts[0] == b and other_parts[1] == a:
                    opposite = other
                    break

            if opposite is None:
                return

            self.rel_list.blockSignals(True)

            if item.checkState() == Qt.CheckState.Checked:
                opposite.setCheckState(Qt.CheckState.Unchecked)
                opposite.setFlags(opposite.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            elif item.checkState() == Qt.CheckState.Unchecked:
                opposite.setFlags(opposite.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            self.rel_list.blockSignals(False)

        except Exception as e:
            logger.error(f"Error processing relation change: {str(e)}")

        self.rel_list.blockSignals(True)

        if item.checkState() == Qt.CheckState.Checked:
            opposite.setCheckState(Qt.CheckState.Unchecked)
            opposite.setFlags(opposite.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

        elif item.checkState() == Qt.CheckState.Unchecked:
            opposite.setFlags(opposite.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        self.rel_list.blockSignals(False)

    def validate_and_accept(self):
        try:
            if not self.name_input.text().strip():
                ErrorHandler.show_warning("Validation Error", "Lattice name is required.")
                return
            
            if not self.elements_input.text().strip():
                ErrorHandler.show_warning("Validation Error", "Elements list cannot be empty.")
                return

            self.accept()
        except Exception as e:
            logger.error(f"Error during lattice validation: {str(e)}")
            ErrorHandler.show_error("Validation Error", "An unexpected error occurred while validating the lattice.")

    def get_data(self) -> Tuple[str, Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], str]]:
        try:
            name = self.name_input.text().strip()
            elements = {e.strip() for e in self.elements_input.text().split(',') if e.strip()}
            
            relations = set()
            for i in range(self.rel_list.count()):
                item = self.rel_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    clean = item.text().replace('(', '').replace(')', '').replace("'", "")
                    p = [x.strip() for x in clean.split(',')]
                    if len(p) == 2:
                        relations.add((p[0], p[1]))

            imp_map = {}
            rows = self.table_imp.rowCount()
            for r in range(rows):
                a = self.table_imp.verticalHeaderItem(r).text()
                for c in range(rows):
                    b = self.table_imp.horizontalHeaderItem(c).text()
                    widget = self.table_imp.cellWidget(r, c)
                    res = widget.currentText() if isinstance(widget, QComboBox) else ""
                    imp_map[(a, b)] = res
                    
            return name, elements, relations, imp_map
        except Exception as e:
            logger.error(f"Error retrieving lattice data: {str(e)}")
            ErrorHandler.show_error("Data Error", "An error occurred while retrieving lattice data.")
            raise