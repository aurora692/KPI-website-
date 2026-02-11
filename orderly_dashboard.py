import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date

# --- CONFIGURATION ---
st.set_page_config(page_title="Orderly KPIs", page_icon="🦅", layout="wide")
st.markdown("""
<style>
    .metric-container { background-color: #1E1E1E; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px; }
    [data-testid="stToolbar"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 1. GOOGLE SHEETS (HISTORY) ---
SHEET_ID = "1ydkI-hz6BP8mCY1pF8_Xuw-383HycWzxO3qzboSqYl0" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_history():
    try:
        if "YOUR_GOOGLE_SHEET_ID" in SHEET_ID:
            return pd.DataFrame([
                {"date": "2026-02-01", "revenue": 14000, "active_users": 1100, "new_users": 50, "omni_tvl": 11.2},
                {"date": "2026-02-08", "revenue": 15000, "active_users": 1200, "new_users": 60, "omni_tvl": 10.9}
            ])
        df = pd.read_csv(SHEET_URL)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    except: return pd.DataFrame()

# --- 2. LIVE DATA (API) ---
@st.cache_data(ttl=600)
def get_live_data():
    data = {"price": 0.055, "rank_lama": 39, "rank_cmc": 799}
    try:
        cg = requests.get("https://api.coingecko.com/api/v3/coins/orderly-network", timeout=3).json()
        data["price"] = cg["market_data"]["current_price"]["usd"]
        data["rank_cmc"] = cg["market_cap_rank"]
        
        lama = requests.get("https://api.llama.fi/overview/dexs?excludeTotalDataChart=true&dataType=dailyVolume", timeout=5).json()
        derivs = [p for p in lama['protocols'] if p.get('category') == "Derivatives"]
        derivs.sort(key=lambda x: x.get('total24h', 0) or 0, reverse=True)
        for i, p in enumerate(derivs):
            if "Orderly" in p['name']:
                data["rank_lama"] = i + 1
                break
    except: pass
    return data


# --- 3. OMNIVAULT CHART DATA ---
def get_omnivault_chart_data():
    dates = pd.date_range(end=datetime.today(), periods=8, freq="W-MON")
    data = []
    base = [13.7, 12.3, 11.0, 10.6, 10.4, 9.9, 9.5, 9.2]
    kronos = [1.9, 2.0, 1.8, 1.5, 0.9, 0.8, 0.8, 0.8]
    smaug = [0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.7, 0.9]
    
    for i, d in enumerate(dates):
        d_str = d.strftime("%Y-%m-%d")
        idx = i if i < len(base) else -1
        data.append({"Date": d_str, "Type": "Orderly OmniVault", "TVL": base[idx]})
        data.append({"Date": d_str, "Type": "Kronos QLS", "TVL": kronos[idx]})
        data.append({"Date": d_str, "Type": "Smaug", "TVL": smaug[idx]})
    return pd.DataFrame(data)

# --- MAIN APP ---
st.title("🦅 Orderly Network KPI Dashboard")

# Load Data
df_hist = load_history()
live = get_live_data()
df_omni = get_omnivault_chart_data()

# Sidebar Input
with st.sidebar:
    st.header("📝 Daily Update")
    last_rec = df_hist.iloc[-1] if not df_hist.empty else {"revenue": 15000, "active_users": 1200, "new_users": 50}
    
    with st.form("input"):
        d_date = st.date_input("Date", date.today())
        in_rev = st.number_input("Revenue", value=float(last_rec.get('revenue', 15000)))
        in_active = st.number_input("Active Users", value=int(last_rec.get('active_users', 1200)))
        in_new = st.number_input("New Users", value=int(last_rec.get('new_users', 50)))
        submitted = st.form_submit_button("Update View")

# Calculate Display Data
current_revenue = in_rev
latest_omni_tvl = df_omni[df_omni['Date'] == df_omni['Date'].max()]['TVL'].sum()

# ROW 1: HEADLINES
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("Omnivault TVL", f"${latest_omni_tvl:.2f}M")
with c2: st.metric("$ORDER Price", f"${live['price']:.4f}")
with c3: st.metric("CMC Rank", f"#{live['rank_cmc']}")
with c4: st.metric("DeFiLlama Rank", f"#{live['rank_lama']}")
with c5: st.metric("Daily Revenue", f"${current_revenue:,.0f}")

# ROW 2: OMNIVAULT STACKED CHART
st.subheader("📊 OmniVault TVL - Weekly Stack")
fig = px.bar(df_omni, x="Date", y="TVL", color="Type", 
             color_discrete_map={"Orderly OmniVault": "#F4D03F", "Kronos QLS": "#9B59B6", "Smaug": "#58D68D"},
             text_auto='.1f')
fig.update_layout(plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E", font_color="white", height=350)
st.plotly_chart(fig, use_container_width=True)

# ROW 3: USER METRICS
st.subheader("👥 User Growth")
u1, u2 = st.columns(2)
with u1: 
    st.metric("Active Users", f"{in_active:,}")
with u2: 
    st.metric("New Users", f"{in_new:,}")

# ROW 4: HISTORY TRENDS
st.subheader("📈 Historical Trends")
if not df_hist.empty and 'revenue' in df_hist:
    st.line_chart(df_hist.set_index("date")[["revenue", "active_users", "new_users"]])
else:
    st.info("Connect Google Sheet to see historical trends.")

