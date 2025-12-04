import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V21", 
    page_icon="💎", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session ---
if 'current_page' not in st.session_state: st.session_state.current_page = "帳本"

# --- 2. CSS 極致深色 & RWD 響應式修復 ---
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp { background-color: #0E0E0E !important; color: #FFFFFF !important; }
    
    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 字體顏色強制反白，並設定行高防止重疊 */
    h1, h2, h3, p, span, div, label, li, b, small {
        color: #FFFFFF !important;
        font-family: sans-serif !important;
        line-height: 1.5 !important;
    }

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
    
    /* === 導航按鈕 (RWD 核心修復) === */
    .stButton button {
        background-color: #1C1C1E !important;
        color: #8E8E93 !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
        font-weight: 500;
        padding: 4px 2px !important; /* 減少內距 */
        height: auto !important;     /* 高度自動，防止文字被切掉 */
        min-height: 50px;
        white-space: pre-wrap !important; /* 允許換行 */
    }
    
    /* 手機版微調 (螢幕小於 600px 時) */
    @media only screen and (max-width: 600px) {
        .stButton button {
            font-size: 12px !important; /* 字體縮小 */
        }
    }

    /* 選中狀態模擬 (主要按鈕) */
    .stButton button:focus {
        border-color: #0A84FF !important;
        color: #0A84FF !important;
    }

    /* === 交易列表卡片 === */
    .tx-card {
        background-color: #1C1C1E;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #333;
    }
    
    /* === 統計區塊 === */
    .stat-box {
        background-color: #1C1C1E;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        border: 1px solid #333;
    }
    
    /* === Expander 修復 === */
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333;
    }
    .streamlit-expanderContent {
        background-color: #111 !important;
        border: 1px solid #333;
        border-top: none;
    }
    
    /* 顏色工具 */
    .c-green { color: #32D74B !important; }
    .c-red { color: #FF453A !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": ["房貸", "餐飲", "交通", "購物", "居住", "娛樂", "醫療", "訂閱"],
        "收入": ["薪資", "獎金", "股息", "副業"]
    }

if 'recurring' not in st.session_state:
    st.session_state['recurring'] = [
        {"name": "Netflix", "amt": 390, "type": "支出", "cat": "訂閱", "curr": "TWD"},
        {"name": "房租", "amt": 25000, "type": "支出", "cat": "居住", "curr": "TWD"}
    ]

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000, "icon": "🏦"},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000, "icon": "🇻🇳"},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000, "icon": "💵"},
    }

if 'loans' not in st.session_state or isinstance(st.session_state['loans'], list):
    st.session_state['loans'] = {
        "自住屋房貸": {
            "total": 10350000, "rate": 2.53, "years": 30, "grace_period": 2,
            "start_date": datetime.date(2025, 11, 1), "remaining": 10350000, "paid_principal": 0
        }
    }

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "河粉"}
    st.session_state['data'] = pd.DataFrame([r1])

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
    if months_passed >= total_months: return 0, 0, 0, "已結清"
    
    interest_payment = remaining * rate_mo
    
    if months_passed < grace_months:
        return interest_payment, interest_payment, 0, f"寬限 ({months_passed+1}/{grace_months})"
    else:
        rem_months = total_months - months_passed
        if rem_months <= 0: rem_months = 1
        if rate_mo > 0:
            pmt = remaining * (rate_mo * (1 + rate_mo)**rem_months) / ((1 + rate_mo)**rem_months - 1)
        else:
            pmt = remaining / rem_months
        principal_payment = pmt - interest_payment
        return pmt, interest_payment, principal_payment, f"還款 ({months_passed+1}/{total_months})"

# --- 5. 導航列 (使用 Button Grid 防止疊字) ---
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    def nav_btn(col, text, icon, page):
        label = f"{icon}\n{text}"
        # 這裡用 type="primary" 來標示當前頁面，讓它變色
        btn_type = "primary" if st.session_state.current_page == page else "secondary"
        if col.button(label, key=f"nav_{page}", use_container_width=True, type=btn_type):
            st.session_state.current_page = page
            st.rerun()

    nav_btn(c1, "帳本", "📅", "帳本")
    nav_btn(c2, "記帳", "➕", "記帳")
    nav_btn(c3, "分析", "📊", "分析")
    nav_btn(c4, "資產", "💳", "資產")
    nav_btn(c5, "設定", "⚙️", "設定")

