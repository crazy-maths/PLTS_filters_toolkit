from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QListWidget, QFrame, QPushButton, QHBoxLayout, QAbstractItemView, QTreeWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

class SidebarWidget(QWidget):
    add_prop_requested = pyqtSignal()
    remove_prop_requested = pyqtSignal()
    item_clicked = pyqtSignal(object)
    context_menu_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(QLabel("<b>Project Explorer:</b>"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(lambda pos: self.context_menu_requested.emit(pos))
        self.tree.itemClicked.connect(lambda item: self.item_clicked.emit(item))
        layout.addWidget(self.tree)

        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))
        layout.addWidget(QLabel("<b>Propositions:</b>"))
        
        self.prop_list = QListWidget()
        self.prop_list.setMaximumHeight(150)
        self.prop_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.prop_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_remove = QPushButton("Remove")
        self.btn_add.clicked.connect(self.add_prop_requested.emit)
        self.btn_remove.clicked.connect(self.remove_prop_requested.emit)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        layout.addLayout(btn_layout)

    def init_tree_categories(self, categories):
        self.tree_categories = {}
        for cat in categories:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, cat)
            item.setExpanded(True)
            self.tree_categories[cat] = item
        return self.tree_categories

    def refresh_props_ui(self, props: set):
        self.prop_list.clear()
        for p in sorted(list(props)):
            self.prop_list.addItem(p)

    def get_selected_props(self):
        return [item.text() for item in self.prop_list.selectedItems()]