import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 設定與初始化 ---
st.set_page_config(page_title="全資產管家 V4 (越南海外版)", page_icon="💰", layout="wide")

# 1. 匯率設定 (基準幣別為 TWD)
# 這裡設定預設匯率，側邊欄可即時調整
DEFAULT_RATES = {
    "TWD": 1.0,
    "USD": 32.5,
    "JPY": 0.21,
    "VND": 0.00128, # 1 TWD 約等於 780 VND，反算 1 VND 約 0.00128 TWD
    "EUR": 35.2,
    "CNY": 4.5
}

# 初始化 Session State
if 'rates' not in st.session_state:
    st.session_state['rates'] = DEFAULT_RATES

# 2. 初始化帳戶 (預設加入越南帳戶)
if 'accounts' not in st.session_state:
    st.session_state['accounts'] = {
        "台幣薪轉": {"type": "銀行", "currency": "TWD", "balance": 150000},
        "越南薪資戶": {"type": "銀行", "currency": "VND", "balance": 50000000}, # 5千萬盾
        "隨身皮夾(VND)": {"type": "現金", "currency": "VND", "balance": 2000000}, # 200萬盾
        "美股帳戶": {"type": "投資", "currency": "USD", "balance": 3500},
    }

# 3. 初始化流水帳
if 'data' not in st.session_state:
    # 預設一些範例資料
    st.session_state['data'] = pd.DataFrame([
        {"日期": datetime.date.today(), "帳戶": "隨身皮夾(VND)", "類型": "支出", "分類": "餐飲", "金額": 65000, "幣別": "VND", "備註": "河粉"},
        {"日期": datetime.date.today(), "帳戶": "隨身皮夾(VND)", "類型": "支出", "分類": "交通", "金額": 30000, "幣別": "VND", "備註": "Grab"},
        {"日期": datetime.date.today(), "帳戶": "台幣薪轉", "類型": "支出", "分類": "保險", "金額": 3000, "幣別": "TWD", "備註": "儲蓄險"},
        {"日期": datetime.date.today(), "帳戶": "越南薪資戶", "類型": "收入", "分類": "薪資", "金額": 45000000, "幣別": "VND", "備註": "11月薪資"},
    ])

# 4. 其他模組初始化
if 'loans' not in st.session_state:
    st.session_state['loans'] = [{
        'name': '台灣老家房貸', 'total': 10350000, 'remaining': 10350000, 
        'rate': 2.53, 'years': 30, 'start_date': datetime.date(2025, 11, 1), 'grace_period': 24
    }]
if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '平均成本', '目前市價', '幣別'])

# --- 側邊欄 ---
with st.sidebar:
    st.title("🇻🇳 全資產管家 V4")
    menu = st.radio("功能選單", ["📱 記帳與帳本", "🍰 統計分析", "💳 帳戶管理", "📊 資產儀表板", "🏠 房貸進度", "📈 投資庫存"])
    
    st.markdown("---")
    st.subheader("匯率調節 (對台幣)")
    # 讓你能調整 VND 匯率
    new_vnd = st.number_input("1 VND =", value=st.session_state['rates']['VND'], format="%.5f")
    new_usd = st.number_input("1 USD =", value=st.session_state['rates']['USD'])
    st.session_state['rates']['VND'] = new_vnd
    st.session_state['rates']['USD'] = new_usd
    
    st.caption(f"目前試算: 100萬 VND ≈ {1000000 * new_vnd:.0f} TWD")

# --- 輔助函數 ---
def convert_to_twd(amount, currency):
    return amount * st.session_state['rates'].get(currency, 1.0)

# --- 1. 記帳與帳本 ---
if menu == "📱 記帳與帳本":
    st.subheader("📝 快速記帳")
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        tx_date = c1.date_input("日期", datetime.date.today())
        tx_type = c2.selectbox("類型", ["支出", "收入", "轉帳"])
        
        # 帳戶選擇 (自動帶出幣別)
        acct_name = c3.selectbox("帳戶", list(st.session_state['accounts'].keys()))
        acct_curr = st.session_state['accounts'][acct_name]['currency']
        
        c4, c5 = st.columns(2)
        if tx_type == "支出":
            tx_cat = c4.selectbox("分類", ["餐飲", "交通", "購物", "居住", "娛樂", "醫療", "房貸", "簽證/機票"])
        elif tx_type == "收入":
            tx_cat = c4.selectbox("分類", ["薪資", "獎金", "股息", "投資收益"])
        else:
            tx_cat = c4.selectbox("分類", ["轉帳", "換匯"])
            
        tx_amt = c5.number_input(f"金額 ({acct_curr})", min_value=0.0, step=1000.0 if acct_curr=="VND" else 10.0)
        
        tx_note = st.text_input("備註")
        
        if st.button("💾 儲存", type="primary", use_container_width=True):
            new_rec = {
                "日期": tx_date, "帳戶": acct_name, "類型": tx_type, 
                "分類": tx_cat, "金額": tx_amt, "幣別": acct_curr, "備註": tx_note
            }
            st.session_state['data'] = pd.concat([pd.DataFrame([new_rec]), st.session_state['data']], ignore_index=True)
            st.success("記帳成功！")

    st.markdown("---")
    
    # 帳本顯示
    st.subheader("📒 最近紀錄")
    df_display = st.session_state['data'].copy()
    
    # 在列表中顯示台幣估值，讓你對花費有感
    df_display['約合台幣'] = df_display.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    st.dataframe(
        df_display, 
        column_config={
            "金額": st.column_config.NumberColumn(format="%.0f"), # 不顯示小數點，適合VND
            "約合台幣": st.column_config.NumberColumn(format="$%.0f"),
            "日期": st.column_config.DateColumn(format="MM-DD"),
        },
        use_container_width=True
    )

