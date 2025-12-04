import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V15.2", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "錢包"

# --- 🚨 自動修復資料結構 ---
if 'loans' in st.session_state and isinstance(st.session_state['loans'], list):
    st.session_state['loans'] = {
        "自住屋房貸": {
            "total": 10350000, "rate": 2.53, "years": 30, "grace_period": 2,
            "start_date": datetime.date(2025, 11, 1), "remaining": 10350000, "paid_principal": 0
        }
    }

# --- 2. CSS 修復 (高對比 & 修正圖示衝突) ---
st.markdown("""
<style>
    /* 1. 背景強制為淺灰，文字強制為深黑 */
    .stApp { background-color: #F0F2F6 !important; }
    
    /* 只針對標題和段落改色，不碰 Icon */
    h1, h2, h3, p, span, div, label {
        color: #111827 !important; 
    }
    
    /* 2. 隱藏預設側邊欄 */
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 3. 卡片設計 (高對比白底) */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        border: 1px solid #E5E7EB; /* 灰色邊框 */
    }
    
    /* 4. 按鈕優化 (深藍色，清楚) */
    .stButton button {
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }
    
    /* 5. 輸入框優化 (白底深框) */
    div[data-baseweb="input"] {
        background-color: white !important;
        border: 1px solid #9CA3AF !important;
        border-radius: 8px;
    }
    div[data-baseweb="select"] {
        background-color: white !important;
        border-radius: 8px;
    }

    /* 6. 修正 Expander 標題看不見的問題 */
    .streamlit-expanderHeader {
        background-color: white !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
    }
    
    /* 7. 特殊文字顏色 */
    .highlight-red { color: #DC2626 !important; font-weight: bold; }
    .highlight-green { color: #059669 !important; font-weight: bold; }
    .sub-text { color: #6B7280 !important; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": ["房貸", "餐飲", "交通", "購物", "居住", "娛樂", "醫療"],
        "收入": ["薪資", "獎金", "股息", "副業"]
    }

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000, "icon": "🏦"},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000, "icon": "🇻🇳"},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000, "icon": "💵"},
    }

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "範例"}
    st.session_state['data'] = pd.DataFrame([r1])

# 房貸初始化
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

# --- 4. 房貸計算核心 ---
def calculate_mortgage_split(loan_info, current_date):
    total = loan_info['total']
    remaining = loan_info['remaining']
    rate_yr = loan_info['rate'] / 100
    rate_mo = rate_yr / 12
    start_date = loan_info['start_date']
    
    diff = relativedelta(current_date, start_date)
    months_passed = diff.years * 12 + diff.months
    
    grace_months = loan_info['grace_period'] * 12
    total_months = loan_info['years'] * 12
    
    if months_passed < 0: return 0, 0, 0, "未開始"
    if months_passed >= total_months or remaining <= 0: return 0, 0, 0, "已結清"
    
    interest_payment = remaining * rate_mo
    
    if months_passed < grace_months:
        return interest_payment, interest_payment, 0, f"寬限期 ({months_passed+1}/{grace_months})"
    else:
        rem_months = total_months - months_passed
        if rem_months <= 0: rem_months = 1
        if rate_mo > 0:
            pmt = remaining * (rate_mo * (1 + rate_mo)**rem_months) / ((1 + rate_mo)**rem_months - 1)
        else:
            pmt = remaining / rem_months
        principal_payment = pmt - interest_payment
        return pmt, interest_payment, principal_payment, f"還款期 ({months_passed+1}/{total_months})"

# --- 5. 導航列 (使用原生按鈕矩陣，解決跑版問題) ---
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    
    def nav_btn(col, text, icon, page):
        # 如果是當前頁面，用不同符號標示
        label = f"{icon}\n{text}"
        if st.session_state.current_page == page:
            if col.button(label, key=f"n_{page}", type="primary", use_container_width=True): pass
        else:
            if col.button(label, key=f"n_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

    nav_btn(c1, "總覽", "🏠", "總覽")
    nav_btn(c2, "記帳", "➕", "記帳")
    nav_btn(c3, "分析", "📊", "分析")
    nav_btn(c4, "錢包", "💳", "錢包")
    nav_btn(c5, "設定", "⚙️", "設定")

# --- 6. 計算資產 ---
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

# === 🏠 總覽 ===
if st.session_state.current_page == "總覽":
    # 總資產卡片 (深色背景，確保文字反白)
    st.markdown(f"""
    <div style="background-color:#1E293B; padding:20px; border-radius:12px; margin-bottom:20px;">
        <div style="color:#94A3B8; font-size:14px;">淨資產 (Net Worth)</div>
        <div style="color:white; font-size:36px; font-weight:bold;">${net_worth:,.0f}</div>
        <div style="display:flex; justify-content:space-between; margin-top:10px; color:#E2E8F0; font-size:13px;">
            <span>資產: ${real_assets:,.0f}</span>
            <span>負債: ${real_liabilities:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("現金 (TWD)", f"${total_assets_twd:,.0f}")
    c2.metric("房貸餘額", f"${loan_rem_total:,.0f}")

# === ➕ 記帳 ===
elif st.session_state.current_page == "記帳":
    st.subheader("新增交易")
    
    # 類型選擇
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
    
    c1, c2 = st.columns(2)
    tx_date = c1.date_input("日期", datetime.date.today())
    
    acct_options = list(st.session_state['accounts'].keys())
    if not acct_options: st.stop()
    acct_name = c2.selectbox("帳戶", acct_options)
    curr = st.session_state['accounts'][acct_name]['currency']
    
    cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
    tx_cat = st.selectbox("分類", cats)
    
    # 房貸智慧判斷
    default_amt = 0.0
    loan_selected = None
    standard_pay = 0
    loan_name = None
    
    if tx_cat == "房貸" and tx_type == "支出":
        loan_names = list(st.session_state['loans'].keys())
        if loan_names:
            st.info("🏠 偵測到房貸還款")
            loan_name = st.selectbox("選擇房貸契約", loan_names)
            loan_selected = st.session_state['loans'][loan_name]
            pay, interest, principal, status = calculate_mortgage_split(loan_selected, tx_date)
            
            st.markdown(f"""
            <div style="background-color:#EFF6FF; padding:15px; border-radius:10px; margin-bottom:10px;">
                <div style="font-weight:bold; color:#1E3A8A;">📊 本期帳單 ({status})</div>
                <div style="font-size:20px; font-weight:bold; color:#DC2626;">${pay:,.0f}</div>
                <div style="font-size:13px; color:#4B5563;">其中 利息: ${interest:,.0f} | 本金: ${principal:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            default_amt = float(int(pay))

    tx_amt = st.number_input(f"金額 ({curr})", value=default_amt, step=1000.0)
    tx_note = st.text_input("備註")

    if loan_selected and tx_amt > standard_pay and standard_pay > 0:
        extra = tx_amt - standard_pay
        st.warning(f"🔥 多出的 ${extra:,.0f} 將自動償還本金！")

    if st.button("確認記帳", use_container_width=True, type="primary"):
        new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
        st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
        
        if loan_selected and loan_name:
            pay, inte, prin_std, stat = calculate_mortgage_split(loan_selected, tx_date)
            # 實際還本 = 應還本 + (實繳 - 應繳)
            actual_prin = prin_std + (tx_amt - pay)
            if actual_prin > 0:
                st.session_state['loans'][loan_name]['remaining'] -= actual_prin
                st.toast(f"本金減少 ${actual_prin:,.0f}")
        
        st.success("已儲存！")

# === 📊 分析 ===
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    df = st.session_state['data'].copy()
    if df.empty: st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        st.bar_chart(df.groupby('類型')['金額(TWD)'].sum())
        st.dataframe(df, use_container_width=True)

# === 💳 錢包 (功能修復) ===
elif st.session_state.current_page == "錢包":
    st.subheader("資產管理")

    # 1. 房貸區塊
    st.markdown("### 🏠 房貸進度")
    with st.expander("➕ 新增房貸契約"):
        l_name = st.text_input("名稱", "新房貸")
        l_total = st.number_input("總額", 10000000)
        l_rate = st.number_input("利率%", 2.53)
        l_year = st.number_input("年限", 30)
        l_grace = st.number_input("寬限期", 2)
        if st.button("建立房貸"):
            st.session_state['loans'][l_name] = {
                "total": l_total, "rate": l_rate, "years": l_year, "grace_period": l_grace,
                "start_date": datetime.date.today(), "remaining": l_total, "paid_principal": 0
            }
            st.rerun()

    for name, info in st.session_state['loans'].items():
        prog = 1 - (info['remaining'] / info['total'])
        next_month = datetime.date.today() + relativedelta(months=1)
        p, i, pr, s = calculate_mortgage_split(info, next_month)
        
        # 使用原生 Expander 避免點擊問題
        with st.expander(f"🏠 {name} (餘額 ${info['remaining']:,.0f})"):
            st.progress(prog)
            st.caption(f"屋主進度: {prog*100:.1f}%")
            
            st.markdown(f"""
            <div style="margin-top:10px; font-size:14px;">
                <b>📅 下月預告 ({s})</b><br>
                應繳: ${p:,.0f}<br>
                <span style="color:#6B7280">利息: ${i:,.0f}</span> | 
                <span style="color:#059669; font-weight:bold;">還本: ${pr:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("刪除此房貸", key=f"dl_{name}"):
                del st.session_state['loans'][name]
                st.rerun()

    # 2. 帳戶區塊
    st.markdown("---")
    st.markdown("### 💳 錢包帳戶")
    with st.expander("➕ 新增帳戶"):
        c1, c2 = st.columns(2)
        n_type = c1.selectbox("類型", ["現金", "銀行", "信用卡"])
        n_curr = c2.selectbox("幣別", ["TWD", "VND", "USD"])
        n_name = st.text_input("名稱")
        n_bal = st.number_input("餘額", 0)
        if st.button("建立帳戶"):
            st.session_state['accounts'][n_name] = {"type":n_type, "currency":n_curr, "balance":n_bal, "icon":"💰"}
            st.rerun()

    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        
        # 使用原生 Expander，保證可展開編輯
        with st.expander(f"{info.get('icon','')} {name} : {info['currency']} {bal:,.0f}"):
            c_ed1, c_ed2 = st.columns(2)
            new_init = c_ed1.number_input("修正初始餘額", value=float(info['balance']), key=f"bal_{name}")
            
            if c_ed1.button("更新", key=f"up_{name}"):
                st.session_state['accounts'][name]['balance'] = new_init
                st.rerun()
            
            if c_ed2.button("刪除", key=f"de_{name}"):
                del st.session_state['accounts'][name]
                st.rerun()

# === 設定 ===
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
