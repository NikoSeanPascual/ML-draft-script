import streamlit as st
import json
import os
from engine import MLBBDraftEngine

st.set_page_config(page_title="MLBB Pro Draft Engine", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .ally-box { padding: 12px; border-radius: 8px; background-color: #1e293b; border-left: 5px solid #3b82f6; margin-bottom: 10px; }
    .enemy-box { padding: 12px; border-radius: 8px; background-color: #1e293b; border-left: 5px solid #ef4444; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

if 'engine' not in st.session_state:
    st.session_state.engine = MLBBDraftEngine()

draft = st.session_state.engine
master_hero_list = sorted([h['name'] for h in draft.heroes.values()])

# 🔄 LINK INTEGRATION: Read current hardware values from state log file
STATE_FILE = "draft_state.json"
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            shared_state = json.load(f)
            # Inject background scans directly into active UI instances
            draft.enemies = set(shared_state.get("enemies", []))
            draft.allies = set(shared_state.get("allies", []))
            draft.banned = set(shared_state.get("banned", []))
    except Exception:
        pass

# Format back to display components mapping
default_allies = [draft.heroes[h]['name'] for h in draft.allies if h in draft.heroes]
default_enemies = [draft.heroes[h]['name'] for h in draft.enemies if h in draft.heroes]
default_bans = [draft.heroes[h]['name'] for h in draft.banned if h in draft.heroes]

st.title("⚔️ MLBB Esports Draft Optimizer")
st.markdown("Automated Hardware Tracking Engine Active")

# Add a manual UI sync reload trigger button for clean rendering updates
if st.button("🔄 Sync Live Device Detections"):
    st.rerun()

st.subheader("🚫 Tournament Ban Phase")
ban_options = [h for h in master_hero_list]
bans = st.multiselect("Banned heroes:", options=ban_options, default=default_bans, key="ban_picks")

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="ally-box"><h3>🔵 Your Team (Allies)</h3></div>', unsafe_allow_html=True)
    ally_options = [h for h in master_hero_list]
    allies = st.multiselect("Your team composition:", options=ally_options, default=default_allies, key="ally_picks")

with col2:
    st.markdown('<div class="enemy-box"><h3>🔴 Enemy Team</h3></div>', unsafe_allow_html=True)
    enemy_options = [h for h in master_hero_list]
    enemies = st.multiselect("Opponent composition:", options=enemy_options, default=default_enemies, key="enemy_picks")

# Save modifications back
draft.allies = {h.lower() for h in allies}
draft.enemies = {h.lower() for h in enemies}
draft.banned = {h.lower() for h in bans}

st.divider()

st.subheader("📊 Allied Team Role Coverage")
filled_roles = draft.get_filled_roles()
all_roles = ["TANK_ENGAGERS", "FIGHTERS_EXP", "ASSASSINS_JUNGLERS", "MAGES_MID", "MARKSMEN_GOLD", "SUPPORTS"]

role_cols = st.columns(len(all_roles))
for idx, role in enumerate(all_roles):
    with role_cols[idx]:
        role_clean = role.replace("_", " ").title()
        if role in filled_roles:
            st.success(f"✅ {role_clean}")
        else:
            st.error(f"❌ {role_clean}")

st.divider()

st.subheader("💡 Strategic Pick Recommendations")
role_filter = st.selectbox("Filter suggestions by specific vacant role:", ["All Roles"] + all_roles)
target_role = None if role_filter == "All Roles" else role_filter

recs = draft.calculate_recommendations(target_role)

if recs:
    filtered_recs = [r for r in recs if
                     r['name'].lower() not in draft.allies and r['name'].lower() not in draft.enemies and r[
                         'name'].lower() not in draft.banned]

    for i, rec in enumerate(filtered_recs[:5]):
        score = rec['score']
        badge = "🔥 High Value Counter/Synergy" if score > 2.0 else "⚖️ Safe Neutral Pick" if score >= 0.0 else "⚠️ Caution"

        with st.expander(f"#{i + 1} {rec['name']} | Match Score: {score} pts ({badge})"):
            st.markdown(f"**Primary Position:** `{rec['primary_role'].replace('_', ' ').title()}`")
            if rec['secondary_roles']:
                st.markdown(
                    f"**Flex Options:** `{', '.join([r.replace('_', ' ').title() for r in rec['secondary_roles']])}`")
            st.markdown(f"**Mechanical Archetype:** `{rec['archetype'].replace('_', ' ').title()}`")
            if rec['reasons']:
                st.markdown("**Draft Analysis:**")
                for reason in set(rec['reasons']):
                    st.write(f"- {reason}")
else:
    st.info("Configure your layout selection items above to see real-time suggestions.")
