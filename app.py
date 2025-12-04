import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V17", 
    page_icon="💎", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session ---
if 'current_page' not in st.session_state: st.session_state.current_page = "總覽"

# --- 2. CSS 極致深色模式 (功能元件修復版) ---
st.markdown("""
<style>
    /* 強制深色主題 */
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* 文字反白 */
    h1, h2, h3, p, span, div, label, li, b { color: #FFFFFF !important; font-family: sans-serif !important; }
    
    /* 隱藏預設 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* === 輸入元件美化 === */
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
    
    /* === 導航按鈕 === */
    .stButton button {
        background-color: #1C1C1E !important;
        color: #AAAAAA !important;
        border: 1px solid #333;
        border-radius: 10px;
        font-weight: 500;
    }
    .stButton button:hover, .stButton button:focus {
        border-color: #0A84FF !important;
        color: #0A84FF !important;
    }

    /* === 錢包卡片 (可點擊樣式) === */
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333;
        border-radius: 10px;
        margin-bottom: 5px;
    }
    .streamlit-expanderContent {
        background-color: #111;
        border: 1px solid #333;
        border-top: none;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    }

    /* === 交易列表卡片 === */
    .tx-card {
        background-color: #1C1C1E;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #333;
    }
    
    /* === 顏色工具 === */
    .text-green { color: #32D74B !important; }
    .text-red { color: #FF453A !important; }
    .text-gray { color: #8E8E93 !important; font-size: 13px; }
    
    /* 統計數字 */
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料初始化 (含房貸結構修復) ---
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

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "河粉"}
    st.session_state['data'] = pd.DataFrame([r1])

# 🚨 自動修復房貸資料結構 (V15.1 邏輯)
if 'loans' in st.session_state and isinstance(st.session_state['loans'], list):
    st.session_state['loans'] = {} # 清空舊格式

if 'loans' not in st.session_state or not st.session_state['loans']:
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

# --- 4. 房貸計算核心 (V15 回歸) ---
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

# --- 5. 導航列 ---
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    def nav_btn(col, text, icon, page):
        label = f"{icon}\n{text}"
        if col.button(label, key=f"n_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()
    nav_btn(c1, "帳本", "📅", "總覽")
    nav_btn(c2, "記帳", "➕", "記帳")
    nav_btn(c3, "分析", "📊", "分析")
    nav_btn(c4, "錢包", "💳", "錢包")
    nav_btn(c5, "設定", "⚙️", "設定")

# --- 6. 總資產計算 ---
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

# === 📅 總覽 (月曆模式) ===
if st.session_state.current_page == "總覽":
    c_date, c_stat = st.columns([1, 2])
    with c_date:
        selected_date = st.date_input("日期", datetime.date.today())
    
    df_day = st.session_state['data'][st.session_state['data']['日期'] == selected_date]
    day_inc = df_day[df_day['類型']=='收入'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    day_exp = df_day[df_day['類型']=='支出'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    
    with c_stat:
        st.markdown(f"""
        <div style="background-color:#1C1C1E; padding:15px; border-radius:10px; display:flex; justify-content:space-around; align-items:center; border:1px solid #333;">
            <div style="text-align:center;"><div class="text-gray">總資產</div><div style="font-weight:bold;">${net_worth:,.0f}</div></div>
            <div style="text-align:center;"><div class="text-green">+{day_inc:,.0f}</div><div class="text-gray">收入</div></div>
            <div style="text-align:center;"><div class="text-red">-{day_exp:,.0f}</div><div class="text-gray">支出</div></div>
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

# === ➕ 記帳 (房貸偵測回歸) ===
elif st.session_state.current_page == "記帳":
    st.subheader("新增交易")
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
    c1, c2 = st.columns(2)
    tx_date = c1.date_input("日期", datetime.date.today())
    
    acct_options = list(st.session_state['accounts'].keys())
    if not acct_options: st.error("請先去錢包新增帳戶！")
    else:
        acct_name = c2.selectbox("帳戶", acct_options)
        curr = st.session_state['accounts'][acct_name]['currency']
        
        cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
        tx_cat = st.selectbox("分類", cats)
        
        # --- 智慧房貸偵測 ---
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

        # 提前還款偵測
        if loan_selected and tx_amt > standard_pay and standard_pay > 0:
            extra = tx_amt - standard_pay
            st.warning(f"🔥 多繳的 ${extra:,.0f} 會自動還本金！")

        if st.button("確認記帳", use_container_width=True, type="primary"):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            
            # 房貸扣款執行
            if loan_selected and loan_name:
                pay, inte, prin_std, stat = calculate_mortgage_split(loan_selected, tx_date)
                actual_prin = prin_std + (tx_amt - pay)
                if actual_prin > 0:
                    st.session_state['loans'][loan_name]['remaining'] -= actual_prin
                    st.toast(f"✅ 房貸本金減少了 ${actual_prin:,.0f}")
            
            st.success("已儲存！")

# === 📊 分析 (圖表美化) ===
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    df = st.session_state['data'].copy()
    if df.empty: st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        
        tab1, tab2 = st.tabs(["支出佔比 (圓餅)", "收支趨勢 (長條)"])
        
        with tab1:
            df_exp = df[df['類型']=='支出']
            if not df_exp.empty:
                chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
                # 甜甜圈圖
                base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
                pie = base.mark_arc(innerRadius=60).encode(
                    color=alt.Color("分類", scale=alt.Scale(scheme='category20')),
                    order=alt.Order("金額(TWD)", sort="descending"),
                    tooltip=["分類", "金額(TWD)"]
                )
                st.altair_chart(pie, use_container_width=True)
                # 列表
                for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                    st.progress(min(1.0, row['金額(TWD)'] / chart_data['金額(TWD)'].sum()))
                    st.caption(f"{row['分類']} - ${row['金額(TWD)']:,.0f}")
            else:
                st.info("尚無支出")

        with tab2:
            # 雙色長條圖
            trend = df.groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
            chart = alt.Chart(trend).mark_bar().encode(
                x='日期', y='金額(TWD)',
                color=alt.Color('類型', scale=alt.Scale(range=['#32D74B', '#FF453A'])),
                column='類型'
            )
            st.altair_chart(chart, use_container_width=True)

# === 💳 錢包 (功能全面回歸) ===
elif st.session_state.current_page == "錢包":
    st.subheader("資產管理")

    # 1. 房貸管理 (支援試算、編輯、進度條)
    st.markdown("### 🏠 房貸進度")
    with st.expander("➕ 新增房貸"):
        l_name = st.text_input("名稱", "新房貸")
        l_total = st.number_input("總額", 10000000)
        l_rate = st.number_input("利率%", 2.53)
        l_year = st.number_input("年限", 30)
        l_grace = st.number_input("寬限期", 2)
        l_start = st.date_input("起算日", datetime.date.today())
        if st.button("建立房貸"):
            st.session_state['loans'][l_name] = {
                "total": l_total, "rate": l_rate, "years": l_year, "grace_period": l_grace,
                "start_date": l_start, "remaining": l_total, "paid_principal": 0
            }
            st.rerun()

    for name, info in st.session_state['loans'].items():
        prog = 1 - (info['remaining'] / info['total'])
        next_month = datetime.date.today() + relativedelta(months=1)
        p, i, pr, s = calculate_mortgage_split(info, next_month)
        
        # 使用 Expander 讓你可以點開編輯
        with st.expander(f"{name} (剩餘 ${info['remaining']:,.0f})"):
            st.progress(prog)
            st.caption(f"屋主進度: {prog*100:.1f}%")
            
            st.markdown(f"""
            <div style="margin:10px 0; font-size:14px; background-color:#111; padding:10px; border-radius:8px;">
                <b>📅 下月預告 ({s})</b><br>
                應繳: ${p:,.0f}<br>
                <span class="text-gray">利息: ${i:,.0f}</span> | 
                <span class="text-green">還本: ${pr:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # 編輯區
            col_e1, col_e2 = st.columns(2)
            if col_e1.button("刪除", key=f"dl_{name}"):
                del st.session_state['loans'][name]
                st.rerun()
            # 這裡可以加更多編輯功能

    # 2. 帳戶管理 (支援編輯與新增)
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
        
        # 使用 Expander 讓你編輯
        with st.expander(f"{info.get('icon','')} {name} : {info['currency']} {bal:,.0f}"):
            c_ed1, c_ed2 = st.columns(2)
            new_init = c_ed1.number_input("修正初始餘額", value=float(info['balance']), key=f"bal_{name}")
            
            if c_ed1.button("更新", key=f"up_{name}"):
                st.session_state['accounts'][name]['balance'] = new_init
                st.rerun()
            
            if c_ed2.button("刪除帳戶", key=f"de_{name}"):
                del st.session_state['accounts'][name]
                st.rerun()

# === ⚙️ 設定 ===
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
