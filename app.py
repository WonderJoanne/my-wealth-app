import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --- 0. 頁面與手機優化設定 ---
st.set_page_config(page_title="AssetFlow V9.1", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# --- 1. CSS 視覺修復 (強制高對比配色) ---
st.markdown("""
<style>
    /* 1. 全局強制設定 (解決深色模式文字消失問題) */
    .stApp {
        background-color: #F4F7F6 !important; /* 強制背景為淺灰 */
    }
    
    html, body, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #1F2937 !important; /* 強制所有文字為深灰 */
        font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    /* 2. 頂部導航列 (深色底，高對比) */
    div[role="radiogroup"] {
        background-color: #1E3A8A !important;
        padding: 10px 5px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* 導航文字與圖示強制轉白 */
    div[role="radiogroup"] p {
        color: #FFFFFF !important; 
        font-size: 20px !important;
        font-weight: 500 !important;
    }
    
    /* 選中狀態 */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: rgba(255,255,255,0.2) !important;
        border-radius: 8px;
    }

    /* 3. 卡片樣式 (白底黑字) */
    .mobile-card {
        background-color: #FFFFFF !important;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #E5E7EB;
    }
    
    .mobile-card div, .mobile-card span, .mobile-card p {
        color: #1F2937 !important;
    }

    /* 4. Streamlit 原生元件優化 */
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
    
    div[data-testid="stMetricValue"] {
        color: #1F2937 !important;
    }
    
    .stProgress > div > div > div > div {
        background-color: #2563EB !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 2. 資料初始化 ---
DEFAULT_RATES = {"TWD": 1.0, "USD": 32.5, "JPY": 0.21, "VND": 0.00128, "EUR": 35.2}

if 'rates' not in st.session_state: st.session_state['rates'] = DEFAULT_RATES

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
    st.session_state['data'] = pd.DataFrame([
        {"日期
