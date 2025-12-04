import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V18", 
    page_icon="💰", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. CSS 極致深色模式 (天天記帳風格) ---
st.markdown("""
<style>
    /* 強制全黑背景 */
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* 文字反白 */
    h1, h2, h3, p, span, div, label, li, b, small { color: #FFFFFF !important; font-family: sans-serif !important; }
    
    /* 隱藏預設 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* === 輸入元件美化 (深灰底白字) === */
    input, textarea, select {
        background-color: #1C1C1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
    }
    div[data-baseweb="select"] > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border-color: #333 !important;
    }
    
    /* === 交易列表卡片 (仿 iOS) === */
    .tx-card {
        background-color: #1C1C1E;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #2C2C2E;
    }
    
    /* === 預算卡片 === */
    .budget-card {
        background-color: #1C1C1E;
        padding: 20px;
        border-radius: 100%; /* 圓形 */
        width: 150px;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 5px solid #30D158; /* 綠色圈圈 */
        margin: 0 auto;
    }

    /* === 顏色工具 === */
    .text-green { color: #30D158 !important; }
    .text-red { color: #FF453A !important; }
    .text-gray { color: #8E8E93 !important; font-size: 13px; }
    
    /* Tabs 優化 */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8E8E93 !important;
        font-size: 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0A84FF !important; /* iOS 藍 */
        font-weight: bold !important;
        border-bottom-color: #0A84FF !important;
    }
    
    /* Expander 樣式 */
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333;
    }
    .streamlit-expanderContent {
        background-color: #111;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療", "固定扣款"],
        "收入": ["薪資", "獎金", "股息", "副業"]
    }

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000, "icon": "🏦"},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000, "icon": "🇻🇳"},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000, "icon": "💵"},
    }

# 初始化預算 (Budget)
if 'monthly_budget' not in st.session_state:
    st.session_state['monthly_budget'] = 50000 # 預設每月預算

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "河粉"}
    st.session_state['data'] = pd.DataFrame([r1])

# 房貸資料
if 'loans' not in st.session_state or isinstance(st.session_state['loans'], list):
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

# --- 3. 房貸計算核心 ---
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
    if months_passed >= total_months: return 0, 0, 0, "已結清"
    
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

# --- 4. 總資產計算 ---
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

# --- 5. 主介面 (使用 Tabs 解決重疊) ---
# 使用 Emoji 作為 Tab 標題，簡潔有力
tab_home, tab_add, tab_chart, tab_wallet, tab_set = st.tabs(["📅 帳本", "➕ 記帳", "📊 報表", "💳 資產", "⚙️ 設定"])

# === 📅 帳本 (月曆模式) ===
with tab_home:
    c_date, c_stat = st.columns([1, 2])
    with c_date:
        selected_date = st.date_input("選擇日期", datetime.date.today())
    
    df_day = st.session_state['data'][st.session_state['data']['日期'] == selected_date]
    day_inc = df_day[df_day['類型']=='收入'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    day_exp = df_day[df_day['類型']=='支出'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    
    with c_stat:
        st.markdown(f"""
        <div style="background-color:#1C1C1E; padding:15px; border-radius:10px; display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;"><div class="text-green">+{day_inc:,.0f}</div><div class="text-gray">收入</div></div>
            <div style="text-align:center;"><div class="text-red">-{day_exp:,.0f}</div><div class="text-gray">支出</div></div>
            <div style="text-align:center;"><div>${day_inc-day_exp:,.0f}</div><div class="text-gray">結餘</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if df_day.empty: st.info("📭 本日無紀錄")
    else:
        for idx, row in df_day.iterrows():
            icon = "🏠" if row['分類']=="房貸" else "💰"
            color = "text-green" if row['類型']=='收入' else "text-red"
            st.markdown(f"""
            <div class="tx-card">
                <div style="display:flex; align-items:center;">
                    <div style="font-size:24px; margin-right:15px;">{icon}</div>
                    <div><div style="font-weight:bold;">{row['分類']}</div><div class="text-gray">{row['帳戶']} | {row['備註']}</div></div>
                </div>
                <div class="{color}" style="font-weight:bold;">{row['幣別']} {row['金額']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

# === ➕ 記帳 (含房貸) ===
with tab_add:
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
    c1, c2 = st.columns(2)
    tx_date = c1.date_input("日期", datetime.date.today(), key="add_date")
    
    acct_options = list(st.session_state['accounts'].keys())
    acct_name = c2.selectbox("帳戶", acct_options)
    curr = st.session_state['accounts'][acct_name]['currency']
    
    cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
    tx_cat = st.selectbox("分類", cats)
    
    # 房貸邏輯
    default_amt = 0.0
    loan_selected = None
    loan_name = None
    standard_pay = 0
    
    if tx_cat == "房貸" and tx_type == "支出":
        loan_names = list(st.session_state['loans'].keys())
        if loan_names:
            loan_name = st.selectbox("選擇房貸契約", loan_names)
            loan_selected = st.session_state['loans'][loan_name]
            pay, interest, principal, status = calculate_mortgage_split(loan_selected, tx_date)
            st.markdown(f"""
            <div style="background-color:#111; padding:10px; border:1px solid #333; border-radius:8px; margin-bottom:10px;">
                <b style="color:#0A84FF">📊 本期帳單 ({status})</b><br>
                應繳：<span class="text-red">${pay:,.0f}</span> (利息 ${interest:,.0f} / 本金 ${principal:,.0f})
            </div>
            """, unsafe_allow_html=True)
            default_amt = float(int(pay))

    tx_amt = st.number_input(f"金額 ({curr})", value=default_amt, step=1000.0)
    tx_note = st.text_input("備註")

    if loan_selected and tx_amt > standard_pay and standard_pay > 0:
        extra = tx_amt - standard_pay
        st.warning(f"🔥 多繳的 ${extra:,.0f} 會自動還本金！")

    if st.button("確認記帳", use_container_width=True, type="primary"):
        new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
        st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
        if loan_selected and loan_name:
            pay, inte, prin_std, stat = calculate_mortgage_split(loan_selected, tx_date)
            actual_prin = prin_std + (tx_amt - pay)
            if actual_prin > 0:
                st.session_state['loans'][loan_name]['remaining'] -= actual_prin
                st.toast(f"房貸本金減少 ${actual_prin:,.0f}")
        st.success("已儲存！")

# === 📊 報表 (預算 & 趨勢) ===
with tab_chart:
    st.subheader("預算與趨勢")
    
    # 計算當月總支出
    this_month = datetime.date.today().replace(day=1)
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    # 篩選本月支出
    mask = (df['日期'] >= this_month) & (df['類型'] == '支出')
    month_exp = df[mask]['金額(TWD)'].sum()
    budget = st.session_state['monthly_budget']
    percent = min(1.0, month_exp / budget)
    
    # 1. 預算圓環 (CSS 實現)
    c_bud, c_trend = st.columns([1, 2])
    with c_bud:
        st.markdown(f"""
        <div style="text-align:center;">
            <div class="budget-card">
                <div style="font-size:12px; color:#888;">本月支出</div>
                <div style="font-size:24px; font-weight:bold; color:#30D158;">{int(percent*100)}%</div>
                <div style="font-size:12px; color:#888;">${month_exp:,.0f} / ${budget:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # 設定預算
        new_bud = st.number_input("設定每月預算", value=budget, step=1000)
        if new_bud != budget: st.session_state['monthly_budget'] = new_bud

    # 2. 趨勢圖 (Altair)
    with c_trend:
        # 按月份分組
        df['月'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m')
        trend_data = df.groupby(['月', '類型'])['金額(TWD)'].sum().reset_index()
        
        chart = alt.Chart(trend_data).mark_bar().encode(
            x='月',
            y='金額(TWD)',
            color=alt.Color('類型', scale=alt.Scale(range=['#30D158', '#FF453A'])),
            column='類型'
        ).properties(height=200)
        st.altair_chart(chart, use_container_width=True)

# === 💳 資產 (可編輯) ===
with tab_wallet:
    st.subheader("資產管理")
    
    # 總資產摘要
    st.markdown(f"""
    <div style="background-color:#1C1C1E; padding:20px; border-radius:15px; margin-bottom:20px; border:1px solid #333;">
        <div style="color:#888; font-size:14px;">淨資產 (Net Worth)</div>
        <div style="color:white; font-size:36px; font-weight:bold;">${net_worth:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. 房貸區塊 (可編輯)
    with st.expander("🏠 房貸管理", expanded=True):
        for name, info in st.session_state['loans'].items():
            prog = 1 - (info['remaining'] / info['total'])
            next_month = datetime.date.today() + relativedelta(months=1)
            p, i, pr, s = calculate_mortgage_split(info, next_month)
            
            st.write(f"**{name}**")
            st.progress(prog)
            st.caption(f"剩餘: ${info['remaining']:,.0f} / ${info['total']:,.0f} ({s})")
            
            if st.button("刪除", key=f"dl_{name}"):
                del st.session_state['loans'][name]
                st.rerun()
        
        st.markdown("---")
        n_ln = st.text_input("新房貸名稱")
        if st.button("新增房貸"):
            st.session_state['loans'][n_ln] = {
                "total": 10000000, "rate": 2.5, "years": 30, "grace_period": 2,
                "start_date": datetime.date.today(), "remaining": 10000000, "paid_principal": 0
            }
            st.rerun()

    # 2. 帳戶區塊 (可編輯)
    st.markdown("### 💳 帳戶列表")
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        
        with st.expander(f"{info.get('icon','💰')} {name} : {info['currency']} {bal:,.0f}"):
            c_ed1, c_ed2 = st.columns(2)
            new_init = c_ed1.number_input("初始餘額", value=float(info['balance']), key=f"bal_{name}")
            if c_ed1.button("更新", key=f"up_{name}"):
                st.session_state['accounts'][name]['balance'] = new_init
                st.rerun()
            if c_ed2.button("刪除", key=f"del_{name}"):
                del st.session_state['accounts'][name]
                st.rerun()

    with st.expander("➕ 新增帳戶"):
        n_name = st.text_input("帳戶名稱")
        n_curr = st.selectbox("幣別", ["TWD", "VND", "USD"])
        if st.button("建立帳戶"):
            st.session_state['accounts'][n_name] = {"type":"銀行", "currency":n_curr, "balance":0, "icon":"💰"}
            st.rerun()

# === ⚙️ 設定 ===
with tab_set:
    st.subheader("設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
