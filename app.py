import streamlit as st
import sqlite3
from datetime import date

# Configuration page
st.set_page_config(page_title="Ménage Maison", page_icon="🧹")

# Connexion base de données
conn = sqlite3.connect('taches.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS taches
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              tache TEXT,
              responsable TEXT,
              faite INTEGER DEFAULT 0,
              date_creation DATE)''')
conn.commit()

st.title("🧹 Planning Ménage")

# Formulaire d'ajout
with st.form("ajouter"):
    col1, col2 = st.columns([3, 2])
    with col1:
        nouvelle_tache = st.text_input("Nouvelle tâche", placeholder="Ex: Passer l'aspirateur")
    with col2:
        responsable = st.selectbox("Responsable", ["Personne 1", "Personne 2", "Les deux"])
    submit = st.form_submit_button("➕ Ajouter")
    if submit and nouvelle_tache:
        c.execute("INSERT INTO taches (tache, responsable, faite, date_creation) VALUES (?, ?, 0, ?)",
                  (nouvelle_tache, responsable, date.today()))
        conn.commit()
        st.rerun()

# Affichage des tâches
st.subheader("📋 Tâches en cours")
taches = c.execute("SELECT * FROM taches WHERE faite = 0 ORDER BY date_creation DESC").fetchall()

if not taches:
    st.info("Aucune tâche en cours ! 🎉")
else:
    for tache in taches:
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.write(f"**{tache[1]}**")
        with col2:
            st.write(f"👤 {tache[2]}")
        with col3:
            if st.button("✅", key=f"fait_{tache[0]}"):
                c.execute("UPDATE taches SET faite = 1 WHERE id = ?", (tache[0],))
                conn.commit()
                st.rerun()

# Historique
with st.expander("📜 Voir l'historique"):
    historique = c.execute("SELECT * FROM taches WHERE faite = 1 ORDER BY date_creation DESC LIMIT 20").fetchall()
    for h in historique:
        st.write(f"✅ {h[1]} ({h[2]}) - {h[4]}")