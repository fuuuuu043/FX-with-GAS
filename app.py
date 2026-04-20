惜しいです！URLの記述にいくつか**不要な記号（// や ? が重なっている箇所）**が含まれており、このままだとStreamlitがCSVファイルを正しく読み込めず、エラー（「スプレッドシートのデータを読み込み中...」の表示）になってしまいます。

また、GAS側のスプレッドシートにヘッダー（見出し）がない場合のエラー回避策もコードに盛り込んでおきました。

1. 修正が必要なURL
以下のURLをコピーして、app.py の SHEET_URL の部分を差し替えてください。

正しい形式のURL:
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qK0JPxTygLD_R9zynMrVOzEx_GsF56CVD0jJu0YLOSA/export?format=csv&gid=1201478238"

修正した点:

.../edit や ...//export となっていた箇所を /export に整理しました。

? が2回使われていたのを、2つ目のパラメータは & でつなぐように修正しました。

末尾の #gid=... は不要なので削除しました。

2. コードの微調整（より確実に動かすために）
GASから送られてくるデータに「見出し」がない場合を想定し、読み込み部分を少し強化した最終版です。

Python
import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="GAS連携 FX予測", layout="wide")
st_autorefresh(interval=60 * 1000, key="fxtracker")

st.title("📈 リアルタイム・ドル円予測（GAS連携版）")

# 【修正済みURL】
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qK0JPxTygLD_R9zynMrVOzEx_GsF56CVD0jJu0YLOSA/export?format=csv&gid=1201478238"

@st.cache_data(ttl=30) # キャッシュを30秒に短縮してリアルタイム性アップ
def load_data():
    # header=None を指定することで、1行目からデータが入っていても読み込めるようにします
    df = pd.read_csv(SHEET_URL, header=None)
    # 最初の2列だけを使用し、名前を固定する
    df = df.iloc[:, [0, 1]] 
    df.columns = ['ds', 'y']
    df['ds'] = pd.to_datetime(df['ds'])
    return df

try:
    df = load_data()
    
    if len(df) < 5:
        st.info("データ蓄積中... あと数分で予測が開始されます。")
    else:
        # 学習
        model = Prophet(daily_seasonality=True, weekly_seasonality=False)
        model.fit(df)
        
        # 予測
        future = model.make_future_dataframe(periods=6, freq='10min')
        forecast = model.predict(future)
        
        # グラフ作成
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], name="実績", line=dict(color='#00d1ff', width=2)))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="予測", line=dict(dash='dash', color='#ff4b4b')))
        
        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        latest_y = df['y'].iloc[-1]
        predict_y = forecast['yhat'].iloc[-1]
        col1.metric("現在価格", f"{latest_y:.3f} JPY")
        col2.metric("10分後予測", f"{predict_y:.3f} JPY", f"{predict_y - latest_y:.4f}")

except Exception as e:
    st.warning("データの読み込みに失敗しました。以下の点を確認してください：")
    st.write("1. スプレッドシートの「共有」設定が『リンクを知っている全員（閲覧者）』になっているか")
    st.write("2. GASが正しく実行され、シートにデータが書き込まれているか")
    # デバッグ用にエラー詳細を表示
    # st.write(f"エラー詳細: {e}")
