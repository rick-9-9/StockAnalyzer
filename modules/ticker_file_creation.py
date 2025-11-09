import requests
import pandas as pd
import io

# Lista aggiornata di URL per i principali mercati azionari mondiali
urls = [
    # Mercati USA
    'https://raw.githubusercontent.com/LondonMarket/Global-Stock-Symbols/master/nyse_1668526574444.csv',
    'https://raw.githubusercontent.com/LondonMarket/Global-Stock-Symbols/master/nasdaq_1668526380140.csv',
    'https://raw.githubusercontent.com/LondonMarket/Global-Stock-Symbols/master/amex_1668526591787.csv',
]

dfs = []

for url in urls:
    try:
        response = requests.get(url)
        response.raise_for_status()

        if url.endswith('.csv'):
            df = pd.read_csv(io.StringIO(response.text), sep=None, engine='python', on_bad_lines='skip')
        elif url.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(response.content))

        # Normalizzare le colonne più comuni
        df_columns = [col.lower().strip() for col in df.columns]
        if 'name' in df_columns:
            df.rename(columns={df.columns[df_columns.index('name')]: 'Company'}, inplace=True)
        elif 'company' in df_columns:
            df.rename(columns={df.columns[df_columns.index('company')]: 'Company'}, inplace=True)

        if 'ticker' in df_columns:
            df.rename(columns={df.columns[df_columns.index('ticker')]: 'Ticker'}, inplace=True)
        elif 'symbol' in df_columns:
            df.rename(columns={df.columns[df_columns.index('symbol')]: 'Ticker'}, inplace=True)

        # Se esistono almeno le colonne Company e Ticker
        if 'Company' in df.columns and 'Ticker' in df.columns:
            dfs.append(df[['Company', 'Ticker']])
            print(f"File scaricato e normalizzato con successo da: {url}")
        else:
            print(f"File {url} non contiene colonne Company/Ticker riconosciute.")

    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download del file da {url}: {e}")

# Concatenazione finale e rimozione duplicati
df_all = pd.concat(dfs, ignore_index=True)
df_all.drop_duplicates(inplace=True)
df_all.to_csv('azioni_mondiali_completo.csv', index=False)
print("File 'azioni_mondiali_completo.csv' creato con successo!")
