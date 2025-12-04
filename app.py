import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面與手機優化設定 ---
st.set_page_config(page_title="AssetFlow V8", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# --- 1. CSS 手機版型優化 (Mobile-First CSS) ---
st.markdown("""
<style>
    /* 強制使用手機系統原生字體 (解決字體問題) */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
    }

    /* 隱藏 Streamlit 預設漢堡選單與 Footer，讓它看起來像純 APP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* 強制隱藏側邊欄 */

    /* 優化頂部導航列 (Radio Button 變身 Tab Bar) */
    div[role="radiogroup"] {
        display: flex;
        justify-content: space-between;
        width: 100%;
        background-color: white;
        padding: 10px 5px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    div[role="radiogroup"] label {
        flex: 1; /* 平均分配寬度 */
        text-align: center;
        background-color: transparent !important;
        border: none !important;
        padding: 5px !important;
    }
    
    div[role="radiogroup"] label p {
        font-size: 24px !important; /* 圖示放大 */
        margin-bottom: 0px !important;
    }
    
    /* 讓選中的項目有點變化 (Streamlit 限制較多，盡量優化) */
    div[role="radiogroup"] label[data-checked="true"] p {
        color: #2e86de !important;
        font-weight: bold;
        transform: scale(1.1);
    }

    /* 卡片樣式優化 */
    .mobile-card {
        background: white;
        padding: 15px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 12px;
        border: 1px solid #f0f2f5;
    }
    
    /* 按鈕全寬優化 */
    .stButton button {
        width: 100%;
        border-radius: 12px;
        height: 50px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 ---
DEFAULT_RATES = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'rates' not in st.session_state: st.session_state['rates'] = DEFAULT_RATES

# 初始化自訂分類 (V8 新功能)
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
    # 預設資料
    st.session_state['data'] = pd.DataFrame([
        {"日期": datetime.date.today(), "帳戶": "隨身皮夾", "類型": "支出", "分類": "餐飲", "金額": 65000, "幣別": "VND", "備註": "Pho Bo"},
        {"日期": datetime.date.today(), "帳戶": "越南薪資", "類型": "收入", "分類": "薪資", "金額": 45000000, "幣別": "VND", "備註": "薪水"},
    ])

if 'loans' not in st.session_state:
    st.session_state['loans'] = [{'name': '台北房貸', 'total': 10350000, 'remaining': 10350000, 'rate': 2.53, 'years': 30, 'grace_period': 24}]

if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '目前市價', '幣別'])

def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 3. 手機版導航列 (Top Navigation) ---
# 這是模擬 APP 的 Tab Bar，放在最上面，直覺好點
selected_tab = st.radio(
    "Mobile Nav",
    ["🏠 總覽", "➕ 記帳", "📊 分析", "💳 錢包", "⚙️ 設定"],
    horizontal=True,
    label_visibility="collapsed"
)

# --- 4. 內容區塊 ---

# 全域資產計算
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


# === 🏠 總覽頁 ===
if selected_tab == "🏠 總覽":
    # Hero Card (總資產)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%); padding: 25px; border-radius: 20px; color: white; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.15);">
        <p style="margin:0; opacity:0.7; font-size: 14px;">淨資產 (Net Worth)</p>
        <h1 style="margin:5px 0; color: white; font-size: 40px; font-weight: 700;">$""" + f"{net_worth:,.0f}" + """</h1>
        <div style="display:flex; justify-content:space-between; margin-top:10px; opacity:0.9; font-size:13px;">
            <span>資產: $""" + f"{total_assets_twd+invest_val+home_val:,.0f}" + """</span>
            <span>負債: $""" + f"{loan_val:,.0f}" + """</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 快捷狀態
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="mobile-card" style="text-align:center;">
            <div style="font-size:12px; color:gray;">現金部位</div>
            <div style="font-size:20px; font-weight:bold; color:#27ae60;">${total_assets_twd:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="mobile-card" style="text-align:center;">
            <div style="font-size:12px; color:gray;">投資現值</div>
            <div style="font-size:20px; font-weight:bold; color:#2980b9;">${invest_val:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # 近期交易
    st.subheader("近期交易")
    df_recent = st.session_state['data'].sort_index(ascending=False).head(5)
    for i, row in df_recent.iterrows():
        # 模仿手機列表設計
        with st.container():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid #f0f0f0;">
                <div style="display:flex; align-items:center;">
                    <div style="background:#f1f3f4; width:40px; height:40px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:20px;">
                        {'🍔' if row['分類'] in ['餐飲', '食品'] else '🚌' if row['分類'] in ['交通'] else '💰'}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:16px;">{row['分類']}</div>
                        <div style="font-size:12px; color:gray;">{row['備註']} · {row['帳戶']}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:bold; color:{'#e74c3c' if row['類型']=='支出' else '#27ae60'};">
                        {row['幣別']} {row['金額']:,.0f}
                    </div>
                    <div style="font-size:11px; color:silver;">{row['日期'].strftime('%m/%d')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# === ➕ 記帳頁 ===
elif selected_tab == "➕ 記帳":
    st.subheader("新增交易")
    
    # 類型切換 (使用 Streamlit 原生 pills 或 radio horizontal)
    tx_type = st.radio("類型", ["支出", "收入", "轉帳"], horizontal=True, label_visibility="collapsed")
    
    with st.container(border=True):
        c_date, c_acct = st.columns([1, 1.5])
        tx_date = c_date.date_input("日期", datetime.date.today())
        acct_name = c_acct.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        curr = st.session_state['accounts'][acct_name]['currency']

        # 金額 (大字體)
        st.markdown(f"<p style='margin-bottom:5px; font-size:14px; color:gray;'>金額 ({curr})</p>", unsafe_allow_html=True)
        tx_amt = st.number_input("金額", min_value=0.0, step=1000.0 if curr=="VND" else 1.0, format="%.0f", label_visibility="collapsed")
        
        if curr == "VND":
            st.caption(f"≈ TWD {convert_to_twd(tx_amt, 'VND'):,.0f}")
        
        # 分類 (動態讀取 session_state)
        st.markdown("<br>", unsafe_allow_html=True)
        if tx_type == "支出":
            cat_list = st.session_state['categories']['支出']
        elif tx_type == "收入":
            cat_list = st.session_state['categories']['收入']
        else:
            cat_list = ["轉帳", "換匯"]
            
        tx_cat = st.selectbox("分類", cat_list)
        tx_note = st.text_input("備註 (選填)", placeholder="例如：午餐")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("確認記帳", type="primary"):
            new_rec = {"日期": tx_date, "帳戶": acct_name, "類型": tx_type, "分類": tx_cat, "金額": tx_amt, "幣別": curr, "備註": tx_note}
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("已儲存！")


# === 📊 分析頁 ===
elif selected_tab == "📊 分析":
    st.subheader("財務分析")
    
    df = st.session_state['data'].copy()
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    # 簡易 Tab 切換
    an_type = st.radio("", ["支出分佈", "收入結構", "收支趨勢"], horizontal=True, label_visibility="collapsed")
    
    if an_type == "支出分佈":
        df_exp = df[df['類型']=='支出']
        if not df_exp.empty:
            st.markdown(f"<h2 style='text-align:center;'>${df_exp['金額(TWD)'].sum():,.0f}</h2>", unsafe_allow_html=True)
            st.caption("本月總支出 (TWD)")
            
            chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            base = alt.Chart(chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(innerRadius=60).encode(
                color=alt.Color("分類", scale=alt.Scale(scheme='category20b')),
                order=alt.Order("金額(TWD)", sort="descending"),
            )
            st.altair_chart(pie, use_container_width=True)
            
            # 排行榜
            for _, row in chart_data.sort_values("金額(TWD)", ascending=False).iterrows():
                pct = (row['金額(TWD)'] / df_exp['金額(TWD)'].sum()) * 100
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
                color=alt.Color("分類", scale=alt.Scale(scheme='category20c')),
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
            color='類型',
            column='類型'
        )
        st.altair_chart(chart, use_container_width=True)


# === 💳 錢包頁 ===
elif selected_tab == "💳 錢包":
    st.subheader("我的資產")
    
    # 房貸進度 (精簡版)
    st.markdown("##### 🏠 房貸")
    for loan in st.session_state['loans']:
        with st.container(border=True):
            prog = 1 - (loan['remaining'] / loan['total'])
            st.write(f"**{loan['name']}** ({prog*100:.1f}%)")
            st.progress(prog)
            st.caption(f"剩餘: ${loan['remaining']:,.0f}")
            
    # 帳戶列表
    st.markdown("##### 💳 帳戶與現金")
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        bal = info['balance'] + df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        
        with st.container():
            st.markdown(f"""
            <div class="mobile-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:bold; font-size:16px;">{name}</div>
                    <div style="font-size:12px; color:gray; background:#f0f0f0; display:inline-block; padding:2px 6px; border-radius:4px; margin-top:4px;">{info['currency']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:18px; font-weight:bold;">{bal:,.0f}</div>
                    <div style="font-size:12px; color:silver;">≈ TWD {convert_to_twd(bal, info['currency']):,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    # 投資列表
    st.markdown("##### 📈 股票庫存")
    if not st.session_state['stocks'].empty:
        st.dataframe(st.session_state['stocks'], use_container_width=True)


# === ⚙️ 設定頁 (新功能) ===
elif selected_tab == "⚙️ 設定":
    st.subheader("設定")
    
    with st.expander("🌍 匯率設定", expanded=True):
        c1, c2 = st.columns(2)
        st.session_state['rates']['VND'] = c1.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
        st.session_state['rates']['USD'] = c2.number_input("1 USD =", value=st.session_state['rates']['USD'])
        
    with st.expander("🏷️ 分類管理 (自訂分類)", expanded=True):
        st.caption("在此新增你的專屬分類")
        
        c_add1, c_add2 = st.columns([2, 1])
        new_exp_cat = c_add1.text_input("輸入新支出分類", placeholder="例如：按摩、孝親費")
        if c_add2.button("新增支出分類"):
            if new_exp_cat and new_exp_cat not in st.session_state['categories']['支出']:
                st.session_state['categories']['支出'].append(new_exp_cat)
                st.success(f"已新增：{new_exp_cat}")
                st.rerun()
                
        c_add3, c_add4 = st.columns([2, 1])
        new_inc_cat = c_add3.text_input("輸入新收入分類", placeholder="例如：代購")
        if c_add4.button("新增收入分類"):
            if new_inc_cat and new_inc_cat not in st.session_state['categories']['收入']:
                st.session_state['categories']['收入'].append(new_inc_cat)
                st.success(f"已新增：{new_inc_cat}")
                st.rerun()
                
        st.markdown("---")
        st.write("目前支出分類：")
        st.write(", ".join(st.session_state['categories']['支出']))
        
    with st.expander("💾 資料備份"):
        st.info("此版本為測試原型，關閉視窗後資料會重置。如需永久保存，需開發正式版 APP 並串接資料庫。")
