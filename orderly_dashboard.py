import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Orderly KPIs", page_icon="🦅", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 14px; color: #888; }
    .metric-value { font-size: 28px; font-weight: bold; color: #FFF; }
</style>
""", unsafe_allow_html=True)

# --- 🔌 METABASE INTEGRATION (V2) ---
METABASE_CONFIG = {
    "enabled": False,  # Set to True when you have credentials
    "url": "https://metabase.orderly.network",  # REPLACE THIS
    "username": "your_email@orderly.network",   # REPLACE THIS
    "password": "your_password",                # REPLACE THIS
    "questions": {
        "revenue": 123,       
        "active_users": 124,  
        "market_share": 125   
    }
}

def get_metabase_token():
    """Authenticates with Metabase and returns a Session ID"""
    if not METABASE_CONFIG["enabled"]: return None
    try:
        res = requests.post(f"{METABASE_CONFIG['url']}/api/session", json={
            "username": METABASE_CONFIG["username"],
            "password": METABASE_CONFIG["password"]
        }, timeout=5)
        if res.status_code == 200:
            return res.json()["id"]
    except Exception as e:
        st.sidebar.error(f"Metabase Auth Failed: {e}")
    return None

def get_metabase_result(session_id, question_id):
    """Fetches the latest value from a specific Metabase Question"""
    if not session_id: return None
    try:
        headers = {"X-Metabase-Session": session_id}
        res = requests.post(f"{METABASE_CONFIG['url']}/api/card/{question_id}/query/json", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                return list(data[0].values())[0] 
    except:
        pass
    return None

# --- PUBLIC DATA FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_crypto_prices():
    """Fetches $ORDER price and rank from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/orderly-network"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            d = res.json()
            return {
                "price": d["market_data"]["current_price"]["usd"],
                "rank": d["market_cap_rank"],
                "change": d["market_data"]["price_change_percentage_24h"]
            }
    except:
        pass
    return {"price": 0.15, "rank": 180, "change": 0}

@st.cache_data(ttl=3600)
def get_defillama_perps():
    return 301_000_000_000  # Placeholder

# --- MAIN APP ---

st.title("🦅 Orderly Network KPI Dashboard")
st.caption("Data Mode: Hybrid (Public APIs + Metabase/Manual)")

# 1. SIDEBAR
with st.sidebar:
    st.header("⚙️ Data Source")
    mb_session = get_metabase_token()
    
    if mb_session:
        st.success(f"✅ Connected to Metabase")
    else:
        st.warning("⚠️ Metabase Not Configured")
        st.markdown("---")
        st.write("**Manual Override:**")
        with st.form("manual_entry"):
            in_revenue = st.number_input("Avg Daily Revenue ($)", 15000)
            in_users = st.number_input("Daily Active Users", 1200)
            in_share = st.number_input("Market Share (%)", 2.5)
            in_dexs = st.number_input("Graduated DEXs", 146)
            st.form_submit_button("Update")

# 2. FETCH VALUES
mb_revenue = get_metabase_result(mb_session, METABASE_CONFIG["questions"]["revenue"]) if mb_session else None
mb_users = get_metabase_result(mb_session, METABASE_CONFIG["questions"]["active_users"]) if mb_session else None

val_revenue = mb_revenue if mb_revenue else (locals().get('in_revenue') or 15000)
val_users = mb_users if mb_users else (locals().get('in_users') or 1200)
val_share = locals().get('in_share') or 2.5
val_dexs = locals().get('in_dexs') or 146

public_data = get_crypto_prices()
global_vol = get_defillama_perps()

# 3. DASHBOARD ROW 1
st.subheader("🌍 Market & Token")
c1, c2, c3, c4 = st.columns(4)
c1.metric("DeFi Perps Vol", f"${global_vol/1e9:.1f}B", "+24%")
c2.metric("$ORDER Price", f"${public_data['price']:.3f}", f"{public_data['change']:.2f}%")
c3.metric("CMC Rank", f"#{public_data['rank']}")
c4.metric("Omnivault TVL", "$10.9M", "-2%")

# 4. DASHBOARD ROW 2
st.subheader("📈 Orderly Internal")
c5, c6, c7, c8 = st.columns(4)
c5.metric("Graduated DEXs", val_dexs, "+4")
c6.metric("Daily Revenue", f"${val_revenue:,.0f}")
c7.metric("Active Users", f"{val_users:,}")
c8.metric("Market Share", f"{val_share}%")

st.divider()
if mb_session:
    st.info("⚡ Internal metrics are automatically synced from Metabase.")
else:
    st.info("ℹ️ Currently using manual data. Edit `orderly_dashboard.py` to enable Metabase auto-sync.")

