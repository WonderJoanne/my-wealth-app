import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(page_title="AssetFlow V7.1", page_icon="💎", layout="wide")

# --- 1. CSS 美學核心 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Roboto:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', 'Noto Sans TC', sans-serif !important; 
    }

    section[data-testid="stSidebar"] {
        background-color: #f7f9fc;
        border-right: 1px solid #e0e0e0;
    }
    
    .stRadio label {
        color: #2c3e50 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 ---
DEFAULT_RATES = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'rates' not in st.session_state: st.session_state['rates'] = DEFAULT_RATES

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000},
        "美股儲蓄": {"type": "投資", "currency": "USD", "balance": 4200},
    }

if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame([
        {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 65000, "幣別": "VND", "備註": "Pho Bo"},
        {"日期": datetime.date.today(), "帳戶": "台幣薪轉", "類型": "支出", "分類": "訂閱", "金額": 390, "幣別": "TWD", "備註": "Netflix"},
        {"日期": datetime.date.today(), "帳戶": "越南薪資", "類型": "收入", "分類": "薪資", "金額": 45000000, "幣別": "VND", "備註": "主業薪水"},
        {"日期": datetime.date.today(), "帳戶": "台幣薪轉", "類型": "收入", "分類": "副業", "金額": 5000, "幣別": "TWD", "備註": "接案"},
        {"日期": datetime.date.today(), "帳戶": "台幣薪轉", "類型": "收入", "分類": "股息", "金額": 2000, "幣別": "TWD", "備註": "ETF配息"},
    ])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{'name': '台北房貸', 'total': 10350000, 'remaining': 10350000, 'rate': 2.53, 'years': 30, 'grace_period': 24}]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown("## 💎 AssetFlow")
    st.caption("Personal Wealth OS")
    
    selected = st.radio(
        "Navigation", 
        ["總覽 Dashboard", "記帳 Add New", "分析 Analytics", "帳戶 Wallets", "資產 Assets"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("#### ⚙️ 匯率 (Exchange)")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("VND", value=st.session_state['rates']['VND'], format="%.5f")
    st.session_state['rates']['USD'] = c2.number_input("USD", value=st.session_state['rates']['USD'])
    st.caption(f"1 TWD ≈ {1/st.session_state['rates']['VND']:.0f} VND")

# --- 4. 內容區 ---

total_assets_twd = 0
for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    total_assets_twd += convert_to_twd(bal, info['currency'])
    
invest_val = 0
if not st.session_state['stocks'].empty:
    invest_val = (st.session_state['stocks']['持有股數'] * st.session_state['stocks']['目前市價']).sum()
loan_val = sum([l['remaining'] for l in st.session_state['loans']])
home_val = sum([l['total'] for l in st.session_state['loans']])
net_worth = total_assets_twd + invest_val + home_val - loan_val

# === 總覽 ===
if selected == "總覽 Dashboard":
    st.markdown("""
    <div style="background: linear-gradient(120deg, #108dc7 0%, #ef8e38 100%); padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
        <p style="margin:0; opacity:0.9; font-size: 14px; font-weight:500;">Total Net Worth (TWD)</p>
        <h1 style="margin:5px 0; color: white; font-size: 42px; font-weight:700;">$""" + f"{net_worth:,.0f}" + """</h1>
        <p style="margin:0; opacity:0.9; font-size: 13px;">
            Assets: $""" + f"{total_assets_twd+invest_val+home_val:,.0f}" + """ &nbsp; • &nbsp; 
            Liabilities: $""" + f"{loan_val:,.0f}" + """
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("💵 現金 (Cash)", f"${total_assets_twd:,.0f}")
    with c2: st.metric("📈 投資 (Invest)", f"${invest_val:,.0f}")
    with c3: st.metric("🏠 房貸 (Loan)", f"${loan_val:,.0f}", delta_color="inverse")

    st.markdown("### 📝 近期交易 Recent Activity")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    for i, row in df_recent.iterrows():
        with st.container(border=True):
            cols = st.columns([0.5, 3, 1.5])
            with cols[0]: st.markdown("🔴" if row['類型']=="支出" else "🟢")
            with cols[1]:
                st.markdown(f"**{row['分類']}** <span style='color:gray; font-size:13px'> {row['備註']}</span>", unsafe_allow_html=True)
                st.caption(f"{row['日期']} · {row['帳戶']}")
            with cols[2]:
                color = "#e74c3c" if row['類型']=="支出" else "#27ae60"
                st.markdown(f"<div style='text-align:right; color:{color}; font-weight:bold;'>{row['幣別']} {row['金額']:,.0f}</div>", unsafe_allow_html=True)

# === 記帳 ===
elif selected == "記帳 Add New":
    st.header("新增交易")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        tx_type = c1.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
        tx_date = c2.date_input("日期", datetime.date.today())
        st.markdown("---")
        c3, c4 = st.columns(2)
        acct_name = c3.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']
        tx_amt = c4.number_input(f"金額 ({curr})", min_value=0.0, step=1000.0 if curr=="VND" else 1.0, format="%.0f")
        if curr == "VND": st.caption(f"💡 約合 TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")
        c5, c6 = st.columns(2)
        cats = ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療"] if tx_type=="支出" else ["薪資", "獎金", "股息", "副業", "投資收益"]
        tx_cat = c5.selectbox("分類", cats)
        tx_note = c6.text_input("備註")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("確認儲存", type="primary", use_container_width=True):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("已記錄！")

# === 分析 (已修正) ===
elif selected == "分析 Analytics":
    st.header("📊 收支與財務分析")
    
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    t1, t2, t3 = st.tabs(["💸 支出分佈", "💰 收入結構", "📅 收支趨勢"])
    
    with t1:
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            total_exp = df_exp['金額(TWD)'].sum()
            st.metric("本月總支出 (TWD)", f"${total_exp:,.0f}")
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=70).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='reds')),
                order=alt.Order("金額(TWD)", sort="descending"),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            text = base.mark_text(radius=100).encode(
                text=alt.Text("金額(TWD)", format=",.0f"),
                order=alt.Order("金額(TWD)", sort="descending"),
                color=alt.value("black")
            )
            st.altair_chart(pie + text, use_container_width=True)
            for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                pct = (row['金額(TWD)'] / total_exp) * 100
                st.write(f"**{row['分類']}** : {pct:.1f}% (${row['金額(TWD)']:,.0f})")
                st.progress(pct/100)
        else:
            st.info("尚無支出資料")

    with t2:
        df_inc = df[df['類型']=='收入']
        if not df_inc.empty:
            total_inc = df_inc['金額(TWD)'].sum()
            st.metric("本月總收入 (TWD)", f"${total_inc:,.0f}", delta="含主業/副業/股息")
            chart_data_inc = df_inc.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data_inc).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=70).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='greens')),
                order=alt.Order("金額(TWD)", sort="descending"),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            text = base.mark_text(radius=100).encode(
                text=alt.Text("金額(TWD)", format=",.0f"),
                order=alt.Order("金額(TWD)", sort="descending"),
                color=alt.value("black")
            )
            st.altair_chart(pie + text, use_container_width=True)
            for _, row in chart_data_inc.sort_values("金額(TWD)", ascending=False).iterrows():
                pct = (row['金額(TWD)'] / total_inc) * 100
                st.write(f"**{row['分類']}** : {pct:.1f}% (${row['金額(TWD)']:,.0f})")
                st.progress(pct/100)
        else:
            st.info("尚無收入資料")

    with t3:
        st.markdown("#### 每月 收 vs 支 對比")
        trend_data = df[df['類型'].isin(['支出', '收入'])].groupby(['日期', '類型'])['金額(TWD)'].sum().reset_index()
        
        # 修正後的圖表代碼
        chart = alt.Chart(trend_data).mark_bar().encode(
            x='日期',
            y='金額(TWD)',
            color=alt.Color('類型', scale=alt.Scale(domain=['收入', '支出'], range=['#27ae60', '#e74c3c'])),
            column='類型:N',
            tooltip=['日期', '類型', '金額(TWD)']
        ).properties(width=150)
        
        st.altair_chart(chart, use_container_width=True)
        
        inc_sum = df[df['類型']=='收入']['金額(TWD)'].sum()
        exp_sum = df[df['類型']=='支出']['金額(TWD)'].sum()
        savings = inc_sum - exp_sum
        rate = (savings / inc_sum * 100) if inc_sum > 0 else 0
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("總結餘 (Savings)", f"${savings:,.0f}")
        c2.metric("儲蓄率 (Rate)", f"{rate:.1f}%")

# === 帳戶 ===
elif selected == "帳戶 Wallets":
    st.header("我的錢包")
    with st.expander("➕ 新增帳戶"):
        c1, c2, c3 = st.columns(3)
        n_name = c1.text_input("名稱")
        n_curr = c2.selectbox("幣別", ["VND", "TWD", "USD", "JPY"])
        n_bal = c3.number_input("餘額", 0)
        if st.button("建立"):
            st.session_state['accounts'][n_name] = {"type": "一般", "currency": n_curr, "balance": n_bal}
            st.rerun()

    cols = st.columns(2)
    idx = 0
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:bold; font-size:18px;">{name}</span>
                    <span style="background:#f1f3f4; padding:2px 8px; border-radius:4px; font-size:12px;">{info['currency']}</span>
                </div>
                <h2 style="margin:10px 0; color:#2c3e50;">{bal:,.0f}</h2>
                <p style="color:gray; font-size:13px; margin:0;">≈ TWD {convert_to_twd(bal, info['currency']):,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        idx += 1

# === 資產 ===
elif selected == "資產 Assets":
    st.header("資產與負債")
    st.markdown("#### 🏠 房貸進度")
    for loan in st.session_state['loans']:
        with st.container(border=True):
            st.markdown(f"**{loan['name']}**")
            prog = 1 - (loan['remaining'] / loan['total'])
            st.progress(prog)
            c1, c2 = st.columns(2)
            c1.caption(f"剩餘: ${loan['remaining']:,.0f}")
            c2.caption(f"已還: {prog*100:.1f}%")

    st.markdown("#### 📈 投資庫存")
    if not st.session_state['stocks'].empty:
        st.dataframe(st.session_state['stocks'], use_container_width=True)
    with st.expander("➕ 新增持股"):
        code = st.text_input("代號")
        qty = st.number_input("股數", 1000)
        price = st.number_input("現價", 100)
        if st.button("新增"):
            new_s = pd.DataFrame([{'代號': code, '名稱': code, '持有股數': qty, '目前市價': price, '幣別': 'TWD'}])
            st.session_state['stocks'] = pd.concat([st.session_state['stocks'], new_s], ignore_index=True)
            st.rerun()
