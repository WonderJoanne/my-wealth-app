import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V10 (Soft UI)", 
    page_icon="✨", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 定義導航常數 ---
TAB_HOME = "🏠 總覽"
TAB_ADD = "➕ 記帳"
TAB_ANALYSIS = "📊 分析"
TAB_WALLET = "💳 錢包"
TAB_SETTINGS = "⚙️ 設定"

# --- 2. CSS 美學 (莫蘭迪柔和配色) ---
st.markdown("""
<style>
    /* 全局背景：極柔和的灰藍色，保護眼睛 */
    .stApp { background-color: #F5F7FA !important; }
    
    /* 字體顏色：使用深灰而非純黑，視覺更舒適 */
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #4A5568 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 導航列：純白懸浮設計，搭配柔和陰影 */
    div[role="radiogroup"] {
        background-color: #FFFFFF !important;
        padding: 8px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); /* 極淡陰影 */
        border: 1px solid #EDF2F7;
        display: flex;
        justify-content: space-around;
    }
    
    div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
        flex: 1; /* 平均分配寬度 */
        text-align: center;
        transition: all 0.3s ease;
    }
    
    /* 導航文字：預設為柔和灰 */
    div[role="radiogroup"] p {
        color: #A0AEC0 !important; 
        font-size: 18px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    
    /* 選中狀態：淡藍色背景 + 深藍文字 */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EBF8FF !important; /* 淡藍底 */
        border-radius: 12px;
        transform: scale(1.02);
    }
    
    div[role="radiogroup"] label[data-checked="true"] p {
        color: #3182CE !important; /* 藍色字 */
        font-weight: 700 !important;
    }

    /* 卡片通用樣式：圓潤、純白、微陰影 */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
        margin-bottom: 16px;
        border: 1px solid #FFFFFF; /* 微調邊框 */
    }
    
    /* 輸入框優化 */
    input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #4A5568 !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    /* 按鈕：漸層柔和藍 */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none;
        border-radius: 15px;
        height: 55px;
        font-weight: 600;
        box-shadow: 0 4px 14px 0 rgba(118, 75, 162, 0.39) !important;
        transition: transform 0.2s;
    }
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* 數字顯示優化 */
    div[data-testid="stMetricValue"] { color: #2D3748 !important; }
    
    /* 進度條顏色 */
    .stProgress > div > div > div > div { background-color: #667eea !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

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
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 65000, "幣別": "VND", "備註": "Pho Bo"}
    r2 = {"日期": datetime.date.today(), "帳戶": "越南薪資", "類型": "收入", "分類": "薪資", "金額": 45000000, "幣別": "VND", "備註": "薪水"}
    st.session_state['data'] = pd.DataFrame([r1, r2])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{'name': '台北房貸', 'total': 10350000, 'remaining': 10350000, 'rate': 2.53, 'years': 30, 'grace_period': 24}]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 4. 導航列 ---
selected_tab = st.radio(
    "Mobile Nav",
    [TAB_HOME, TAB_ADD, TAB_ANALYSIS, TAB_WALLET, TAB_SETTINGS],
    horizontal=True,
    label_visibility="collapsed"
)

# --- 5. 計算核心 ---
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


# === 🏠 總覽 ===
if selected_tab == TAB_HOME:
    # Hero Card: 莫蘭迪漸層 (極光紫 -> 寧靜藍)
    hero_style = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 24px; color: white !important; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(118, 75, 162, 0.3);"
    hero_html = """
    <div style="{}">
        <p style="margin:0; opacity:0.8; font-size: 14px; color: white !important; letter-spacing: 0.5px;">NET WORTH (淨資產)</p>
        <h1 style="margin:10px 0; color: white !important; font-size: 42px; font-weight: 800; letter-spacing: -1px;">${:,.0f}</h1>
        <div style="display:flex; justify-content:space-between; margin-top:15px; padding-top:15px; border-top: 1px solid rgba(255,255,255,0.2); font-size:13px; color: white !important;">
            <span style="color: white !important; opacity:0.9;">總資產: ${:,.0f}</span>
            <span style="color: white !important; opacity:0.9;">總負債: ${:,.0f}</span>
        </div>
    </div>
    """.format(hero_style, net_worth, total_assets_twd + invest_val + home_val, loan_val)
    st.markdown(hero_html, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="mobile-card" style="text-align:center;"><div style="font-size:13px; color:#A0AEC0; font-weight:600;">現金部位</div><div style="font-size:22px; font-weight:700; color:#48BB78;">${total_assets_twd:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="mobile-card" style="text-align:center;"><div style="font-size:13px; color:#A0AEC0; font-weight:600;">投資現值</div><div style="font-size:22px; font-weight:700; color:#4299E1;">${invest_val:,.0f}</div></div>""", unsafe_allow_html=True)

    st.subheader("近期交易")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    
    for i, row in df_recent.iterrows():
        icon = '💰'
        if row['分類'] in ['餐飲', '食品']: icon = '🍜'
        elif row['分類'] in ['交通']: icon = '🚌'
        
        # 柔和的紅與綠
        color = '#F56565' if row['類型']=='支出' else '#48BB78'
        date_str = row['日期'].strftime('%m/%d')
        
        row_html = '<div style="display:flex; justify-content:space-between; align-items:center; padding: 16px 0; border-bottom: 1px solid #F7FAFC;">'
        row_html += f'<div style="display:flex; align-items:center;"><div style="background:#F7FAFC; width:46px; height:46px; border-radius:14px; display:flex; justify-content:center; align-items:center; margin-right:15px; font-size:22px; color:#4A5568;">{icon}</div>'
        row_html += f'<div><div style="font-weight:700; font-size:16px; color:#2D3748 !important;">{row["分類"]}</div><div style="font-size:13px; color:#A0AEC0;">{row["備註"]} · {row["帳戶"]}</div></div></div>'
        row_html += f'<div style="text-align:right;"><div style="font-weight:700; font-size:16px; color:{color} !important;">{row["幣別"]} {row["金額"]:,.0f}</div><div style="font-size:12px; color:#CBD5E0;">{date_str}</div></div></div>'
        st.markdown(row_html, unsafe_allow_html=True)


