import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(page_title="AssetFlow V6", page_icon="✨", layout="wide")

# --- 1. CSS 美學核心 (修復字體問題) ---
# 強制引入 Google Fonts (Noto Sans TC)
st.markdown("""
<style>
    /* 引入雲端字體：思源黑體 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Roboto:wght@400;700&display=swap');

    /* 套用到全域 */
    html, body, [class*="css"] {
        font-family: 'Roboto', 'Noto Sans TC', sans-serif !important; 
    }

    /* 側邊欄專屬優化 */
    section[data-testid="stSidebar"] {
        background-color: #f7f9fc; /* 極淺藍灰 */
        border-right: 1px solid #e0e0e0;
    }
    
    /* 側邊欄的 Radio 按鈕文字 */
    div[data-testid="stSidebar"] label[data-baseweb="radio"] {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #2c3e50 !important;
        padding-top: 8px;
        padding-bottom: 8px;
    }

    /* 標題與大數字優化 */
    h1, h2, h3 {
        color: #1a202c;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Metric 元件優化 */
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-family: 'Roboto', sans-serif !important; /* 數字用 Roboto 比較好看 */
    }

    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 (邏輯層) ---
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
    ])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{'name': '台北房貸', 'total': 10350000, 'remaining': 10350000, 'rate': 2.53, 'years': 30, 'grace_period': 24}]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 3. 側邊欄導航 (UI層) ---
with st.sidebar:
    st.markdown("## 💎 AssetFlow")
    st.caption("Personal Wealth OS")
    
    # 使用清楚的 Emoji + 中文，不需要依賴 CSS 隱藏標籤
    selected = st.radio(
        "功能導航", 
        ["總覽 Dashboard", "記帳 Add New", "分析 Analytics", "帳戶 Wallets", "資產 Assets"],
        index=0,
        label_visibility="collapsed" # 隱藏標題，只顯示選項
    )
    
    st.markdown("---")
    st.markdown("#### ⚙️ 匯率調節")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("VND", value=st.session_state['rates']['VND'], format="%.5f")
    st.session_state['rates']['USD'] = c2.number_input("USD", value=st.session_state['rates']['USD'])
    st.caption(f"1 TWD ≈ {1/st.session_state['rates']['VND']:.0f} VND")

# --- 4. 內容區 ---

# 計算全域資產
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

# === 總覽頁 ===
if selected == "總覽 Dashboard":
    # Hero 區塊：模仿銀行 APP 的漸層背景卡片
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <p style="margin:0; opacity:0.8; font-size: 14px;">Total Net Worth (TWD)</p>
        <h1 style="margin:5px 0; color: white; font-size: 42px;">$""" + f"{net_worth:,.0f}" + """</h1>
        <p style="margin:0; opacity:0.9; font-size: 14px;">
            Assets: $""" + f"{total_assets_twd+invest_val+home_val:,.0f}" + """ &nbsp;|&nbsp; 
            Liabilities: $""" + f"{loan_val:,.0f}" + """
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 關鍵指標
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💵 現金 (Cash)", f"${total_assets_twd:,.0f}", delta="含外幣換算")
    with c2:
        st.metric("📈 投資 (Invest)", f"${invest_val:,.0f}")
    with c3:
        st.metric("🏠 房貸 (Loan)", f"${loan_val:,.0f}", delta_color="inverse")

    # 近期交易列表 (優化版)
    st.markdown("### 📝 近期交易 Recent Activity")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    
    for i, row in df_recent.iterrows():
        with st.container(border=True):
            cols = st.columns([0.5, 3, 1.5])
            with cols[0]:
                st.markdown("🛍️" if row['類型']=="支出" else "💰")
            with cols[1]:
                st.markdown(f"**{row['分類']}** <span style='color:gray; font-size:14px'> | {row['備註']}</span>", unsafe_allow_html=True)
                st.caption(f"{row['日期']} · {row['帳戶']}")
            with cols[2]:
                color = "#e74c3c" if row['類型']=="支出" else "#27ae60" # 紅綠分明
                st.markdown(f"<div style='text-align:right; color:{color}; font-weight:bold;'>{row['幣別']} {row['金額']:,.0f}</div>", unsafe_allow_html=True)

# === 記帳頁 ===
elif selected == "記帳 Add New":
    st.header("新增一筆交易")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        tx_type = c1.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
        tx_date = c2.date_input("日期", datetime.date.today())

        st.markdown("---")
        
        c3, c4 = st.columns(2)
        acct_name = c3.selectbox("帳戶 (Wallet)", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']
        
        # 金額輸入特別優化
        tx_amt = c4.number_input(f"金額 ({curr})", min_value=0.0, step=1000.0 if curr=="VND" else 1.0, format="%.0f")
        if curr == "VND":
            st.caption(f"💡 約合 TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")

        c5, c6 = st.columns(2)
        cats = ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療", "簽證"] if tx_type=="支出" else ["薪資", "獎金", "投資"]
        tx_cat = c5.selectbox("分類", cats)
        tx_note = c6.text_input("備註")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("確認儲存 (Save)", type="primary", use_container_width=True):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("已成功記錄！")

# === 分析頁 ===
elif selected == "分析 Analytics":
    st.header("收支分析報表")
    
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    t1, t2 = st.tabs(["支出分佈", "每月趨勢"])
    
    with t1:
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            
            # 使用更簡潔的圓餅圖
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=80).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='set2')), # 使用 set2 色票，較柔和
                order=alt.Order("金額(TWD)", sort="descending"),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            text = base.mark_text(radius=120).encode(
                text=alt.Text("金額(TWD)", format=",.0f"),
                order=alt.Order("金額(TWD)", sort="descending"),
                color=alt.value("black")
            )
            st.altair_chart(pie + text, use_container_width=True)
        else:
            st.info("尚無支出資料")

    with t2:
        trend = df[df['類型']=='支出'].groupby('日期')['金額(TWD)'].sum().reset_index()
        st.bar_chart(trend.set_index('日期'))

# === 帳戶頁 ===
elif selected == "帳戶 Wallets":
    st.header("我的錢包 (My Wallets)")
    
    # 增加帳戶
    with st.expander("➕ 新增帳戶"):
        c1, c2, c3 = st.columns(3)
        n_name = c1.text_input("名稱")
        n_curr = c2.selectbox("幣別", ["VND", "TWD", "USD", "JPY"])
        n_bal = c3.number_input("餘額", 0)
        if st.button("建立"):
            st.session_state['accounts'][n_name] = {"type": "一般", "currency": n_curr, "balance": n_bal}
            st.rerun()

    # 卡片式顯示
    cols = st.columns(2)
    idx = 0
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        
        with cols[idx % 2]:
            # 使用 CSS 畫出卡片邊框
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0; border-radius:10px; padding:15px; margin-bottom:15px; background:white;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; font-size:18px;">{name}</span>
                    <span style="background:#f1f3f4; padding:2px 8px; border-radius:5px; font-size:12px;">{info['currency']}</span>
                </div>
                <h2 style="margin:10px 0; color:#2c3e50;">{bal:,.0f}</h2>
                <p style="color:gray; font-size:13px; margin:0;">≈ TWD {convert_to_twd(bal, info['currency']):,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        idx += 1

# === 資產頁 ===
elif selected == "資產 Assets":
    st.header("資產與負債管理")
    
    st.markdown("#### 🏠 房貸進度")
    for loan in st.session_state['loans']:
        with st.container(border=True):
            st.markdown(f"**{loan['name']}** (利率 {loan['rate']}%)")
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
