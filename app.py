import streamlit as st
from supabase import create_client
from datetime import datetime, date, time

st.set_page_config(page_title="Ménage", page_icon="🏠", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# Catégories dans l'ordre d'affichage
CATEGORIES = ["Salon", "Cuisine", "Salle de bains", "Chambre", "Bureau", "Jardin", "Autres"]
ICONES_CAT = {
    "Salon": "🛋️", "Cuisine": "🍽️ ", "Salle de bains": "🛁", "Chambre": "🛏️",
    "Bureau": "💻", "Jardin": "🌳", "Autres": "📦",
}

def cat_valide(c):
    """Renvoie la catégorie si elle existe, sinon 'Autres'."""
    return c if c in CATEGORIES else "Autres"

def freq_vers_bdd(f):
    """0 jour = sans fréquence (NULL dans Supabase)."""
    return int(f) if f and int(f) > 0 else None

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
}

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

/* Catégories plus compactes */
[data-testid="stExpander"] details summary {
    padding: 0.4rem 0.6rem !important;
    font-weight: bold !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0.2rem 0.4rem 0.4rem 0.4rem !important;
}

/* Bouton + rouge (passer en urgent) */
[class*="st-key-plus_"] button {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
}
/* Bouton − gris (annuler l'urgence) */
[class*="st-key-moins_"] button {
    background-color: #9ca3af !important;
    color: white !important;
    border: none !important;
}

/* --- Ligne de tâche sur mobile --- */
/* Colonnes des boutons ＋ / － / ✅ : largeur fixe * - TAILLE COLONNE BOUTONS*/
[data-testid="stColumn"]:has([class*="st-key-plus_"]),
[data-testid="stColumn"]:has([class*="st-key-moins_"]),
[data-testid="stColumn"]:has([class*="st-key-fait_"]) {
    flex: 0 0 2.0rem !important;
    width: 2.0rem !important;
    min-width: 2.0rem !important;
}
/* Colonne du menu "Qui" : largeur fixe */
[data-testid="stColumn"]:has([class*="st-key-qui_"]) {
    flex: 0 0 5.8rem !important;
    width: 5.8rem !important;
    min-width: 5.8rem !important;
}
/* Les boutons remplissent leur colonne */
[class*="st-key-plus_"] button, 
[class*="st-key-moins_"] button,
[class*="st-key-fait_"] button {
    width: 2.0rem !important;  /* ← largeur (même valeur que la colonne) */
    min-width: 2.0rem !important;  /* ← largeur (même valeur que la colonne) */
    min-height: 2.0rem !important;  /* ← hauteur  */
    padding: 0 !important;
}

/* TAILLE SYMBOLE BOUTONS*/
[class*="st-key-plus_"] button p,
[class*="st-key-moins_"] button p,
[class*="st-key-fait_"] button p {
    font-size: 1.3rem !important;     /* ← taille de l'icône */
}

/* Le nom prend la place restante et passe à la ligne si besoin */
[data-testid="stColumn"]:has([data-testid="stMarkdown"]) {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}
[data-testid="stColumn"] [data-testid="stMarkdown"] p {
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.25;
    margin: 0;
}

