import streamlit as st
import pandas as pd
import numpy as np
import datetime

# 設定頁面配置
st.set_page_config(page_title="全資產管家", page_icon="💰", layout="wide")

# --- 側邊欄導航 ---
st.sidebar.title("💰 全資產管家")
page = st.sidebar.radio("功能選單", ["總覽儀表板", "記一筆 (含載具)", "房貸進度管理", "投資庫存管理"])

# --- 模擬資料庫 (Session State) ---
if 'balance' not in st.session_state:
    st.session_state['balance'] = 1500000 # 初始現金
if 'loans' not in st.session_state:
    st.session_state['loans'] = [] # 房貸列表
if 'stocks' not in st.session_state:
    st.session_state['stocks'] = pd.DataFrame(columns=['代號', '名稱', '持有股數', '平均成本', '目前市價'])

# --- 1. 總覽儀表板 ---
if page == "總覽儀表板":
    st.title("📊 淨資產儀表板")
    
    # 計算資產
    cash = st.session_state['balance']
    
    # 計算股票現值
    stock_value = 0
    if not st.session_state['stocks'].empty:
        stock_value = (st.session_state['stocks']['持有股數'] * st.session_state['stocks']['目前市價']).sum()
        
    # 計算負債 (房貸剩餘本金)
    liability = 0
    for loan in st.session_state['loans']:
        liability += loan['remaining_principal']
        
    net_worth = cash + stock_value - liability
    
    col1, col2, col3 = st.columns(3)
    col1.metric("總資產 (現金+股票)", f"${cash + stock_value:,.0f}", delta=None)
    col2.metric("總負債 (房貸)", f"${liability:,.0f}", delta_color="inverse")
    col3.metric("🔥 淨資產 (身價)", f"${net_worth:,.0f}", delta=f"{net_worth/1000000:.2f}M")
    
    st.markdown("---")
    st.subheader("資產分佈")
    chart_data = pd.DataFrame({
        '類別': ['現金', '投資現值', '房地產(淨值)'],
        '金額': [cash, stock_value, (10000000 - liability)] # 假設房產價值 1000萬
    })
    st.bar_chart(chart_data.set_index('類別'))

# --- 2. 記一筆 (含載具模擬) ---
elif page == "記一筆 (含載具)":
    st.title("📝 快速記帳")
    
    tab1, tab2 = st.tabs(["手動輸入", "☁️ 載具同步 (模擬)"])
    
    with tab1:
        with st.form("manual_entry"):
            date = st.date_input("日期", datetime.date.today())
            category = st.selectbox("分類", ["餐飲", "交通", "購物", "房貸還款", "投資轉帳"])
            amount = st.number_input("金額", min_value=0)
            note = st.text_input("備註")
            submitted = st.form_submit_button("記帳")
            
            if submitted:
                st.session_state['balance'] -= amount
                st.success(f"已記錄：{category} ${amount}")
                if category == "房貸還款":
                    st.info("💡 系統提示：這筆房貸支出將自動拆分為「利息」與「本金償還」")

    with tab2:
        st.write("模擬從財政部 API 抓取資料...")
        if st.button("🔄 同步載具資料"):
            # 模擬抓到的資料
            st.write("找到 3 筆新發票：")
            invoices = [
                {"store": "統一超商", "amount": 85, "cat": "早餐"},
                {"store": "台灣中油", "amount": 1200, "cat": "交通"},
                {"store": "全聯福利中心", "amount": 560, "cat": "日常用品"}
            ]
            for inv in invoices:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                col_a.text(f"{inv['store']} - ${inv['amount']}")
                col_b.text(inv['cat'])
                if col_c.button("確認入帳", key=inv['store']):
                    st.session_state['balance'] -= inv['amount']
                    st.toast(f"{inv['store']} 已入帳！")

