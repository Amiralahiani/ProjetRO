# models/diagnostics.py

from typing import Any


def diagnose_network(network: Any) -> str:
    """
    Produit un diagnostic textuel du réseau avant résolution.

    On suppose que `network` a les attributs :
      - nodes          : iterable des noeuds
      - arcs           : liste de dicts avec au moins "u", "v", "capacity", "min_flow"
      - demands        : dict {node: demand}
    """
    lines = []
    lines.append("=== DIAGNOSTIC DU RÉSEAU ===")

    # Nombre de noeuds / arcs
    nb_nodes = len(list(network.nodes))
    nb_arcs = len(list(network.arcs))
    lines.append(f"Nombre de noeuds : {nb_nodes}")
    lines.append(f"Nombre d'arcs   : {nb_arcs}")

    # Bilan des demandes
    total_demand = 0.0
    total_pos = 0.0
    total_neg = 0.0
    for n in network.nodes:
        d = network.demands[n]
        total_demand += d
        if d > 0:
            total_pos += d
        elif d < 0:
            total_neg += d

    lines.append(f"Somme des demandes (Σ d_i) : {total_demand:.3f}")
    lines.append(f"  > Part positive (consommation) : {total_pos:.3f}")
    lines.append(f"  > Part négative (production max) : {total_neg:.3f}")

    # Check arcs douteux
    bad_capacity = []
    bad_minflow = []
    for arc in network.arcs:
        u, v = arc["u"], arc["v"]
        C = arc["capacity"]
        mf = arc["min_flow"]
        thr = arc["threshold"]

        if C < 0:
            bad_capacity.append(f"{u}->{v} (capacity={C})")
        if mf > C:
            bad_minflow.append(f"{u}->{v} (min_flow={mf} > capacity={C})")
        if thr > C:
            # Pas bloquant, mais on le signale
            lines.append(f"⚠ Seuil > capacité sur arc {u}->{v} (threshold={thr}, capacity={C})")

    if bad_capacity:
        lines.append("⚠ Capacité négative détectée sur les arcs :")
        for s in bad_capacity:
            lines.append(f"  - {s}")

    if bad_minflow:
        lines.append("⚠ Min_flow > capacité sur les arcs :")
        for s in bad_minflow:
            lines.append(f"  - {s}")

    if abs(total_demand) > 1e-6:
        lines.append("⚠ Attention : la somme des demandes n'est pas nulle.")
        lines.append("  Cela peut être normal si tu autorises des slacks,")
        lines.append("  mais en théorie un réseau parfaitement équilibré aurait Σ d_i = 0.")

    lines.append("=== FIN DIAGNOSTIC ===")
    return "\n".join(lines)


def explain_infeasibility(error_message: str) -> str:
    """
    Essaie de fournir une explication lisible à partir d'un message d'erreur
    (par exemple, erreur Gurobi).

    Pour l'instant, on se contente de renvoyer un texte générique annoté.
    Tu peux enrichir cette fonction (analyse du status, etc.) si besoin.
    """
    lines = []
    lines.append("=== ANALYSE D'INFEASIBILITÉ / ERREUR SOLVEUR ===")
    lines.append("Message brut du solveur / Python :")
    lines.append(error_message)
    lines.append("")
    lines.append("Causes fréquentes possibles :")
    lines.append("  - min_flow > capacity sur certains arcs ;")
    lines.append("  - demandes impossibles à satisfaire même avec slack ;")
    lines.append("  - réseau déconnecté (certaines demandes n'ont aucun chemin depuis les sources) ;")
    lines.append("  - erreur de licence Gurobi ou de configuration ;")
    lines.append("")
    lines.append("Vérifie aussi le diagnostic du réseau (noeuds, arcs, bilans de demande).")
    lines.append("=== FIN ANALYSE ===")

    return "\n".join(lines)
