import streamlit as st
import pandas as pd
import numpy as np
import datetime

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V13", 
    page_icon="📱", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 初始化 Session State (導航用) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "總覽"

# --- 2. CSS 修復 (只針對顏色，不碰字體與結構) ---
st.markdown("""
<style>
    /* 背景色 */
    .stApp { background-color: #F8F9FA !important; }
    
    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 按鈕美化 (除了導航列之外的按鈕) */
    .stButton button {
        border-radius: 12px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 輸入框優化 */
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
    }
    
    /* 卡片效果 (僅用於裝飾，不包裹互動元件) */
    .info-card {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    /* 解決深色模式文字問題 (指定文字顏色，但不強制覆蓋 icon) */
    h1, h2, h3, p, span, label, div[data-testid="stMetricValue"] {
        color: #2D3748 !important;
    }
    
    /* 特別修正：讓 Expander 的標題正常顯示 */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 10px !important;
        color: #2D3748 !important;
        border: 1px solid #E0E0E0;
    }
    
    /* 修正錯誤提示文字顏色 */
    .stAlert { color: black !important; }
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
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000, "icon": "🏦"},
        "越南薪資": {"type": "銀行", "currency": "VND", "balance": 50000000, "icon": "🇻🇳"},
        "隨身皮夾": {"type": "現金", "currency": "VND", "balance": 2500000, "icon": "💵"},
    }

if 'data' not in st.session_state:
    r1 = {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 50000, "幣別": "VND", "備註": "範例"}
    st.session_state['data'] = pd.DataFrame([r1])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{'name': '台北房貸', 'total': 10350000, 'remaining': 10350000, 'rate': 2.53, 'years': 30, 'grace_period': 24}]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 4. 導航列 (使用 Native Buttons 防止跑版) ---
# 使用 container 包住導航，給予一個白色背景
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # 定義導航按鈕邏輯
    def nav_btn(col, label, icon, page_name):
        # 簡單的樣式判斷：如果是當前頁面，使用主要顏色，否則使用次要顏色
        if st.session_state.current_page == page_name:
            if col.button(f"{icon}\n{label}", key=f"nav_{page_name}", use_container_width=True, type="primary"):
                pass # 已經在當前頁面
        else:
            if col.button(f"{icon}\n{label}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()

    nav_btn(col1, "總覽", "🏠", "總覽")
    nav_btn(col2, "記帳", "➕", "記帳")
    nav_btn(col3, "分析", "📊", "分析")
    nav_btn(col4, "錢包", "💳", "錢包")
    nav_btn(col5, "設定", "⚙️", "設定")
    
    st.markdown("---") # 分隔線

# --- 5. 計算核心 ---
total_assets_twd = 0
total_liability_twd = 0

for name, info in st.session_state['accounts'].items():
    df = st.session_state['data']
    inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
    exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
    bal = info['balance'] + inc - exp
    
    twd_val = convert_to_twd(bal, info['currency'])
    if twd_val >= 0:
        total_assets_twd += twd_val
    else:
        total_liability_twd += abs(twd_val)
    
invest_val = 0
if not st.session_state['stocks'].empty:
    s_df = st.session_state['stocks']
    invest_val = (s_df['持有股數'] * s_df['目前市價']).sum()

loan_val = sum([l['remaining'] for l in st.session_state['loans']])
home_val = sum([l['total'] for l in st.session_state['loans']])

real_assets = total_assets_twd + invest_val + home_val
real_liabilities = total_liability_twd + loan_val
net_worth = real_assets - real_liabilities


# === 🏠 總覽 ===
if st.session_state.current_page == "總覽":
    # 總資產卡片 (使用 Markdown 渲染，不影響互動)
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
    with c1:
        st.metric("現金部位 (TWD)", f"${total_assets_twd:,.0f}")
    with c2:
        st.metric("投資現值 (TWD)", f"${invest_val:,.0f}")

    st.subheader("近期交易")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    
    for i, row in df_recent.iterrows():
        with st.container():
            st.markdown(f"**{row['分類']}** - {row['幣別']} {row['金額']:,.0f}")
            st.caption(f"{row['日期']} | {row['帳戶']} | {row['備註']}")
            st.markdown("---")


# === ➕ 記帳 ===
elif st.session_state.current_page == "記帳":
    st.subheader("新增交易")
    
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True)
    
    c_date, c_acct = st.columns(2)
    tx_date = c_date.date_input("日期", datetime.date.today())
    
    # 確保有帳戶可選
    acct_options = list(st.session_state['accounts'].keys())
    if not acct_options:
        st.warning("請先至「錢包」建立帳戶！")
        st.stop()
        
    acct_name = c_acct.selectbox("帳戶", acct_options)
    curr = st.session_state['accounts'][acct_name]['currency']

    tx_amt = st.number_input(f"金額 ({curr})", min_value=0.0, step=1000.0 if curr=="VND" else 1.0, format="%.0f")
    if curr == "VND":
        st.caption(f"≈ TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")
        
    cats = st.session_state['categories']['支出'] if tx_type == "支出" else st.session_state['categories']['收入']
    if tx_type == "轉帳": cats = ["轉帳", "換匯"]
        
    tx_cat = st.selectbox("分類", cats)
    tx_note = st.text_input("備註", placeholder="例如：午餐")

    if st.button("確認記帳", type="primary", use_container_width=True):
        new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
        st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
        st.success("已儲存！")


# === 📊 分析 ===
elif st.session_state.current_page == "分析":
    st.subheader("收支分析")
    
    df = st.session_state['data'].copy()
    if df.empty:
        st.info("尚無資料")
    else:
        df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
        
        # 簡單長條圖，避免複雜圖表報錯
        st.markdown("#### 收支趨勢")
        chart_data = df.groupby(['類型'])['金額(TWD)'].sum()
        st.bar_chart(chart_data)
        
        st.markdown("#### 詳細列表")
        st.dataframe(df, use_container_width=True)


# === 💳 錢包 (功能修復版) ===
elif st.session_state.current_page == "錢包":
    st.subheader("帳戶與資產管理")

    # 1. 新增帳戶區塊
    with st.expander("➕ 新增帳戶", expanded=False):
        c1, c2 = st.columns(2)
        n_type = c1.selectbox("類型", ["現金", "銀行", "信用卡", "投資"])
        n_curr = c2.selectbox("幣別", ["TWD", "VND", "USD"])
        n_name = st.text_input("帳戶名稱")
        n_bal = st.number_input("初始餘額", value=0)
        
        if st.button("建立"):
            if n_name:
                icon_map = {"現金":"💵", "銀行":"🏦", "信用卡":"💳", "投資":"📈"}
                st.session_state['accounts'][n_name] = {
                    "type": n_type,
                    "currency": n_curr,
                    "balance": n_bal,
                    "icon": icon_map.get(n_type, "💰")
                }
                st.rerun()

    # 2. 帳戶列表 (使用原生 Expander，保證可點擊)
    st.markdown("#### 我的帳戶 (點擊可編輯)")
    
    display_groups = ["現金", "銀行", "信用卡", "投資"]
    
    for group in display_groups:
        # 篩選
        group_accs = {k:v for k,v in st.session_state['accounts'].items() if v.get('type') == group}
        
        if group_accs:
            st.caption(f"--- {group} ---")
            for name, info in group_accs.items():
                # 計算餘額
                df = st.session_state['data']
                inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
                exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
                curr_bal = info['balance'] + inc - exp
                
                # 原生 Expander：標題直接顯示資訊
                # 注意：這裡不加任何 DIV 包裹，直接用 st.expander
                with st.expander(f"{info.get('icon','💰')} {name} : {info['currency']} {curr_bal:,.0f}"):
                    
                    c_edit1, c_edit2 = st.columns(2)
                    new_init = c_edit1.number_input("修正初始餘額", value=float(info['balance']), key=f"bal_{name}")
                    
                    if c_edit1.button("更新", key=f"save_{name}"):
                        st.session_state['accounts'][name]['balance'] = new_init
                        st.success("已更新")
                        st.rerun()
                        
                    if c_edit2.button("刪除帳戶", key=f"del_{name}"):
                        del st.session_state['accounts'][name]
                        st.rerun()
                        
                    st.caption(f"流水帳變動: +{inc} / -{exp}")

    # 3. 房貸
    st.markdown("#### 房貸")
    for loan in st.session_state['loans']:
        with st.container():
            st.info(f"{loan['name']} - 剩餘: ${loan['remaining']:,.0f}")
            st.progress(1 - (loan['remaining'] / loan['total']))


# === ⚙️ 設定 ===
elif st.session_state.current_page == "設定":
    st.subheader("設定")
    st.write("匯率設定")
    c1, c2 = st.columns(2)
    st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
    st.session_state['rates']['USD'] = c2.number_input("1 USD =", value=st.session_state['rates']['USD'])
