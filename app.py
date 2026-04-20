import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="GAS連携 FX予測", layout="wide")
st_autorefresh(interval=60 * 1000, key="fxtracker") # 1分自動更新

st.title("📈 リアルタイム・ドル円予測（GAS連携版）")

# スプレッドシートのURL（「リンクを知っている全員が閲覧可能」に設定してください）
# 末尾を /export?format=csv に変えるのがコツです
SHEET_URL = "あなたのスプレッドシートのURL/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = ['ds', 'y']
    df['ds'] = pd.to_datetime(df['ds'])
    return df

try:
    df = load_data()
    
    # グラフと予測の推移
    model = Prophet(daily_seasonality=True, weekly_seasonality=False)
    model.fit(df)
    
    future = model.make_future_dataframe(periods=6, freq='10min')
    forecast = model.predict(future)
    
    # メイングラフ：実績と予測推移
    fig = go.Figure()
    # 実績（青い実線）
    fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], name="現在までの推移", line=dict(color='#00d1ff')))
    # 予測（赤い点線）
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="未来の予測推移", line=dict(dash='dash', color='#ff4b4b')))
    
    fig.update_layout(template="plotly_dark", height=500, xaxis_title="時刻", yaxis_title="価格 (JPY)")
    st.plotly_chart(fig, use_container_width=True)
    
    # 予測数値のサマリー
    col1, col2 = st.columns(2)
    col1.metric("最新価格", f"{df['y'].iloc[-1]:.3f}")
    col2.metric("10分後予測", f"{forecast['yhat'].iloc[-1]:.3f}", f"{forecast['yhat'].iloc[-1] - df['y'].iloc[-1]:.4f}")

except Exception as e:
    st.write("スプレッドシートのデータを読み込み中、または設定待ちです。")
