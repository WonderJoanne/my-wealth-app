import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V9.8", 
    page_icon="📱", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 定義導航常數 ---
TAB_HOME = "🏠 總覽"
TAB_ADD = "➕ 記帳"
TAB_ANALYSIS = "📊 分析"
TAB_WALLET = "💳 錢包"
TAB_SETTINGS = "⚙️ 設定"

# --- 2. CSS 樣式 (強制高對比) ---
st.markdown("""
<style>
    /* 全局背景與字體 */
    .stApp { background-color: #F4F7F6 !important; }
    
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #1F2937 !important;
        font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 導航列樣式 */
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

    /* 卡片與元件優化 */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #E5E7EB;
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

# --- 3. 資料初始化 (垂直寫法防止報錯) ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {
        "TWD": 1.0,
        "USD": 32.5,
        "JPY": 0.21,
        "VND": 0.00128,
        "EUR": 35.2
    }

if 'categories' not in st.session_state:
    st.session_state['categories'] = {
        "支出": [
            "餐飲", "交通", "購物", "居住", 
            "娛樂", "房貸", "醫療", "簽證/機票"
        ],
        "收入": [
            "薪資", "獎金", "股息", "副業", "投資收益"
        ]
    }

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {
            "type": "銀行", 
            "currency": "TWD", 
            "balance": 150000
        },
        "越南薪資": {
            "type": "銀行", 
            "currency": "VND", 
            "balance": 50000000
        },
        "隨身皮夾": {
            "type": "現金", 
            "currency": "VND", 
            "balance": 2500000
        },
        "美股儲蓄": {
            "type": "投資", 
            "currency": "USD", 
            "balance": 4200
        }
    }

if 'data' not in st.session_state:
    # 建立範例資料，每行分開寫
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
    st.session_state['stocks'] = pd.DataFrame(columns=[
        '代號', '名稱', '持有股數', '目前市價', '幣別'
    ])

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
    # 使用 .format 拼接 HTML，避免 f-string 錯誤
    hero_style = "background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 20px; color: white !important; margin-bottom: 20px;"
    hero_html = """
    <div style="{}">
        <p style="margin:0; opacity:0.8; font-size: 14px; color: white !important;">淨資產 (Net Worth)</p>
        <h1 style="margin:5px 0; color: white !important; font-size: 40px; font-weight: 700;">${:,.0f}</h1>
        <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:13px; color: white !important;">
            <span style="color: white !important;">資產: ${:,.0f}</span>
            <span style="color: white !important;">負債: ${:,.0f}</span>
        </div>
    </div>
    """.format(hero_style, net_worth, total_assets_twd + invest_val + home_val, loan_val)
    st.markdown(hero_html, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="mobile-card" style="text-align:center;"><div style="font-size:12px; color:#6B7280;">現金部位</div><div style="font-size:20px; font-weight:bold; color:#059669;">${total_assets_twd:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="mobile-card" style="text-align:center;"><div style="font-size:12px; color:#6B7280;">投資現值</div><div style="font-size:20px; font-weight:bold; color:#2563EB;">${invest_val:,.0f}</div></div>""", unsafe_allow_html=True)

    st.subheader("近期交易")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    
    for i, row in df_recent.iterrows():
        icon = '💰'
        if row['分類'] in ['餐飲', '食品']: icon = '🍜'
        elif row['分類'] in ['交通']: icon = '🚌'
        
        color = '#DC2626' if row['類型']=='支出' else '#059669'
        date_str = row['日期'].strftime('%m/%d')
        
        # 簡單字串拼接，防止斷行錯誤
        row_html = '<div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid #E5E7EB;">'
        row_html += f'<div style="display:flex; align-items:center;"><div style="background:#EFF6FF; width:42px; height:42px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px;">{icon}</div>'
        row_html += f'<div><div style="font-weight:600; font-size:16px; color:#111827 !important;">{row["分類"]}</div><div style="font-size:12px; color:#6B7280;">{row["備註"]} · {row["帳戶"]}</div></div></div>'
        row_html += f'<div style="text-align:right;"><div style="font-weight:bold; color:{color} !important;">{row["幣別"]} {row["金額"]:,.0f}</div><div style="font-size:11px; color:#9CA3AF;">{date_str}</div></div></div>'
        st.markdown(row_html, unsafe_allow_html=True)