/* Garder les colonnes sur une seule ligne sur téléphone */
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.3rem !important; }
[data-testid="stColumn"], [data-testid="column"] { min-width: 0 !important; }
</style>
""", unsafe_allow_html=True)

# Ordre : À faire > Historique > Créer > Gestion
tab_a_faire, tab_historique, tab_creer, tab_gestion = st.tabs([
    "📋 À faire", "📜 Historique", "➕ Créer", "⚙️ Gérer"
])

# ==========================================
# ONGLET 1 : À FAIRE
# ==========================================
with tab_a_faire:
    taches = supabase.table("taches").select("*").execute().data
    execs = supabase.table("executions") \
        .select("tache_id, date_execution") \
        .order("date_execution", desc=True) \
        .execute().data

    # Dernière exécution de chaque tâche
    derniere = {}
    for ex in execs:
        if ex["tache_id"] not in derniere:
            derniere[ex["tache_id"]] = datetime.fromisoformat(
                ex["date_execution"].replace("Z", "+00:00")).date()

    # Calcul du retard
    for t in taches:
        t["urgent"] = bool(t.get("urgent"))
        d = derniere.get(t["id"])
        t["derniere"] = d
        t["jours"] = (date.today() - d).days if d else None
        freq = t.get("frequence_jours")
        if not freq:
            t["retard"] = None                  # sans fréquence
        elif d is None:
            t["retard"] = 9999                  # jamais faite = très en retard
        else:
            t["retard"] = t["jours"] - freq

    def cle_tri(t):
        if t["urgent"]:
            groupe = 0        # 🔴 urgentes
        elif t["retard"] is None:
            groupe = 3        # 🔵 sans fréquence
        elif t["derniere"] is None:
            groupe = 2        # 🟢 jamais faites
        else:
            groupe = 1        # retards / aujourd'hui / pas encore dues
        retard = t["retard"] if groupe == 1 else 0
        return (groupe, -retard, -t["priorite"])


    if not taches:
        st.info("Aucune tâche. Crée-en une dans l'onglet Créer.")

    for cat in CATEGORIES:
        liste = sorted([t for t in taches if cat_valide(t.get("categorie")) == cat],
                       key=cle_tri)
        if not liste:
            continue

        nb_urg = sum(t["urgent"] for t in liste)
        nb_retard = sum(1 for t in liste
                        if not t["urgent"]
                        and t["derniere"] is not None      # exclut les jamais faites
                        and t["retard"] is not None
                        and t["retard"] > 0)
        infos = []
        if nb_urg:
            infos.append(f"🔴 {nb_urg} à faire")
            if nb_retard:
                infos.append(f"{nb_retard} en retard")
        else:
            if nb_retard:
                infos.append(f"🔴 {nb_retard} en retard")
        
        titre = f"{ICONES_CAT[cat]} {cat}" + (f" — {' · '.join(infos)}" if infos else "")

        with st.expander(titre, expanded=nb_urg > 0):
            for t in liste:
                # Pastille + texte
                if t["urgent"]:
                    icone, txt = "🔴", "à faire !"
                elif t["retard"] is None:
                    icone, txt = "🔵", ""
                elif t["derniere"] is None:
                    icone, txt = "🟢", f"jamais"
                elif t["retard"] > 0:
                    icone, txt = "🔴", f"+{t['retard']}j"
                elif t["retard"] == 0:
                    icone, txt = "🟡", "auj."
                else:
                    icone, txt = "🟢", f"{-t['retard']}j"

                details = (f"Fréquence : {t['frequence_jours']} j" if t.get("frequence_jours")
                           else "Sans fréquence")
                details += " — Dernière fois : " + (
                    t["derniere"].strftime("%d/%m/%Y") if t["derniere"] else "jamais")

                c1, c2, c3, c0 = st.columns([5, 2, 1, 1], vertical_alignment="center")

                # Bouton + / −
                with c0:
                    if not t["urgent"]:
                        if st.button("＋", key=f"plus_{t['id']}", help="Passer en à faire"):
                            supabase.table("taches").update({"urgent": True}) \
                                .eq("id", t["id"]).execute()
                            st.rerun()
                    else:
                        if st.button("－", key=f"moins_{t['id']}", help="Annuler"):
                            supabase.table("taches").update({"urgent": False}) \
                                .eq("id", t["id"]).execute()
                            st.rerun()

                with c1:
                    st.markdown(f"{icone} **{t['nom']}** <small>{txt}</small>",
                                unsafe_allow_html=True, help=details)
                with c2:
                    qui = st.selectbox("Qui", ["Tifenn", "Gaël"],
                                       key=f"qui_{t['id']}",
                                       label_visibility="collapsed")
                with c3:
                    if st.button("✅", key=f"fait_{t['id']}", help="C'est fait"):
                        supabase.table("executions").insert({
                            "tache_id": t["id"],
                            "personne": qui,
                            "date_execution": datetime.now().isoformat()
                        }).execute()
                        if t["urgent"]:
                            supabase.table("taches").update({"urgent": False}) \
                                .eq("id", t["id"]).execute()
                        st.rerun()

# ==========================================
# ONGLET 2 : HISTORIQUE (MODIFIABLE)
# ==========================================
with tab_historique:
    st.header("📜 Historique")

    # Récupérer avec jointure (nom + catégorie de la tâche)
    histo = supabase.table("executions") \
        .select("*, taches(nom, categorie)") \
        .order("date_execution", desc=True) \
        .execute().data

    if not histo:
        st.info("Vide pour l'instant.")
    else:
        filtre = st.radio("Filtrer:", ["Tous", "Tifenn", "Gaël"], horizontal=True)
        if filtre != "Tous":
            histo = [e for e in histo if e["personne"] == filtre]
        filtre_cat = st.selectbox("Catégorie", ["Toutes"] + CATEGORIES)
        if filtre_cat != "Toutes":
            histo = [e for e in histo
                     if cat_valide((e.get("taches") or {}).get("categorie")) == filtre_cat]

        for e in histo:
            d = datetime.fromisoformat(e["date_execution"].replace("Z", "+00:00"))

            if e.get("taches"):
                nom = e["taches"]["nom"]
                cat = cat_valide(e["taches"].get("categorie"))
            else:
                nom, cat = "❓", "Autres"

            label = (f"{d.strftime('%d/%m/%Y')} — {ICONES_CAT[cat]} {cat} · "
                     f"{nom} — {e['personne']}")

            with st.expander(label):
                with st.form(key=f"edit_{e['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_date = st.date_input("Date", value=d.date(),
                                                 format="DD/MM/YYYY",
                                                 key=f"date_{e['id']}")
                    with c2:
                        new_pers = st.selectbox(
                            "Qui a fait ?", ["Tifenn", "Gaël"],
                            index=0 if e["personne"] == "Tifenn" else 1,
                            key=f"pers_{e['id']}"
                        )

                    if st.form_submit_button("💾 Modifier"):
                        # On garde l'heure d'origine (invisible) pour conserver l'ordre du tri
                        new_dt = datetime.combine(new_date, d.time()).isoformat()
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
        categorie = st.selectbox("Catégorie", CATEGORIES)
        c1, c2 = st.columns(2)
        freq = c1.number_input("Tous les X jours (0 = sans fréquence)", 0, 365, 7)
        prio = c2.slider("Priorité", 1, 5, 3)
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                supabase.table("taches").insert({
                    "nom": nom.strip(),
                    "frequence_jours": freq_vers_bdd(freq),
                    "priorite": int(prio),
                    "categorie": categorie
                }).execute()
                st.success("Ajouté !")
                st.rerun()

# ==========================================
# ONGLET 4 : GÉRER
# ==========================================
with tab_gestion:
    st.header("⚙️ Gérer les tâches")
    taches = supabase.table("taches").select("*").order("date_creation").execute().data

    for cat in CATEGORIES:
        taches_cat = [t for t in taches if cat_valide(t.get("categorie")) == cat]
        if not taches_cat:
            continue

        st.subheader(f"{ICONES_CAT[cat]} {cat}")
        for t in taches_cat:
            pastille = "🔵 " if not t.get("frequence_jours") else ""
            with st.expander(f"🔧 {pastille}{t['nom']}"):
                with st.form(key=f"m{t['id']}"):
                    n = st.text_input("Nom", value=t["nom"])
                    cat_t = st.selectbox(
                        "Catégorie", CATEGORIES,
                        index=CATEGORIES.index(cat_valide(t.get("categorie"))),
                        key=f"cat{t['id']}"
                    )
                    c1, c2 = st.columns(2)
                    f = c1.number_input("Jours (0 = sans)", 0, 365,
                                        t.get("frequence_jours") or 0)
                    p = c2.slider("Prio", 1, 5, t["priorite"])
                    if st.form_submit_button("Enregistrer"):
                        supabase.table("taches").update({
                            "nom": n, "frequence_jours": freq_vers_bdd(f),
                            "priorite": int(p), "categorie": cat_t
                        }).eq("id", t["id"]).execute()
                        st.rerun()
                if st.button("🗑️ Supprimer", key=f"d{t['id']}"):
                    supabase.table("taches").delete().eq("id", t["id"]).execute()
                    st.rerun()