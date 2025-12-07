"""
app_min_cost_flow_modern.py
Version modernisée de l'IHM Flux à coût minimum (PyQt5 + Gurobi)
- UI stylée (stylesheet)
- QTableWidget pour coûts / capacités / b
- Thread non bloquant pour Gurobi
- Visualisation avec Matplotlib + NetworkX
- Import/Export Excel (.xlsx)
"""

import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog, QSpinBox,
    QTextEdit, QFrame, QHeaderView, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Gurobi import (handle absence gracefully)
try:
    from gurobipy import Model, GRB, quicksum
    HAVE_GUROBI = True
except Exception as e:
    HAVE_GUROBI = False
    GUR_ERROR = str(e)


# ------------ Solver Thread ------------
class SolverThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, nodes, arcs, costs, caps, b, silent=True):
        super().__init__()
        # ensure names are clean copies
        self.nodes = [str(n).strip() for n in nodes]
        self.arcs = [(str(i).strip(), str(j).strip()) for (i, j) in arcs]
        # normalize costs/caps keys
        self.costs = {(str(i).strip(), str(j).strip()): float(v) for (i, j), v in costs.items()}
        self.caps = {(str(i).strip(), str(j).strip()): (float(v) if (v is not None and v != float('inf')) else float('inf'))
                     for (i, j), v in caps.items()}
        # normalize b
        self.b = {str(k).strip(): float(v) for k, v in b.items()}
        self.silent = silent

    def run(self):
        try:
            if not HAVE_GUROBI:
                self.error_signal.emit("gurobipy non installé : " + GUR_ERROR)
                return

            m = Model("MinCostFlow")
            if self.silent:
                m.setParam('OutputFlag', 0)

            # create vars
            x = {}
            for (i, j) in self.arcs:
                ub = self.caps.get((i, j), float('inf'))
                if ub is None:
                    ub = float('inf')
                ub_g = ub if (ub != float('inf')) else GRB.INFINITY
                # variable name without spaces
                varname = f"x_{i}_{j}".replace(" ", "_")
                x[(i, j)] = m.addVar(lb=0.0, ub=ub_g, name=varname)

            # objective
            m.setObjective(quicksum(self.costs.get((i, j), 0.0) * x[(i, j)] for (i, j) in self.arcs), GRB.MINIMIZE)

            # flow conservation (corrected)
            for node in self.nodes:
                outgoing = quicksum(x[(i, j)] for (i, j) in self.arcs if i == node)
                incoming = quicksum(x[(i, j)] for (i, j) in self.arcs if j == node)
                rhs = self.b.get(node, 0.0)
                m.addConstr(outgoing - incoming == rhs, name=f"flow_{node}")

            # optional: emit progress (fake steps)
            self.progress_signal.emit(5)
            m.optimize()
            self.progress_signal.emit(80)

            # build flows dict (normalized)
            flows = {}
            if m.status == GRB.OPTIMAL:
                for (i, j) in self.arcs:
                    val = x[(i, j)].X
                    # cast to float
                    try:
                        v = float(val)
                    except:
                        v = 0.0
                    flows[f"{i}->{j}"] = v

                result = {"status": "OPTIMAL", "obj": float(m.ObjVal), "flows": flows}
            else:
                result = {"status": f"STATUS_{m.status}", "obj": None, "flows": {}}

            # debug print to console so you can see raw solver output
            print("\n[DEBUG] SolverThread result flows:")
            for k, vv in result["flows"].items():
                print(f"  {k} = {vv}")
            print("[DEBUG] Obj:", result["obj"])
            print("--------------------------------------------------\n")

            self.progress_signal.emit(100)
            self.finished_signal.emit(result)

        except Exception as e:
            tb = traceback.format_exc()
            self.error_signal.emit(str(e) + "\n" + tb)


# ------------ Matplotlib canvas wrapper ------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5.5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)


