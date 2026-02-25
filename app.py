import streamlit as st
from reservation_checker import fetch_weather, judge

st.title("矢板カントリークラブ 予約最適化システム")

# 天気取得
df = fetch_weather()
results = judge(df)

# 表用 DataFrame 作成
table_df = []
for r in results:
    table_df.append({
        "日付": f"{r[0]} ({r[1]})",
        "天気": r[2],
        "判定": r[3],
        "理由": r[4]
    })

st.table(table_df)

# 赤色強調（不可の場合）
for idx, r in enumerate(results):
    if r[3] == "× 不可":
        st.markdown(f"<span style='color:red'>日付: {r[0]} 判定: {r[3]}</span>", unsafe_allow_html=True)

# 情報源リンク
st.markdown(
    "[情報源: tenki.jp 矢板カントリークラブ２週間予報](https://tenki.jp/leisure/golf/3/12/644217/week.html)"
)
