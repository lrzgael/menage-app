import streamlit as st
from supabase import create_client
from datetime import datetime

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Ménage", page_icon="🏠", layout="wide")

# ==========================================
# CSS POUR FORCER L'AFFICHAGE HORIZONTAL SUR MOBILE
# ==========================================
st.markdown("""
<style>
@media (max-width: 768px) {
    /* Force toutes les lignes de colonnes à rester horizontales */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }
    [data-testid="column"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 auto !important;
    }
    /* Compacte les selectbox */
    [data-testid="stSelectbox"] > div > div {
        min-height: 32px !important;
        padding: 2px 6px !important;
    }
    [data-testid="stSelectbox"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] {
        font-size: 13px !important;
    }
    /* Compacte les boutons */
    [data-testid="stButton"] > button {
        min-height: 32px !important;
        padding: 2px 8px !important;
        font-size: 14px !important;
        white-space: nowrap !important;
    }
    /* Texte tronqué avec ... si trop long */
    .task-name {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-size: 14px !important;
        line-height: 1.3 !important;
    }
    /* Réduit les espacements verticaux */
    .block-container {
        padding-top: 0.5rem !important;
    }
    [data-testid="stExpander"] {
        margin-top: 0 !important;
        margin-bottom: 0.2rem !important;
    }
    hr {
        margin: 0.3rem 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("🏠 Ménage")

# Ordre : À faire > Historique > Créer > Gérer
tab_a_faire, tab_historique, tab_creer, tab_gestion = st.tabs([
    "📋 À faire", "📜 Historique", "➕ Créer", "⚙️ Gérer"
])

# ==========================================
# ONGLET 1 : À FAIRE (1 LIGNE PAR TÂCHE)
# ==========================================
with tab_a_faire:
    taches = supabase.table("taches").select("*").execute().data
    executions = supabase.table("executions").select("*").order("date_execution", desc=True).execute().data

    derniere_exec = {}
    for e in executions:
        if e["tache_id"] not in derniere_exec:
            derniere_exec[e["tache_id"]] = e

    liste = []
    maintenant = datetime.now()
    for t in taches:
        e = derniere_exec.get(t["id"])
        if e:
            d = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00")).replace(tzinfo=None)
            qui = e["personne"]
        else:
            d = datetime.fromisoformat(t["date_creation"].replace("Z", "+00:00")).replace(tzinfo=None)
            qui = None

        jours = (maintenant - d).days
        retard = jours - t["frequence_jours"]
        liste.append({"id": t["id"], "nom": t["nom"], "freq": t["frequence_jours"],
                      "prio": t["priorite"], "retard": retard, "date": d, "qui": qui})

    liste.sort(key=lambda x: (x["retard"], x["prio"]), reverse=True)

    if not liste:
        st.info("Aucune tâche. Va dans ➕ Créer.")
    else:
        for t in liste:
            # Couleur et texte jours
            if t["retard"] > 0:
                icone, txt, couleur = "🔴", f"+{t['retard']}j", "#ff4b4b"
            elif t["retard"] == 0:
                icone, txt, couleur = "🟡", "Auj", "#ff9500"
            else:
                icone, txt, couleur = "🟢", f"{-t['retard']}j", "#28a745"

            # 4 colonnes sur UNE SEULE LIGNE : [icône] [nom+jours] [qui] [bouton]
            # Ratios : icône fixe petit, nom large, select moyen, bouton petit
            c1, c2, c3, c4 = st.columns([0.25, 3.5, 1.3, 0.6])

            with c1:
                st.markdown(f"<div style='font-size:1em; text-align:center; line-height:1;'>{icone}</div>",
                          unsafe_allow_html=True)

            with c2:
                # Nom avec classe task-name pour l'ellipsis + jours restants en couleur
                st.markdown(
                    f"<div class='task-name'><b>{t['nom']}</b> "
                    f"<span style='color:{couleur}; font-size:0.85em; white-space:nowrap;'> {txt}</span></div>",
                    unsafe_allow_html=True
                )

            with c3:
                qui = st.selectbox("Qui", ["Tifenn", "Gaël"], key=f"q{t['id']}",
                                 label_visibility="collapsed")

            with c4:
                if st.button("✓", key=f"b{t['id']}", help="C'est fait !"):
                    supabase.table("executions").insert({
                        "tache_id": t["id"],
                        "personne": qui,
                        "date_execution": datetime.now().isoformat()
                    }).execute()
                    st.rerun()

            # Détails cachés (cliquer pour voir fréquence et dernière fois)
            with st.expander("ℹ️", expanded=False):
                col_a, col_b = st.columns(2)
                col_a.caption(f"Tous les {t['freq']}j • Prio {t['prio']}/5")
                if t["qui"]:
                    col_b.caption(f"Dernière : {t['date'].strftime('%d/%m')} par {t['qui']}")
                else:
                    col_b.caption(f"Jamais faite (créée {t['date'].strftime('%d/%m')})")

            st.divider()

# ==========================================
# ONGLET 2 : HISTORIQUE (MODIFIABLE)
# ==========================================
with tab_historique:
    st.header("📜 Historique")

    histo = supabase.table("executions").select("*, taches(nom)").order("date_execution", desc=True).execute().data

    if not histo:
        st.info("Vide pour l'instant.")
    else:
        filtre = st.radio("Filtrer :", ["Tous", "Tifenn", "Gaël"], horizontal=True)
        if filtre != "Tous":
            histo = [e for e in histo if e["personne"] == filtre]

        for e in histo:
            d = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))
            nom = e["taches"]["nom"] if e.get("taches") else "❓ Tâche supprimée"
            label = f"{d.strftime('%d/%m/%Y %H:%M')} — {nom} — {e['personne']}"

            with st.expander(label):
                with st.form(key=f"edit_{e['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_date = st.date_input("Date", value=d.date())
                    with c2:
                        new_time = st.time_input("Heure", value=d.time())

                    new_pers = st.selectbox("Qui a fait ?", ["Tifenn", "Gaël"],
                                          index=0 if e["personne"] == "Tifenn" else 1)

                    if st.form_submit_button("💾 Modifier"):
                        new_dt = datetime.combine(new_date, new_time).isoformat()
                        supabase.table("executions").update({
                            "date_execution": new_dt,
                            "personne": new_pers
                        }).eq("id", e["id"]).execute()
                        st.success("Modifié !")
                        st.rerun()

                if st.button("🗑️ Supprimer cette entrée", key=f"del_{e['id']}"):
                    supabase.table("executions").delete().eq("id", e["id"]).execute()
                    st.rerun()

# ==========================================
# ONGLET 3 : CRÉER
# ==========================================
with tab_creer:
    with st.form("new", clear_on_submit=True):
        nom = st.text_input("Nom de la tâche", placeholder="Aspirateur salon...")
        c1, c2 = st.columns(2)
        freq = c1.number_input("Tous les X jours", 1, 365, 7)
        prio = c2.slider("Priorité", 1, 5, 3)
        if st.form_submit_button("➕ Ajouter"):
            if nom.strip():
                supabase.table("taches").insert({
                    "nom": nom.strip(),
                    "frequence_jours": int(freq),
                    "priorite": int(prio)
                }).execute()
                st.success("Ajouté !")
                st.rerun()
            else:
                st.error("Donne un nom !")

# ==========================================
# ONGLET 4 : GÉRER
# ==========================================
with tab_gestion:
    st.header("⚙️ Gérer les tâches")
    taches = supabase.table("taches").select("*").order("date_creation").execute().data

    for t in taches:
        with st.expander(f"🔧 {t['nom']}"):
            with st.form(key=f"m{t['id']}"):
                n = st.text_input("Nom", value=t["nom"])
                c1, c2 = st.columns(2)
                f = c1.number_input("Jours", 1, 365, t["frequence_jours"])
                p = c2.slider("Prio", 1, 5, t["priorite"])
                if st.form_submit_button("💾 Enregistrer"):
                    supabase.table("taches").update({
                        "nom": n, "frequence_jours": int(f), "priorite": int(p)
                    }).eq("id", t["id"]).execute()
                    st.rerun()
            if st.button("🗑️ Supprimer", key=f"d{t['id']}"):
                supabase.table("taches").delete().eq("id", t["id"]).execute()
                st.rerun()