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

st.title("Inventario")

file_path = os.path.join("Dataset", "tcg_monitor.xlsx")
print(file_path)
fix_excel(file_path)

if os.path.exists(file_path):
    df = pd.read_excel(file_path)

    # Ottieni il prezzo_minimo più recente per ogni combinazione unica
    idx_latest = df.groupby("nome_carta_completo")["data"].idxmax()
    df_latest_prices = df.loc[idx_latest, ["nome_carta_completo", "prezzo_minimo"]]

    # Unisci al dataframe principale
    df_inventario = df.drop(columns=[
        "articoli_disponibili", "tendenza_prezzo_global", 
        "prezzo_medio_30_gg_global", "prezzo_medio_7_gg_global", 
        "prezzo_medio_1_gg_global", "prezzo_minimo_professional", "data"
    ]).drop_duplicates()

    df_inventario = df_inventario.merge(df_latest_prices, on="nome_carta_completo", how="left", suffixes=('', '_latest')).drop_duplicates()

    df_inventario = df_inventario.drop(columns=['prezzo_minimo'], errors='ignore')
    df_inventario = df_inventario.rename(columns={"prezzo_minimo_latest": "prezzo_minimo"})

    # Ordina per prezzo_minimo desc
    df_inventario = df_inventario.sort_values(by="prezzo_minimo", ascending=False).drop_duplicates()

    # Layout in due colonne: sinistra (70%), destra (30%)
    col1, col2 = st.columns([4, 2])  # Puoi regolare le proporzioni a piacere

    with col1:
        st.subheader("📋 Inventario completo")
        # st.dataframe(df_inventario)
        st.dataframe(df_inventario.reset_index(drop=True), use_container_width=True)


    with col2:
        # Selezione carta da visualizzare
        carte = df_inventario["nome_carta_completo"].unique()
        carta_scelta = st.selectbox("Scegli una carta per vedere l'andamento del prezzo:", carte)

        # Filtro dati originali per la carta selezionata
        df_carta = df[df["nome_carta_completo"] == carta_scelta].sort_values("data")

        df_carta["data"] = pd.to_datetime(df_carta["data"])

        # Controllo che ci sia almeno una colonna prezzi
        colonne_prezzo = ["data", "prezzo_minimo", "prezzo_minimo_professional", "tendenza_prezzo_global"]
        colonne_presenti = [col for col in colonne_prezzo if col in df_carta.columns]

        if len(colonne_presenti) > 1:
            st.subheader(f"📈 Prezzi per: {carta_scelta}")

            # Plot Matplotlib
            plt.figure(figsize=(8, 4))
            for col in colonne_presenti[1:]:  # salta la colonna 'data'
                plt.plot(df_carta["data"], df_carta[col], label=col.replace("_", " ").title())

            plt.xlabel("Data")
            plt.ylabel("Prezzo (€)")
            plt.legend()
            plt.grid(True)
            st.pyplot(plt)

        else:
            st.info("Dati di prezzo non disponibili per questa carta.")


    # Aggiungi l'intestazione
    st.subheader("Carte in inventario")

    # Seleziona le colonne da visualizzare (inclusa l'immagine)
    cols_to_show = ["image_path", "nome_carta_completo", "specie", "rarita", "prezzo_minimo"]

    # Aggiungi il prefisso all'immagine
    # df_inventario['image_path'] = "./" + df_inventario['image_path']
    df_inventario['image_path'] = df_inventario['image_path'].apply(lambda x: os.path.join(".", x))

    # Seleziona solo le colonne necessarie
    cards = df_inventario[cols_to_show]

    # Ordina per prezzo_minimo desc
    cards = cards.sort_values(by="prezzo_minimo", ascending=False).drop_duplicates()
    cards.reset_index(drop=True)

    # Imposta il numero di colonne per la visualizzazione
    num_columns = 5
    cols = st.columns(num_columns)

    # Ciclo per visualizzare ogni carta nelle colonne
    for i, row in enumerate(cards.itertuples(index=False)):

        # Seleziona la colonna corretta utilizzando l'indice
        col_idx = i % num_columns
        
        print(row)
        with cols[col_idx]:
            # Crea il contenitore per ogni carta
            tile = st.container(border=True)
            
            # Mostra l'immagine
            tile.image(row.image_path, caption=row.nome_carta_completo, width=250)
            
            # Visualizza le informazioni della carta
            tile.write(f"**Specie:** {row.specie}")
            tile.write(f"**Rarità:** {row.rarita}")
            tile.write(f"**Prezzo Minimo:** {row.prezzo_minimo}€")

