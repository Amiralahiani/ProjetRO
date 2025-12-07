import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import sys
from PyQt5.QtWidgets import QApplication
from projet_ro.gui.main_window import MainWindow

def main():
    """
    Point d'entrée de l'application.
    Initialise l'application Qt et affiche la fenêtre principale.
    """
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