# === ➕ 記帳 ===
elif selected_tab == TAB_ADD:
    st.subheader("新增交易")
    
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True, label_visibility="collapsed")
    
    with st.container(border=True):
        c_date, c_acct = st.columns([1, 1.5])
        tx_date = c_date.date_input("日期", datetime.date.today())
        acct_name = c_acct.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']

        st.markdown(f"<p style='margin-bottom:5px; font-size:14px; color:#6B7280;'>金額 ({curr})</p>", unsafe_allow_html=True)
        
        step_val = 1000.0 if curr == "VND" else 1.0
        tx_amt = st.number_input(
            label="金額",
            min_value=0.0,
            step=step_val,
            format="%.0f",
            label_visibility="collapsed"
        )
        
        if curr == "VND":
            st.caption(f"≈ TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        cats = st.session_state['categories']['支出'] if tx_type == "支出" else st.session_state['categories']['收入']
        if tx_type == "轉帳": cats = ["轉帳", "換匯"]
            
        tx_cat = st.selectbox("分類", cats)
        tx_note = st.text_input("備註 (選填)", placeholder="例如：午餐")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("確認記帳", type="primary"):
            new_rec = {
                "日期": tx_date,
                "帳戶": acct_name,
                "類型": tx_type,
                "分類": tx_cat,
                "金額": tx_amt,
                "幣別": curr,
                "備註": tx_note
            }
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("已儲存！")


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
            st.markdown(f"<h2 style='text-align:center; color:#DC2626 !important;'>${total_exp:,.0f}</h2>", unsafe_allow_html=True)
            st.caption("本月總支出 (TWD)")
            
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=60).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='tableau10')),
                order=alt.Order("金額(TWD)", sort="descending"),
            )
            st.altair_chart(pie, use_container_width=True)
            
            for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                pct = (row['金額(TWD)'] / total_exp) * 100
                st.write(f"**{row['分類']}** {pct:.1f}%")
                st.progress(pct/100)
        else:
            st.info("尚無支出紀錄")

    elif an_type == "收入結構":
        df_inc = df[df['類型']=='收入']
        if not df_inc.empty:
            chart_data = df_inc.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=60).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='set2')),
                order=alt.Order("金額(TWD)", sort="descending"),
            )
            st.altair_chart(pie, use_container_width=True)
        else:
            st.info("尚無收入紀錄")
            
    elif an_type == "收支趨勢":
        trend = df[df['類型'].isin(['支出', '收入'])].groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
        chart = alt.Chart(trend).mark_bar().encode(
            x='日期',
            y='金額(TWD)',
            color=alt.Color('類型', scale=alt.Scale(range=['#059669', '#DC2626'])),
            column='類型'
        )
        st.altair_chart(chart, use_container_width=True)


# === 💳 錢包 ===
elif selected_tab == TAB_WALLET:
    st.subheader("我的資產")
    
    st.markdown("##### 🏠 房貸")
    for loan in st.session_state['loans']:
        with st.container(border=True):
            prog = 1 - (loan['remaining'] / loan['total'])
            st.write(f"**{loan['name']}** ({prog*100:.1f}%)")
            st.progress(prog)
            st.caption(f"剩餘: ${loan['remaining']:,.0f}")
            
    st.markdown("##### 💳 帳戶與現金")
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        bal = info['balance'] + inc - exp
        twd_val = convert_to_twd(bal, info['currency'])
        
        # 安全拼接 HTML
        card_html = '<div class="mobile-card" style="display:flex; justify-content:space-between; align-items:center;">'
        card_html += f'<div><div style="font-weight:bold; font-size:16px; color:#111827 !important;">{name}</div><div style="font-size:12px; color:#6B7280; background:#F3F4F6; display:inline-block; padding:2px 6px; border-radius:4px; margin-top:4px;">{info["currency"]}</div></div>'
        card_html += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:bold; color:#111827 !important;">{bal:,.0f}</div><div style="font-size:12px; color:#9CA3AF;">≈ TWD {twd_val:,.0f}</div></div></div>'
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

# --- 結束 ---
