:wq:import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from modele_plm import run_plm_model


class GraphWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualisation - Plan de Production")
        self.setGeometry(250, 150, 1000, 650)

        # Style sombre avec bleu
        self.setStyleSheet("""
            background-color: #0f1419;
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.setLayout(layout)

        # Titre minimal
        title_label = QLabel("Analyse des Flux")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("""
            color: #ffffff;
            padding: 12px;
            background-color: #1c2530;
            border-radius: 6px;
            border-left: 4px solid #4fc3f7;
        """)
        layout.addWidget(title_label)

        # Figure avec style sombre bleuté
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.fig.patch.set_facecolor('#0f1419')
        self.canvas = FigureCanvas(self.fig)

        # Cadre pour le graphique
        graph_frame = QFrame()
        graph_frame.setStyleSheet("""
            QFrame {
                background-color: #1c2530;
                border-radius: 6px;
                border: 1px solid #2a3a4a;
                padding: 3px;
            }
        """)
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.addWidget(self.canvas)
        layout.addWidget(graph_frame)

        # Bouton simple
        btn_close = QPushButton("Fermer")
        btn_close.setFont(QFont("Segoe UI", 9))
        btn_close.setFixedSize(100, 35)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2a3a4a;
                color: #e1f5fe;
                padding: 6px 15px;
                border-radius: 4px;
                border: 1px solid #374a5f;
            }
            QPushButton:hover {
                background-color: #4fc3f7;
                border-color: #4fc3f7;
                color: #0f1419;
            }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

    def update_graph(self, results, T):
        """Mettre à jour le graphique avec les nouveaux résultats"""
        self.ax.clear()
        periods = range(1, T + 1)

        # Palette de bleus différents
        colors = ['#4fc3f7', '#29b6f6', '#03a9f4', '#0288d1', '#0277bd']

        # Traçage des courbes
        self.ax.plot(periods, results['R'], label="Production",
                     linewidth=2.2, marker='o', markersize=6,
                     color=colors[0], markerfacecolor='#1c2530', markeredgewidth=1.5)

        self.ax.plot(periods, results['A'], label="Achat",
                     linewidth=2.2, marker='s', markersize=6,
                     color=colors[1], markerfacecolor='#1c2530', markeredgewidth=1.5)

        self.ax.plot(periods, results['T'], label="Transformation",
                     linewidth=2.2, marker='^', markersize=6,
                     color=colors[2], markerfacecolor='#1c2530', markeredgewidth=1.5)

        self.ax.plot(periods, results['S'], label="Stock",
                     linewidth=2.2, marker='D', markersize=6,
                     color=colors[3], markerfacecolor='#1c2530', markeredgewidth=1.5)

        # Style minimal des axes
        self.ax.set_xlabel("Périodes", fontsize=11, color='#b0bec5')
        self.ax.set_ylabel("Quantités", fontsize=11, color='#b0bec5')

        # Grille très subtile
        self.ax.grid(True, alpha=0.15, color='#37474f', linestyle=':')
        self.ax.set_facecolor('#1c2530')

        # Style des bordures
        for spine in self.ax.spines.values():
            spine.set_color('#37474f')
            spine.set_linewidth(0.8)

        # Légende compacte
        legend = self.ax.legend(frameon=True, loc='upper left', bbox_to_anchor=(1.02, 1),
                                fontsize=10, framealpha=0.95)
        legend.get_frame().set_facecolor('#1c2530')
        legend.get_frame().set_edgecolor('#37474f')
        legend.get_frame().set_linewidth(1)

        self.ax.set_xticks(periods)
        self.ax.set_xlim(0.5, T + 0.5)

        # Ajustements
        self.fig.subplots_adjust(right=0.85)

        self.canvas.draw()


class ROApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation Agricole")
        self.setGeometry(80, 40, 1250, 800)
        self.T = 6
        self.graph_window = None
        self.current_results = None

        # Palette de couleurs bleutée
        self.colors = {
            'dark': '#0f1419',
            'darker': '#1c2530',
            'medium': '#2a3a4a',
            'light': '#374a5f',
            'surface': '#1e2a38',
            'surface_light': '#2a3a4a',
            'border': '#37474f',
            'text': '#e1f5fe',
            'text_light': '#b0bec5',
            'text_muted': '#78909c',
            'text_dark': '#2a3a4a',
            'primary': '#4fc3f7',
            'primary_dark': '#29b6f6',
            'secondary': '#81d4fa',
            'accent': '#bbdefb',
            'success': '#4fc3f7'
        }

        # Style général minimal
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['dark']};
                font-family: 'Segoe UI', 'Arial', sans-serif;
                color: {self.colors['text_light']};
            }}
            QGroupBox {{
                border: 0px;
                margin-top: 5px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        # Header minimal
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['darker']};
                border-radius: 6px;
                border: 1px solid {self.colors['border']};
                border-left: 4px solid {self.colors['primary']};
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("OPTIMISATION MULTI-PÉRIODE")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['primary']};
                padding: 2px;
            }}
        """)
        header_layout.addWidget(title_label)

        main_layout.addWidget(header_frame)

        # -------------------------------
        # SECTION PARAMÈTRES
        # -------------------------------
        section_title = QLabel("Configuration")
        section_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        section_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['primary']};
                margin-top: 10px;
                margin-bottom: 5px;
            }}
        """)
        main_layout.addWidget(section_title)

        params_frame = QFrame()
        params_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['darker']};
                border-radius: 6px;
                border: 1px solid {self.colors['border']};
            }}
        """)
        params_layout = QVBoxLayout(params_frame)
        params_layout.setContentsMargins(15, 15, 15, 15)

        # Ligne des paramètres
        input_row = QHBoxLayout()
        input_row.setSpacing(25)

        def create_input_field(label, default, width=140):
            container = QVBoxLayout()
            container.setSpacing(4)

            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet(f"color: {self.colors['text_light']};")

            input_field = QLineEdit(default)
            input_field.setMinimumWidth(width)
            input_field.setMaximumWidth(width)
            input_field.setFont(QFont("Segoe UI", 10))
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    padding: 8px;
                    border: 1px solid {self.colors['border']};
                    border-radius: 4px;
                    background-color: {self.colors['surface']};
                    color: {self.colors['text']};
                    selection-background-color: {self.colors['primary']};
                }}
                QLineEdit:focus {{
                    border-color: {self.colors['primary']};
                    border-width: 2px;
                }}
            """)

            container.addWidget(lbl)
            container.addWidget(input_field)
            return container, input_field

        # Champs de saisie
        s0_container, self.S0_input = create_input_field("Stock Initial", "")
        smax_container, self.Smax_input = create_input_field("Stock Max", "")
        r_container, self.r_input = create_input_field("Taux Actual.", "")
        period_container, self.period_input = create_input_field("Périodes", "6")

        input_row.addStretch()
        input_row.addLayout(s0_container)
        input_row.addLayout(smax_container)
        input_row.addLayout(r_container)
        input_row.addLayout(period_container)

        # Bouton appliquer
        self.apply_periods_btn = QPushButton("Mettre à jour")
        self.apply_periods_btn.setFont(QFont("Segoe UI", 9))
        self.apply_periods_btn.setFixedSize(120, 35)
        self.apply_periods_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['primary']};
                color: {self.colors['dark']};
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.colors['primary_dark']};
            }}
        """)
        self.apply_periods_btn.clicked.connect(self.update_periods)

        input_row.addWidget(self.apply_periods_btn)
        input_row.addStretch()

        params_layout.addLayout(input_row)
        main_layout.addWidget(params_frame)

        # -------------------------------
        # DONNÉES PAR PÉRIODE
        # -------------------------------
        data_title = QLabel("Données Périodiques")
        data_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        data_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['primary']};
                margin-top: 10px;
                margin-bottom: 5px;
            }}
        """)
        main_layout.addWidget(data_title)

        data_frame = QFrame()
        data_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['darker']};
                border-radius: 6px;
                border: 1px solid {self.colors['border']};
            }}
        """)
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(15, 15, 15, 15)

        # Légende minimaliste
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(15)

        indicators = [
            ("D", self.colors['primary']),
            ("Rmax", self.colors['secondary']),
            ("Tmax", "#81d4fa"),
            ("cR", "#bbdefb"),
            ("cA", "#4fc3f7"),
            ("cT", "#29b6f6"),
            ("cS", "#03a9f4")
        ]

        for symbol, color in indicators:
            indicator = QLabel("●")
            indicator.setStyleSheet(f"color: {color}; font-size: 8px;")
            label = QLabel(symbol)
            label.setFont(QFont("Segoe UI", 8))
            label.setStyleSheet(f"color: {self.colors['text_muted']}; margin-left: 2px;")

            item_layout = QHBoxLayout()
            item_layout.addWidget(indicator)
            item_layout.addWidget(label)
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        data_layout.addLayout(legend_layout)

        # Tableau de saisie
        self.table_widget = QTableWidget(self.T, 7)
        self.setup_table()
        data_layout.addWidget(self.table_widget)

        main_layout.addWidget(data_frame)

        # -------------------------------
        # BOUTONS PRINCIPAUX
        # -------------------------------
        button_row = QHBoxLayout()
        button_row.setSpacing(15)

        def create_main_button(text, primary=True):
            btn = QPushButton(text)
            btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
            btn.setFixedHeight(40)
            btn.setMinimumWidth(180)

            if primary:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors['primary']};
                        color: {self.colors['dark']};
                        border-radius: 4px;
                        border: none;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.colors['primary_dark']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors['medium']};
                        color: {self.colors['text']};
                        border-radius: 4px;
                        border: 1px solid {self.colors['border']};
                    }}
                    QPushButton:hover {{
                        background-color: {self.colors['light']};
                        border-color: {self.colors['primary']};
                    }}
                    QPushButton:disabled {{
                        background-color: {self.colors['border']};
                        color: {self.colors['text_muted']};
                    }}
                """)

            return btn

        self.calc_btn = create_main_button("Lancer le Calcul", True)
        self.calc_btn.clicked.connect(self.run_optimization)

        self.graph_btn = create_main_button("Afficher Graphique", False)
        self.graph_btn.clicked.connect(self.show_graph)
        self.graph_btn.setEnabled(False)

        self.reset_btn = create_main_button("Réinitialiser", False)
        self.reset_btn.clicked.connect(self.reset_inputs)

        button_row.addStretch()
        button_row.addWidget(self.calc_btn)
        button_row.addWidget(self.graph_btn)
        button_row.addWidget(self.reset_btn)
        button_row.addStretch()

        main_layout.addLayout(button_row)

        # -------------------------------
        # RÉSULTATS
        # -------------------------------
        results_title = QLabel("Résultats")
        results_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        results_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['primary']};
                margin-top: 15px;
                margin-bottom: 5px;
            }}
        """)
        main_layout.addWidget(results_title)

        results_frame = QFrame()
        results_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['darker']};
                border-radius: 6px;
                border: 1px solid {self.colors['border']};
            }}
        """)
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(15, 15, 15, 15)

        # Coût total
        cost_layout = QHBoxLayout()
        cost_label = QLabel("Coût Total:")
        cost_label.setFont(QFont("Segoe UI", 10))
        cost_label.setStyleSheet(f"color: {self.colors['text_light']};")

        self.result_label = QLabel("--")
        self.result_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.result_label.setStyleSheet(f"color: {self.colors['primary']};")

        cost_layout.addWidget(cost_label)
        cost_layout.addWidget(self.result_label)
        cost_layout.addStretch()

        results_layout.addLayout(cost_layout)

        # Tableau des résultats
        self.result_table = QTableWidget(self.T, 5)
        self.setup_result_table()
        results_layout.addWidget(self.result_table)

        main_layout.addWidget(results_frame)

        # Espace final
        main_layout.addStretch()

        # Initialisation
        self.initialize_empty_data()

    def setup_table(self):
        """Configurer le tableau de saisie"""
        headers = ["D", "Rmax", "Tmax", "cR", "cA", "cT", "cS"]

        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.horizontalHeader().setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.table_widget.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.colors['surface']};
                gridline-color: {self.colors['border']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                color: {self.colors['text']};
            }}
            QHeaderView::section {{
                background-color: {self.colors['medium']};
                color: {self.colors['text']};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.colors['primary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.colors['border']};
                color: {self.colors['text']};
            }}
        """)

        self.update_table_rows()
        self.table_widget.setAlternatingRowColors(True)

        palette = self.table_widget.palette()
        palette.setColor(QPalette.AlternateBase, QColor(self.colors['medium']))
        palette.setColor(QPalette.Text, QColor(self.colors['text']))
        self.table_widget.setPalette(palette)

    def setup_result_table(self):
        """Configurer le tableau des résultats"""
        result_headers = ["Prod", "Achat", "Trans", "Stock", "Actif"]

        self.result_table.setHorizontalHeaderLabels(result_headers)
        self.result_table.horizontalHeader().setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.result_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.colors['surface']};
                gridline-color: {self.colors['border']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                color: {self.colors['text']};
            }}
            QHeaderView::section {{
                background-color: {self.colors['medium']};
                color: {self.colors['text']};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.colors['secondary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                text-align: center;
                border-bottom: 1px solid {self.colors['border']};
                color: {self.colors['text']};
            }}
        """)

        self.update_result_table_rows()
        self.result_table.setAlternatingRowColors(True)

        palette = self.result_table.palette()
        palette.setColor(QPalette.AlternateBase, QColor(self.colors['medium']))
        palette.setColor(QPalette.Text, QColor(self.colors['text']))
        self.result_table.setPalette(palette)

    def update_periods(self):
        """Mettre à jour le nombre de périodes"""
        try:
            new_T = int(self.period_input.text())
            if new_T <= 0:
                self.show_message("Erreur", "Nombre de périodes invalide", "error")
                return

            old_data = []
            for row in range(min(self.T, new_T)):
                row_data = []
                for col in range(7):
                    item = self.table_widget.item(row, col)
                    row_data.append(item.text() if item and item.text() else "")
                old_data.append(row_data)

            self.T = new_T
            self.table_widget.setRowCount(self.T)
            self.result_table.setRowCount(self.T)

            self.update_table_rows()
            self.update_result_table_rows()

            for row in range(min(len(old_data), self.T)):
                for col in range(7):
                    if row < len(old_data) and col < len(old_data[row]):
                        item = QTableWidgetItem(old_data[row][col])
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFont(QFont("Segoe UI", 10))
                        item.setForeground(QColor(self.colors['text']))
                        self.table_widget.setItem(row, col, item)

            self.clear_results()
            self.show_message("Succès", f"Périodes: {self.T}", "success")

        except ValueError:
            self.show_message("Erreur", "Valeur invalide", "error")

    def show_message(self, title, message, type="info"):
        """Afficher un message"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setFont(QFont("Segoe UI", 9))

        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.colors['darker']};
            }}
            QLabel {{
                color: {self.colors['text']};
            }}
            QPushButton {{
                background-color: {self.colors['medium']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['primary']};
                color: {self.colors['dark']};
                border-color: {self.colors['primary']};
            }}
        """)

        if type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "success":
            msg.setIcon(QMessageBox.Information)
        else:
            msg.setIcon(QMessageBox.Warning)

        msg.exec_()

    def update_table_rows(self):
        """Mettre à jour les lignes du tableau de saisie"""
        self.table_widget.setVerticalHeaderLabels([f"{i + 1}" for i in range(self.T)])
        self.table_widget.verticalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self.colors['medium']};
                color: {self.colors['text_light']};
                padding: 10px;
                border: none;
                border-right: 1px solid {self.colors['border']};
            }}
        """)

    def update_result_table_rows(self):
        """Mettre à jour les lignes du tableau des résultats"""
        self.result_table.setVerticalHeaderLabels([f"{i + 1}" for i in range(self.T)])
        self.result_table.verticalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self.colors['medium']};
                color: {self.colors['text_light']};
                padding: 10px;
                border: none;
                border-right: 1px solid {self.colors['border']};
            }}
        """)

    def initialize_empty_data(self):
        """Initialiser avec des champs vides"""
        for row in range(self.T):
            for col in range(7):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 10))
                item.setForeground(QColor(self.colors['text']))
                self.table_widget.setItem(row, col, item)

    def clear_results(self):
        """Effacer les résultats"""
        self.result_label.setText("--")
        self.graph_btn.setEnabled(False)
        self.current_results = None

        for row in range(self.T):
            for col in range(5):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 10))
                item.setForeground(QColor(self.colors['text']))
                self.result_table.setItem(row, col, item)

    def reset_inputs(self):
        """Réinitialiser tous les champs"""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Réinitialiser toutes les données ?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.No:
            return

        self.S0_input.setText("")
        self.Smax_input.setText("")
        self.r_input.setText("")
        self.period_input.setText("6")

        self.T = 6
        self.table_widget.setRowCount(self.T)
        self.result_table.setRowCount(self.T)
        self.update_table_rows()
        self.update_result_table_rows()

        for row in range(self.T):
            for col in range(7):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 10))
                item.setForeground(QColor(self.colors['text']))
                self.table_widget.setItem(row, col, item)

        self.clear_results()

        if self.graph_window and self.graph_window.isVisible():
            self.graph_window.close()

        self.initialize_empty_data()
        self.show_message("Info", "Données réinitialisées", "success")

    def run_optimization(self):
        """Exécuter l'optimisation"""
        try:
            S0 = float(self.S0_input.text())
            Smax = float(self.Smax_input.text())
            r = float(self.r_input.text())
            T = self.T

            if S0 > Smax:
                self.show_message("Erreur", "Stock initial > Capacité max", "error")
                return

        except ValueError:
            self.show_message("Erreur", "Paramètres globaux invalides", "error")
            return

        D, Rmax, Tmax, cR, cA, cT, cS = [], [], [], [], [], [], []
        try:
            for t in range(T):
                D_val = float(self.table_widget.item(t, 0).text())
                Rmax_val = float(self.table_widget.item(t, 1).text())
                Tmax_val = float(self.table_widget.item(t, 2).text())
                cR_val = float(self.table_widget.item(t, 3).text())
                cA_val = float(self.table_widget.item(t, 4).text())
                cT_val = float(self.table_widget.item(t, 5).text())
                cS_val = float(self.table_widget.item(t, 6).text())

                if Tmax_val > Rmax_val:
                    reply = QMessageBox.question(self, "Avertissement",
                                                 f"Période {t + 1}: Transf. > Prod.\nContinuer ?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        return

                D.append(D_val)
                Rmax.append(Rmax_val)
                Tmax.append(Tmax_val)
                cR.append(cR_val)
                cA.append(cA_val)
                cT.append(cT_val)
                cS.append(cS_val)
        except Exception:
            self.show_message("Erreur", "Données de période invalides", "error")
            return

        try:
            results = run_plm_model(T, D, Rmax, Tmax, cR, cA, cT, cS, S0=S0, Smax=Smax, r=r)

            if results is None or results.get('obj_val') is None:
                self.show_message("Erreur", "Pas de solution optimale", "error")
                return

        except Exception as e:
            self.show_message("Erreur", f"Erreur: {str(e)[:50]}", "error")
            return

        self.current_results = results
        self.graph_btn.setEnabled(True)
        self.display_results(results, T, S0)
        self.show_message("Succès", "Calcul terminé", "success")

    def display_results(self, results, T, S0):
        """Afficher les résultats"""
        if results['obj_val'] is None:
            self.result_label.setText("--")
        else:
            self.result_label.setText(f"{results['obj_val']:,.0f}")

        self.result_table.setRowCount(T)
        for t in range(T):
            data = [
                f"{results['R'][t]:.0f}",
                f"{results['A'][t]:.0f}",
                f"{results['T'][t]:.0f}",
                f"{results['S'][t]:.0f}",
                f"{results['U'][t]}"
            ]

            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 10))

                # Assurer la lisibilité sur les lignes alternées
                if t % 2 == 0:  # Ligne paire
                    item.setForeground(QColor(self.colors['text']))
                else:  # Ligne impaire
                    item.setForeground(QColor(self.colors['text']))

                if col == 4:
                    if results['U'][t] == 1:
                        item.setForeground(QColor(self.colors['primary']))
                        item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    else:
                        item.setForeground(QColor(self.colors['text_muted']))

                self.result_table.setItem(t, col, item)

    def show_graph(self):
        """Afficher le graphique"""
        if not self.current_results:
            self.show_message("Info", "Aucun résultat à afficher", "warning")
            return

        if self.graph_window is None or not self.graph_window.isVisible():
            self.graph_window = GraphWindow(self)

        self.graph_window.update_graph(self.current_results, self.T)
        self.graph_window.show()
        self.graph_window.raise_()


