import pandas as pd
import os

class DataLoader:
    def __init__(self, data_dir="Data"):
        base_dir = os.path.dirname(os.path.abspath(__file__))  

        # 📌 On remonte au dossier Data puis Data2
        self.data_dir = os.path.join(base_dir, "..", "Data")  # -> .../Data/Data

        self.banks_file = os.path.join(self.data_dir, "Banks.csv")
        self.rates_file = os.path.join(self.data_dir, "Rates.csv")

    def load_banks_data(self):
        df = pd.read_csv(self.banks_file)
        df = df.dropna(how='all')  # Supprimer les lignes vides
        
        banks_set = set()
        balances = {}
        required = {}
        for _, row in df.iterrows():
            bank = str(row['bank']).strip()
            currency = str(row['currency']).strip()
            balance = float(row['balance'])
            req = float(row['required'])
            banks_set.add(bank)
            balances[(bank, currency)] = balance
            required[(bank, currency)] = req
        banks = list(banks_set)
        return banks, balances, required

    def load_rates(self):
        df = pd.read_csv(self.rates_file)
        df = df.dropna(how='all')  # Supprimer les lignes vides
        
        rates = {}
        for _, row in df.iterrows():
            from_cur = str(row['from_currency']).strip()
            to_cur = str(row['to_currency']).strip()
            rate = float(row['rate'])
            rates[(from_cur, to_cur)] = rate
        return rates