# ==========================================
# 📅 帳本 (月曆總覽)
# ==========================================
if st.session_state.current_page == "帳本":
    c_date, c_inc, c_exp = st.columns([2, 1, 1])
    with c_date:
        selected_date = st.date_input("日期", datetime.date.today(), label_visibility="collapsed")
    
    # 統計當日
    df_day = st.session_state['data'][st.session_state['data']['日期'] == selected_date]
    day_inc = df_day[df_day['類型']=='收入'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    day_exp = df_day[df_day['類型']=='支出'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    
    with c_inc:
        st.markdown(f'<div class="stat-box"><div style="font-size:12px; color:#888;">收入</div><div class="c-green" style="font-weight:bold;">{day_inc:,.0f}</div></div>', unsafe_allow_html=True)
    with c_exp:
        st.markdown(f'<div class="stat-box"><div style="font-size:12px; color:#888;">支出</div><div class="c-red" style="font-weight:bold;">{day_exp:,.0f}</div></div>', unsafe_allow_html=True)

    st.write("") # Spacer
    
    if df_day.empty:
        st.info("📭 本日無紀錄")
    else:
        for idx, row in df_day.iterrows():
            icon = "🏠" if row['分類']=="房貸" else "💰"
            color_class = "c-green" if row['類型']=="收入" else "c-red"
            sign = "+" if row['類型']=="收入" else "-"
            
            st.markdown(f"""
            <div class="tx-card">
                <div style="display:flex; align-items:center;">
                    <div style="font-size:24px; margin-right:15px; width:30px; text-align:center;">{icon}</div>
                    <div>
                        <div style="font-weight:bold; font-size:16px; color:white;">{row['分類']}</div>
                        <div style="font-size:12px; color:#8E8E93;">{row['帳戶']} • {row['備註']}</div>
                    </div>
                </div>
                <div style="font-weight:bold; font-size:16px;" class="{color_class}">
                    {sign} {row['幣別']} {row['金額']:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# ➕ 記帳 (含房貸 & 固定收支)
# ==========================================
elif st.session_state.current_page == "記帳":
    st.subheader("新增交易")
    
    # 使用 Radio 切換模式
    mode = st.radio("模式", ["一般記帳", "固定收支"], horizontal=True)
    
    if mode == "一般記帳":
        tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("日期", datetime.date.today())
        
        acct_opts = list(st.session_state['accounts'].keys())
        acct_name = c2.selectbox("帳戶", acct_opts) if acct_opts else None
        
        if acct_name:
            curr = st.session_state['accounts'][acct_name]['currency']
            cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
            tx_cat = st.selectbox("分類", cats)
            
            # 房貸偵測
            default_amt = 0.0
            loan_obj = None
            loan_key = None
            std_pay = 0
            
            if tx_cat == "房貸" and tx_type == "支出":
                loan_opts = list(st.session_state['loans'].keys())
                if loan_opts:
                    loan_key = st.selectbox("房貸契約", loan_opts)
                    loan_obj = st.session_state['loans'][loan_key]
                    pay, inte, prin, stat = calculate_mortgage_split(loan_obj, tx_date)
                    st.info(f"📊 本期: ${pay:,.0f} (利息 ${inte:,.0f})")
                    default_amt = float(int(pay))
                    std_pay = pay

            tx_amt = st.number_input(f"金額 ({curr})", value=default_amt, step=1000.0)
            tx_note = st.text_input("備註")
            
            if loan_obj and tx_amt > std_pay and std_pay > 0:
                st.warning(f"🔥 超額還款！多出的 ${tx_amt - std_pay:,.0f} 將償還本金")

            if st.button("確認儲存", type="primary", use_container_width=True):
                new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
                st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
                
                if loan_obj:
                    p, i, p_std, s = calculate_mortgage_split(loan_obj, tx_date)
                    actual_prin = p_std + (tx_amt - p)
                    if actual_prin > 0:
                        st.session_state['loans'][loan_key]['remaining'] -= actual_prin
                        st.toast(f"本金減少 ${actual_prin:,.0f}")
                st.success("已記帳")
    
    else: # 固定收支模式
        st.write("點擊入帳")
        for item in st.session_state['recurring']:
            c_info, c_btn = st.columns([3, 1])
            c_info.write(f"**{item['name']}** - {item['curr']} {item['amt']}")
            if c_btn.button("入帳", key=f"rec_{item['name']}"):
                new_rec = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": item['type'], "分類": item['cat'], "金額": item['amt'], "幣別": item['curr'], "備註": f"固定: {item['name']}"}
                st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
                st.success("OK")

# ==========================================
# 📊 分析 (圖表優化)
# ==========================================
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    df = st.session_state['data'].copy()
    if df.empty:
        st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        
        col_type = st.selectbox("分析類型", ["支出佔比", "收支趨勢"])
        
        if col_type == "支出佔比":
            df_exp = df[df['類型']=='支出']
            if not df_exp.empty:
                chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
                base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
                pie = base.mark_arc(innerRadius=60).encode(
                    color=alt.Color("分類", scale=alt.Scale(scheme='tableau20')),
                    order=alt.Order("金額(TWD)", sort="descending"),
                    tooltip=["分類", "金額(TWD)"]
                )
                st.altair_chart(pie, use_container_width=True)
            else:
                st.info("無支出資料")
                
        else: # 趨勢 (改用面積圖 Area Chart)
            trend = df.groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
            area = alt.Chart(trend).mark_area(opacity=0.6).encode(
                x='日期', y='金額(TWD)',
                color=alt.Color('類型', scale=alt.Scale(range=['#32D74B', '#FF453A'])),
            )
            st.altair_chart(area, use_container_width=True)

# ==========================================
# 💳 資產 (全功能回歸)
# ==========================================
elif st.session_state.current_page == "資產":
    # 總資產計算
    total_asset = 0
    total_debt = 0
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        twd = convert_to_twd(bal, info['currency'])
        if twd >= 0: total_asset += twd
        else: total_debt += abs(twd)
    
    loan_debt = sum([l['remaining'] for l in st.session_state['loans'].values()])
    total_debt += loan_debt
    home_asset = sum([l['total'] for l in st.session_state['loans'].values()])
    total_asset += home_asset
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1C1C1E 0%, #2C2C2E 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333;">
        <div style="color:#888; font-size:14px;">淨資產</div>
        <div style="color:white; font-size:32px; font-weight:bold;">${total_asset - total_debt:,.0f}</div>
        <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:13px; color:#AAA;">
            <span>資產: ${total_asset:,.0f}</span>
            <span>負債: ${total_debt:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. 房貸區
    st.markdown("#### 🏠 房貸智慧管家")
    with st.expander("➕ 新增/編輯房貸"):
        l_name = st.text_input("名稱", "新房貸")
        l_total = st.number_input("總額", 10000000)
        l_rate = st.number_input("利率", 2.53)
        l_year = st.number_input("年限", 30)
        l_grace = st.number_input("寬限期", 2)
        if st.button("建立/更新"):
            st.session_state['loans'][l_name] = {
                "total": l_total, "rate": l_rate, "years": l_year, "grace_period": l_grace,
                "start_date": datetime.date.today(), "remaining": l_total, "paid_principal": 0
            }
            st.rerun()

    for name, info in st.session_state['loans'].items():
        prog = 1 - (info['remaining'] / info['total'])
        next_m = datetime.date.today() + relativedelta(months=1)
        p, i, pr, s = calculate_mortgage_split(info, next_m)
        
        with st.expander(f"{name} (剩餘 ${info['remaining']:,.0f})"):
            st.progress(prog)
            st.caption(f"進度: {prog*100:.1f}% | 下期: {s}")
            st.write(f"下月應繳: **${p:,.0f}** (利息 ${i:,.0f})")
            if st.button("刪除", key=f"del_l_{name}"):
                del st.session_state['loans'][name]
                st.rerun()

    # 2. 帳戶區
    st.markdown("#### 💳 帳戶列表")
    with st.expander("➕ 新增帳戶"):
        n_n = st.text_input("名稱")
        n_c = st.selectbox("幣別", ["TWD", "VND", "USD"])
        n_b = st.number_input("餘額", 0)
        if st.button("建立"):
            st.session_state['accounts'][n_n] = {"type":"一般", "currency":n_c, "balance":n_b, "icon":"💰"}
            st.rerun()

    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        
        with st.expander(f"{info.get('icon','')} {name} : {info['currency']} {bal:,.0f}"):
            new_bal = st.number_input("修正餘額", value=float(info['balance']), key=f"ed_{name}")
            if st.button("更新", key=f"up_{name}"):
                st.session_state['accounts'][name]['balance'] = new_bal
                st.rerun()
            if st.button("刪除", key=f"dl_{name}"):
                del st.session_state['accounts'][name]
                st.rerun()

# ==========================================
# ⚙️ 設定
# ==========================================
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    with st.expander("🏷️ 分類管理", expanded=True):
        c1, c2 = st.columns([3, 1])
        new_cat = c1.text_input("新增支出分類")
        if c2.button("新增"):
            st.session_state['categories']['支出'].append(new_cat)
            st.rerun()
        st.write(", ".join(st.session_state['categories']['支出']))
        
    with st.expander("🌍 匯率"):
        st.session_state['rates']['VND'] = st.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
