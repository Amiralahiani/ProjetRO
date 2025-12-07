import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def visualize_graph(transfers, conversions, ax):
    """
    Visualise les transferts et conversions entre banques dans un graphe.
    
    transfers : dict {(src,dst,currency): montant}
    conversions : dict {(b_src,b_dst,from_cur,to_cur): montant}
    ax : matplotlib.axes.Axes pour dessiner le graphe
    """

    G = nx.MultiDiGraph()

    # --- Ajouter les nœuds (banques) ---
    banks_set = set()
    for (src, dst, cur) in transfers.keys():
        banks_set.add(src)
        banks_set.add(dst)
    for (b_dst, b_src, from_cur, to_cur) in conversions.keys():
        banks_set.add(b_dst)
        banks_set.add(b_src)

    for b in banks_set:
        G.add_node(b)

    # --- Générer les positions ---
    pos = nx.spring_layout(G, seed=42)

    # --- Dessiner les nœuds ---
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue', node_size=2000)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10)

    # --- Dessiner les arcs des transferts ---
    rad_values = [0.3, -0.3]  # arcs parallèles
    rad_index = 0
    for (src, dst, cur), amount in transfers.items():
        rad = rad_values[rad_index % len(rad_values)]
        ax.annotate(
            "",
            xy=pos[dst],
            xytext=pos[src],
            arrowprops=dict(
                arrowstyle='-|>',
                color='blue',
                lw=2,
                connectionstyle=f"arc3,rad={rad}"
            )
        )
        # Label au milieu de l'arc
        x = (pos[src][0] + pos[dst][0]) / 2
        y = (pos[src][1] + pos[dst][1]) / 2
        ax.text(x, y, f"{amount:,.0f} {cur}", color="blue", fontsize=9, ha="center", va="center")
        rad_index += 1

    # --- Dessiner les arcs des conversions ---
    conv_rad_values = [0.2, -0.2]  # arcs parallèles pour conversions
    conv_index = 0
    for (b_dst, b_src, from_cur, to_cur), amount in conversions.items():
        rad = conv_rad_values[conv_index % len(conv_rad_values)]
        ax.annotate(
            "",
            xy=pos[b_src],       # banque qui reçoit paiement (a distribué)
            xytext=pos[b_dst],   # banque bénéficiaire qui a converti
            arrowprops=dict(
                arrowstyle='-|>',
                color='purple',
                lw=2,
                linestyle='dashed',
                connectionstyle=f"arc3,rad={rad}"
            )
        )
        # Ajouter le label au milieu
        x = (pos[b_dst][0] + pos[b_src][0]) / 2
        y = (pos[b_dst][1] + pos[b_src][1]) / 2 + rad * 1.5
        ax.text(x, y, f"{amount:,.0f} {from_cur}", color="purple", fontsize=9, ha="center", va="center")
        conv_index += 1

    ax.axis('off')

