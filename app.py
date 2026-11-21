import streamlit as st
from supabase import create_client
from datetime import datetime

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Ménage Tifenn & Gaël", page_icon="🏠", layout="wide")
st.title("🏠 Suivi des tâches de ménage")

# ==========================================
# ORDRE DES ONGLETS : À faire > Historique > Créer > Gestion
# ==========================================
tab_a_faire, tab_historique, tab_creer, tab_gestion = st.tabs([
    "📋 À faire",
    "📜 Historique",
    "➕ Créer une tâche",
    "⚙️ Gestion des tâches"
])

# ==========================================
# ONGLET 1 : À FAIRE (format compact)
# ==========================================
with tab_a_faire:
    st.header("📋 Tâches à faire")

    # Récupération des données
    taches = supabase.table("taches").select("*").execute().data
    executions = supabase.table("executions").select("*").order("date_execution", desc=True).execute().data

    # Dernière exécution par tâche
    derniere_exec = {}
    for e in executions:
        if e["tache_id"] not in derniere_exec:
            derniere_exec[e["tache_id"]] = e

    # Calcul et tri
    liste_triee = []
    maintenant = datetime.now()

    for t in taches:
        exec_info = derniere_exec.get(t["id"])
        if exec_info:
            date_ref = datetime.fromisoformat(exec_info["date_execution"].replace("Z", "+00:00")).replace(tzinfo=None)
            personne = exec_info["personne"]
        else:
            date_ref = datetime.fromisoformat(t["date_creation"].replace("Z", "+00:00")).replace(tzinfo=None)
            personne = None

        jours_ecoules = (maintenant - date_ref).days
        retard = jours_ecoules - t["frequence_jours"]  # >0 = en retard

        liste_triee.append({
            "id": t["id"],
            "nom": t["nom"],
            "frequence": t["frequence_jours"],
            "priorite": t["priorite"],
            "retard": retard,
            "date_ref": date_ref,
            "personne": personne
        })

    # Tri : plus en retard d'abord, puis priorité haute
    liste_triee.sort(key=lambda x: (x["retard"], x["priorite"]), reverse=True)

    if not liste_triee:
        st.info("Aucune tâche ! Crée-en une dans l'onglet '➕ Créer une tâche'.")
    else:
        for t in liste_triee:
            # Déterminer l'affichage des jours
            if t["retard"] > 0:
                couleur = "🔴"
                texte_jours = f"En retard de {t['retard']} j"
            elif t["retard"] == 0:
                couleur = "🟡"
                texte_jours = "À faire aujourd'hui"
            else:
                couleur = "🟢"
                texte_jours = f"Dans {-t['retard']} j"

            # === LIGNE COMPACTE (toujours visible) ===
            col_couleur, col_nom, col_qui, col_btn = st.columns([0.4, 3, 1.5, 1.5])

            with col_couleur:
                st.markdown(f"### {couleur}")

            with col_nom:
                st.markdown(f"**{t['nom']}**")
                st.caption(texte_jours)

            with col_qui:
                qui = st.selectbox("Qui ?", ["Tifenn", "Gaël"], key=f"qui_{t['id']}")

            with col_btn:
                st.write("")  # petit espacement vertical
                if st.button("✅ C'est fait", key=f"btn_{t['id']}", use_container_width=True):
                    supabase.table("executions").insert({
                        "tache_id": t["id"],
                        "personne": qui,
                        "date_execution": datetime.now().isoformat()
                    }).execute()
                    st.success(f"'{t['nom']}' marquée comme faite par {qui} !")
                    st.rerun()

            # === DÉTAILS DÉROULANTS ===
            with st.expander("ℹ️ Voir détails (fréquence, dernière fois...)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Fréquence :** tous les {t['frequence']} jours")
                    st.write(f"**Priorité :** {t['priorite']}/5")
                with c2:
                    if t["personne"]:
                        st.write(f"**Dernière fois :** {t['date_ref'].strftime('%d/%m/%Y')} par **{t['personne']}**")
                    else:
                        st.write(f"**Jamais faite** (créée le {t['date_ref'].strftime('%d/%m/%Y')})")

            st.divider()

# ==========================================
# ONGLET 2 : HISTORIQUE
# ==========================================
with tab_historique:
    st.header("📜 Historique des tâches effectuées")

    histo = supabase.table("executions").select("*, taches(nom)").order("date_execution", desc=True).execute().data

    if not histo:
        st.info("Rien dans l'historique pour l'instant.")
    else:
        filtre = st.selectbox("Filtrer par personne :", ["Tout le monde", "Tifenn", "Gaël"])
        if filtre != "Tout le monde":
            histo = [e for e in histo if e["personne"] == filtre]

        for e in histo:
            date_e = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))
            nom_tache = e["taches"]["nom"] if e.get("taches") else "❓ Tâche supprimée"
            st.write(f"• **{nom_tache}** — {date_e.strftime('%d/%m/%Y à %H:%M')} par **{e['personne']}**")

# ==========================================
# ONGLET 3 : CRÉER UNE TÂCHE
# ==========================================
with tab_creer:
    st.header("➕ Nouvelle tâche")
    with st.form("creer_tache", clear_on_submit=True):
        nom = st.text_input("Nom de la tâche", placeholder="Ex: Passer l'aspirateur")
        col1, col2 = st.columns(2)
        with col1:
            frequence = st.number_input("Tous les combien de jours ?", min_value=1, value=7, step=1)
        with col2:
            priorite = st.slider("Priorité (1=basse, 5=haute)", 1, 5, 3)

        if st.form_submit_button("✅ Ajouter la tâche", use_container_width=True):
            if nom.strip():
                supabase.table("taches").insert({
                    "nom": nom.strip(),
                    "frequence_jours": int(frequence),
                    "priorite": int(priorite)
                }).execute()
                st.success(f"Tâche '{nom}' ajoutée !")
                st.rerun()
            else:
                st.error("Donne un nom à la tâche !")

# ==========================================
# ONGLET 4 : GESTION (modifier/supprimer)
# ==========================================
with tab_gestion:
    st.header("⚙️ Gestion des tâches existantes")

    taches = supabase.table("taches").select("*").order("date_creation", desc=True).execute().data

    if not taches:
        st.info("Aucune tâche à gérer.")
    else:
        for t in taches:
            with st.expander(f"🔧 {t['nom']} (tous les {t['frequence_jours']} j, prio {t['priorite']}/5)"):
                # Formulaire de modification
                with st.form(key=f"modif_{t['id']}"):
                    nouveau_nom = st.text_input("Nom", value=t["nom"])
                    c1, c2 = st.columns(2)
                    with c1:
                        nouvelle_freq = st.number_input("Fréquence (jours)", min_value=1, value=t["frequence_jours"], step=1, key=f"freq_{t['id']}")
                    with c2:
                        nouvelle_prio = st.slider("Priorité", 1, 5, t["priorite"], key=f"prio_{t['id']}")

                    if st.form_submit_button("💾 Enregistrer les modifications"):
                        supabase.table("taches").update({
                            "nom": nouveau_nom.strip(),
                            "frequence_jours": int(nouvelle_freq),
                            "priorite": int(nouvelle_prio)
                        }).eq("id", t["id"]).execute()
                        st.success("Tâche modifiée !")
                        st.rerun()

                # Bouton suppression
                if st.button("🗑️ Supprimer définitivement", key=f"suppr_{t['id']}", type="primary"):
                    supabase.table("taches").delete().eq("id", t["id"]).execute()
                    st.success(f"Tâche '{t['nom']}' supprimée !")
                    st.rerun()