# --- 2. 統計分析 (NEW! 天天記帳風格) ---
elif menu == "🍰 統計分析":
    st.title("收支分析報表")
    
    df = st.session_state['data'].copy()
    # 關鍵步驟：將所有交易換算成 TWD 以進行統一比較
    df['金額(TWD)'] = df.apply(lambda x: convert_to_twd(x['金額'], x['幣別']), axis=1)
    
    col1, col2 = st.columns(2)
    
    # --- 支出分析 ---
    with col1:
        st.subheader("💸 支出分佈 (TWD計價)")
        df_exp = df[df['類型'] == '支出']
        if not df_exp.empty:
            # 依分類加總
            exp_chart_data = df_exp.groupby('分類')['金額(TWD)'].sum().reset_index()
            
            # 畫圓餅圖
            base = alt.Chart(exp_chart_data).encode(theta=alt.Theta("金額(TWD)", stack=True))
            pie = base.mark_arc(outerRadius=120, innerRadius=60).encode(
                color=alt.Color("分類"),
                order=alt.Order("金額(TWD)", sort="descending"),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            text = base.mark_text(radius=140).encode(
                text=alt.Text("金額(TWD)", format=",.0f"),
                order=alt.Order("金額(TWD)", sort="descending"),
                color=alt.value("black") 
            )
            st.altair_chart(pie + text, use_container_width=True)
            
            # 顯示前三名列表
            top3 = exp_chart_data.sort_values("金額(TWD)", ascending=False).head(3)
            st.write("支出 Top 3:")
            for _, row in top3.iterrows():
                st.progress(min(1.0, row['金額(TWD)'] / exp_chart_data['金額(TWD)'].sum()))
                st.caption(f"{row['分類']}: ${row['金額(TWD)']:,.0f}")
        else:
            st.info("尚無支出資料")

    # --- 收入/帳戶分析 ---
    with col2:
        st.subheader("💰 收入來源")
        df_inc = df[df['類型'] == '收入']
        if not df_inc.empty:
            inc_chart_data = df_inc.groupby('分類')['金額(TWD)'].sum().reset_index()
            pie_inc = alt.Chart(inc_chart_data).mark_arc(outerRadius=120).encode(
                theta=alt.Theta("金額(TWD)", stack=True),
                color=alt.Color("分類", scale=alt.Scale(scheme='greens')),
                tooltip=["分類", alt.Tooltip("金額(TWD)", format=",.0f")]
            )
            st.altair_chart(pie_inc, use_container_width=True)
        else:
            st.info("尚無收入資料")
            
    st.markdown("---")
    st.subheader("📊 帳戶收支流向")
    # 長條圖看哪個帳戶花最多
    bar_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('帳戶'),
        y=alt.Y('金額(TWD)', stack=True),
        color='類型',
        tooltip=['帳戶', '類型', '金額(TWD)']
    )
    st.altair_chart(bar_chart, use_container_width=True)

