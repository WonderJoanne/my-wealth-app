import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面與 CSS 設定 (美學核心) ---
st.set_page_config(page_title="AssetFlow V5", page_icon="✨", layout="wide")

# 注入自定義 CSS 來美化介面
st.markdown("""
<style>
    /* 全局字體與背景優化 */
    .stApp {
        background-color: #f8f9fa; /* 極淺灰背景，保護眼睛 */
    }
    
    /* 調整側邊欄樣式 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* 卡片式容器樣式 (配合 st.container) */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        /* 這邊比較難精準定位，主要依賴 st.container(border=True) */
    }

    /* 標題樣式 */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* 讓 Metric 數字更漂亮 */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #2c3e50;
    }
    
    /* 隱藏 Streamlit 預設選單以保持乾淨 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 1. 資料初始化 (沿用 V4 邏輯) ---
DEFAULT_RATES = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'rates' not in st.session_state: st.session_state['rates'] = DEFAULT_RATES

if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000},
        "越南薪資戶": {"type": "銀行", "currency": "VND", "balance": 50000000},
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

# --- 輔助函數 ---
def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 2. 側邊欄設計 (更簡約) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2953/2953363.png", width=60) # 放一個假 Logo
    st.markdown("### AssetFlow")
    st.caption("Personal Wealth OS")
    
    st.markdown("---")
    
    # 使用 Emoji 作為導航圖示
    menu = st.radio(
        "MENU", 
        ["Dashboard 總覽", "Add Transaction 記帳", "Analytics 分析", "Accounts 帳戶", "Loans & Invest"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("🌏 匯率中心 (VND/USD)")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("VND", value=st.session_state['rates']['VND'], format="%.5f")
    st.session_state['rates']['USD'] = c2.number_input("USD", value=st.session_state['rates']['USD'])

# --- 3. 主要內容區 ---

# 計算總資產 (全頁面共用)
total_assets_twd = 0
for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    total_assets_twd += convert_to_twd(bal, info['currency'])
    
# 加上投資與房產 (簡化計算)
invest_val = 0
if not st.session_state['stocks'].empty:
    invest_val = (st.session_state['stocks']['持有股數'] * st.session_state['stocks']['目前市價']).sum() # 暫設TWD
loan_val = sum([l['remaining'] for l in st.session_state['loans']])
home_val = sum([l['total'] for l in st.session_state['loans']])
net_worth = total_assets_twd + invest_val + home_val - loan_val

# ==========================
# 🏠 Dashboard 總覽 (高質感首頁)
# ==========================
if menu == "Dashboard 總覽":
    # 1. 歡迎語 (根據時間)
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if 5 <= hour < 12 else "Good Afternoon" if 12 <= hour < 18 else "Good Evening"
    st.markdown(f"<h2 style='color:#555;'>{greeting}, User! ☕</h2>", unsafe_allow_html=True)
    
    # 2. 總資產 Hero Card (使用原生 container 模擬卡片)
    with st.container(border=True):
        col_hero1, col_hero2 = st.columns([2, 1])
        with col_hero1:
            st.caption("NET WORTH (TWD)")
            st.markdown(f"<h1 style='margin-top:-10px; font-size: 48px; color: #1e8e3e;'>${net_worth:,.0f}</h1>", unsafe_allow_html=True)
            st.caption(f"Asset: ${total_assets_twd+invest_val+home_val:,.0f} | Liability: ${loan_val:,.0f}")
        with col_hero2:
            # 簡單的進度條或裝飾
            st.write("")
            st.markdown("##### 🚀 財務自由進度")
            st.progress(min(1.0, net_worth / 30000000)) # 假設目標3000萬
            st.caption("Goal: $30M")

    # 3. 快速資訊區
    st.markdown("#### Overview")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        with st.container(border=True):
            st.metric("💵 現金部位", f"${total_assets_twd:,.0f}", delta="含 VND 換算")
    with c2:
        with st.container(border=True):
            st.metric("📈 投資現值", f"${invest_val:,.0f}", delta=f"+{(invest_val*0.05):,.0f} (Sim)")
    with c3:
        with st.container(border=True):
            st.metric("🏠 房貸餘額", f"${loan_val:,.0f}", delta_color="inverse")

    # 4. 近期交易 (簡化版列表)
    st.markdown("#### Recent Activity")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    
    for i, row in df_recent.iterrows():
        # 每一行交易做成一個小橫條
        with st.container(border=True):
            rc1, rc2, rc3 = st.columns([1, 3, 1])
            with rc1:
                # 根據類別給一個 Emoji
                icon = "🍔" if row['分類'] in ["餐飲"] else "🚌" if row['分類'] in ["交通"] else "💰"
                st.markdown(f"<div style='font-size:24px; text-align:center;'>{icon}</div>", unsafe_allow_html=True)
            with rc2:
                st.markdown(f"**{row['分類']}** - {row['備註']}")
                st.caption(f"{row['日期']} | {row['帳戶']}")
            with rc3:
                color = "red" if row['類型']=="支出" else "green"
                st.markdown(f"<div style='color:{color}; font-weight:bold; text-align:right;'>{row['幣別']} {row['金額']:,.0f}</div>", unsafe_allow_html=True)

# ==========================
# ➕ Add Transaction 記帳
# ==========================
elif menu == "Add Transaction 記帳":
    st.title("New Transaction")
    
    with st.container(border=True):
        # 第一排：日期與類型
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("Date", datetime.date.today())
        tx_type = c2.segmented_control("Type", ["支出", "收入", "轉帳"], default="支出") # 新版 Streamlit 元件 (若報錯請改回 selectbox)
        
        st.markdown("---")
        
        # 第二排：帳戶與金額
        c3, c4 = st.columns(2)
        acct_name = c3.selectbox("Account", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']
        
        # 針對 VND 特別優化的金額輸入
        tx_amt = c4.number_input(f"Amount ({curr})", min_value=0.0, step=1000.0 if curr=="VND" else 1.0, format="%.0f")
        
        # 第三排：分類與備註
        c5, c6 = st.columns(2)
        cats = ["餐飲", "交通", "購物", "居住", "娛樂", "房貸", "醫療"] if tx_type=="支出" else ["薪資", "獎金", "投資"]
        tx_cat = c5.selectbox("Category", cats)
        tx_note = c6.text_input("Note", placeholder="Ex: Coffee with friend")
        
        # 提交按鈕 (全寬)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Confirm Transaction", type="primary", use_container_width=True):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("✅ Saved successfully!")
            st.balloons()

# ==========================
# 📊 Analytics 分析 (美圖版)
# ==========================
elif menu == "Analytics 分析":
    st.title("Financial Insights")
    
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    tab1, tab2 = st.tabs(["Spending 支出", "Trend 趨勢"])
    
    with tab1:
        # 支出甜甜圈圖
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            
            # 使用 Altair 製作更現代的圖表
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(outerRadius=120, innerRadius=80, cornerRadius=10).encode( # cornerRadius 讓邊緣圓滑
                color=alt.Color("分類", scale=alt.Scale(scheme='tableau10')),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            text = base.mark_text(radius=140).encode(
                text=alt.Text("分類"), 
                color=alt.value("#333")
            )
            st.altair_chart(pie + text, use_container_width=True)
            
            # 下方顯示 Top 支出列表
            st.markdown("#### Top Expenses")
            for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['分類']}**")
                    c1.progress(min(1.0, row['金額(TWD)'] / chart_data['金額(TWD)'].sum()))
                    c2.write(f"${row['金額(TWD)']:,.0f}")
        else:
            st.info("No expense data yet.")

    with tab2:
        st.caption("Daily Spending Trend (TWD)")
        trend_data = df_exp.groupby('日期')['金額(TWD)'].sum().reset_index()
        line = alt.Chart(trend_data).mark_area(
            color="lightblue",
            interpolate='monotone',
            line={'color':'darkblue'}
        ).encode(
            x='日期',
            y='金額(TWD)'
        )
        st.altair_chart(line, use_container_width=True)

# ==========================
# 💳 Accounts 帳戶 (錢包風格)
# ==========================
elif menu == "Accounts 帳戶":
    st.title("My Wallets")
    
    # 新增帳戶按鈕
    with st.expander("➕ Add New Wallet"):
        ac1, ac2, ac3 = st.columns(3)
        n_name = ac1.text_input("Name")
        n_curr = ac2.selectbox("Currency", ["VND", "TWD", "USD"])
        n_bal = ac3.number_input("Initial Balance", 0)
        if st.button("Create"):
            st.session_state['accounts'][n_name] = {"type": "一般", "currency": n_curr, "balance": n_bal}
            st.rerun()

    # 顯示帳戶卡片
    cols = st.columns(2) # 兩欄排列
    idx = 0
    for name, info in st.session_state['accounts'].items():
        # 計算餘額
        df = st.session_state['data']
        curr_bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        
        with cols[idx % 2]:
            with st.container(border=True):
                # 卡片頭部：名稱與幣別
                c_head1, c_head2 = st.columns([3, 1])
                c_head1.markdown(f"**{name}**")
                c_head2.caption(info['currency'])
                
                # 卡片中間：大數字餘額
                st.markdown(f"<h3 style='color:#2c3e50;'>{info['currency']} {curr_bal:,.0f}</h3>", unsafe_allow_html=True)
                
                # 卡片底部：折合台幣
                twd_val = convert_to_twd(curr_bal, info['currency'])
                st.caption(f"≈ TWD {twd_val:,.0f}")
        idx += 1

# ==========================
# 🏠 Loans & Invest (資產管理)
# ==========================
elif menu == "Loans & Invest":
    st.title("Assets Management")
    
    tab_l, tab_i = st.tabs(["🏠 房貸 (Loans)", "📈 投資 (Invest)"])
    
    with tab_l:
        for loan in st.session_state['loans']:
            with st.container(border=True):
                st.markdown(f"### {loan['name']}")
                st.caption(f"Total: ${loan['total']:,.0f} | Rate: {loan['rate']}%")
                
                rem = loan['remaining']
                prog = 1 - (rem / loan['total'])
                
                # 客製化進度條樣式
                st.progress(prog)
                c1, c2 = st.columns(2)
                c1.metric("Remaining", f"${rem:,.0f}")
                c2.metric("Ownership", f"{prog*100:.1f}%")
                
                if st.button("Pay Month (Sim)", key=loan['name']):
                    st.toast("Payment recorded in simulation!")

    with tab_i:
        col_inv1, col_inv2 = st.columns([1, 2])
        with col_inv1:
            with st.container(border=True):
                st.markdown("#### Add Stock")
                code = st.text_input("Code (e.g., 2330)")
                qty = st.number_input("Qty", 1000)
                price = st.number_input("Price", 500)
                if st.button("Add"):
                    new_stk = pd.DataFrame([{'代號': code, '持有股數': qty, '目前市價': price, '幣別': 'TWD'}])
                    st.session_state['stocks'] = pd.concat([st.session_state['stocks'], new_stk], ignore_index=True)
                    st.rerun()
        
        with col_inv2:
            if not st.session_state['stocks'].empty:
                stk_df = st.session_state['stocks']
                stk_df['Val'] = stk_df['持有股數'] * stk_df['目前市價']
                
                # 顯示漂亮的清單
                for i, row in stk_df.iterrows():
                    with st.container(border=True):
                        sc1, sc2, sc3 = st.columns([2, 2, 2])
                        sc1.write(f"**{row['代號']}**")
                        sc2.write(f"{row['持有股數']} shares")
                        sc3.write(f"**${row['Val']:,.0f}**")
