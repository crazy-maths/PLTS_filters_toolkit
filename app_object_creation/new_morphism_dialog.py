"""
New Morphism Dialog Module.

Provides an interactive dialog for users to define and validate morphisms between
two compatible PLTS models, enforcing that mapping rules satisfy morphism conditions.
"""

from typing import Dict, List, Tuple, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from math_objects.model import Model
from math_objects.world import World
from math_objects.morphism import PLTSMorphism


class NewMorphismDialog(QDialog):
    """
    Dialog allowing the user to select a source and target PLTS, map their states,
    verify morphism conditions in real-time, and save the result.
    """

    def __init__(self, models_map: Dict[str, Model], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New PLTS Morphism")
        self.resize(650, 500)
        
        self.models_map = models_map
        self.source_model: Optional[Model] = None
        self.target_model: Optional[Model] = None
        self.mapping_combos: Dict[World, QComboBox] = {}
        
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Morphism Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. morphism_1")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        selection_layout = QHBoxLayout()
        
        self.source_combo = QComboBox()
        self.source_combo.addItem("-- Select Source PLTS --")
        self.source_combo.addItems(sorted(self.models_map.keys()))
        self.source_combo.currentIndexChanged.connect(self.on_models_changed)
        
        self.target_combo = QComboBox()
        self.target_combo.addItem("-- Select Target PLTS --")
        self.target_combo.addItems(sorted(self.models_map.keys()))
        self.target_combo.currentIndexChanged.connect(self.on_models_changed)

        selection_layout.addWidget(QLabel("Source:"))
        selection_layout.addWidget(self.source_combo)
        selection_layout.addWidget(QLabel("Target:"))
        selection_layout.addWidget(self.target_combo)
        layout.addLayout(selection_layout)

        layout.addWidget(QLabel("State Mapping Function (h: Source State -> Target State):"))
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Source State (w)", "Target State Image h(w)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        self.btn_verify = QPushButton("Verify Morphism Conditions")
        self.btn_verify.clicked.connect(self.verify_mapping)
        self.btn_verify.setEnabled(False)

        self.btn_save = QPushButton("Save Morphism")
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setEnabled(False)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_verify)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def on_models_changed(self) -> None:
        src_name = self.source_combo.currentText()
        tgt_name = self.target_combo.currentText()

        self.table.setRowCount(0)
        self.mapping_combos.clear()
        self.btn_verify.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.status_label.setText("")

        self.target_combo.blockSignals(True)

        if src_name in self.models_map:
            self.source_model = self.models_map[src_name]
            
            current_target = self.target_combo.currentText()
            self.target_combo.clear()
            self.target_combo.addItem("-- Select Target PLTS --")
            
            compatible_models = []
            for name, m in self.models_map.items():
                if (m.twist_structure.name == self.source_model.twist_structure.name and
                    m.actions == self.source_model.actions and
                    m.props == self.source_model.props):
                    compatible_models.append(name)
            
            self.target_combo.addItems(sorted(compatible_models))
            
            idx = self.target_combo.findText(current_target)
            if idx != -1:
                self.target_combo.setCurrentIndex(idx)

        self.target_combo.blockSignals(False)

        tgt_name = self.target_combo.currentText()
        if src_name in self.models_map and tgt_name in self.models_map:
            self.source_model = self.models_map[src_name]
            self.target_model = self.models_map[tgt_name]

            target_worlds = sorted(list(self.target_model.worlds), key=lambda w: w.name_long)
            source_worlds = sorted(list(self.source_model.worlds), key=lambda w: w.name_long)

            self.table.setRowCount(len(source_worlds))
            for row, sw in enumerate(source_worlds):
                self.table.setItem(row, 0, QTableWidgetItem(f"{sw.name_long} ({sw.name_short})"))
                
                combo = QComboBox()
                for tw in target_worlds:
                    combo.addItem(f"{tw.name_long} ({tw.name_short})", tw)
                
                self.mapping_combos[sw] = combo
                self.table.setCellWidget(row, 1, combo)

            self.btn_verify.setEnabled(True)

    def build_current_morphism(self) -> Optional[PLTSMorphism]:
        name = self.name_input.text().strip()
        if not name:
            name = f"{self.source_model.name_model}_to_{self.target_model.name_model}"

        mapping = {}
        for sw, combo in self.mapping_combos.items():
            tw = combo.currentData()
            mapping[sw] = tw

        return PLTSMorphism(
            name=name,
            source_model=self.source_model,
            target_model=self.target_model,
            mapping=mapping
        )

    def verify_mapping(self) -> None:
        if not self.source_model or not self.target_model:
            return

        morphism = self.build_current_morphism()
        is_valid, errors = morphism.verify_morphism()

        if is_valid:
            self.status_label.setText("Success! The mapping function is a valid morphism.")
            self.status_label.setStyleSheet("color: green;")
            self.btn_save.setEnabled(True)
            QMessageBox.information(self, "Validation Successful", "The mapping satisfies both valuation and accessibility conditions.")
        else:
            self.status_label.setText("Verification Failed. See details below.")
            self.status_label.setStyleSheet("color: red;")
            self.btn_save.setEnabled(False)
            
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n...and {len(errors) - 10} more error(s)."
            
            QMessageBox.warning(self, "Morphism Validation Failed", f"The mapping is not a valid morphism:\n\n{error_text}")

    def get_data(self) -> Tuple[str, PLTSMorphism]:
        name = self.name_input.text().strip()
        morphism = self.build_current_morphism()
        if name:
            morphism.name = name
        return morphism.name, morphism