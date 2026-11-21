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
            # Texte jours compact
            if t["retard"] > 0:
                icone, txt = "🔴", f"+{t['retard']}j"
            elif t["retard"] == 0:
                icone, txt = "🟡", "Auj"
            else:
                icone, txt = "🟢", f"{-t['retard']}j"

            # LIGNE COMPACTE : [icone] [nom + jours] [qui] [bouton]
            c1, c2, c3, c4 = st.columns([0.4, 3.5, 1.3, 1.0])

            with c1:
                st.markdown(f"<div style='font-size:1.2em'>{icone}</div>", unsafe_allow_html=True)

            with c2:
                st.markdown(f"**{t['nom']}** <span style='color:gray;font-size:0.9em'>{txt}</span>", unsafe_allow_html=True)

            with c3:
                qui = st.selectbox("Qui", ["Tifenn", "Gaël"], key=f"q{t['id']}",
                                 label_visibility="collapsed")

            with c4:
                if st.button("✓", key=f"b{t['id']}", help="Marquer comme faite"):
                    supabase.table("executions").insert({
                        "tache_id": t["id"],
                        "personne": qui,
                        "date_execution": datetime.now().isoformat()
                    }).execute()
                    st.rerun()

            # Détails cachés (très discret)
            with st.expander("ℹ️", expanded=False):
                c = st.columns(2)
                c[0].write(f"Fréquence: {t['freq']}j | Prio: {t['prio']}/5")
                if t["qui"]:
                    c[1].write(f"Dernière: {t['date'].strftime('%d/%m')} par {t['qui']}")
                else:
                    c[1].write(f"Jamais faite (créée {t['date'].strftime('%d/%m')})")

            st.divider()

# ==========================================
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