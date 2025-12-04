import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta

# --- 0. 頁面設定 (強制寬螢幕) ---
st.set_page_config(
    page_title="AssetFlow V16", 
    page_icon="📅", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session ---
if 'current_page' not in st.session_state: st.session_state.current_page = "總覽"

# --- 2. CSS 極致深色模式 (解決看不清楚的問題) ---
st.markdown("""
<style>
    /* 強制深色主題 */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* 所有文字強制反白 */
    h1, h2, h3, p, span, div, label, li {
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* === 輸入框與日期修復 (關鍵) === */
    /* 輸入框背景改深灰，文字改白 */
    input, textarea, select {
        background-color: #1C1C1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
    /* 下拉選單 */
    div[data-baseweb="select"] > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border-color: #333333 !important;
    }
    /* 日期選擇器文字顏色 */
    input[type="text"] {
        color: #FFFFFF !important; 
    }
    /* 修正日期彈出視窗的對比度 */
    div[data-baseweb="calendar"] {
        background-color: #1C1C1E !important;
    }
    div[data-baseweb="calendar"] button {
        color: white !important;
    }

    /* === 導航列 (按鈕矩陣) === */
    .stButton button {
        background-color: #1C1C1E !important;
        color: #AAAAAA !important;
        border: 1px solid #333333;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    /* 選中狀態的高亮 */
    .stButton button:focus, .stButton button:active, .stButton button:hover {
        border-color: #FF9F0A !important;
        color: #FF9F0A !important;
        background-color: #2C2C2E !important;
    }

    /* === 交易列表卡片 (模仿截圖) === */
    .tx-card {
        background-color: #1C1C1E;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #333;
    }
    .tx-icon {
        font-size: 24px;
        margin-right: 15px;
        width: 40px;
        text-align: center;
    }
    .tx-details { flex-grow: 1; }
    .tx-amount { font-weight: bold; font-size: 16px; }
    .income-text { color: #32D74B !important; } /* 綠色 */
    .expense-text { color: #FF453A !important; } /* 紅色 */
    
    /* 資產卡片 */
    .asset-card {
        background-color: #1C1C1E;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    
    /* 統計數字 */
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    /* Expander 標題 */
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療", "固定扣款"],
        "收入": ["薪資", "獎金", "股息", "副業"]
    }

# 固定收支 (Recurring) 初始化
if 'recurring' not in st.session_state:
    st.session_state['recurring'] = [
        {"name": "Netflix", "amount": 390, "type": "支出", "cat": "固定扣款", "acct": "玉山信用卡"},
        {"name": "房租/房貸", "amount": 25000, "type": "支出", "cat": "居住", "acct": "台幣薪轉"},
    ]

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000, "icon": "🏦"},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000, "icon": "🇻🇳"},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000, "icon": "💵"},
        "玉山信用卡": {"type": "信用卡", "currency": "TWD", "balance": -5000, "icon": "💳"},
    }

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "河粉"}
    st.session_state['data'] = pd.DataFrame([r1])

if 'loans' not in st.session_state:
    st.session_state['loans'] = {
        "自住屋房貸": {
            "total": 10350000, "rate": 2.53, "years": 30, "grace_period": 2,
            "start_date": datetime.date(2025, 11, 1), "remaining": 10350000, "paid_principal": 0
        }
    }

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 4. 導航列 (深色按鈕) ---
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    def nav_btn(col, text, icon, page):
        label = f"{icon}\n{text}"
        if col.button(label, key=f"n_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

    nav_btn(c1, "帳本", "📅", "總覽") # 改名為帳本，符合天天記帳習慣
    nav_btn(c2, "記帳", "➕", "記帳")
    nav_btn(c3, "分析", "📊", "分析")
    nav_btn(c4, "錢包", "💳", "錢包")
    nav_btn(c5, "設定", "⚙️", "設定")

# --- 5. 計算核心 ---
total_assets_twd = 0
total_liability_twd = 0
for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
    exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    bal = info['balance'] + inc - exp
    twd_val = convert_to_twd(bal, info['currency'])
    if twd_val >= 0: total_assets_twd += twd_val
    else: total_liability_twd += abs(twd_val)
    
invest_val = 0
if not st.session_state['stocks'].empty:
    s_df = st.session_state['stocks']
    invest_val = (s_df['持有股數'] * s_df['目前市價']).sum()

loan_rem_total = sum([l['remaining'] for l in st.session_state['loans'].values()])
home_val_total = sum([l['total'] for l in st.session_state['loans'].values()])
real_assets = total_assets_twd + invest_val + home_val_total
real_liabilities = total_liability_twd + loan_rem_total
net_worth = real_assets - real_liabilities

# === 📅 帳本總覽 (模仿天天記帳首頁) ===
if st.session_state.current_page == "總覽":
    
    # 上半部：日期選擇與當日統計
    c_date, c_stat = st.columns([1, 2])
    with c_date:
        st.markdown("### 選擇日期")
        # 這裡的日期選擇器現在背景是深色的，文字是白色的
        selected_date = st.date_input("查看哪一天的帳？", datetime.date.today(), label_visibility="collapsed")
    
    # 篩選當日資料
    df_day = st.session_state['data'][st.session_state['data']['日期'] == selected_date]
    day_inc = df_day[df_day['類型']=='收入'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    day_exp = df_day[df_day['類型']=='支出'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    
    with c_stat:
        st.markdown(f"""
        <div style="background-color:#1C1C1E; padding:15px; border-radius:10px; display:flex; justify-content:space-around; align-items:center; border:1px solid #333;">
            <div style="text-align:center;">
                <div style="color:#888; font-size:12px;">{selected_date.strftime('%Y-%m-%d')}</div>
                <div style="font-weight:bold; font-size:14px;">當日收支</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#32D74B; font-weight:bold; font-size:20px;">+{day_inc:,.0f}</div>
                <div style="color:#888; font-size:12px;">收入</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#FF453A; font-weight:bold; font-size:20px;">-{day_exp:,.0f}</div>
                <div style="color:#888; font-size:12px;">支出</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 下半部：交易列表
    if df_day.empty:
        st.info("📭 這一天沒有任何紀錄")
    else:
        for idx, row in df_day.iterrows():
            icon = "💰"
            if row['分類'] in ['餐飲', '食品']: icon = "🍜"
            elif row['分類'] in ['交通']: icon = "🚕"
            elif row['分類'] in ['購物']: icon = "🛍️"
            elif row['分類'] in ['房貸']: icon = "🏠"
            
            amt_color = "income-text" if row['類型']=='收入' else "expense-text"
            sign = "+" if row['類型']=='收入' else "-"
            
            st.markdown(f"""
            <div class="tx-card">
                <div style="display:flex; align-items:center;">
                    <div class="tx-icon">{icon}</div>
                    <div class="tx-details">
                        <div style="font-size:16px; font-weight:bold;">{row['分類']}</div>
                        <div style="font-size:12px; color:#888;">{row['帳戶']} | {row['備註']}</div>
                    </div>
                </div>
                <div class="tx-amount {amt_color}">{sign} {row['幣別']} {row['金額']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

# === ➕ 記帳 (新增固定收支功能) ===
elif st.session_state.current_page == "記帳":
    
    tab1, tab2 = st.tabs(["📝 一般記帳", "🔄 固定收支 (訂閱)"])
    
    with tab1:
        tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("日期", datetime.date.today())
        
        acct_options = list(st.session_state['accounts'].keys())
        acct_name = c2.selectbox("帳戶", acct_options if acct_options else ["無帳戶"])
        if not acct_options: st.stop()
        
        curr = st.session_state['accounts'][acct_name]['currency']
        cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
        tx_cat = st.selectbox("分類", cats)
        
        tx_amt = st.number_input(f"金額 ({curr})", step=1000.0 if curr=="VND" else 1.0)
        tx_note = st.text_input("備註")

        if st.button("確認記帳", type="primary", use_container_width=True):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("已儲存！")

    with tab2:
        st.caption("一鍵加入每個月的固定支出 (如 Netflix, 房租)")
        
        # 顯示固定收支列表
        for item in st.session_state['recurring']:
            c_info, c_act = st.columns([3, 1])
            with c_info:
                st.markdown(f"**{item['name']}** - ${item['amount']:,} ({item['type']})")
                st.caption(f"{item['acct']} | {item['cat']}")
            with c_act:
                if st.button("入帳", key=f"rec_{item['name']}"):
                    # 抓取對應帳戶的幣別
                    rec_curr = st.session_state['accounts'].get(item['acct'], {}).get('currency', 'TWD')
                    new_rec = {
                        "日期": datetime.date.today(),
                        "帳戶": item['acct'],
                        "類型": item['type'],
                        "分類": item['cat'],
                        "金額": item['amount'],
                        "幣別": rec_curr,
                        "備註": f"固定: {item['name']}"
                    }
                    st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
                    st.toast(f"{item['name']} 已入帳！")

        st.markdown("---")
        with st.expander("➕ 新增固定項目"):
            r_name = st.text_input("名稱 (如 Netflix)")
            r_amt = st.number_input("金額", 0)
            r_type = st.selectbox("類型", ["支出", "收入"], key="r_type")
            r_acct = st.selectbox("預設扣款帳戶", acct_options, key="r_acct")
            r_cat = st.selectbox("預設分類", cats, key="r_cat")
            
            if st.button("新增模版"):
                st.session_state['recurring'].append({
                    "name": r_name, "amount": r_amt, "type": r_type, "cat": r_cat, "acct": r_acct
                })
                st.rerun()

# === 📊 分析 ===
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    df = st.session_state['data'].copy()
    if df.empty: st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        st.bar_chart(df.groupby('類型')['金額(TWD)'].sum())
        st.dataframe(df, use_container_width=True)

# === 💳 錢包 ===
elif st.session_state.current_page == "錢包":
    st.subheader("我的資產")
    
    # 總資產摘要 (Dark Mode Card)
    st.markdown(f"""
    <div style="background-color:#1C1C1E; padding:20px; border-radius:15px; margin-bottom:20px; border:1px solid #333;">
        <div style="color:#888; font-size:14px;">淨資產 (Net Worth)</div>
        <div style="color:white; font-size:36px; font-weight:bold;">${net_worth:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # 帳戶列表
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        
        # 負數顯示紅色
        val_color = "#FF453A" if bal < 0 else "#FFFFFF"
        
        st.markdown(f"""
        <div class="asset-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:24px; margin-right:10px;">{info.get('icon','💰')}</span>
                <span style="font-weight:bold; font-size:18px;">{name}</span>
            </div>
            <div style="text-align:right;">
                <div style="color:{val_color}; font-weight:bold; font-size:18px;">{bal:,.0f}</div>
                <div style="color:#666; font-size:12px;">{info['currency']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# === ⚙️ 設定 ===
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    st.write("匯率設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
