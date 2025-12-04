import streamlit as st
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V20", 
    page_icon="📅", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session (導航與日期狀態) ---
if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date.today()

# --- 2. CSS 極致優化 (修復重疊問題) ---
st.markdown("""
<style>
    /* 全局設定 */
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* 修正字體重疊：設定行高為正常，並允許換行 */
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        line-height: 1.5 !important; /* 關鍵修復 */
        word-wrap: break-word !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* === 日曆條樣式 === */
    .calendar-day {
        text-align: center;
        padding: 5px;
        border-radius: 8px;
        cursor: pointer;
        border: 1px solid #333;
        background-color: #1C1C1E;
        transition: all 0.2s;
    }
    .calendar-day.active {
        background-color: #0A84FF; /* iOS Blue */
        border-color: #0A84FF;
        color: white;
    }
    .day-name { font-size: 12px; color: #8E8E93; }
    .day-num { font-size: 18px; font-weight: bold; }
    .day-active .day-name, .day-active .day-num { color: white !important; }

    /* === 交易卡片 === */
    .tx-card {
        background-color: #1C1C1E;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-height: 60px; /* 防止內容擠壓 */
    }
    
    /* === 統計區塊 === */
    .stat-row {
        display: flex;
        justify-content: space-between;
        background-color: #1C1C1E;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .stat-item { text-align: center; flex: 1; }
    .stat-label { font-size: 12px; color: #8E8E93; margin-bottom: 4px; }
    .stat-val { font-size: 16px; font-weight: bold; }
    
    /* === 輸入框與按鈕 === */
    input, textarea, select {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
    }
    div[data-baseweb="select"] > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border-color: #333 !important;
    }
    .stButton button {
        background-color: #2C2C2E !important;
        color: white !important;
        border: 1px solid #3A3A3C !important;
        border-radius: 10px;
    }
    
    /* 顏色 */
    .c-green { color: #30D158 !important; }
    .c-red { color: #FF453A !important; }
    
    /* Expander 修正 */
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        color: white !important;
    }
    .streamlit-expanderContent {
        background-color: #111 !important;
        border: 1px solid #333;
        border-top: none; 
    }
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

if 'loans' not in st.session_state:
    st.session_state['loans'] = {
        "自住屋房貸": {
            "total": 10350000, "rate": 2.53, "years": 30, "grace_period": 2,
            "start_date": datetime.date(2025, 11, 1), "remaining": 10350000, "paid_principal": 0
        }
    }

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "範例"}
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

# --- 5. 主導航 (原生 Tabs) ---
tab_home, tab_add, tab_analysis, tab_assets, tab_settings = st.tabs([
    "📅 帳本", "➕ 記帳", "📊 分析", "💳 資產", "⚙️ 設定"
])

# ==========================================
# 📅 帳本 (重現天天記帳首頁 - 週曆模式)
# ==========================================
with tab_home:
    # 1. 頂部月份與切換
    current_view = st.session_state.view_date
    col_prev, col_month, col_next = st.columns([1, 4, 1])
    
    if col_prev.button("◀", key="prev_week"):
        st.session_state.view_date -= datetime.timedelta(days=7)
        st.rerun()
        
    with col_month:
        # 顯示當前年月
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{current_view.strftime('%Y年 %m月')}</h3>", unsafe_allow_html=True)
        
    if col_next.button("▶", key="next_week"):
        st.session_state.view_date += datetime.timedelta(days=7)
        st.rerun()

    # 2. 週曆條 (7個按鈕)
    # 算出本週第一天 (週一)
    start_of_week = current_view - datetime.timedelta(days=current_view.weekday())
    week_cols = st.columns(7)
    week_days = ["一", "二", "三", "四", "五", "六", "日"]
    
    selected_date = st.session_state.view_date
    
    for i in range(7):
        day_date = start_of_week + datetime.timedelta(days=i)
        is_selected = (day_date == selected_date)
        
        # 樣式判斷
        bg_color = "#0A84FF" if is_selected else "#1C1C1E"
        border_color = "#0A84FF" if is_selected else "#333"
        text_color = "white"
        
        with week_cols[i]:
            # 使用按鈕模擬點擊
            # 顯示格式: 週\n日期
            btn_label = f"{week_days[i]}\n{day_date.day}"
            if st.button(btn_label, key=f"day_{i}", use_container_width=True):
                st.session_state.view_date = day_date
                st.rerun()
            
            # 如果是被選中的，下方顯示一個小標示 (用 CSS 無法動態做，這裡用按鈕狀態呈現)

    # 3. 當日統計
    df_day = st.session_state['data'][st.session_state['data']['日期'] == selected_date]
    day_inc = df_day[df_day['類型']=='收入'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    day_exp = df_day[df_day['類型']=='支出'].apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1).sum()
    
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-label">收入</div>
            <div class="stat-val c-green">+{day_inc:,.0f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">支出</div>
            <div class="stat-val c-red">-{day_exp:,.0f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">結餘</div>
            <div class="stat-val">${day_inc-day_exp:,.0f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 交易清單
    if df_day.empty:
        st.info(f"{selected_date.strftime('%m/%d')} 無紀錄")
    else:
        for idx, row in df_day.iterrows():
            icon = "🏠" if row['分類']=="房貸" else "🍜" if row['分類'] in ["餐飲","食品"] else "💰"
            color_class = "c-green" if row['類型']=="收入" else "c-red"
            sign = "+" if row['類型']=="收入" else "-"
            
            st.markdown(f"""
            <div class="tx-card">
                <div class="tx-left">
                    <div class="tx-icon">{icon}</div>
                    <div>
                        <div class="tx-title">{row['分類']}</div>
                        <div style="font-size:12px; color:#888;">{row['帳戶']} • {row['備註']}</div>
                    </div>
                </div>
                <div style="font-weight:bold; font-size:16px;" class="{color_class}">
                    {sign} {row['幣別']} {row['金額']:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# ➕ 記帳
# ==========================================
with tab_add:
    st.subheader("新增交易")
    sub_t1, sub_t2 = st.tabs(["一般記帳", "固定收支"])
    
    with sub_t1:
        tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("日期", datetime.date.today())
        
        acct_opts = list(st.session_state['accounts'].keys())
        acct_name = c2.selectbox("帳戶", acct_opts) if acct_opts else None
        
        if acct_name:
            curr = st.session_state['accounts'][acct_name]['currency']
            cats = st.session_state['categories']['支出'] if tx_type=="支出" else st.session_state['categories']['收入']
            tx_cat = st.selectbox("分類", cats)
            
            # 房貸智慧偵測
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
                    st.info(f"📊 本期 ({stat}): ${pay:,.0f} (利息 ${inte:,.0f})")
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

    with sub_t2:
        for item in st.session_state['recurring']:
            c_info, c_btn = st.columns([3, 1])
            c_info.write(f"**{item['name']}** - {item['curr']} {item['amt']}")
            if c_btn.button("入帳", key=f"rec_{item['name']}"):
                # 簡化：預設帳戶為隨身皮夾，實際應可選
                new_rec = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": item['type'], "分類": item['cat'], "金額": item['amt'], "幣別": item['curr'], "備註": f"固定: {item['name']}"}
                st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
                st.success("OK")

# ==========================================
# 📊 分析
# ==========================================
with tab_analysis:
    df = st.session_state['data'].copy()
    if df.empty:
        st.info("無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        
        st.markdown("### 支出分佈")
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=60).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='category20')),
                order=alt.Order("金額(TWD)", sort="descending"),
                tooltip=["分類", "金額(TWD)"]
            )
            st.altair_chart(pie, use_container_width=True)
        
        st.markdown("### 收支趨勢")
        trend = df.groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
        bar = alt.Chart(trend).mark_bar().encode(
            x='日期', y='金額(TWD)',
            color=alt.Color('類型', scale=alt.Scale(range=['#32D74B', '#FF453A'])),
            column='類型'
        )
        st.altair_chart(bar, use_container_width=True)

# ==========================================
# 💳 資產 (房貸與帳戶編輯)
# ==========================================
with tab_assets:
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
    
    # 淨資產卡片
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

# === ⚙️ 設定 ===
with tab_settings:
    st.subheader("設定")
    with st.expander("🏷️ 分類管理"):
        new_cat = st.text_input("新增支出分類")
        if st.button("新增"):
            st.session_state['categories']['支出'].append(new_cat)
            st.rerun()
    with st.expander("🌍 匯率"):
        st.session_state['rates']['VND'] = st.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
