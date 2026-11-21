import streamlit as st
from supabase import create_client
from datetime import datetime, date

# Configuration
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Ménage Tifenn & Gaël", page_icon="🏠")
st.title("🏠 Suivi des tâches de ménage")

# Navigation par onglets
tab1, tab2, tab3 = st.tabs(["➕ Créer une tâche", "📋 À faire", "📜 Historique"])

# ==========================================
# ONGLET 1 : CRÉATION
# ==========================================
with tab1:
    st.header("Nouvelle tâche")
    with st.form("creer_tache", clear_on_submit=True):
        nom = st.text_input("Nom de la tâche", placeholder="Ex: Passer l'aspirateur")
        col1, col2 = st.columns(2)
        with col1:
            frequence = st.number_input("Tous les combien de jours ?", min_value=1, value=7, step=1)
        with col2:
            priorite = st.slider("Priorité (1 = basse, 5 = haute)", 1, 5, 3)

        if st.form_submit_button("✅ Ajouter la tâche"):
            if nom.strip():
                supabase.table("taches").insert({
                    "nom": nom.strip(),
                    "frequence_jours": frequence,
                    "priorite": priorite
                }).execute()
                st.success(f"Tâche '{nom}' ajoutée !")
                st.rerun()
            else:
                st.error("Donne un nom à la tâche !")

# ==========================================
# ONGLET 2 : LISTE À FAIRE (triée par urgence)
# ==========================================
with tab2:
    st.header("📋 Tâches à faire")

    # Récupération des données
    taches = supabase.table("taches").select("*").execute().data
    executions = supabase.table("executions").select("*").order("date_execution", desc=True).execute().data

    # Map : tache_id -> dernière exécution
    dernieres = {}
    for e in executions:
        if e["tache_id"] not in dernieres:
            dernieres[e["tache_id"]] = e

    aujourdhui = date.today()
    liste = []

    for t in taches:
        derniere = dernieres.get(t["id"])
        if derniere:
            # Parse la date (Supabase renvoie une string ISO)
            date_ref = datetime.fromisoformat(derniere["date_execution"].replace("Z", "+00:00")).date()
            personne = derniere["personne"]
        else:
            date_ref = datetime.fromisoformat(t["date_creation"].replace("Z", "+00:00")).date()
            personne = None

        jours_ecoules = (aujourdhui - date_ref).days
        retard = jours_ecoules - t["frequence_jours"]  # >0 = en retard

        liste.append({
            **t,
            "date_ref": date_ref,
            "personne": personne,
            "retard": retard
        })

    # TRI : plus en retard d'abord (retard décroissant), puis priorité haute d'abord (5 avant 1)
    liste.sort(key=lambda x: (-x["retard"], -x["priorite"]))

    if not liste:
        st.info("Aucune tâche pour le moment. Va dans l'onglet 'Créer une tâche' !")
    else:
        for t in liste:
            # Indicateur visuel
            if t["retard"] > 0:
                emoji = "🔴"
                statut = f"En retard de {t['retard']} jour(s) !"
                couleur = "red"
            elif t["retard"] == 0:
                emoji = "🟡"
                statut = "À faire aujourd'hui"
                couleur = "orange"
            else:
                emoji = "🟢"
                statut = f"Prochaine fois dans {-t['retard']} jour(s)"
                couleur = "green"

            with st.container():
                col_info, col_action = st.columns([3, 2])

                with col_info:
                    st.markdown(f"### {emoji} {t['nom']}")
                    st.caption(f"Fréquence: tous les {t['frequence_jours']} j | Priorité: {'⭐' * t['priorite']} ({t['priorite']}/5)")
                    st.markdown(f"<span style='color:{couleur}'><b>{statut}</b></span>", unsafe_allow_html=True)
                    if t["personne"]:
                        st.caption(f"Dernière fois : le {t['date_ref'].strftime('%d/%m/%Y')} par {t['personne']}")
                    else:
                        st.caption(f"Jamais faite (créée le {t['date_ref'].strftime('%d/%m/%Y')})")

                with col_action:
                    with st.form(key=f"form_{t['id']}"):
                        qui = st.selectbox("Qui l'a faite ?", ["Tifenn", "Gaël"], key=f"qui_{t['id']}")
                        if st.form_submit_button("✅ C'est fait !"):
                            supabase.table("executions").insert({
                                "tache_id": t["id"],
                                "personne": qui,
                                "date_execution": datetime.now().isoformat()
                            }).execute()
                            st.success("Enregistré dans l'historique !")
                            st.rerun()

                st.divider()

# ==========================================
# ONGLET 3 : HISTORIQUE
# ==========================================
with tab3:
    st.header("📜 Historique des tâches effectuées")

    # Jointure pour avoir le nom de la tâche
    histo = supabase.table("executions").select("*, taches(nom)").order("date_execution", desc=True).execute().data

    if not histo:
        st.info("Rien dans l'historique pour l'instant.")
    else:
        for e in histo:
            date_e = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))
            nom_tache = e["taches"]["nom"] if e.get("taches") else "❓ Tâche supprimée"
            st.write(f"• **{nom_tache}** — {date_e.strftime('%d/%m/%Y à %H:%M')} par **{e['personne']}**")