# ================================================================
# gui/results_window.py  —  VERSION OPTIMISÉE AVEC SEUILS & LÉGENDE
# ================================================================
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class ResultsWindow(QWidget):
    def __init__(self, main, result_data):
        super().__init__()
        self.main = main

        self.flux, self.obj_value, self.slacks, self.fair_mode, self.s_ratio, self.opens = result_data

        self.setWindowTitle("Résultats optimisation")
        self.setMinimumSize(1500, 830)

        # ----------------------------------------------------------
        # STYLE — RESPIRATION, LOOK "iOS"
        # ----------------------------------------------------------
        self.setStyleSheet("""
            QWidget{background:#F5F7FB;font-family:'Segoe UI';color:#0C1D2E;}

            QLabel.title{font-size:27px;font-weight:900;color:#003159;}
            QLabel.block_title{font-size:20px;font-weight:700;color:#004D89;margin-bottom:8px;}
            
            QFrame.card{
                background:white;border-radius:16px;
                border:1px solid #D3E1ED;
                padding:16px;margin-bottom:14px;
            }
            QLabel.item{font-size:15px;margin:3px;}
            
            QPushButton#back{
                background:#0074C7;color:white;font-size:17px;
                border-radius:12px;padding:12px;font-weight:600;
            }
            QPushButton#back:hover{background:#005A97;}
        """)

        layout = QHBoxLayout(self)

        # =====================   PANNEAU GAUCHE   =====================
        left = QVBoxLayout()
        left.setSpacing(18)

        left.addWidget(self.card_resume())
        left.addWidget(self.card_slack())
        left.addWidget(self.card_flux())
        left.addWidget(self.card_plne())

        btn_back = QPushButton("⬅ Retour au menu principal", objectName="back")
        btn_back.clicked.connect(self.return_main)
        left.addWidget(btn_back)

        left_panel = QWidget()
        left_panel.setLayout(left)
        left_panel.setFixedWidth(440)

        # =====================   PANNEAU DROIT   ======================
        right_panel = self.graph_panel()

        layout.addWidget(left_panel)
        layout.addLayout(right_panel)


    # ===============================================================
    # 🔹 Résumé global
    # ===============================================================
    def card_resume(self):
        c = QFrame(objectName="card")
        L = QVBoxLayout(c)

        title = QLabel("📊 Résumé global", objectName="block_title")
        title.setStyleSheet("font-size:20px;font-weight:800;color:#003159;")
        L.addWidget(title)

        L.addWidget(QLabel(f"<b>Mode utilisé :</b> {self.fair_mode}", objectName="item"))
        L.addWidget(QLabel(f"<b>Coût total du réseau :</b> "
                        f"<font color='#CE0037'><b>{self.obj_value:.3f}</b></font>",
                        objectName="item"))

        if self.s_ratio is not None:
            L.addWidget(QLabel(f"<b>Ratio d’équité :</b> {self.s_ratio:.3f}", objectName="item"))
        return c


    # ===============================================================
    # 🔹 Slack par nœud
    # ===============================================================
    def card_slack(self):
        c = QFrame(objectName="card")
        L = QVBoxLayout(c)

        title = QLabel("Slack par nœud (manque d'approvisionnement)", objectName="block_title")
        title.setStyleSheet("font-size:16px;font-weight:800;color:#003159;")
        L.addWidget(title)

        for n,v in self.slacks.items():
            col = "red" if v > 0 else "green"
            L.addWidget(QLabel(f"• <b>{n}</b> = <font color='{col}'><b>{v:.2f}</b></font>", objectName="item"))
        return c


    # ===============================================================
    # 🔹 Flux détecté sur chaque canal
    # ===============================================================
    def card_flux(self):
        c = QFrame(objectName="card")
        L = QVBoxLayout(c)

        title = QLabel("Flux circulant dans les canalisations", objectName="block_title")
        title.setStyleSheet("font-size:16px;font-weight:800;color:#003159;")
        L.addWidget(title)

        for (u,v),f in self.flux.items():
            L.addWidget(QLabel(f"• <b>{u}</b> → <b>{v}</b> = {f:.2f}", objectName="item"))
        return c


    # ===============================================================
    # 🔹 Activation des arcs (PLNE)
    # ===============================================================
    def card_plne(self):
        c = QFrame(objectName="card")
        L = QVBoxLayout(c)

        title = QLabel("Ouverture/Fermeture des canaux (PLNE)", objectName="block_title")
        title.setStyleSheet("font-size:16px;font-weight:800;color:#003159;")
        L.addWidget(title)

        for (u,v),a in self.opens.items():
            state = "<font color='green'><b>OUVERT</b></font>" if a>0.5 else "<font color='red'><b>FERMÉ</b></font>"
            L.addWidget(QLabel(f"• {u} → {v} : {state}", objectName="item"))
        return c



    # ===============================================================
    # GRAPHE + ANALYSE + LÉGENDE + COULEURS SEUILS
    # ===============================================================
    def graph_panel(self):

        wrapper = QVBoxLayout()

        card = QFrame(objectName="card")
        L = QVBoxLayout(card)

        title = QLabel("Structure du réseau optimisé")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:800;color:#002844;")
        L.addWidget(title)

        # ----------------------------------------------------
        # Construction du graphe NX en tenant compte des seuils
        # ----------------------------------------------------
        fig = plt.figure(figsize=(7.2,6))
        canvas = FigureCanvasQTAgg(fig)

        G = nx.DiGraph()
        for (u,v),f in self.flux.items():
            arc = self.main.network.get_arc(u,v)    # ← récupération capacite / seuil
            T  = arc["threshold"]
            C  = arc["capacity"]

            if f < 0.7*T:              color = "#3BAA4A"     # 🟩 sous seuil
            elif f <= T:               color = "#F1A208"     # 🟧 proche seuil
            else:                      color = "#D7263D"     # 🟥 dépassement !

            G.add_edge(u,v,flow=f,color=color,cap=C,thr=T)

        pos = nx.spring_layout(G,seed=2)

        nx.draw(
            G,pos,
            node_size=3500,node_color="LightSkyBlue",
            edge_color=[d["color"] for _,_,d in G.edges(data=True)],
            width = [1.2 + (d["flow"]/max(self.flux.values()))*6 for _,_,d in G.edges(data=True)],
            arrowsize=22
        )
        nx.draw_networkx_labels(G,pos,font_size=13,font_weight="bold")

        # labels
        nx.draw_networkx_edge_labels(
            G,pos,
            edge_labels={(u,v):f"{d['flow']:.1f}/{d['cap']}" for u,v,d in G.edges(data=True)},
            font_size=11
        )

        L.addWidget(canvas)

        # ----------------------------------------------------
        #  🔍 LÉGENDE COULEURS + EXPLICATION CLAIRE
        # ----------------------------------------------------
        legend = QFrame(objectName="card")
        X = QVBoxLayout(legend)
        X.addWidget(QLabel("📎 Code couleur des canaux :", objectName="block_title"))
        X.addWidget(QLabel("🟩 <b>Débit stable</b> – sous le seuil", objectName="item"))
        X.addWidget(QLabel("🟧 <b>Zone critique</b> – proche du seuil", objectName="item"))
        X.addWidget(QLabel("🟥 <b>Sur-utilisation</b> → augmente fortement le coût !", objectName="item"))
        L.addWidget(legend)

        wrapper.addWidget(card)
        return wrapper


    def return_main(self):
        self.close()
        self.main.show()
