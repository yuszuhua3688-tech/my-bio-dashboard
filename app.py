import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="台灣生物多樣性儀表板", layout="wide")

st.title("🌿 台灣生物多樣性即時觀測儀表板")
st.markdown("本專案透過 **TBN Open API** 實作自動化數據流水線。")

# 1. Data Pipeline: 數據抓取與清洗 (修正版)
@st.cache_data
def fetch_data(area):
    # 使用正確的 API 參數格式
    url = f"https://www.tbn.org.tw/api/v25/occurrence?adminarea={area}&limit=100"
    try:
        response = requests.get(url, timeout=10)
        res_json = response.json()
        
        # 修正: TBN API 的資料有時在 'data'，有時直接回傳 list
        data = res_json.get('data', []) if isinstance(res_json, dict) else res_json
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # 確保座標是數字
            df['decimalLatitude'] = pd.to_numeric(df['decimalLatitude'], errors='coerce')
            df['decimalLongitude'] = pd.to_numeric(df['decimalLongitude'], errors='coerce')
            df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])
        return df
    except Exception as e:
        st.error(f"連線失敗或數據格式有誤: {e}")
        return pd.DataFrame()

# 2. 側邊欄
with st.sidebar:
    st.header("控制面板")
    city = st.selectbox("選擇城市", ["臺北市", "新北市", "臺中市", "高雄市", "嘉義市"])
    if st.button('🔄 更新數據'):
        st.cache_data.clear()
        st.rerun()

df = fetch_data(city)

if not df.empty:
    col1, col2 = st.columns([6, 4])
    with col1:
        st.subheader(f"📍 {city} 物種發現地圖")
        fig_map = px.scatter_mapbox(df, lat="decimalLatitude", lon="decimalLongitude", 
                                    hover_name="vernacularName", zoom=10, height=500)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    with col2:
        st.subheader("📊 物種分布統計")
        fig_pie = px.pie(df, names='vernacularName', hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)
    st.subheader("📋 觀測明細表")
    st.dataframe(df[['vernacularName', 'scientificName', 'eventDate']], use_container_width=True)
else:
    st.warning(f"目前 {city} 暫無數據，請稍後再試或更換城市。")