# ------------ Main Window ------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flux à coût minimum — IHM Moderne")
        self.setWindowIcon(QIcon())  # add path to icon if you want
        self.resize(1200, 800)

        # Data placeholders
        self.nodes = []
        self.arcs = []
        self.costs = {}
        self.caps = {}
        self.b = {}

        # central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # left side: controls and tables
        left_frame = QFrame()
        left_frame.setMinimumWidth(480)
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)

        # header
        title = QLabel("Flux à coût minimum — Interface")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        left_layout.addWidget(title)

        # node count and generate button
        h_top = QHBoxLayout()
        left_layout.addLayout(h_top)
        h_top.addWidget(QLabel("Nombre de nœuds :"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(2, 20)
        self.spin_n.setValue(3)
        self.spin_n.setFixedWidth(80)
        h_top.addWidget(self.spin_n)
        btn_gen = QPushButton("Générer matrices")
        btn_gen.clicked.connect(self.generate_tables)
        h_top.addWidget(btn_gen)

        # tables area (costs, caps, b)
        sub_title = QLabel("Saisie des données")
        sub_title.setStyleSheet("color: #e0e0e0;")
        left_layout.addWidget(sub_title)

        # Costs table
        lbl_cost = QLabel("Matrice des coûts (c_ij)")
        lbl_cost.setStyleSheet("color: #d0d0d0;")
        left_layout.addWidget(lbl_cost)
        self.table_cost = QTableWidget()
        self.table_cost.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.table_cost, 2)

        # Caps table
        lbl_cap = QLabel("Matrice des capacités (u_ij)")
        lbl_cap.setStyleSheet("color: #d0d0d0;")
        left_layout.addWidget(lbl_cap)
        self.table_cap = QTableWidget()
        left_layout.addWidget(self.table_cap, 2)

        # b vector
        lbl_b = QLabel("Bilan b_i (positive=offre, negative=demande)")
        lbl_b.setStyleSheet("color: #d0d0d0;")
        left_layout.addWidget(lbl_b)
        self.table_b = QTableWidget()
        self.table_b.setFixedHeight(150)
        left_layout.addWidget(self.table_b)

        # buttons area
        btn_layout = QHBoxLayout()
        left_layout.addLayout(btn_layout)
        btn_load = QPushButton("Charger (.xlsx)")
        btn_load.clicked.connect(self.load_file)
        btn_layout.addWidget(btn_load)
        btn_save = QPushButton("Sauvegarder (.xlsx)")
        btn_save.clicked.connect(self.save_file)
        btn_layout.addWidget(btn_save)

        # run and export
        btn_run = QPushButton("Lancer résolution")
        btn_run.setStyleSheet("padding:10px; font-weight:bold;")
        btn_run.clicked.connect(self.launch_solver)
        left_layout.addWidget(btn_run)

        # progress bar and log
        self.progress = QProgressBar()
        self.progress.setValue(0)
        left_layout.addWidget(self.progress)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(140)
        left_layout.addWidget(self.log)

        # right side: visualization and results
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)

        right_header = QLabel("Visualisation & Résultats")
        right_header.setFont(QFont("Arial", 14, QFont.Bold))
        right_header.setStyleSheet("color:#ffffff;")
        right_layout.addWidget(right_header)

        # canvas
        self.canvas = MplCanvas(self, width=6, height=4, dpi=110)
        right_layout.addWidget(self.canvas, 4)

        # results table
        lbl_res = QLabel("Flux optimaux")
        lbl_res.setStyleSheet("color:#e0e0e0;")
        right_layout.addWidget(lbl_res)
        self.results_widget = QTableWidget()
        self.results_widget.setColumnCount(3)
        self.results_widget.setHorizontalHeaderLabels(["Arc", "Flux", "Capacité"])
        self.results_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.results_widget, 2)

        # status bar
        self.status = self.statusBar()
        self.status.showMessage("Prêt")

        # add frames
        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame, 1)

        # styling
        self.apply_stylesheet()
        self.generate_tables()

    def apply_stylesheet(self):
        # simple dark-modern style with vibrant accents
        style = """
        QMainWindow { background-color: #2b2f36; }
        QLabel { color: #dfe6ee; }
        QPushButton { 
            background-color: #4b8bf5; color: white; border-radius: 8px; padding: 6px;
        }
        QPushButton:hover { background-color: #6ea2ff; }
        QTableWidget { background-color: #f8fbff; border: 1px solid #ddd; }
        QHeaderView::section { background-color: #4b8bf5; color: white; padding:6px; border: none; }
        QProgressBar { background: #dcdcdc; border-radius: 5px; text-align: center; }
        QProgressBar::chunk { background-color: #4b8bf5; }
        QTextEdit { background-color: #1f2328; color: #cfe3ff; border-radius:6px; }
        """
        self.setStyleSheet(style)

    def generate_tables(self):
        # create default nodes N1..Nn
        n = self.spin_n.value()
        nodes = [f"N{i+1}" for i in range(n)]
        self.nodes = nodes

        # costs table
        self.table_cost.setColumnCount(n)
        self.table_cost.setRowCount(n)
        self.table_cost.setHorizontalHeaderLabels(nodes)
        self.table_cost.setVerticalHeaderLabels(nodes)
        self.table_cost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_cost.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # caps table
        self.table_cap.setColumnCount(n)
        self.table_cap.setRowCount(n)
        self.table_cap.setHorizontalHeaderLabels(nodes)
        self.table_cap.setVerticalHeaderLabels(nodes)
        self.table_cap.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_cap.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # fill defaults
        for i in range(n):
            for j in range(n):
                if i == j:
                    item_c = QTableWidgetItem("")
                    item_c.setFlags(Qt.ItemIsEnabled)
                    self.table_cost.setItem(i, j, item_c)
                    item_u = QTableWidgetItem("")
                    item_u.setFlags(Qt.ItemIsEnabled)
                    self.table_cap.setItem(i, j, item_u)
                else:
                    # more modern default values
                    self.table_cost.setItem(i, j, QTableWidgetItem("1"))
                    self.table_cap.setItem(i, j, QTableWidgetItem("100"))

        # b table
        self.table_b.setColumnCount(2)
        self.table_b.setRowCount(n)
        self.table_b.setHorizontalHeaderLabels(["Noeud", "b_i"])
        self.table_b.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, node in enumerate(nodes):
            itn = QTableWidgetItem(node)
            itn.setFlags(Qt.ItemIsEnabled)
            self.table_b.setItem(i, 0, itn)
            default = "0"
            if i == 0:
                default = "20"
            elif i == 1:
                default = "-15"
            elif i == 2:
                default = "-5"
            self.table_b.setItem(i, 1, QTableWidgetItem(default))

        self.log.append("Tables générées (UI moderne).")

    def read_tables(self):
        # read b
        n = self.table_b.rowCount()
        nodes = []
        b = {}
        for i in range(n):
            node_item = self.table_b.item(i, 0)
            node = node_item.text().strip() if node_item else f"N{i+1}"
            nodes.append(node)
            val_item = self.table_b.item(i, 1)
            try:
                val = float(val_item.text()) if val_item and val_item.text() != "" else 0.0
            except:
                val = 0.0
            b[node] = val

        costs = {}
        caps = {}
        arcs = []
        for i, ni in enumerate(nodes):
            for j, nj in enumerate(nodes):
                if i == j:
                    continue
                cell = self.table_cost.item(i, j)
                # only accept non-empty cells (strip)
                if cell and cell.text().strip() != "":
                    try:
                        cval = float(cell.text().strip())
                    except:
                        cval = 0.0
                    costs[(ni, nj)] = cval
                    cell_u = self.table_cap.item(i, j)
                    try:
                        uval = float(cell_u.text().strip()) if (cell_u and cell_u.text().strip() != "") else float('inf')
                    except:
                        uval = float('inf')
                    caps[(ni, nj)] = uval
                    arcs.append((ni, nj))
        return nodes, arcs, costs, caps, b


    def launch_solver(self):
        nodes, arcs, costs, caps, b = self.read_tables()
        # update the UI state (important so plot & table can access caps/costs)
        self.nodes = nodes
        self.arcs = arcs
        self.costs = costs
        self.caps = caps
        self.b = b

        self.log.append(f"Données prêtes : {len(nodes)} nœuds, {len(arcs)} arcs.")
        self.status.showMessage("Vérification des données...")

        # check balance
        sumb = sum(b.values())
        if abs(sumb) > 1e-6:
            msg = (f"Somme des b_i = {sumb:.4f} (doit être 0). "
                   "Ajouter un noeud Dummy pour équilibrer ?")
            res = QMessageBox.question(self, "Équilibre", msg, QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                dummy = "Dummy"
                # avoid name clash
                idx = 1
                while dummy in nodes:
                    dummy = f"Dummy{idx}"
                    idx += 1
                nodes.append(dummy)
                # create arcs to absorb/extract surplus
                if sumb > 0:
                    # surplus: add edges from nodes -> dummy
                    for nd in list(nodes):
                        if nd == dummy: continue
                        arcs.append((nd, dummy))
                        costs[(nd, dummy)] = 0.0
                        caps[(nd, dummy)] = abs(sumb)
                else:
                    for nd in list(nodes):
                        if nd == dummy: continue
                        arcs.append((dummy, nd))
                        costs[(dummy, nd)] = 0.0
                        caps[(dummy, nd)] = abs(sumb)
                b[dummy] = -sumb
                self.log.append(f"Noeud {dummy} ajouté (b={-sumb:.4f})")
            else:
                self.log.append("Annulé : corriger b_i")
                self.status.showMessage("Annulé - somme b_i non nulle")
                return

        # start thread
        self.thread = SolverThread(nodes, arcs, costs, caps, b)
        self.thread.progress_signal.connect(self.on_progress)
        self.thread.finished_signal.connect(self.on_solved)
        self.thread.error_signal.connect(self.on_error)
        self.progress.setValue(0)
        self.log.append("Lancement du solveur (thread)...")
        self.status.showMessage("Solveur en cours...")
        self.thread.start()

    def on_progress(self, v):
        self.progress.setValue(v)

    def on_error(self, msg):
        QMessageBox.critical(self, "Erreur Gurobi", msg)
        self.log.append("Erreur: " + msg)
        self.status.showMessage("Erreur solveur")

    def on_solved(self, result):
        status = result.get("status", "")
        self.log.append("Solveur: " + str(status))

        # DEBUG: print raw result to console for troubleshooting
        print("\n[DEBUG] on_solved received result:")
        print(result)
        print("--------------------------------------------------\n")

        if status == "OPTIMAL":
            obj = result.get("obj", None)
            flows = result.get("flows", {})  # flows should be like {"N1->N2": val}
            
            # normalize flows: strip names and cast to float
            norm_flows = {}
            for arcstr, val in flows.items():
                if not isinstance(arcstr, str):
                    arcstr = str(arcstr)
                parts = arcstr.split("->")
                if len(parts) != 2:
                    continue
                i = parts[0].strip()
                j = parts[1].strip()
                try:
                    v = float(val)
                except:
                    v = 0.0
                # CORRECTION: Garder la vraie valeur, ne pas la mettre à 0 !
                norm_flows[f"{i}->{j}"] = v
            
            print("\n[DEBUG] Normalized flows in on_solved:")
            for k, v in norm_flows.items():
                print(f"  {k} = {v}")
            print("--------------------------------------------------\n")

            self.log.append(f"Coût optimal = {obj}")
            # fill results table
            self.results_widget.setRowCount(len(norm_flows))
            r = 0
            for arc, val in norm_flows.items():
                arc_item = QTableWidgetItem(str(arc))
                flux_item = QTableWidgetItem(f"{val:.6g}")
                # cap lookup using tuple
                try:
                    parts = arc.split("->")
                    cap_val = self.caps.get((parts[0].strip(), parts[1].strip()), "")
                except:
                    cap_val = ""
                cap_item = QTableWidgetItem(str(cap_val))
                self.results_widget.setItem(r, 0, arc_item)
                self.results_widget.setItem(r, 1, flux_item)
                self.results_widget.setItem(r, 2, cap_item)
                r += 1
            # plot using normalized flows
            self.plot_solution(norm_flows)
            self.status.showMessage(f"Terminé — coût = {obj}")
            self.progress.setValue(100)
        else:
            QMessageBox.warning(self, "Résolution", f"Le solveur a renvoyé : {status}")
            self.status.showMessage(f"Terminé : {status}")

    def plot_solution(self, flows):
        """
        flows: dict avec clés "N1->N2" et valeurs numériques (ex: 15.0)
        """
        self.canvas.ax.clear()

        if not flows:
            self.canvas.ax.text(0.5, 0.5, "Aucun flux à afficher", ha='center', va='center',
                                transform=self.canvas.ax.transAxes, fontsize=14)
            self.canvas.ax.set_axis_off()
            self.canvas.draw()
            return

        # Créer un graphe VIERGE
        G = nx.DiGraph()

        # Ajouter UNIQUEMENT les arêtes qui ont un flux défini (même à 0 si tu veux les voir)
        edge_list = []
        for arcstr, val in flows.items():
            if not isinstance(arcstr, str):
                continue
            parts = arcstr.replace(" ", "").split("->")
            if len(parts) != 2:
                continue
            i, j = parts[0], parts[1]

            try:
                v = float(val)
            except:
                v = 0.0

            # Ajouter l'arête avec son flux
            G.add_edge(i, j, weight=v)
            edge_list.append((i, j, v))

        if len(G.nodes()) == 0:
            self.canvas.ax.text(0.5, 0.5, "Aucun nœud détecté", ha='center', va='center',
                                transform=self.canvas.ax.transAxes, fontsize=14)
            self.canvas.ax.set_axis_off()
            self.canvas.draw()
            return

        # --- Positionnement ---
        n_nodes = len(G.nodes())
        if n_nodes <= 4:
            # Disposition manuelle plus lisible pour petits graphes
            nodes_sorted = sorted(G.nodes())
            pos = {}
            if n_nodes == 3:
                pos[nodes_sorted[0]] = (0, 0)
                pos[nodes_sorted[1]] = (1, 1)
                pos[nodes_sorted[2]] = (2, 0)
            elif n_nodes == 4:
                pos[nodes_sorted[0]] = (0, 1)
                pos[nodes_sorted[1]] = (0, 0)
                pos[nodes_sorted[2]] = (1, 1)
                pos[nodes_sorted[3]] = (1, 0)
            else:
                pos = nx.circular_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42, k=1.5)

        # --- Dessin des nœuds ---
        nx.draw_networkx_nodes(G, pos, ax=self.canvas.ax,
                            node_size=1000, node_color="#4b8bf5", edgecolors="white", linewidths=2)
        nx.draw_networkx_labels(G, pos, ax=self.canvas.ax,
                                font_color="white", font_weight="bold", font_size=12)

        # --- Préparation des largeurs et couleurs ---
        flows_values = [abs(data['weight']) for u, v, data in G.edges(data=True)]
        max_flow = max(flows_values) if flows_values else 1
        min_width = 1.0
        max_width = 8.0

        # --- Dessin des arêtes une par une (contrôle total) ---
        for u, v, val in edge_list:
            width = min_width if max_flow == 0 else min_width + (max_width - min_width) * (abs(val) / max_flow)
            width = max(width, 1.0)

            # Couleur selon intensité du flux
            if abs(val) > 1e-6:
                color = "#2ecc71"   # vert vif pour flux positif
            else:
                color = "#95a5a6"   # gris pour flux nul

            # Dessin de l'arête
            nx.draw_networkx_edges(G, pos,
                                edgelist=[(u, v)],
                                ax=self.canvas.ax,
                                width=width,
                                arrowsize=25,
                                arrowstyle="-|>",
                                edge_color=color,
                                connectionstyle="arc3,rad=0.15")

            # Label du flux au milieu de l'arête
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            xm = (x1 + x2) / 2 + (0.05 if x1 > x2 else -0.05)  # petit décalage pour lisibilité
            ym = (y1 + y2) / 2 + 0.08

            label = "0" if abs(val) < 0.01 else f"{val:.2f}".rstrip("0").rstrip(".")
            self.canvas.ax.text(xm, ym, label,
                                fontsize=11, fontweight='bold',
                                ha='center', va='center',
                                bbox=dict(facecolor='white', alpha=0.85, edgecolor='none',
                                        boxstyle='round,pad=0.4', linewidth=0))

        self.canvas.ax.set_axis_off()
        self.canvas.ax.margins(0.15)
        self.canvas.draw()
        print("[DEBUG] Graphe affiché correctement avec uniquement les vraies arêtes")

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger fichier Excel", "", "Excel (*.xlsx *.xls)")
        if not path:
            return
        try:
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names
            # require sheets: costs, caps, b
            if all(s in sheets for s in ["costs", "caps", "b"]):
                df_cost = pd.read_excel(path, sheet_name="costs", index_col=0)
                df_caps = pd.read_excel(path, sheet_name="caps", index_col=0)
                df_b = pd.read_excel(path, sheet_name="b")
                nodes = list(df_cost.index.astype(str))
                self.spin_n.setValue(len(nodes))
                self.generate_tables()
                # fill costs & caps & b
                for i, ni in enumerate(nodes):
                    for j, nj in enumerate(nodes):
                        if ni == nj:
                            continue
                        try:
                            v = df_cost.loc[ni, nj]
                            self.table_cost.setItem(i, j, QTableWidgetItem(str(v)))
                        except:
                            pass
                        try:
                            u = df_caps.loc[ni, nj]
                            self.table_cap.setItem(i, j, QTableWidgetItem(str(u)))
                        except:
                            pass
                # b
                for idx, row in df_b.iterrows():
                    node = str(row.iloc[0])
                    val = str(row.iloc[1])
                    try:
                        i = nodes.index(node)
                        self.table_b.setItem(i, 1, QTableWidgetItem(val))
                    except:
                        pass
                self.log.append("Fichier importé (sheets: costs, caps, b).")
            else:
                QMessageBox.information(self, "Format attendu",
                                        "Le fichier Excel doit contenir les feuilles: costs, caps, b.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur import", str(e))

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier", "", "Excel (*.xlsx)")
        if not path:
            return
        try:
            nodes, arcs, costs, caps, b = self.read_tables()
            df_cost = pd.DataFrame(index=nodes, columns=nodes)
            df_cap = pd.DataFrame(index=nodes, columns=nodes)
            for i in nodes:
                for j in nodes:
                    if i == j:
                        df_cost.loc[i, j] = ""
                        df_cap.loc[i, j] = ""
                    else:
                        df_cost.loc[i, j] = costs.get((i, j), "")
                        df_cap.loc[i, j] = caps.get((i, j), "")
            df_b = pd.DataFrame([(n, b[n]) for n in nodes], columns=["Node", "b"])
            with pd.ExcelWriter(path) as writer:
                df_cost.to_excel(writer, sheet_name="costs")
                df_cap.to_excel(writer, sheet_name="caps")
                df_b.to_excel(writer, sheet_name="b", index=False)
            self.log.append("Fichier sauvegardé: " + path)
        except Exception as e:
            QMessageBox.critical(self, "Erreur sauvegarde", str(e))


# ---------- main ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # set application font
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())