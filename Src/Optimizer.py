def optimize_transfers(banks, balances, required, rates, interet=0.03):
    """
    Optimisation des transferts et conversions entre banques.
    
    transfers[(b_src, b_dst, cur)] : montant transféré de b_src à b_dst dans la devise cur.
    conversions[(b_dst, b_src, from_cur, to_cur)] : montant payé par b_dst à b_src dans from_cur pour recevoir to_cur.
    
    Chaque transfert déclenche automatiquement un paiement (conversion) avec le taux interbancaire et l'intérêt.
    """
    transfers = {}
    conversions = {}

    for b_dst in banks:
        for cur in ['EUR', 'USD']:
            deficit = required.get((b_dst, cur), 0) - balances.get((b_dst, cur), 0)
            if deficit <= 0:
                continue  # Pas de déficit

            for b_src in banks:
                if b_src == b_dst:
                    continue
                surplus = balances.get((b_src, cur), 0) - required.get((b_src, cur), 0)
                if surplus <= 0:
                    continue

                # Montant transférable
                transfer = min(deficit, surplus)
                transfers[(b_src, b_dst, cur)] = transfer
                balances[(b_src, cur)] -= transfer
                balances[(b_dst, cur)] += transfer
                deficit -= transfer

                # --- Conversion automatique pour payer b_src ---
                other_cur = 'EUR' if cur == 'USD' else 'USD'
                rate = rates.get((other_cur, cur), 1)
                amount_to_pay = transfer * rate * (1 + interet)
                conversions[(b_dst, b_src, other_cur, cur)] = amount_to_pay

                if deficit <= 0:
                    break
            if deficit <= 0:
                break

    return transfers, conversions
