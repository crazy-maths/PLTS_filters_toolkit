from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QComboBox, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

class InterpreterWidget(QWidget):
    evaluate_requested = pyqtSignal()
    validity_requested = pyqtSignal()
    symbol_inserted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        selection_layout = QHBoxLayout()
        selection_layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_models = QComboBox()
        self.combo_worlds = QComboBox()
        self.combo_filters = QComboBox()
        
        selection_layout.addWidget(QLabel("PLTS:"))
        selection_layout.addWidget(self.combo_models, stretch=1)
        selection_layout.addWidget(QLabel("State:"))
        selection_layout.addWidget(self.combo_worlds, stretch=1)
        selection_layout.addWidget(QLabel("Twist Filter:"))
        selection_layout.addWidget(self.combo_filters, stretch=1)
        
        layout.addLayout(selection_layout)

        symbols_layout = QHBoxLayout()
        symbols_layout.setContentsMargins(0, 0, 0, 0)
        for label, text in [("□", "[a]"), ("◇", "<a>"), ("¬", "~"), ("▷", "->"), ("▷◁", "<->"), ("∧", "&"), ("∨", "|"), ("⊥", "0"), ("⊤", "1")]:
            btn = QPushButton(label)
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked, t=text: self.symbol_inserted.emit(t))
            symbols_layout.addWidget(btn)
        
        self.btn_legend = QPushButton("?")
        self.btn_legend.setFixedWidth(30)
        symbols_layout.addWidget(self.btn_legend)
        symbols_layout.addStretch()
        layout.addLayout(symbols_layout)

        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Type formula here...")
        layout.addWidget(self.formula_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_eval = QPushButton("Local Satisfaction")
        self.btn_validity = QPushButton("Global Satisfaction")
        btn_layout.addWidget(self.btn_eval)
        btn_layout.addWidget(self.btn_validity)
        layout.addLayout(btn_layout)

        self.result_label = QLabel("Result: ")
        self.validity_label = QLabel("")
        layout.addWidget(self.result_label)
        layout.addWidget(self.validity_label)

        self.btn_eval.clicked.connect(self.evaluate_requested.emit)
        self.btn_validity.clicked.connect(self.validity_requested.emit)
        self.formula_input.returnPressed.connect(self.evaluate_requested.emit)

        size_policy = self.sizePolicy()
        size_policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        self.setSizePolicy(size_policy)

    def set_model_list(self, models: list):
        self.combo_models.blockSignals(True)
        self.combo_models.clear()
        self.combo_models.addItems(models)
        self.combo_models.blockSignals(False)

    def set_world_list(self, worlds: list):
        self.combo_worlds.clear()
        self.combo_worlds.addItems(worlds)

    def set_filter_list(self, filters: list):
        self.combo_filters.clear()
        self.combo_filters.addItems(filters)

    def get_selected_model(self) -> str:
        return self.combo_models.currentText()

    def get_selected_world(self) -> str:
        return self.combo_worlds.currentText()

    def get_selected_filter(self) -> str:
        return self.combo_filters.currentText()