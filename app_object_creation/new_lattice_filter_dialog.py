from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QListWidget, QDialogButtonBox, QAbstractItemView

class NewLatticeFilterDialog(QDialog):
    def __init__(self, lattices_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Lattice Filter")
        self.resize(350, 400)
        self.lattices_dict = lattices_dict
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Filter Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("Select Base Lattice:"))
        self.combo_lattice = QComboBox()
        self.combo_lattice.addItems(list(lattices_dict.keys()))
        self.combo_lattice.currentIndexChanged.connect(self.populate_elements)
        layout.addWidget(self.combo_lattice)
        
        layout.addWidget(QLabel("Select Filter Elements (Multi-select):"))
        self.list_elements = QListWidget()
        self.list_elements.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.list_elements)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        if lattices_dict:
            self.populate_elements()

    def populate_elements(self):
        self.list_elements.clear()
        lat_name = self.combo_lattice.currentText()
        if lat_name in self.lattices_dict:
            lat = self.lattices_dict[lat_name]
            bottom_element = lat.bottom
            for elem in sorted(list(lat.elements), key=str):
                if elem != bottom_element:
                    self.list_elements.addItem(str(elem))

    def get_data(self):
        filter_name = self.name_input.text().strip()
        lat_name = self.combo_lattice.currentText()
        selected_elements = {item.text() for item in self.list_elements.selectedItems()}
        return filter_name, lat_name, selected_elements