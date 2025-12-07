# gui/network_editor.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt


class NetworkEditor(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.setWindowTitle("Éditeur du réseau")
        self.setMinimumSize(1100, 650)

        # -------------------------------------------------------------
        # STYLE MODERNE
        # -------------------------------------------------------------
        self.setStyleSheet("""
            QLabel#SectionTitle {
                font-size: 20px;
                font-weight: 600;
                color: #1F2D3A;
                margin-top: 18px;
                margin-bottom: 8px;
            }
            QTableWidget {
                background: white;
                border-radius: 12px;
                border: 1px solid #D6DFEA;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 16px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #217dbb;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(18)

        # =============================================================
        # TABLE DES NOEUDS
        # =============================================================
        lbl_nodes = QLabel("Nœuds du réseau (demandes)")
        lbl_nodes.setObjectName("SectionTitle")
        layout.addWidget(lbl_nodes)

        self.table_nodes = QTableWidget()
        self.table_nodes.setColumnCount(2)
        self.table_nodes.setHorizontalHeaderLabels(["Nœud", "Demande"])
        self.table_nodes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_nodes)

        btn_add_node = QPushButton("Ajouter un nœud")
        btn_add_node.clicked.connect(self.add_node)
        layout.addWidget(btn_add_node)

        btn_import_nodes = QPushButton("Importer nœuds (CSV)")
        btn_import_nodes.clicked.connect(self.import_nodes)
        layout.addWidget(btn_import_nodes)

        # =============================================================
        # TABLE DES ARCS
        # =============================================================
        lbl_arcs = QLabel("Arcs du réseau")
        lbl_arcs.setObjectName("SectionTitle")
        layout.addWidget(lbl_arcs)

        self.table_arcs = QTableWidget()
        self.table_arcs.setColumnCount(8)
        self.table_arcs.setHorizontalHeaderLabels([
            "u", "v", "Capacité", "MinFlow",
            "Coût bas", "Coût haut", "Seuil", "Pertes"
        ])
        self.table_arcs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_arcs)

        btn_add_arc = QPushButton("Ajouter un arc")
        btn_add_arc.clicked.connect(self.add_arc)
        layout.addWidget(btn_add_arc)

        btn_import_arcs = QPushButton("Importer arcs (CSV)")
        btn_import_arcs.clicked.connect(self.import_arcs)
        layout.addWidget(btn_import_arcs)

        # =============================================================
        # BOUTON SAUVEGARDE
        # =============================================================
        btn_save = QPushButton("Enregistrer le réseau")
        btn_save.clicked.connect(self.save_network)
        layout.addWidget(btn_save)

        btn_back = QPushButton("⬅ Retour au menu principal")
        btn_back.clicked.connect(self.back_to_main)
        layout.addWidget(btn_back)


        self.setLayout(layout)

    # =======================================================================================
    # FONCTIONS TABLE NODES
    # =======================================================================================
    def add_node(self):
        self.table_nodes.insertRow(self.table_nodes.rowCount())

    def import_nodes(self):
        file, _ = QFileDialog.getOpenFileName(self, "Importer nodes.csv", "", "CSV (*.csv)")
        if not file:
            return

        try:
            with open(file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if "node" not in reader.fieldnames or "demand" not in reader.fieldnames:
                    QMessageBox.warning(self, "Erreur", "CSV invalide (colonnes : node, demand).")
                    return

                self.table_nodes.setRowCount(0)

                for row in reader:
                    r = self.table_nodes.rowCount()
                    self.table_nodes.insertRow(r)
                    self.table_nodes.setItem(r, 0, QTableWidgetItem(row["node"]))
                    self.table_nodes.setItem(r, 1, QTableWidgetItem(row["demand"]))

            QMessageBox.information(self, "OK", "Nœuds importés avec succès !")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # =======================================================================================
    # FONCTIONS TABLE ARCS
    # =======================================================================================
    def add_arc(self):
        self.table_arcs.insertRow(self.table_arcs.rowCount())

    def import_arcs(self):
        file, _ = QFileDialog.getOpenFileName(self, "Importer arcs.csv", "", "CSV (*.csv)")
        if not file:
            return

        try:
            with open(file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                expected = ["u", "v", "capacity", "min_flow",
                            "cost_low", "cost_high", "threshold", "loss_rate"]

                if any(col not in reader.fieldnames for col in expected):
                    QMessageBox.warning(self, "Erreur", f"CSV invalide. Colonnes attendues : {', '.join(expected)}")
                    return

                self.table_arcs.setRowCount(0)

                for row in reader:
                    r = self.table_arcs.rowCount()
                    self.table_arcs.insertRow(r)

                    for c, col in enumerate(expected):
                        self.table_arcs.setItem(r, c, QTableWidgetItem(row[col]))

            QMessageBox.information(self, "OK", "Arcs importés avec succès !")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # =======================================================================================
    # SAUVEGARDE DU RÉSEAU
    # =======================================================================================
    def save_network(self):
        nodes = {}
        arcs = []

        # ------------------ Vérification NODES ------------------
        for r in range(self.table_nodes.rowCount()):
            name_item = self.table_nodes.item(r, 0)
            dem_item = self.table_nodes.item(r, 1)

            if not name_item or not dem_item:
                continue

            try:
                nodes[name_item.text()] = float(dem_item.text())
            except ValueError:
                QMessageBox.warning(self, "Erreur", f"Demande invalide ligne {r+1}")
                return

        # ------------------ Vérification ARCS -------------------
        for r in range(self.table_arcs.rowCount()):
            row_vals = []
            for c in range(8):
                item = self.table_arcs.item(r, c)
                if not item:
                    QMessageBox.warning(self, "Erreur", f"Case vide (ligne {r+1})")
                    return
                row_vals.append(item.text())

            u, v, cap, minf, c1, c2, thr, loss = row_vals

            try:
                arcs.append({
                    "u": u,
                    "v": v,
                    "capacity": float(cap),
                    "min_flow": float(minf),
                    "cost_low": float(c1),
                    "cost_high": float(c2),
                    "threshold": float(thr),
                    "loss_rate": float(loss)
                })
            except ValueError:
                QMessageBox.warning(self, "Erreur", f"Valeur numérique invalide en ligne {r+1}")
                return

        # Charger dans MainWindow
        self.main.network.load(nodes, arcs)

        QMessageBox.information(self, "Succès", "Réseau enregistré avec succès.")

        resp = QMessageBox.question(
            self, "Résoudre ?",
            "Souhaites-tu lancer la résolution maintenant ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resp == QMessageBox.Yes:
            self.main.run_solver()     # Lance l'optimisation
            if self.main.solution is not None:
                self.main.open_results()   # Affiche la fenêtre résultats
                self.close()               # On ferme l'éditeur


    def back_to_main(self):
        self.close()
        self.main.show()   # Réaffiche la fenêtre principale

    


