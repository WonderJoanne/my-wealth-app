import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面與手機優化設定 ---
st.set_page_config(
    page_title="AssetFlow V9.3", 
    page_icon="📱", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. CSS 視覺修復 (強制高對比配色) ---
st.markdown("""
<style>
    /* 1. 全局強制設定 */
    .stApp {
        background-color: #F4F7F6 !important;
    }
    
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #1F2937 !important;
        font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 2. 頂部導航列 */
    div[role="radiogroup"] {
        background-color: #1E3A8A !important;
        padding: 10px 5px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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

    /* 3. 卡片樣式 */
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

    /* 4. 元件優化 */
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
    
    div[data-testid="stMetricValue"] {
        color: #1F2937 !important;
    }
    
    .stProgress > div > div > div > div {
        background-color: #2563EB !important;
    }
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
    # 使用多行定義避免錯誤
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

# --- 3. 手機版導航列 ---
selected_tab = st.radio(
    "Mobile Nav",
    ["🏠 總覽", "➕ 記帳", "📊 分析", "💳 錢包", "⚙️ 設定"],
    horizontal=True,
    label_visibility="collapsed"
)

# --- 4. 內容區塊計算 ---

total_assets_twd = 0
for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    # 分開計算避免單行太長
    inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
    exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    bal = info['balance'] + inc - exp
    total_assets_twd += convert_to_twd(bal, info['currency'])
    
invest_val = 0
if not st.session_state['stocks'].empty:
    # 安全計算
    s_df = st.session_state['stocks']
    invest_val = (s_df['持有股數'] * s_df['目前市價']).sum()

loan_val = sum([l['remaining'] for l in st.session_state['loans']])
home_val = sum([l['total'] for l in st.session_state['loans']])
net_worth = total_assets_twd + invest_val + home_val - loan_val


# === 🏠 總覽 ===
if selected_tab == "🏠 總覽":
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 20px; color: white !important; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);">
        <p style="margin:0; opacity:0.8; font-size: 14px; color: white !important;">淨資產 (Net Worth)</p>
        <h1 style="margin:5px 0; color: white !important; font-size: 40px; font-weight: 700;">$""" + f"{net_worth:,.0f}" + """</h1>
        <div style="display:flex; justify-content:space-between; margin-top:10px; opacity:0.9; font-size:13px; color: white !important;">
            <span style="color: white !important;">資產: $""" + f"{total_assets_twd+invest_val+home_val:,.0f}" + """</span>
            <span style="color: white !important;">負債: $""" + f"{loan_val:,.0f}" + """</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="mobile-card" style="text-align:center;">
            <div style="font-size:12px; color:#6B7280 !important;">現金部位</div>
            <div style="font-size:20px; font-weight:bold; color:#059669 !important;">${total_assets_twd:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="mobile-card" style="text-align:center;">
            <div style="font-size:12px; color:#6B7280 !important;">投資現值</div>
            <div style="font-size:20px; font-weight:bold; color:#2563EB !important;">${invest_val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("近期交易")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    for i, row in df_recent.iterrows():
        # 安全取得圖示
        icon = '💰'
        if row['分類'] in ['餐飲', '食品']: icon = '🍜'
        elif row['分類'] in ['交通']: icon = '🚌'
        
        # 安全取得顏色
        color = '#DC2626' if row['類型']=='支出' else '#059669'

        with st.container():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid #E5E7EB;">
                <div style="display:flex; align-items:center;">
                    <div style="background:#EFF6FF; width:42px; height:42px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px;">
                        {icon}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:16px; color:#111827 !important;">{row['分類']}</div>
                        <div style="font-size:12px; color:#6B7280 !important;">{row['備註']} · {row['帳戶']}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:bold; color:{color} !important;">
                        {row['幣別']} {row['金額']:,.0f}
                    </div>
                    <div style="font-size:11px; color:#9CA3AF !important;">{row['日期'].strftime('%m/%d')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# === ➕ 記帳 ===
elif selected_tab == "➕ 記帳":
    st.subheader("新增交易")
    
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True, label_visibility="collapsed")
    
    with st.container(border=True):
        c_date, c_acct = st.columns([1, 1.5])
        tx_date = c_date.date_input("日期", datetime.date.today())
        acct_name = c_acct.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']

        st.markdown(f"<p style='margin-bottom:5px; font-size:14px; color:#6B7280 !important;'>金額 ({curr})</p>", unsafe_allow_html=True)
        tx_amt = st.number_input("金額", min_value=
