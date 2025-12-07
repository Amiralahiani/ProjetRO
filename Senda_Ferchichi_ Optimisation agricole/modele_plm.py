# modele_plm_corrige.py
from gurobipy import Model, GRB

def run_plm_model(T, D, Rmax, Tmax, cR, cA, cT, cS, S0=10, Smax=60, r=0.02):
    """
    Modèle PLM multi-période corrigé
    Variables :
      - R[t] : quantité produite (disponible pour transformation)
      - T[t] : quantité transformée
      - A[t] : achat produit fini
      - S[t] : stock en fin de période
      - U[t] : binaire production activée
    """
    delta = [1.0 / ((1 + r) ** t) for t in range(T)]

    m = Model("PLM_multi_periode")

    # VARIABLES (créées variable par variable avec bornes individuelles)
    R, Tvar, A, S, U = {}, {}, {}, {}, {}
    for t in range(T):
        R[t] = m.addVar(lb=0.0, ub=Rmax[t], vtype=GRB.CONTINUOUS, name=f"R_{t}")
        Tvar[t] = m.addVar(lb=0.0, ub=Tmax[t], vtype=GRB.CONTINUOUS, name=f"T_{t}")
        A[t] = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"A_{t}")
        S[t] = m.addVar(lb=0.0, ub=Smax, vtype=GRB.CONTINUOUS, name=f"S_{t}")
        U[t] = m.addVar(vtype=GRB.BINARY, name=f"U_{t}")

    # Lien production binaire
    for t in range(T):
        m.addConstr(R[t] <= Rmax[t] * U[t], name=f"prod_active_{t}")

    # Contraintes transformation
    for t in range(T):
        m.addConstr(Tvar[t] <= R[t], name=f"transf_le_prod_{t}")
        m.addConstr(Tvar[t] <= Tmax[t], name=f"transf_cap_{t}")

    #  Contrainte Satisfaction de la demande
    for t in range(T):
        m.addConstr(Tvar[t] + A[t] >= D[t], name=f"demand_{t}")

    # Contraintes de stock
    for t in range(T):
        if t == 0:
            m.addConstr(S[t] == S0 + Tvar[t] + A[t] - D[t], name=f"stock_balance_{t}")
        else:
            m.addConstr(S[t] == S[t-1] + Tvar[t] + A[t] - D[t], name=f"stock_balance_{t}")

    # Fonction objectif : coûts actualisés
    obj = sum(delta[t] * (cR[t] * R[t] + cA[t] * A[t] + cT[t] * Tvar[t] + cS[t] * S[t])
              for t in range(T))
    m.setObjective(obj, GRB.MINIMIZE)

    # Résolution
    m.optimize()

    # Récupération sécurisée des résultats
    if m.status == GRB.OPTIMAL or m.status == GRB.INTERRUPTED:
        results = {
            "R": [R[t].X for t in range(T)],
            "A": [A[t].X for t in range(T)],
            "T": [Tvar[t].X for t in range(T)],
            "S": [S[t].X for t in range(T)],
            "U": [int(U[t].X) for t in range(T)],
            "obj_val": m.objVal
        }
    else:
        results = {
            "R": [0.0]*T, "A": [0.0]*T, "T": [0.0]*T, "S": [0.0]*T, "U": [0]*T, "obj_val": None
        }
    return results
