import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面設定 ---
st.set_page_config(
    page_title="AssetFlow V9.7", 
    page_icon="📱", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 1. 定義常數 (防止 SyntaxError) ---
# 將帶有 Emoji 的字串定義為變數，避免在邏輯判斷中出錯
TAB_HOME = "🏠 總覽"
TAB_ADD = "➕ 記帳"
TAB_ANALYSIS = "📊 分析"
TAB_WALLET = "💳 錢包"
TAB_SETTINGS = "⚙️ 設定"

# --- 2. CSS 樣式 ---
st.markdown("""
<style>
    .stApp { background-color: #F4F7F6 !important; }
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #1F2937 !important;
        font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 導航列 */
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

    /* 卡片與元件 */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #E5E7EB;
    }
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

# --- 3. 資料初始化 ---
if 'rates' not in st.session_state: 
    st.session_state['rates'] = {"TWD": 1.0, "USD": 32.5, "JPY
