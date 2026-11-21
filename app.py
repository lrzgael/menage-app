import streamlit as st
from supabase import create_client, Client
from datetime import date

# Configuration
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Ménage Maison", page_icon="🧹")
st.title("🧹 Planning Ménage")

# Ajouter une tâche
with st.form("ajouter"):
    col1, col2 = st.columns([3, 2])
    with col1:
        nouvelle_tache = st.text_input("Nouvelle tâche")
    with col2:
        responsable = st.selectbox("Responsable", ["Personne 1", "Personne 2"])
    if st.form_submit_button("➕ Ajouter") and nouvelle_tache:
        supabase.table("taches").insert({
            "tache": nouvelle_tache,
            "responsable": responsable,
            "faite": False
        }).execute()
        st.rerun()

# Afficher tâches non faites
st.subheader("📋 À faire")
response = supabase.table("taches").select("*").eq("faite", False).order("date_creation", desc=True).execute()

for tache in response.data:
    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        st.write(f"**{tache['tache']}**")
    with col2:
        st.write(f"👤 {tache['responsable']}")
    with col3:
        if st.button("✅", key=f"fait_{tache['id']}"):
            supabase.table("taches").update({"faite": True}).eq("id", tache['id']).execute()
            st.rerun()

# Historique
with st.expander("📜 Historique"):
    histo = supabase.table("taches").select("*").eq("faite", True).order("date_creation", desc=True).limit(20).execute()
    for h in histo.data:
        st.write(f"✅ {h['tache']} ({h['responsable']}) - {h['date_creation']}")