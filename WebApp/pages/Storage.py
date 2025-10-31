import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

def fix_excel(file_path):
    df = pd.read_excel(file_path)

    key_columns = ['tcg', 'nome_carta_completo', 'specie', 'rarita', 'numero_carta',
                   'sigla_espansione', 'nome_set', 'lingua', 'condizione_carta']

    # Separazione dei dati
    df_without_image = df[(df['image_path'].isna()) | (df['image_path'] == "Immagine già salvata in precedenza")].copy()
    df_with_image = df[(df['image_path'].notna()) & (df['image_path'] != "Immagine già salvata in precedenza")].copy()

    # Ciclo riga per riga su df_without_image per assegnare image_path corrispondente
    for idx, row in df_without_image.iterrows():
        mask = (df_with_image[key_columns] == row[key_columns]).all(axis=1)
        matched = df_with_image[mask]

        if not matched.empty:
            # Se c'è almeno una corrispondenza, assegna il primo image_path trovato
            df.at[idx, 'image_path'] = matched.iloc[0]['image_path']

    # Sostituisci "Immagine già salvata in precedenza" con NA per uniformità
    df['image_path'].replace("Immagine già salvata in precedenza", pd.NA, inplace=True)

    # Salvataggio
    df.to_excel(file_path, index=False)

st.title("Storage")

current_dir = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(current_dir, ".."))
file_path = os.path.join(base_dir, "Dataset", "tcg_monitor.xlsx")

fix_excel(file_path)

if os.path.exists(file_path):
    df = pd.read_excel(file_path)

    # Assicurati che la colonna 'data' sia di tipo datetime
    df["data"] = pd.to_datetime(df["data"])    

    # Ordina df per data decrescente e prendi la seconda data più recente per ogni carta
    df_sorted = df.sort_values(["nome_carta_completo", "data"], ascending=[True, False])
    
    df_latest = df_sorted.groupby("nome_carta_completo").nth(0).reset_index()
    df_second_latest = df_sorted.groupby("nome_carta_completo").nth(1).reset_index()

    # Unisci df_inventario con i valori di prezzo_minimo della seconda data più recente da df
    merged = pd.merge(df_latest, df_second_latest[["nome_carta_completo", "prezzo_minimo", "prezzo_minimo_professional", "tendenza_prezzo_global", "articoli_disponibili"]], on="nome_carta_completo", how="left", suffixes=("", "_seconda_data"))

    # Calcola Informazioni
    merged["variazione_percentuale_prezzo_minimo"] = ((merged["prezzo_minimo_seconda_data"] - merged["prezzo_minimo"]) / merged["prezzo_minimo"].replace(0, pd.NA)).mul(100).astype(float).round(2)
    merged["variazione_percentuale_prezzo_minimo_professional"] = ((merged["prezzo_minimo_professional_seconda_data"] - merged["prezzo_minimo_professional"]) / merged["prezzo_minimo_professional"].replace(0, pd.NA)).mul(100).astype(float).round(2)
    merged["variazione_percentuale_tendenza_prezzo_global"] = ((merged["tendenza_prezzo_global_seconda_data"] - merged["tendenza_prezzo_global"]) / merged["tendenza_prezzo_global"].replace(0, pd.NA)).mul(100).astype(float).round(2)
    merged["variazione_percentuale_articoli_disponibili"] = ((merged["articoli_disponibili_seconda_data"] - merged["articoli_disponibili"]) / merged["articoli_disponibili"].replace(0, pd.NA)).mul(100).astype(float).round(2)
    merged = merged.sort_values("prezzo_minimo", ascending= False)
    # Aggiungi il prefisso all'immagine
    current_dir = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(current_dir, ".."))
    # merged['image_path'] = merged['image_path'].apply(lambda x: os.path.join(base_dir, x))
    merged['image_path'] = merged['image_path'].apply(
        lambda x: os.path.normpath(os.path.join(base_dir, x.replace("\\", "/"))) if pd.notna(x) else x
    )
    st.dataframe(merged.reset_index(drop=True), use_container_width=True)

    # Aggiungi l'intestazione
    st.subheader("Carte in inventario")

    cols_to_show = ["image_path", "nome_carta_completo", "specie", "rarita", "prezzo_minimo", "prezzo_minimo_professional", "articoli_disponibili", "variazione_percentuale_prezzo_minimo", "variazione_percentuale_prezzo_minimo_professional", "variazione_percentuale_tendenza_prezzo_global", "variazione_percentuale_articoli_disponibili"]
    cards = merged[cols_to_show]
    num_columns = 5
    cols = st.columns(num_columns)

    def format_variation(value):
        if value > 0:
            return f":green[▲ {value:.2f}%]"
        elif value < 0:
            return f":red[▼ {value:.2f}%]"
        else:
            return f":gray[= {value:.2f}%]"

    # Ciclo per visualizzare ogni carta nelle colonne
    for i, row in enumerate(cards.itertuples(index=False)):
        col_idx = i % num_columns
        with cols[col_idx]:
            tile = st.container(border=True)
            tile.image(row.image_path, caption=row.nome_carta_completo)
            tile.markdown('<style>img { height: 400px; object-fit: cover; }</style>', unsafe_allow_html=True)
            tile.write(f"**Specie:** {row.specie}")
            tile.write(f"**Rarità:** {row.rarita}")
            tile.write(f"**Articoli disponibili:** {row.articoli_disponibili}")
            tile.write(f"**Prezzo:** {row.prezzo_minimo}€")
            tile.write(f"**Prezzo PRO:** {row.prezzo_minimo_professional}€")
            tile.write(f"**Variazione Prezzo:** {format_variation(row.variazione_percentuale_prezzo_minimo)}")
            tile.write(f"**Variazione Prezzo PRO:** {format_variation(row.variazione_percentuale_prezzo_minimo_professional)}")
            tile.write(f"**Variazione Prezzo Global:** {format_variation(row.variazione_percentuale_tendenza_prezzo_global)}")

