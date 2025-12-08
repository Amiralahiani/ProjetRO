#!/usr/bin/env python3
"""
Point d'entrée principal de l'application d'optimisation agricole
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Import de l'interface principale
from ro_ihm import ROApp


def main():
    """
    Fonction principale lançant l'application
    """
    # Initialisation de l'application Qt
    app = QApplication(sys.argv)

    # Configuration de la police
    font = QFont("Segoe UI", 9)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # Création et affichage de la fenêtre principale
    window = ROApp()
    window.show()

    # Exécution de la boucle d'événements
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()