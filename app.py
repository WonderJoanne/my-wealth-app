import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V15", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "錢包"

# --- 2. CSS 美學 (V14 Soft UI) ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 卡片與容器 */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #FFFFFF;
    }
    
    /* 按鈕與輸入 */
    .stButton button {
        border-radius: 12px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s;
    }
    .stButton button:active { transform: translateY(1px); }
    
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }

    h1, h2, h3, p, span, label, div[data-testid="stMetricValue"] {
        color: #2D3748 !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* 房貸專屬樣式 */
    .loan-stat {
        background-color: #F0FFF4;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #C6F6D5;
        margin-top: 10px;
    }
    .highlight-green { color: #38A169; font-weight: bold; }
    .highlight-red { color: #E53E3E; font-weight: bold; }
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

if 'loans' not in st.session_state:
    st.session_state['loans'] = {
        "自住屋房貸": {
            "total": 10350000,
            "rate": 2.53,
            "years": 30,
            "grace_period": 2,
            "start_date": datetime.date(2025, 11, 1),
            "remaining": 10350000, # 初始剩餘本金
            "paid_principal": 0    # 已還本金
        }
    }

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 4. 房貸計算核心 (PMT & 拆帳) ---
def calculate_mortgage_split(loan_info, current_date):
    """
    計算「當月」的應繳金額結構
    """
    total = loan_info['total']
    remaining = loan_info['remaining']
    rate_yr = loan_info['rate'] / 100
    rate_mo = rate_yr / 12
    start_date = loan_info['start_date']
    
    # 計算過了幾個月
    diff = relativedelta(current_date, start_date)
    months_passed = diff.years * 12 + diff.months
    
    grace_months = loan_info['grace_period'] * 12
    total_months = loan_info['years'] * 12
    
    # 狀態判斷
    if months_passed < 0: return 0, 0, 0, "未開始"
    if months_passed >= total_months or remaining <= 0: return 0, 0, 0, "已結清"
    
    # 計算當月利息 (基於目前剩餘本金)
    interest_payment = remaining * rate_mo
    
    if months_passed < grace_months:
        # 寬限期：只繳利息
        return interest_payment, interest_payment, 0, "寬限期"
    else:
        # 還款期：本息均攤
        # 剩餘期數 (重新計算，因為可能有提前還款)
        rem_months = total_months - months_passed
        if rem_months <= 0: rem_months = 1
        
        # 重新計算 PMT (因為本金可能變動過)
        # PMT = P * r * (1+r)^n / ((1+r)^n - 1)
        pmt = remaining * (rate_mo * (1 + rate_mo)**rem_months) / ((1 + rate_mo)**rem_months - 1)
        
        principal_payment = pmt - interest_payment
        return pmt, interest_payment, principal_payment, "還款期"

# --- 5. 導航列 ---
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    def nav_btn(col, label, icon, page_name):
        if st.session_state.current_page == page_name:
            if col.button(f"{icon}\n{label}", key=f"nav_{page_name}", use_container_width=True, type="primary"): pass
        else:
            if col.button(f"{icon}\n{label}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
    nav_btn(col1, "總覽", "🏠", "總覽")
    nav_btn(col2, "記帳", "➕", "記帳")
    nav_btn(col3, "分析", "📊", "分析")
    nav_btn(col4, "錢包", "💳", "錢包")
    nav_btn(col5, "設定", "⚙️", "設定")
    st.markdown("---")

# --- 6. 計算總資產 ---
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

# 房貸餘額 (負債)
loan_remaining_total = sum([l['remaining'] for l in st.session_state['loans'].values()])
# 房產價值 (資產 - 假設等於買入價)
home_value_total = sum([l['total'] for l in st.session_state['loans'].values()])

real_assets = total_assets_twd + invest_val + home_value_total
real_liabilities = total_liability_twd + loan_remaining_total
net_worth = real_assets - real_liabilities

# === 🏠 總覽 ===
if st.session_state.current_page == "總覽":
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%); padding: 25px; border-radius: 20px; color: white; margin-bottom: 20px;">
        <p style="margin:0; font-size: 14px; color:rgba(255,255,255,0.8) !important;">淨資產 (Net Worth)</p>
        <h1 style="margin:5px 0; font-size: 40px; font-weight: 700; color:white !important;">${net_worth:,.0f}</h1>
        <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:13px;">
            <span style="color:white !important;">資產: ${real_assets:,.0f}</span>
            <span style="color:white !important;">負債: ${real_liabilities:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("現金 (TWD)", f"${total_assets_twd:,.0f}")
    c2.metric("房貸餘額", f"${loan_remaining_total:,.0f}")

# === ➕ 記帳 (V15 智慧房貸連動) ===
elif st.session_state.current_page == "記帳":
    st.subheader("新增交易")
    
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
    
    # 欄位
    c1, c2 = st.columns(2)
    tx_date = c1.date_input("日期", datetime.date.today())
    
    # 帳戶
    acct_options = list(st.session_state['accounts'].keys())
    if not acct_options: st.stop()
    acct_name = c2.selectbox("帳戶", acct_options)
    curr = st.session_state['accounts'][acct_name]['currency']
    
    # 分類
    cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
    tx_cat = st.selectbox("分類", cats)
    
    # --- 房貸智慧邏輯區 ---
    default_amt = 0.0
    loan_selected = None
    standard_pay = 0
    
    if tx_cat == "房貸" and tx_type == "支出":
        loan_names = list(st.session_state['loans'].keys())
        if loan_names:
            st.info("🏠 偵測到房貸記帳模式")
            loan_name = st.selectbox("選擇房貸契約", loan_names)
            loan_selected = st.session_state['loans'][loan_name]
            
            # 計算本期應繳
            standard_pay, interest, principal, status = calculate_mortgage_split(loan_selected, tx_date)
            
            st.markdown(f"""
            <div class="loan-stat">
                <b>📊 本期帳單試算 ({status})</b><br>
                應繳總額：<span class="highlight-red">${standard_pay:,.0f}</span><br>
                <small>利息：${interest:,.0f} | 本金：${principal:,.0f}</small>
            </div>
            """, unsafe_allow_html=True)
            default_amt = float(int(standard_pay))
        else:
            st.warning("尚未設定房貸，請去錢包新增！")

    # 金額輸入 (若為房貸，預設帶入應繳金額)
    tx_amt = st.number_input(f"金額 ({curr})", value=default_amt, step=1000.0)
    tx_note = st.text_input("備註")

    # --- 房貸超額還款偵測 ---
    extra_principal = 0
    if loan_selected and tx_amt > standard_pay:
        extra_principal = tx_amt - standard_pay
        st.markdown(f"""
        <div style="padding:10px; background-color:#FFF5F5; border-left:4px solid #E53E3E; margin:10px 0;">
            🔥 <b>偵測到大額還款！</b><br>
            多出的 <b style="color:#E53E3E">${extra_principal:,.0f}</b> 將自動用於償還本金！
        </div>
        """, unsafe_allow_html=True)

    if st.button("確認記帳", use_container_width=True, type="primary"):
        # 1. 寫入流水帳
        new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
        st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
        
        # 2. 房貸連動邏輯 (自動扣本金)
        if loan_selected:
            # 本次總共還的本金 = 應還本金(若有) + 超額還款
            # 注意：calculate_mortgage_split 算出的 principal 是這一期「應該」還的
            # 我們要從 remaining 中扣掉的是：這一期的本金 + 多繳的錢
            
            # 重新取得計算值 (避免 UI 變數未更新)
            pay, inte, prin_std, stat = calculate_mortgage_split(loan_selected, tx_date)
            
            # 實際還本金 = 標準本金 + (實繳 - 標準應繳)
            actual_principal_paid = prin_std + (tx_amt - pay)
            
            # 更新 Session State
            st.session_state['loans'][loan_name]['remaining'] -= actual_principal_paid
            st.session_state['loans'][loan_name]['paid_principal'] += actual_principal_paid
            
            st.toast(f"✅ 記帳成功！房貸本金減少了 ${actual_principal_paid:,.0f}")
        else:
            st.success("已儲存！")

# === 📊 分析 ===
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    df = st.session_state['data'].copy()
    if df.empty: st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        st.bar_chart(df.groupby('類型')['金額(TWD)'].sum())
        st.dataframe(df)

# === 💳 錢包 (進度條與預演) ===
elif st.session_state.current_page == "錢包":
    st.subheader("資產管理")

    # 1. 房貸卡片 (V15 完整版)
    st.markdown("### 🏠 房貸進度")
    
    # 新增房貸功能
    with st.expander("➕ 新增房貸"):
        nl_name = st.text_input("名稱", "新房貸")
        nl_total = st.number_input("總額", 10000000)
        nl_rate = st.number_input("利率%", 2.53)
        nl_year = st.number_input("年限", 30)
        nl_grace = st.number_input("寬限期", 2)
        if st.button("建立"):
            st.session_state['loans'][nl_name] = {
                "total": nl_total, "rate": nl_rate, "years": nl_year, "grace_period": nl_grace,
                "start_date": datetime.date.today(), "remaining": nl_total, "paid_principal": 0
            }
            st.rerun()

    for name, info in st.session_state['loans'].items():
        # 計算進度
        progress = 1 - (info['remaining'] / info['total'])
        
        # 下個月預告
        next_month = datetime.date.today() + relativedelta(months=1)
        n_pay, n_inte, n_prin, n_stat = calculate_mortgage_split(info, next_month)
        
        with st.container():
            st.markdown(f"""
            <div class="mobile-card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:bold; font-size:18px;">{name}</span>
                    <span style="color:#718096;">{n_stat}</span>
                </div>
                <div style="font-size:24px; font-weight:bold; color:#2D3748; margin:10px 0;">
                    ${info['remaining']:,.0f} <small style="font-size:14px; color:#A0AEC0;">/ ${info['total']:,.0f}</small>
                </div>
                
                <div style="background:#EDF2F7; height:10px; border-radius:5px; margin-bottom:5px;">
                    <div style="background:#48BB78; width:{progress*100}%; height:100%; border-radius:5px;"></div>
                </div>
                <div style="text-align:right; font-size:12px; color:#48BB78; font-weight:bold;">
                    屋主擁有權：{progress*100:.1f}%
                </div>
                
                <hr style="border-top: 1px solid #EDF2F7;">
                
                <div style="font-size:14px;">
                    <b>📅 下月預告 ({next_month.strftime('%Y/%m')})</b><br>
                    預計繳款：${n_pay:,.0f}<br>
                    <span style="color:#718096;">利息：${n_inte:,.0f}</span> 
                    <span style="color:#38A169; margin-left:10px;">➔ 償還本金：${n_prin:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 2. 帳戶列表
    st.markdown("### 💳 我的帳戶")
    for name, info in st.session_state['accounts'].items():
        # 簡單顯示帳戶 (略過編輯功能以節省篇幅，V14已有)
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        
        st.markdown(f"""
        <div class="mobile-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div><span style="font-size:20px;">{info.get('icon','💰')}</span> <b>{name}</b></div>
            <b>{info['currency']} {bal:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

# === 設定 ===
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    st.write("匯率設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
