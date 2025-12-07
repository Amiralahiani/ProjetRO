import sys
from PyQt5 import QtWidgets, uic
from gurobipy import Model, GRB

# ----------------------------
# Fonction Gurobi
# ----------------------------
def run_crew_optimizer(flights, pairings, cost):
    m = Model("crew_pairing_dynamic")
    y = {p: m.addVar(vtype=GRB.BINARY, name=f"y_{p}") for p in pairings}
    m.update()

    # Minimiser le coût total
    m.setObjective(sum(cost[p]*y[p] for p in pairings), GRB.MINIMIZE)

    # Contraintes : chaque vol au moins une fois
    for f in flights:
        expr = sum(y[p] for p in pairings if f in pairings[p])
        m.addConstr(expr >= 1, name=f"cover_{f}")

    m.optimize()

    chosen = {}
    if m.status == GRB.Status.OPTIMAL:
        for p in pairings:
            if y[p].x > 0.5:
                chosen[p] = pairings[p]
    return chosen

# ----------------------------
# Classe principale
# ----------------------------
class CrewApp(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("crew_app.ui", self)

        # Rendre resultTable non éditable
        self.resultTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Connexion des boutons
        self.optimizeButton.clicked.connect(self.optimize)
        self.addFlightButton.clicked.connect(lambda: self.flightsTable.insertRow(self.flightsTable.rowCount()))
        self.addPairingButton.clicked.connect(lambda: self.pairingsTable.insertRow(self.pairingsTable.rowCount()))
        self.removeFlightButton.clicked.connect(lambda: self.remove_selected_row(self.flightsTable))
        self.removePairingButton.clicked.connect(lambda: self.remove_selected_row(self.pairingsTable))

    # Supprimer ligne sélectionnée
    def remove_selected_row(self, table):
        selected = set(item.row() for item in table.selectedItems())
        for row in sorted(selected, reverse=True):
            table.removeRow(row)

    # Optimisation
    def optimize(self):
        # Récupérer vols
        flights = [self.flightsTable.item(row,0).text().strip()
                   for row in range(self.flightsTable.rowCount())
                   if self.flightsTable.item(row,0) and self.flightsTable.item(row,0).text().strip()]

        # Récupérer pairings
        pairings = {}
        for row in range(self.pairingsTable.rowCount()):
            name_item = self.pairingsTable.item(row,0)
            vols_item = self.pairingsTable.item(row,1)
            if name_item and vols_item and name_item.text().strip() and vols_item.text().strip():
                vols = [v.strip() for v in vols_item.text().split(",")]
                pairings[name_item.text().strip()] = vols

        if not flights or not pairings:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Veuillez saisir au moins un vol et un pairing.")
            return

        # Coût = 1 par pairing
        cost = {p: 1 for p in pairings}

        # Optimiser
        chosen = run_crew_optimizer(flights, pairings, cost)

        # Afficher résultat
        self.resultTable.clear()
        self.resultTable.setRowCount(len(chosen))
        self.resultTable.setColumnCount(2)
        self.resultTable.setHorizontalHeaderLabels(["Pairing choisi", "Vols couverts"])
        for row, (p, vols) in enumerate(chosen.items()):
            self.resultTable.setItem(row,0,QtWidgets.QTableWidgetItem(p))
            self.resultTable.setItem(row,1,QtWidgets.QTableWidgetItem(", ".join(vols)))

# ----------------------------
# Lancer l'application
# ----------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = CrewApp()
    window.show()
    sys.exit(app.exec_())
