import tkinter as tk
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tkinter import ttk
from Src.DataLoader import DataLoader
from Src.Optimizer import optimize_transfers
from Src.Visualizer import visualize_graph
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class BankApp:
    def __init__(self, master):
        self.master = master
        master.title("Optimisation Transferts Multi-Devises")
        self.dataloader = DataLoader("Data")
        self.banks, self.balances, self.required = self.dataloader.load_banks_data()
        self.rates = self.dataloader.load_rates()

        # --- Frames ---
        self.frame_welcome = tk.Frame(master)
        self.frame_data = tk.Frame(master)

        for frame in (self.frame_welcome, self.frame_data):
            frame.grid(row=0, column=0, sticky="nsew")

        self.build_welcome_frame()
        self.build_data_frame()

        self.show_frame(self.frame_welcome)

    def show_frame(self, frame):
        frame.tkraise()

    # --- Accueil ---
    def build_welcome_frame(self):
        tk.Label(self.frame_welcome, text="Bienvenue dans l'application de transferts multi-devises",
                 font=("Helvetica", 16), fg="red").pack(pady=20)

        description_text = (
        "Dans ce réseau, chaque banque possède des soldes en différentes devises et doit couvrir ses besoins financiers. "
        "Certaines banques ont un excédent, tandis que d'autres disposent de moins que ce dont elles ont besoin.\n\n"
        "L'objectif de cette application est de calculer les transferts et conversions optimaux pour que chaque banque atteigne ses besoins, "
        "tout en minimisant le coût total et en respectant les contraintes:\n\n"
        "- Chaque banque ne peut pas envoyer plus que son solde disponible dans chaque devise.\n"
        "- Chaque banque doit recevoir au moins le montant dont elle a besoin dans chaque devise.\n"
        "- Pour chaque transaction entre banques, une banque peut envoyer un flux et en recevoir un seul, certaines transactions sont activées ou non selon les besoins.\n\n"
        "Ce problème se modélise à l'aide de Programmation Linéaire (PL) pour les montants à transférer et de Programmation Linéaire en Nombres Entiers (PLNE) "
        "pour les choix des transactions, garantissant un équilibre optimal du réseau bancaire.\n\n"
        "Cette combinaison permet de générer un plan de transferts optimal, assurant que toutes les banques déficitaires reçoivent exactement ce dont elles ont besoin, "
        "en minimisant les coûts et en garantissant un réseau bancaire équilibré et réaliste."
    )

        # Utiliser un Label avec wraplength pour que le texte se mette à la ligne
        tk.Label(self.frame_welcome, text=description_text, justify="left", wraplength=750).pack(padx=20, pady=10)

        tk.Button(self.frame_welcome, text="Continuer", command=lambda: self.show_frame(self.frame_data)).pack(pady=20)

    # --- Interface du tableau ---
    def build_data_frame(self):
        tk.Label(self.frame_data, text="Saisie des Soldes et Besoins par Banque",
             font=("Helvetica", 14), fg="red").pack(pady=10)

    # Texte explicatif au-dessus du tableau
        description_text = (
        "Ce tableau illustre les soldes et besoins de chaque banque pour chaque devise.\n"
        "*) Solde (Balance) : montant actuel disponible dans la banque.\n"
        "*) Besoin (Required) : montant minimum nécessaire pour couvrir les opérations.\n\n"
        "Ces informations permettront à l'application de calculer les transferts optimaux entre banques.\n\n"
        "Chaque modification impactera le résultat final de l'optimisation et la représentation graphique des flux financiers.\n"
        "Le problème ici c'est que la Banque BNP possède un solde insuffisant en USD pour couvrir son besoin, "
        "nécessitant des transferts depuis d'autres banques.\n\n"
        "Cliquez ensuite sur 'Optimiser' pour passer à l’optimisation et visualiser les transferts calculés."
        )

        tk.Label(self.frame_data, text=description_text, justify="left", wraplength=750).pack(padx=20, pady=5)

        # --- Création du tableau ---
        self.tree = ttk.Treeview(self.frame_data, columns=("Bank", "Currency", "Balance", "Required"), show="headings")
        for col, text in [("Bank","Banque"), ("Currency","Devise"), ("Balance","Solde"), ("Required","Besoin")]:
            self.tree.heading(col, text=text)
        self.tree.pack(padx=10, pady=10, fill="x")

        # Charger les données dans le tableau
        self.load_table()

        # Bouton pour lancer l'optimisation
        tk.Button(self.frame_data, text="Optimiser", command=self.run_optimization).pack(pady=10)

    def load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for (bank, cur), bal in self.balances.items():
            req = self.required[(bank, cur)]
            self.tree.insert("", "end", values=(bank, cur, bal, req))

    def run_optimization(self):
        # Mettre à jour les données depuis le tableau
        for row in self.tree.get_children():
            bank, currency, balance, req = self.tree.item(row)['values']
            self.balances[(bank, currency)] = float(balance)
            self.required[(bank, currency)] = float(req)

        transfers, conversions = optimize_transfers(list(self.banks), self.balances, self.required, self.rates, interet=0.03)


        # Fenêtre d'explications
        explain_window = tk.Toplevel(self.master)
        explain_window.title("Explications des transferts")
        tk.Label(explain_window, text="Explications étape par étape", font=("Helvetica", 14), fg="red").pack(pady=5)
        explanation_text = tk.Text(explain_window, height=20, width=80)
        explanation_text.pack(padx=10, pady=10, fill="both", expand=True)

        explanation_text.insert(tk.END, "Transferts :\n")
        for (src,dst,cur), amt in transfers.items():
            explanation_text.insert(tk.END, f"- {src} transfère {amt:,.2f} {cur} à {dst}\n")

        explanation_text.insert(tk.END, "\nConversions :\n")
        for (dst, src, from_cur, to_cur), amt in conversions.items():
            explanation_text.insert(tk.END,
                f"- {dst} reçoit {to_cur} et paie {amt:,.2f} {from_cur} à {src}\n")
        explanation_text.config(state="disabled")
        
        # --- Graphe ---
        graph_window = tk.Toplevel(self.master)
        graph_window.title("Graphe des transferts optimisés")
        fig, ax = plt.subplots(figsize=(10,7))
        visualize_graph(transfers, conversions, ax)
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(padx=10, pady=10)
        canvas.draw()


# --- Lancer l'application ---
def run_app():
        root = tk.Tk()
        root.geometry("800x600")  # Taille de la fenêtre principale
        app = BankApp(root)
        root.mainloop()


if __name__ == "__main__":
        run_app()

