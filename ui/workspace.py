from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt

class WorkspaceWidget(QWidget):
    hasse_requested = pyqtSignal()
    plts_requested = pyqtSignal()
    filtered_plts_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(5)

        label_details = QLabel("Object Details:")
        label_details.setStyleSheet("font-weight: bold;")
        layout.addWidget(label_details)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select an object in the tree to view details.")
        self.details_text.setMaximumHeight(250)
        self.details_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.details_text)

        btn_layout = QHBoxLayout()
        self.btn_hasse = QPushButton("Show Hasse Diagram")
        self.btn_hasse.setEnabled(False)
        self.btn_hasse.clicked.connect(self.hasse_requested.emit)
        
        self.btn_plts = QPushButton("Show PLTS")
        self.btn_plts.setEnabled(False)
        self.btn_plts.clicked.connect(self.plts_requested.emit)

        self.btn_filtered_plts = QPushButton("Show Filtered PLTS")
        self.btn_filtered_plts.setEnabled(False)
        self.btn_filtered_plts.clicked.connect(self.filtered_plts_requested.emit)
        
        btn_layout.addWidget(self.btn_hasse)
        btn_layout.addWidget(self.btn_plts)
        btn_layout.addWidget(self.btn_filtered_plts)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))