# === ➕ 記帳 ===
elif selected_tab == TAB_ADD:
    st.subheader("新增交易")
    
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True, label_visibility="collapsed")
    
    with st.container():
        # 用卡片包覆表單，更有質感
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        
        c_date, c_acct = st.columns([1, 1.5])
        tx_date = c_date.date_input("日期", datetime.date.today())
        acct_name = c_acct.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']

        st.markdown(f"<p style='margin-bottom:8px; font-size:14px; color:#718096; font-weight:500;'>金額 ({curr})</p>", unsafe_allow_html=True)
        
        step_val = 1000.0 if curr == "VND" else 1.0
        tx_amt = st.number_input("金額", min_value=0.0, step=step_val, format="%.0f", label_visibility="collapsed")
        
        if curr == "VND":
            st.caption(f"≈ TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        cats = st.session_state['categories']['支出'] if tx_type == "支出" else st.session_state['categories']['收入']
        if tx_type == "轉帳": cats = ["轉帳", "換匯"]
            
        tx_cat = st.selectbox("分類", cats)
        tx_note = st.text_input("備註 (選填)", placeholder="例如：午餐")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("確認記帳", type="primary"):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("🎉 記帳成功！")
            
        st.markdown('</div>', unsafe_allow_html=True)


# === 📊 分析 ===
elif selected_tab == TAB_ANALYSIS:
    st.subheader("財務分析")
    
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    an_type = st.radio("", ["支出分佈", "收入結構", "收支趨勢"], horizontal=True, label_visibility="collapsed")
    
    if an_type == "支出分佈":
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            total_exp = df_exp['金額(TWD)'].sum()
            # 柔和的紅色大標
            st.markdown(f"<h2 style='text-align:center; color:#F56565 !important; font-size:36px; margin-bottom:0;'>${total_exp:,.0f}</h2>", unsafe_allow_html=True)
            st.caption("本月總支出 (TWD)")
            
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            # 使用更柔和的色票 'pastel'
            pie = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=8).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='tableau20')),
                order=alt.Order("金額(TWD)", sort="descending"),
            )
            st.altair_chart(pie, use_container_width=True)
            
            st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
            for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                pct = (row['金額(TWD)'] / total_exp) * 100
                st.write(f"**{row['分類']}** {pct:.1f}%")
                st.progress(pct/100)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("尚無支出紀錄")

    elif an_type == "收入結構":
        df_inc = df[df['類型']=='收入']
        if not df_inc.empty:
            chart_data = df_inc.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=8).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='set3')),
                order=alt.Order("金額(TWD)", sort="descending"),
            )
            st.altair_chart(pie, use_container_width=True)
        else:
            st.info("尚無收入紀錄")
            
    elif an_type == "收支趨勢":
        trend = df[df['類型'].isin(['支出', '收入'])].groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
        chart = alt.Chart(trend).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x='日期',
            y='金額(TWD)',
            color=alt.Color('類型', scale=alt.Scale(range=['#48BB78', '#F56565'])), # 綠色收入，紅色支出
            column=alt.Column('類型', header=alt.Header(title=None))
        ).properties(width=120)
        st.altair_chart(chart, use_container_width=True)


