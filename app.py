import streamlit as st
from supabase import create_client
from datetime import datetime, date, time

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="Ménage", page_icon="🏠", layout="wide")
st.title("🏠 Ménage")

st.markdown("""
<style>
/* Laisser de la place sous la barre d'en-tête Streamlit */
.block-container {
    padding-top: 3.5rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
}

/* Empêcher les colonnes de s'empiler sur mobile */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.4rem !important;
    align-items: center !important;
}
[data-testid="stColumn"], [data-testid="column"] {
    min-width: 0 !important;
}
[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }



/* Bouton ✓ : large, vert, bien visible */
.stButton button[kind="primary"],
.stButton button[data-testid="stBaseButton-primary"] {
    min-height: 2.4rem !important;
    min-width: 0 !important;
    width: 200% !important;
    padding: 0.2rem !important;
    font-size: 1.3rem !important;
    font-weight: bold !important;
    background-color: #2e9e5b !important;
    border: none !important;
    color: white !important;
    border-radius: 0.6rem !important;
}
.stButton button[kind="primary"]:hover,
.stButton button[data-testid="stBaseButton-primary"]:hover {
    background-color: #24804a !important;
}
.stButton button[kind="primary"]:active,
.stButton button[data-testid="stBaseButton-primary"]:active {
    background-color: #1b6338 !important;

/* Menu Tifenn / Gaël : compact, texte toujours visible */
div[data-baseweb="select"] > div {
    min-height: 2.4rem !important;
    padding: 0 0.3rem !important;
}
div[data-baseweb="select"] div {
    overflow: visible !important;
    text-overflow: clip !important;
    font-size: 0.9rem !important;
}
/* Flèche ▼ plus discrète */
div[data-baseweb="select"] svg {
    width: 0.8rem !important;
}

/* Supprimer la marge sous le texte des tâches */
[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] p,
[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stMarkdown"] {
    margin-bottom: 0 !important;
}

/* Centrer le contenu de chaque colonne */
[data-testid="stColumn"] > div,
[data-testid="column"] > div {
    justify-content: center !important;
}

</style>
""", unsafe_allow_html=True)


# Ordre : À faire > Historique > Créer > Gestion
tab_a_faire, tab_historique, tab_creer, tab_gestion = st.tabs([
    "📋 À faire", "📜 Historique", "➕ Créer", "⚙️ Gérer"
])

# ==========================================
# ONGLET 1 : À FAIRE (ULTRA COMPACT)
# ==========================================
with tab_a_faire:
    taches = supabase.table("taches").select("*").execute().data
    executions = supabase.table("executions").select("*").order("date_execution", desc=True).execute().data

    # Dernière exécution par tâche
    derniere_exec = {}
    for e in executions:
        if e["tache_id"] not in derniere_exec:
            derniere_exec[e["tache_id"]] = e

    # Calcul tri
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
            if t["retard"] > 0:
                icone, txt, couleur = "🔴", f"+{t['retard']}j", "#d33"
            elif t["retard"] == 0:
                icone, txt, couleur = "🟡", "Auj.", "#c90"
            else:
                icone, txt, couleur = "🟢", f"{-t['retard']}j", "gray"

            # [pastille + nom + jours] [qui] [✓]
            c1, c2, c3 = st.columns([2.6, 1.7, 1.4], vertical_alignment="center")

            with c1:
                st.markdown(
                    f"<div style='display:flex;align-items:center;"
                    f"min-height:2.4rem;font-size:0.95em;line-height:1.2;"
                    f"transform:translateY(-8px)'>"
                    f"<span>{icone} <b>{t['nom']}</b> "
                    f"<span style='color:{couleur};font-size:0.85em'>{txt}</span>"
                    f"</span></div>",
                    unsafe_allow_html=True
                )

            with c2:
                qui = st.selectbox(
                    "Qui", ["Tifenn", "Gaël"], key=f"q{t['id']}",
                    label_visibility="collapsed"
                )

            with c3:
                if st.button("✓", key=f"b{t['id']}", type="primary"):
                    supabase.table("executions").insert({
                        "tache_id": t["id"],
                        "personne": qui,
                        "date_execution": datetime.now().isoformat()
                    }).execute()
                    st.rerun()
# ONGLET 2 : HISTORIQUE (MODIFIABLE)
# ==========================================
with tab_historique:
    st.header("📜 Historique")

    # Récupérer avec jointure
    histo = supabase.table("executions").select("*, taches(nom)").order("date_execution", desc=True).execute().data

    if not histo:
        st.info("Vide pour l'instant.")
    else:
        filtre = st.radio("Filtrer:", ["Tous", "Tifenn", "Gaël"], horizontal=True)
        if filtre != "Tous":
            histo = [e for e in histo if e["personne"] == filtre]

        for e in histo:
            d = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))
            nom = e["taches"]["nom"] if e.get("taches") else "❓"
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

                # Bouton supprimer l'entrée d'historique
                if st.button("🗑️ Supprimer cette entrée", key=f"del_{e['id']}"):
                    supabase.table("executions").delete().eq("id", e["id"]).execute()
                    st.rerun()

# ==========================================
# ONGLET 3 : CRÉER
# ==========================================
with tab_creer:
    with st.form("new", clear_on_submit=True):
        nom = st.text_input("Nom", placeholder="Aspirateur...")
        c1, c2 = st.columns(2)
        freq = c1.number_input("Tous les X jours", 1, 365, 7)
        prio = c2.slider("Priorité", 1, 5, 3)
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                supabase.table("taches").insert({
                    "nom": nom.strip(),
                    "frequence_jours": int(freq),
                    "priorite": int(prio)
                }).execute()
                st.success("Ajouté !")
                st.rerun()

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
                if st.form_submit_button("Enregistrer"):
                    supabase.table("taches").update({
                        "nom": n, "frequence_jours": int(f), "priorite": int(p)
                    }).eq("id", t["id"]).execute()
                    st.rerun()
            if st.button("🗑️ Supprimer", key=f"d{t['id']}"):
                supabase.table("taches").delete().eq("id", t["id"]).execute()
                st.rerun()