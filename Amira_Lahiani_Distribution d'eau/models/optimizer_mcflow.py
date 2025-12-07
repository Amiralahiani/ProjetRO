
from gurobipy import Model, GRB
from models.diagnostics import diagnose_network, explain_infeasibility


# ============================================================================
#  ROUTINE PRINCIPALE — Proportionnel puis fallback Absolu
# ============================================================================
def solve_min_cost_flow(network):
    pre_diag = diagnose_network(network)

    try:
        return solve_with_proportional_slack(network, pre_diag)
    except Exception as e1:
        proportional_error = str(e1)

    try:
        return solve_with_absolute_slack(network, pre_diag)
    except Exception as e2:
        absolute_error = str(e2)

    msg = (
        pre_diag
        + "\n\n=== ECHEC DES DEUX MODES ===\n"
        + "\n--- MODE PROPORTIONNEL ---\n" + proportional_error
        + "\n--- MODE ABSOLU ---\n" + absolute_error
    )
    raise Exception(msg)



# ============================================================================
#  MODE 1 — Équité proportionnelle + Sélection binaire des tuyaux
# ============================================================================
def solve_with_proportional_slack(network, pre_diag):
    m = Model("WaterFlow_Binary_Proportional")
    m.Params.OutputFlag = 0

    # Importance des critères
    alpha = 1.0    # coût de transport
    beta  = 10.0   # surcharge (80% capacité)
    gamma = 500.0  # pénurie globale
    k_act = 3.0    # coût d'activer un tuyau 

    x1, x2, x, overload = {}, {}, {}, {}
    slack = {}
    active = {}  #  VARIABLE BINAIRE  (ouvre/ferme un tuyau)

    r = m.addVar(lb=0, ub=1, name="ratio")

    # === Activation tuyaux
    for arc in network.arcs:
        u, v = arc["u"], arc["v"]
        active[(u,v)] = m.addVar(vtype=GRB.BINARY, name=f"open_{u}_{v}")

    # === Flux classique
    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        C = arc["capacity"]
        T = min(arc["threshold"], C)

        x1[(u,v)] = m.addVar(lb=0, ub=T, name=f"x1_{u}_{v}")
        x2[(u,v)] = m.addVar(lb=0, ub=max(C-T,0), name=f"x2_{u}_{v}")
        x[(u,v)]  = m.addVar(lb=0, ub=C, name=f"x_{u}_{v}")
        overload[(u,v)] = m.addVar(lb=0, name=f"over_{u}_{v}")

    # Slack tous noeuds
    for n in network.nodes:
        slack[n] = m.addVar(lb=0, name=f"slack_{n}")

    m.update()

    # === Lien flux
    for (u,v) in x:
        m.addConstr(x[(u,v)] == x1[(u,v)] + x2[(u,v)])

    # === Couplage activ/binaire → si y=0 → x=0
    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        C = arc["capacity"]
        m.addConstr(x[(u,v)] <= C * active[(u,v)])

    # === Min Flow & surcharge
    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        C = arc["capacity"]
        m.addConstr(x[(u,v)] >= arc["min_flow"])
        m.addConstr(overload[(u,v)] >= x[(u,v)] - 0.8*C)

    # === Conservation flux
    for n in network.nodes:
        incoming = []
        outgoing = []
        demand = network.demands[n]

        for arc in network.arcs:
            u,v = arc["u"], arc["v"]
            loss = arc["loss_rate"]
            if v == n: incoming.append((u,v,1-loss))
            if u == n: outgoing.append((u,v))

        if demand > 0:   # CONSOMMATEUR
            m.addConstr(sum(k*x[(u,v)] for (u,v,k) in incoming)
                        - sum(x[(u,v)] for (u,v) in outgoing)
                        + slack[n] == demand)
            m.addConstr(slack[n] == (1-r)*demand)

        else:            # PRODUCTEUR
            m.addConstr(sum(k*x[(u,v)] for (u,v,k) in incoming)
                        - sum(x[(u,v)] for (u,v) in outgoing) >= demand)
            m.addConstr(slack[n] == 0)

    # === OBJECTIF  (coût + surcharge + pénurie + tuyaux activés)
    obj = 0
    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        obj += alpha*(arc["cost_low"]*x1[(u,v)] + arc["cost_high"]*x2[(u,v)])
        obj += beta*overload[(u,v)]
        obj += k_act*active[(u,v)]   #  coût ouverture tuyau

    obj += gamma*(1-r)

    m.setObjective(obj, GRB.MINIMIZE)
    m.optimize()

    flows  = {(u,v):x[(u,v)].X       for (u,v) in x}
    slacks = {n:slack[n].X          for n in slack}
    opens  = {(u,v):active[(u,v)].X for (u,v) in active}

    return flows, m.objVal, slacks, "Équité proportionnelle", r.X, opens



