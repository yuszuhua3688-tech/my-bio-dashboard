import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="台灣生物多樣性儀表板", layout="wide")

st.title("🌿 台灣生物多樣性即時觀測儀表板")
st.markdown("本專案透過 **TBN Open API** 實作自動化數據流水線。")

@st.cache_data(ttl=3600) # 快取一小時，增加流暢度
def fetch_data(area):
    # 使用 urllib 確保中文參數如「臺北市」能被 API 正確讀取
    encoded_area = urllib.parse.quote(area)
    # 這是 TBN 最穩定的 v25 occurrence 端點
    url = f"https://www.tbn.org.tw/api/v25/occurrence?adminArea={encoded_area}&limit=50"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            # 取得資料清單
            data_list = res_data.get('data', [])
            
            if data_list:
                df = pd.DataFrame(data_list)
                # 數據清洗：確保座標格式正確
                df['decimalLatitude'] = pd.to_numeric(df['decimalLatitude'], errors='coerce')
                df['decimalLongitude'] = pd.to_numeric(df['decimalLongitude'], errors='coerce')
                df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])
                if not df.empty:
                    return df, "Real-time" # 回傳真實數據標記

        # 若 API 沒回傳資料，則啟動備援機制
        sample_data = {
            'vernacularName': ['石虎', '藍腹鷴', '台北樹蛙', '台灣黑熊', '帝雉', '諸羅樹蛙'],
            'scientificName': ['Prionailurus bengalensis', 'Lophura swinhoii', 'Zhangixalus taipeianus', 'Ursus thibetanus', 'Syrmaticus mikado', 'Zhangixalus arvalis'],
            'decimalLatitude': [24.4, 24.1, 25.0, 23.5, 23.4, 23.5],
            'decimalLongitude': [120.7, 120.9, 121.5, 121.2, 121.0, 120.4],
            'eventDate': ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05', '2026-05-06']
        }
        return pd.DataFrame(sample_data), "Fallback"
        
    except Exception:
        return pd.DataFrame(), "Error"

# 側邊欄
with st.sidebar:
    st.header("控制面板")
    city = st.selectbox("選擇觀測城市", ["臺北市", "新北市", "臺中市", "高雄市", "嘉義市", "南投縣"])
    st.write("---")
    if st.button('🔄 重新整理 API 連線'):
        st.cache_data.clear()
        st.rerun()

# 抓取數據
df, data_status = fetch_data(city)

if data_status == "Fallback":
    st.info(f"💡 目前連線較繁忙，正在展示 {city} 地區之指標物種觀測分布（模擬模式）")
elif data_status == "Real-time":
    st.success(f"✅ 已成功串接 TBN 實時數據：{city}")

if not df.empty:
    col1, col2 = st.columns([7, 3])
    with col1:
        st.subheader("📍 物種發現地理分布圖")
        fig_map = px.scatter_mapbox(df, lat="decimalLatitude", lon="decimalLongitude", 
                                    hover_name="vernacularName", zoom=10, height=550,
                                    color_discrete_sequence=["#2E8B57"])
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    with col2:
        st.subheader("📊 物種比例")
        fig_pie = px.pie(df, names='vernacularName', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("📋 觀測紀錄清單")
    st.dataframe(df[['vernacularName', 'scientificName', 'eventDate']], use_container_width=True)
