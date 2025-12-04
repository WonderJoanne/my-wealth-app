import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V9.5", 
    page_icon="📱", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. CSS 樣式 (強制高對比) ---
st.markdown("""
<style>
    .stApp { background-color: #F4F7F6 !important; }
    
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #1F2937 !important;
        font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 頂部導航 */
    div[role="radiogroup"] {
        background-color: #1E3A8A !important;
        padding: 10px 5px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
    }
    div[role="radiogroup"] p {
        color: #FFFFFF !important; 
        font-size: 20px !important;
        font-weight: 500 !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: rgba(255,255,255,0.2) !important;
        border-radius: 8px;
    }

    /* 卡片通用樣式 */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #E5E7EB;
    }
    .mobile-card div, .mobile-card span, .mobile-card p {
        color: #1F2937 !important;
    }

    /* 輸入框與按鈕 */
    input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        border-color: #D1D5DB !important;
    }
    .stButton button {
        background-color: #2563EB !important;
        color: white !important;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] { color: #1F2937 !important; }
    .stProgress > div > div > div > div { background-color: #2563EB !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 ---
DEFAULT_RATES = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'rates' not in st.session_state: 
    st.session_state['rates'] = DEFAULT_RATES

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療", "簽證/機票"],
        "收入": ["薪資", "獎金", "股息", "副業", "投資收益"]
    }

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000},
        "美股儲蓄": {"type": "投資", "currency": "USD", "balance": 4200},
    }

if 'data' not in st.session_state:
    r1 = {
        "日期": datetime.date.today(),
        "帳戶": "隨身皮夾",
        "類型": "支出",
        "分類": "餐飲",
        "金額": 65000,
        "幣別": "VND",
        "備註": "Pho Bo"
    }
    r2 = {
        "日期": datetime.date.today(),
        "帳戶": "越南薪資",
        "類型": "收入",
        "分類": "薪資",
        "金額": 45000000,
        "幣別": "VND",
        "備註": "薪水"
    }
    st.session_state['data'] = pd.DataFrame([r1, r2])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{
        'name': '台北房貸', 
        'total': 10350000, 
        'remaining': 10350000, 
        'rate': 2.53, 
        'years': 30, 
        'grace_period': 24
    }]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 3. 導航列 ---
selected_tab = st.radio(
    "Mobile Nav",
    ["🏠 總覽", "➕ 記帳", "📊 分析", "💳 錢包", "⚙️ 設定"],
    horizontal=True,
    label_visibility="collapsed"
)

# --- 4. 計算邏輯 ---
total_assets_twd = 0
for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
    exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    bal = info['balance'] + inc - exp
    total_assets_twd += convert_to_twd(bal, info['currency'])
    
invest_val = 0
if not st.session_state['stocks'].empty:
    s_df = st.session_state['stocks']
    invest_val = (s_df['持有股數'] * s_df['目前市價']).sum()

loan_val = sum([l['remaining'] for l in st.session_state['loans']])
home_val = sum([l['total'] for l in st.session_state['loans']])
net_worth = total_assets_twd + invest_val + home_val - loan_val


# === 🏠 總覽頁 ===
if selected_tab == "🏠 總覽":
    # Hero Card HTML 生成
    hero_style = "background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 20px; color: white !important; margin-bottom: 20px;"
    hero_html = f"""
    <div style="{hero_style}">
        <p style="margin:0; opacity:0.8; font-size: 14px; color: white !important;">淨資產 (Net Worth)</p>
        <h1 style="margin:5px 0; color: white !important; font-size: 40px; font-weight: 700;">${net_worth:,.0f}</h1>
        <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:13px; color: white !important;">
            <span style="color: white !important;">資產: ${total_assets_twd+invest_val+home_val:,.0f}</span>
            <span style="color: white !important;">負債: ${loan_val:,.0f}</span>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="mobile