# === 💳 錢包 ===
elif selected_tab == TAB_WALLET:
    st.subheader("我的資產")
    
    st.markdown("##### 🏠 房貸")
    for loan in st.session_state['loans']:
        with st.container():
            st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
            prog = 1 - (loan['remaining'] / loan['total'])
            st.write(f"**{loan['name']}** ({prog*100:.1f}%)")
            st.progress(prog)
            st.caption(f"剩餘: ${loan['remaining']:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("##### 💳 帳戶與現金")
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        twd_val = convert_to_twd(bal, info['currency'])
        
        card_html = '<div class="mobile-card" style="display:flex; justify-content:space-between; align-items:center;">'
        card_html += f'<div><div style="font-weight:bold; font-size:16px; color:#2D3748 !important;">{name}</div><div style="font-size:12px; color:#718096; background:#EDF2F7; display:inline-block; padding:3px 8px; border-radius:6px; margin-top:6px;">{info["currency"]}</div></div>'
        card_html += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:800; color:#2D3748 !important; letter-spacing:-0.5px;">{bal:,.0f}</div><div style="font-size:12px; color:#A0AEC0;">≈ TWD {twd_val:,.0f}</div></div></div>'
        st.markdown(card_html, unsafe_allow_html=True)
            
    st.markdown("##### 📈 股票庫存")
    if not st.session_state['stocks'].empty:
        st.dataframe(st.session_state['stocks'], use_container_width=True)


# === ⚙️ 設定 ===
elif selected_tab == TAB_SETTINGS:
    st.subheader("設定")
    
    with st.expander("🌍 匯率設定", expanded=True):
        c1, c2 = st.columns(2)
        st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
        st.session_state['rates']['USD'] = c2.number_input("1 USD =", value=st.session_state['rates']['USD'])
        
    with st.expander("🏷️ 分類管理", expanded=True):
        c_add1, c_add2 = st.columns([2, 1])
        new_exp_cat = c_add1.text_input("輸入新支出分類", placeholder="例如：按摩")
        if c_add2.button("新增支出"):
            if new_exp_cat and new_exp_cat not in st.session_state['categories']['支出']:
                st.session_state['categories']['支出'].append(new_exp_cat)
                st.rerun()
                
        c_add3, c_add4 = st.columns([2, 1])
        new_inc_cat = c_add3.text_input("輸入新收入分類", placeholder="例如：代購")
        if c_add4.button("新增收入"):
            if new_inc_cat and new_inc_cat not in st.session_state['categories']['收入']:
                st.session_state['categories']['收入'].append(new_inc_cat)
                st.rerun()