# ============================================================================
#  MODE 2 — Absolu (fallback)  + binaire aussi
# ============================================================================
def solve_with_absolute_slack(network, pre_diag):
    m = Model("WaterFlow_Binary_Absolute")
    m.Params.OutputFlag = 0

    alpha = 1.0
    beta  = 10.0
    gamma = 1000.0
    k_act = 3.0

    x1,x2,x,overload={}, {}, {}, {}
    slack={}
    active={}     #  binaire
    s_max = m.addVar(lb=0,name="s_max")


    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        active[(u,v)] = m.addVar(vtype=GRB.BINARY,name=f"open_{u}_{v}")

    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        C = arc["capacity"]
        T = min(arc["threshold"],C)

        x1[(u,v)] = m.addVar(lb=0,ub=T)
        x2[(u,v)] = m.addVar(lb=0,ub=max(C-T,0))
        x[(u,v)]  = m.addVar(lb=0,ub=C)
        overload[(u,v)] = m.addVar(lb=0)

    for n in network.nodes:
        slack[n] = m.addVar(lb=0)

    m.update()

    for (u,v) in x:
        m.addConstr(x[(u,v)] == x1[(u,v)] + x2[(u,v)])

    for arc in network.arcs:
        u,v = arc["u"], arc["v"]
        C = arc["capacity"]
        m.addConstr(x[(u,v)] <= C*active[(u,v)]) #  binaire

        m.addConstr(x[(u,v)] >= arc["min_flow"])
        m.addConstr(overload[(u,v)] >= x[(u,v)]-0.8*C)

    # === Conservation ===
    for n in network.nodes:
        incoming, outgoing = [], []
        demand = network.demands[n]

        for arc in network.arcs:
            u,v = arc["u"], arc["v"]
            loss = arc["loss_rate"]
            if v==n: incoming.append((u,v,1-loss))
            if u==n: outgoing.append((u,v))

        if demand>0:
            m.addConstr(sum(k*x[(u,v)] for (u,v,k) in incoming)
                        -sum(x[(u,v)] for (u,v) in outgoing)
                        +slack[n]==demand)
            m.addConstr(slack[n] <= s_max)

        else:
            m.addConstr(sum(k*x[(u,v)] for (u,v,k) in incoming)
                        -sum(x[(u,v)] for (u,v) in outgoing)>=demand)
            m.addConstr(slack[n]==0)


    # === Objectif
    obj=0
    for arc in network.arcs:
        u,v=arc["u"],arc["v"]
        obj+=alpha*(arc["cost_low"]*x1[(u,v)] + arc["cost_high"]*x2[(u,v)])
        obj+=beta*overload[(u,v)]
        obj+=k_act*active[(u,v)]  # coût d’activer un arc

    obj+=gamma*s_max

    m.setObjective(obj,GRB.MINIMIZE)
    m.optimize()

    flows={(u,v):x[(u,v)].X for (u,v) in x}
    slacks={n:slack[n].X for n in slack}
    opens={(u,v):active[(u,v)].X for (u,v) in active}

    return flows, m.objVal, slacks, "Équité absolue", None, opens
