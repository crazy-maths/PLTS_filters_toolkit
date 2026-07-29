from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
from typing import Dict, Tuple
from math_objects.lattice import TwistStructure
from math_objects.filters import LatticeFilter

class NewTwistFilterDialog(QDialog):
    def __init__(self, twists_map: Dict[str, TwistStructure], lat_filters_map: Dict[str, LatticeFilter], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Twist Filter")
        self.resize(400, 200)
        
        self.twists_map = twists_map
        self.lat_filters_map = lat_filters_map
        
        layout = QVBoxLayout(self)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Filter Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., custom_twist_filter")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        ts_layout = QHBoxLayout()
        ts_layout.addWidget(QLabel("Twist Structure:"))
        self.ts_combo = QComboBox()
        self.ts_combo.addItems(sorted(list(self.twists_map.keys())))
        self.ts_combo.currentIndexChanged.connect(self.on_twist_changed)
        ts_layout.addWidget(self.ts_combo)
        layout.addLayout(ts_layout)

        lf_layout = QHBoxLayout()
        lf_layout.addWidget(QLabel("Lattice Filter:"))
        self.lf_combo = QComboBox()
        lf_layout.addWidget(self.lf_combo)
        layout.addLayout(lf_layout)

        self.on_twist_changed()

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def on_twist_changed(self) -> None:
        """Updates the lattice filter combo to only show filters compatible with the selected twist structure's base lattice."""
        self.lf_combo.clear()
        selected_ts_name = self.ts_combo.currentText()
        
        if selected_ts_name in self.twists_map:
            ts_obj = self.twists_map[selected_ts_name]
            target_lattice_name = ts_obj.lattice.name
            
            compatible_filters = [
                lf_name for lf_name, lf_obj in self.lat_filters_map.items()
                if lf_obj.lattice_name == target_lattice_name
            ]
            self.lf_combo.addItems(sorted(compatible_filters))

    def get_data(self) -> Tuple[str, str, str]:
        return (
            self.name_input.text().strip(),
            self.ts_combo.currentText(),
            self.lf_combo.currentText()
        )