
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

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
