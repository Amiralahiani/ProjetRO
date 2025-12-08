import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# ===== PATH BASE DU PROJET =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # <-- chemin dynamique du dossier RO


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📌 Menu Principal - Projets RO")
        self.resize(800, 900)

        # ======== STYLE DASHBOARD CLEAN ========
        self.setStyleSheet("""
            QWidget { background-color:#F4F6F9; color:#2d3436; font-family:'Segoe UI'; }
            
            QLabel#title {
                font-size:32px; font-weight:600; color:#0984e3;
                padding:15px; margin:15px;
            }

            QGroupBox {
                background:#ffffff; padding:25px;
                border-radius:12px; border:1px solid #dfe6e9;
                margin-bottom:22px;
                transition:0.4s;
            }

            QGroupBox:hover {
                border:1px solid #0984e3;
                box-shadow:0px 4px 12px rgba(0,0,0,0.08);
            }

            QLabel { font-size:16px; margin-top:5px; }

            QPushButton {
                background:#0984e3; color:white;
                font-size:17px; padding:10px;
                border-radius:6px; font-weight:500;
                margin-top:12px;
            }

            QPushButton:hover { background:#74b9ff; }
            QScrollArea{ border:none; }
        """)

        layout = QVBoxLayout()

        # ======== TITRE ========
        title = QLabel("📌 Sélectionnez un projet")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        vbox = QVBoxLayout(content)

        # ======== CARTES APPS ========
        self.addCard(vbox,"Application 1","Flux à Coût Minimum avec Capacités",
                     "Optimisation du réseau hydraulique","Amira Lahiani",self.open_app1)

        self.addCard(vbox,"Application 2","Flux à Coût Minimum avec Capacités",
                     "Simulation du transport logistique","Mohamed Abdelwahed",self.open_app2)

        self.addCard(vbox,"Application 3","Flot Multicommmodités",
                     "Gestion des devises interbanques","Omar Trigui",self.open_app3)

        self.addCard(vbox,"Application 4","Planification de Quarts (Shift Scheduling)",
                     "Optimisation des plannings","Rakia Tsouri",self.open_app4)

        self.addCard(vbox,"Application 5","Ordonnancement Multi-Période",
                     "Gestion intelligente des cultures","Senda Ferchichi",self.open_app5)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)



    # ========= TEMPLATE DES CARTES ==========
    def addCard(self,layout,title,pb,sol,realise,action):
        box = QGroupBox(f"🔹 {title}")
        v = QVBoxLayout()

        v.addWidget(QLabel(f"🔴 <b>Problème :</b> {pb}"))
        v.addWidget(QLabel(f"🟢 <b>Application :</b> {sol}"))
        v.addWidget(QLabel(f"🔵 <b>Réalisé par :</b> {realise}"))

        btn = QPushButton(f"▶ Ouvrir {title}")
        btn.clicked.connect(action)
        v.addWidget(btn)

        box.setLayout(v)
        layout.addWidget(box)



    # ========= APPS AVEC PATH RELATIF ==========
    def open_app1(self):
        path = os.path.join(BASE_DIR, "Amira_Lahiani_Distribution d'eau", "main.py")
        subprocess.Popen(f'python "{path}"', shell=True)

    def open_app2(self):
        path = os.path.join(BASE_DIR, "Mohamed_Abdelwahed_Transport de matériaux", 
                            "Transport de matériaux en vrac (pétrole, grain).py")
        subprocess.Popen(f'python "{path}"', shell=True)

    def open_app3(self):
        path = os.path.join(BASE_DIR, "OmarTrigui_Transfert_de_devise_entre_Banques",
                            "Data","Src","main.py")
        subprocess.Popen(f'python "{path}"', shell=True)

    def open_app4(self):
        path = os.path.join(BASE_DIR, "Rakia_Tsouri_Planification des equipages", "mini_app.py")
        subprocess.Popen(f'python "{path}"', shell=True)

    def open_app5(self):
        path = os.path.join(BASE_DIR, "Senda_Ferchichi_ Optimisation agricole", "main.py")
        subprocess.Popen(f'python "{path}"', shell=True)



# ========= LANCEMENT ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