# --- 3. 帳戶管理 ---
elif menu == "💳 帳戶管理":
    st.subheader("錢包與帳戶")
    
    with st.expander("➕ 新增帳戶 (支援 VND)"):
        c1, c2, c3, c4 = st.columns(4)
        n_name = c1.text_input("名稱", "越南銀行")
        n_curr = c2.selectbox("幣別", ["TWD", "VND", "USD", "JPY"])
        n_bal = c3.number_input("初始餘額", value=0)
        if c4.button("新增"):
            st.session_state['accounts'][n_name] = {"type": "一般", "currency": n_curr, "balance": n_bal}
            st.success("建立成功")
            
    # 計算並顯示所有帳戶餘額
    rows = []
    total_in_twd = 0
    
    for name, info in st.session_state['accounts'].items():
        # 計算流水帳後的餘額
        df = st.session_state['data']
        inc = df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum()
        exp = df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        curr_bal = info['balance'] + inc - exp
        
        twd_val = convert_to_twd(curr_bal, info['currency'])
        total_in_twd += twd_val
        
        rows.append({
            "帳戶名稱": name,
            "幣別": info['currency'],
            "帳面餘額": curr_bal,
            "折合台幣 (TWD)": twd_val
        })
        
    st.dataframe(
        pd.DataFrame(rows),
        column_config={
            "帳面餘額": st.column_config.NumberColumn(format=",.0f"), # VND友善格式
            "折合台幣 (TWD)": st.column_config.NumberColumn(format="$%.0f"),
        },
        use_container_width=True
    )
    st.metric("👉 所有現金/存款總值 (TWD)", f"${total_in_twd:,.0f}")

# --- 4. 資產儀表板 (含房貸/投資) ---
elif menu == "📊 資產儀表板":
    st.title("全資產總覽")
    
    # 1. 帳戶總資產 (TWD)
    acct_total_twd = 0
    for name, info in st.session_state['accounts'].items():
        df = st.session_state['data']
        curr_bal = info['balance'] + \
                   df[(df['帳戶']==name) & (df['類型']=='收入')]['金額'].sum() - \
                   df[(df['帳戶']==name) & (df['類型']=='支出')]['金額'].sum()
        acct_total_twd += convert_to_twd(curr_bal, info['currency'])
        
    # 2. 投資總現值
    invest_total_twd = 0
    if not st.session_state['stocks'].empty:
        df_s = st.session_state['stocks']
        # 假設目前投資都是用 USD 或 TWD，這裡簡化計算
        # 進階版應針對每一檔股票的幣別做換算
        invest_total_twd = (df_s['持有股數'] * df_s['目前市價']).sum() # 暫時視為台幣
        
    # 3. 房產與貸款
    home_val = sum([l['total'] for l in st.session_state['loans']])
    loan_val = sum([l['remaining'] for l in st.session_state['loans']])
    
    net_worth = acct_total_twd + invest_total_twd + home_val - loan_val
    
    # 顯示
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("現金部位 (TWD)", f"${acct_total_twd:,.0f}", "含 VND/USD 換算")
    col2.metric("投資部位", f"${invest_total_twd:,.0f}")
    col3.metric("房貸負債", f"${loan_val:,.0f}", delta_color="inverse")
    col4.metric("🏆 淨資產", f"${net_worth:,.0f}")

    # 資產分佈圓餅圖
    st.subheader("資產配置")
    chart_data = pd.DataFrame([
        {"類別": "現金/存款", "金額": acct_total_twd},
        {"類別": "投資", "金額": invest_total_twd},
        {"類別": "房產淨值", "金額": home_val - loan_val}
    ])
    c = alt.Chart(chart_data).mark_arc(innerRadius=60).encode(
        theta=alt.Theta("金額", stack=True),
        color=alt.Color("類別"),
        tooltip=["類別", alt.Tooltip("金額", format=",.0f")]
    )
    st.altair_chart(c, use_container_width=True)

# --- 5. 房貸進度 ---
elif menu == "🏠 房貸進度":
    st.title("房貸管理")
    for loan in st.session_state['loans']:
        st.info(f"{loan['name']} (利率 {loan['rate']}%)")
        rem = loan['remaining']
        prog = 1 - (rem / loan['total'])
        st.progress(prog)
        c1, c2 = st.columns(2)
        c1.metric("剩餘本金", f"${rem:,.0f}")
        c2.metric("已還進度", f"{prog*100:.2f}%")
        
        if st.button("模擬繳款 (本月)"):
            st.toast("請至記帳頁面記錄房貸支出，此處僅供檢視進度")

# --- 6. 投資庫存 ---
elif menu == "📈 投資庫存":
    st.title("投資部位")
    # 這裡沿用簡易版
    with st.expander("➕ 更新持股"):
        c1, c2, c3 = st.columns(3)
        code = c1.text_input("代號")
        qty = c2.number_input("股數", 1000)
        price = c3.number_input("現價", 100.0)
        if st.button("加入"):
            new_row = pd.DataFrame([{'代號': code, '持有股數': qty, '目前市價': price, '幣別': 'TWD'}])
            st.session_state['stocks'] = pd.concat([st.session_state['stocks'], new_row], ignore_index=True)
    
    if not st.session_state['stocks'].empty:
        df = st.session_state['stocks']
        df['市值'] = df['持有股數'] * df['目前市價']
        st.dataframe(df, use_container_width=True)