# --- 3. 房貸進度管理 ---
elif page == "房貸進度管理":
    st.title("🏠 房貸管家")
    
    # 新增房貸功能
    with st.expander("➕ 新增房貸設定"):
        l_name = st.text_input("貸款名稱", "自住屋房貸")
        l_total = st.number_input("貸款總額", value=10000000)
        l_rate = st.number_input("年利率 (%)", value=2.1)
        l_years = st.number_input("總年限", value=30)
        if st.button("建立房貸帳戶"):
            st.session_state['loans'].append({
                'name': l_name,
                'total': l_total,
                'remaining_principal': l_total, # 初始剩餘本金
                'rate': l_rate,
                'months': l_years * 12
            })
            st.success("房貸帳戶建立完成！")

    # 顯示房貸卡片
    for i, loan in enumerate(st.session_state['loans']):
        st.markdown(f"### {loan['name']}")
        
        # 進度條計算
        progress = 1 - (loan['remaining_principal'] / loan['total'])
        st.progress(progress)
        st.caption(f"屋主擁有權進度：{progress*100:.1f}%")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("原始貸款", f"${loan['total']:,.0f}")
        c2.metric("剩餘本金", f"${loan['remaining_principal']:,.0f}")
        c3.metric("目前利率", f"{loan['rate']}%")
        
        # 試算本期還款拆帳
        monthly_rate = loan['rate'] / 100 / 12
        # 本息均攤公式簡化版
        monthly_pay = np.pmt(monthly_rate, loan['months'], -loan['total']) 
        interest = loan['remaining_principal'] * monthly_rate
        principal_pay = monthly_pay - interest
        
        st.info(f"📅 下期預估繳款：${monthly_pay:,.0f}")
        st.write(f"└─ 其中利息支出 (丟水裡)： **${interest:,.0f}**")
        st.write(f"└─ 其中償還本金 (存房子)： **${principal_pay:,.0f}**")
        
        if st.button("模擬本月繳款", key=f"pay_{i}"):
            loan['remaining_principal'] -= principal_pay
            loan['months'] -= 1
            st.session_state['balance'] -= monthly_pay
            st.success("繳款成功！剩餘本金已更新，淨資產重新計算中...")
            st.rerun()

# --- 4. 投資庫存管理 ---
elif page == "投資庫存管理":
    st.title("📈 投資庫存")
    
    with st.expander("➕ 買入股票/更新行情"):
        col_in1, col_in2, col_in3 = st.columns(3)
        s_code = col_in1.text_input("代號", "2330")
        s_name = col_in2.text_input("名稱", "台積電")
        s_qty = col_in3.number_input("股數", 1000)
        
        col_in4, col_in5 = st.columns(2)
        s_cost = col_in4.number_input("平均成本", 500.0)
        s_price = col_in5.number_input("目前市價 (模擬API)", 550.0) # 這裡模擬自動抓到的市價
        
        if st.button("新增/更新持股"):
            new_row = pd.DataFrame({
                '代號': [s_code], '名稱': [s_name], 
                '持有股數': [s_qty], '平均成本': [s_cost], '目前市價': [s_price]
            })
            st.session_state['stocks'] = pd.concat([st.session_state['stocks'], new_row], ignore_index=True)
            st.success("庫存已更新")

    if not st.session_state['stocks'].empty:
        df = st.session_state['stocks']
        # 計算損益
        df['市值'] = df['持有股數'] * df['目前市價']
        df['成本總額'] = df['持有股數'] * df['平均成本']
        df['未實現損益'] = df['市值'] - df['成本總額']
        df['報酬率'] = (df['未實現損益'] / df['成本總額']) * 100
        
        st.dataframe(df.style.format({
            "平均成本": "{:.1f}", "目前市價": "{:.1f}", 
            "市值": "{:,.0f}", "未實現損益": "{:+,.0f}", "報酬率": "{:+.2f}%"
        }))
        
        total_pl = df['未實現損益'].sum()
        st.metric("總未實現損益", f"${total_pl:+,.0f}", delta_color="normal")
