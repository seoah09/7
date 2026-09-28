import streamlit as st
import requests
import pandas as pd
from datetime import date

URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

# 인증키는 Streamlit Secrets에서 가져옴
API_KEY = st.secrets["NEIS_API_KEY"]

EDU_CODE = "J10"
SCHOOL_CODE = "7530480"
MEAL_CODE = "2"

START_DATE = "20260628"
END_DATE = "20260928"

DESSERT_KEYWORDS = [
    "과일", "사과", "배", "포도", "수박", "귤",
    "오렌지", "바나나", "딸기", "키위", "복숭아",
    "메론", "멜론", "요구르트", "요거트", "푸딩",
    "아이스크림", "빙수", "케이크", "쿠키", "머핀",
    "와플", "주스", "쥬스", "음료", "식혜", "수정과",
    "우유"
]


def has_dessert(menu):
    foods = menu.replace("<br/>", "\n").split("\n")

    for food in foods:
        food = food.strip()

        for keyword in DESSERT_KEYWORDS:
            if keyword in food:
                return True

    return False


params = {
    "KEY": API_KEY,
    "Type": "json",
    "pIndex": 1,
    "pSize": 1000,
    "ATPT_OFCDC_SC_CODE": EDU_CODE,
    "SD_SCHUL_CODE": SCHOOL_CODE,
    "MMEAL_SC_CODE": MEAL_CODE,
    "MLSV_FROM_YMD": START_DATE,
    "MLSV_TO_YMD": END_DATE
}

response = requests.get(URL, params=params)
data = response.json()


if "mealServiceDietInfo" not in data:

    st.error("급식 데이터를 가져오지 못했습니다.")
    st.write(data)

else:

    rows = data["mealServiceDietInfo"][1]["row"]

    weekday_names = {
        0: "월요일",
        1: "화요일",
        2: "수요일",
        3: "목요일",
        4: "금요일"
    }

    result = []

    for row in rows:

        ymd = row["MLSV_YMD"]

        meal_date = date(
            int(ymd[:4]),
            int(ymd[4:6]),
            int(ymd[6:8])
        )

        if meal_date.weekday() >= 5:
            continue

        weekday = weekday_names[meal_date.weekday()]
        menu = row["DDISH_NM"]

        result.append({
            "날짜": meal_date,
            "요일": weekday,
            "메뉴": menu,
            "후식": "있음" if has_dessert(menu) else "없음"
        })

    df = pd.DataFrame(result)

    weekday_order = [
        "월요일",
        "화요일",
        "수요일",
        "목요일",
        "금요일"
    ]

    summary = []

    for weekday in weekday_order:

        weekday_df = df[df["요일"] == weekday]

        total = len(weekday_df)
        dessert_count = len(
            weekday_df[weekday_df["후식"] == "있음"]
        )

        percentage = (
            dessert_count / total * 100
            if total > 0 else 0
        )

        summary.append({
            "요일": weekday,
            "전체 급식 횟수": total,
            "후식 제공 횟수": dessert_count,
            "후식 제공 비율": round(percentage, 1)
        })

    summary_df = pd.DataFrame(summary)

    st.title("송탄고 급식 후식 분석")

    st.subheader("요일별 후식 제공 비율")

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        summary_df.set_index("요일")["후식 제공 비율"]
    )

    with st.expander("3개월 급식 데이터 확인"):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
