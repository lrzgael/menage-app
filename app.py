import streamlit as st
from supabase import create_client
from datetime import datetime

# Configuration
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Ménage Tifenn & Gaël", page_icon="🏠", layout="wide")
st.title("🏠 Suivi des tâches de ménage")

# ==========================================
# ONGLETS DANS L'ORDRE SOUHAITÉ
# ==========================================
tab_a_faire, tab_creer, tab_gestion, tab_historique = st.tabs([
    "📋 À faire",
    "➕ Créer une tâche",
    "⚙️ Gestion des tâches",
    "📜 Historique"
])

# ==========================================
# ONGLET 1 : LISTE DES TÂCHES À FAIRE (EN PREMIER)
# ==========================================
with tab_a_faire:
    st.header("📋 Tâches à faire maintenant")

    # Récupérer toutes les tâches
    taches = supabase.table("taches").select("*").execute().data

    # Récupérer la dernière exécution de chaque tâche
    executions = supabase.table("executions").select("*").order("date_execution", desc=True).execute().data

    # Créer un dict : tache_id -> dernière exécution
    derniere_exec = {}
    for e in executions:
        if e["tache_id"] not in derniere_exec:
            derniere_exec[e["tache_id"]] = e

    # Calculer le retard pour chaque tâche et trier
    liste_triee = []
    maintenant = datetime.now()

    for t in taches:
        exec_info = derniere_exec.get(t["id"])
        if exec_info:
            date_derniere = datetime.fromisoformat(exec_info["date_execution"].replace("Z", "+00:00")).replace(tzinfo=None)
            jours_ecoules = (maintenant - date_derniere).days
            personne = exec_info["personne"]
        else:
            # Jamais faite : on considère la date de création
            date_derniere = datetime.fromisoformat(t["date_creation"].replace("Z", "+00:00")).replace(tzinfo=None)
            jours_ecoules = (maintenant - date_derniere).days
            personne = None

        retard = jours_ecoules - t["frequence_jours"]  # > 0 = en retard
        liste_triee.append({
            "id": t["id"],
            "nom": t["nom"],
            "frequence": t["frequence_jours"],
            "priorite": t["priorite"],
            "retard": retard,
            "jours_ecoules": jours_ecoules,
            "personne": personne,
            "date_ref": date_derniere
        })

    # Trier : d'abord par retard décroissant (plus en retard = plus haut), puis par priorité décroissante
    liste_triee.sort(key=lambda x: (x["retard"], x["priorite"]), reverse=True)

    if not liste_triee:
        st.info("Aucune tâche créée pour l'instant. Va dans l'onglet '➕ Créer une tâche' !")
    else:
        for t in liste_triee:
            # Couleur selon l'urgence
            if t["retard"] > 0:
                couleur = "🔴"
                statut = f"En retard de {t['retard']} jour(s) !"
            elif t["retard"] == 0:
                couleur = "🟡"
                statut = "À faire aujourd'hui"
            else:
                couleur = "🟢"
                statut = f"Dans {-t['retard']} jour(s)"

            col_info, col_action = st.columns([3, 2])

            with col_info:
                st.markdown(f"### {couleur} {t['nom']} — Priorité {t['priorite']}/5")
                st.write(f"Fréquence : tous les {t['frequence']} jours")
                st.markdown(f"<span style='color:gray'>{statut}</span>", unsafe_allow_html=True)
                if t["personne"]:
                    st.caption(f"Dernière fois : le {t['date_ref'].strftime('%d/%m/%Y')} par {t['personne']}")
                else:
                    st.caption(f"Jamais faite (créée le {t['date_ref'].strftime('%d/%m/%Y')})")

            with col_action:
                with st.form(key=f"form_faite_{t['id']}"):
                    qui = st.selectbox("Qui l'a faite ?", ["Tifenn", "Gaël"], key=f"qui_{t['id']}")
                    if st.form_submit_button("✅ C'est fait !", use_container_width=True):
                        supabase.table("executions").insert({
                            "tache_id": t["id"],
                            "personne": qui,
                            "date_execution": datetime.now().isoformat()
                        }).execute()
                        st.success("Enregistré !")
                        st.rerun()

            st.divider()

# ==========================================
# ONGLET 2 : CRÉATION DE TÂCHE
# ==========================================
with tab_creer:
    st.header("➕ Nouvelle tâche")
    with st.form("creer_tache", clear_on_submit=True):
        nom = st.text_input("Nom de la tâche", placeholder="Ex: Passer l'aspirateur")
        col1, col2 = st.columns(2)
        with col1:
            frequence = st.number_input("Tous les combien de jours ?", min_value=1, value=7, step=1)
        with col2:
            priorite = st.slider("Priorité (1 = basse, 5 = haute)", 1, 5, 3)

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
# ONGLET 3 : GESTION DES TÂCHES (MODIFIER / SUPPRIMER)
# ==========================================
with tab_gestion:
    st.header("⚙️ Gestion des tâches existantes")

    taches = supabase.table("taches").select("*").order("date_creation", desc=True).execute().data

    if not taches:
        st.info("Aucune tâche à gérer. Crée-en une dans l'onglet '➕ Créer une tâche'.")
    else:
        for t in taches:
            with st.expander(f"🔧 {t['nom']} (tous les {t['frequence_jours']} jours, priorité {t['priorite']}/5)"):
                col_modif, col_suppr = st.columns([4, 1])

                with col_modif:
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

                with col_suppr:
                    st.write("")  # espacement
                    st.write("")
                    if st.button("🗑️ Supprimer", key=f"suppr_{t['id']}", type="primary"):
                        # Supprimer la tâche (les exécutions seront supprimées automatiquement grâce au ON DELETE CASCADE)
                        supabase.table("taches").delete().eq("id", t["id"]).execute()
                        st.success(f"Tâche '{t['nom']}' supprimée !")
                        st.rerun()

# ==========================================
# ONGLET 4 : HISTORIQUE
# ==========================================
with tab_historique:
    st.header("📜 Historique des tâches effectuées")

    # Jointure pour avoir le nom de la tâche
    histo = supabase.table("executions").select("*, taches(nom)").order("date_execution", desc=True).execute().data

    if not histo:
        st.info("Rien dans l'historique pour l'instant.")
    else:
        # Optionnel : filtre par personne
        filtre = st.selectbox("Filtrer par personne :", ["Tout le monde", "Tifenn", "Gaël"])
        if filtre != "Tout le monde":
            histo = [e for e in histo if e["personne"] == filtre]

        for e in histo:
            date_e = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))
            nom_tache = e["taches"]["nom"] if e.get("taches") else "❓ Tâche supprimée"
            st.write(f"• **{nom_tache}** — {date_e.strftime('%d/%m/%Y à %H:%M')} par **{e['personne']}**")