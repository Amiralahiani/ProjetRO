# models/network_utils.py

class NetworkData:
    def __init__(self):
        self.nodes = []          # Liste des noms
        self.demands = {}        # {node: demand}
        self.arcs = []           # liste de dictionnaires

    # ----------------------------------------------------------------------
    def load(self, nodes_dict, arcs_list):
        """Charge le réseau depuis l'éditeur."""
        self.nodes = list(nodes_dict.keys())
        self.demands = dict(nodes_dict)
        self.arcs = list(arcs_list)

    def get_arc(self, u, v):
        """
        Retourne l'arc u→v avec sa capacité, seuil, pertes, coûts etc.
        Si aucun arc trouvé → None
        """
        for arc in self.arcs:
            if arc["u"] == u and arc["v"] == v:
                return arc
        return None

    # ----------------------------------------------------------------------
    def validate(self):
        """
        Vérifie que le réseau est *simplement* valide :
        - pas de nom vide
        - toutes les demandes sont numériques
        - les arcs ont tous les champs nécessaires
        - les noeuds cités dans arcs existent vraiment
        """

        # ----------------------------
        # 1. Vérification des noeuds
        # ----------------------------
        if len(self.nodes) == 0:
            print("❌ Aucun nœud dans le réseau.")
            return False

        for n in self.nodes:
            if n is None or n.strip() == "":
                print("❌ Un nœud a un nom vide.")
                return False
            if n not in self.demands:
                print(f"❌ Demande manquante pour le nœud {n}.")
                return False
            try:
                float(self.demands[n])
            except:
                print(f"❌ Demande invalide pour {n}.")
                return False

        # ----------------------------
        # 2. Vérification des arcs
        # ----------------------------
        for arc in self.arcs:
            expected = [
                "u", "v", "capacity", "min_flow",
                "cost_low", "cost_high", "threshold", "loss_rate"
            ]
            for key in expected:
                if key not in arc:
                    print(f"❌ Arc incomplet : champ '{key}' manquant.")
                    return False

            # arc nodes must exist
            if arc["u"] not in self.nodes:
                print(f"❌ Arc invalide : u '{arc['u']}' n'existe pas.")
                return False
            if arc["v"] not in self.nodes:
                print(f"❌ Arc invalide : v '{arc['v']}' n'existe pas.")
                return False

            # numeric fields
            try:
                float(arc["capacity"])
                float(arc["min_flow"])
                float(arc["cost_low"])
                float(arc["cost_high"])
                float(arc["threshold"])
                float(arc["loss_rate"])
            except:
                print(f"❌ Arc {arc['u']} → {arc['v']} contient une valeur non numérique.")
                return False

        # 🎉 Si aucune erreur → réseau OK
        return True
