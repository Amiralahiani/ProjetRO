# gui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from projet_ro.gui.network_editor import NetworkEditor
from projet_ro.gui.results_window import ResultsWindow
from projet_ro.models.network_utils import NetworkData
from projet_ro.models.optimizer_mcflow import solve_min_cost_flow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ---------- STYLE UI ----------
        self.setStyleSheet("""
            QWidget {background:#F4F6F9;font-family:'Segoe UI';font-size:15px;}
            QLabel#Title {font-size:30px;font-weight:800;color:#1B2B3C;padding:20px;}
            QPushButton {
                background:#0C6CC7;color:white;border-radius:10px;
                font-size:16px;font-weight:bold;padding:12px;margin:6px;
            }
            QPushButton:hover {background:#084E99;}
        """)

        self.setWindowTitle("Projet RO – Distribution d'eau")
        self.setMinimumSize(950, 600)

        layout = QVBoxLayout()
        title = QLabel("💧 OPTIMISATION DE RÉSEAU D’EAU")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ========= BOUTONS =========
        b1 = QPushButton("Configurer le réseau")
        b1.clicked.connect(self.open_network_editor); layout.addWidget(b1)

        b2 = QPushButton("Résoudre le modèle")
        b2.clicked.connect(self.run_solver); layout.addWidget(b2)

        b3 = QPushButton("Afficher les résultats")
        b3.clicked.connect(self.open_results); layout.addWidget(b3)

        container = QWidget(); container.setLayout(layout)
        self.setCentralWidget(container)

        # ======== Données =========
        self.network = NetworkData()
        self.solution = None
        self.obj_value = None
        self.slacks = None
        self.fair_mode = None
        self.s_ratio = None
        self.opens = None       # <<🔥 corrige "s_max"


    # =============================================================
    def open_network_editor(self):
        self.hide()
        self.editor = NetworkEditor(self)
        self.editor.show()


    # =============================================================
    def run_solver(self):
        if not self.network.validate():
            QMessageBox.warning(self, "Erreur", "⚠ Le réseau n'est pas valide.")
            return

        try:
            (
                self.solution,
                self.obj_value,
                self.slacks,
                self.fair_mode,
                self.s_ratio,
                self.opens,      # <<🔥 ce que renvoie le solveur réellement
            ) = solve_min_cost_flow(self.network)

            QMessageBox.information(self, "Succès", "✔ Optimisation terminée")

        except Exception as e:
            QMessageBox.critical(self, "Erreur Solveur", str(e))


    # =============================================================
    def open_results(self):
        if self.solution is None:
            QMessageBox.warning(self,"Aucun résultat","Résous d'abord le modèle.")
            return

        result_data = (
            self.solution,
            self.obj_value,
            self.slacks,
            self.fair_mode,
            self.s_ratio,
            self.opens,  # <<🔥 cohérent
        )

        self.results_window = ResultsWindow(self, result_data)
        self.results_window.show()
