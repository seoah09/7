import streamlit as st
import requests
import pandas as pd
from datetime import date

# =========================
# 1. 기본 설정
# =========================

URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

# 인증키는 Streamlit Secrets에서 가져옴
API_KEY = st.secrets["NEIS_API_KEY"]

# 송탄고
EDU_CODE = "J10"
SCHOOL_CODE = "7530480"

# 중식
MEAL_CODE = "2"

# 2026년 6월 ~ 9월
START_DATE = "20260601"
END_DATE = "20260930"


# =========================
# 2. 후식 기준
# =========================

DESSERT_KEYWORDS = [
    # 과일
    "사과",
    "배",
    "포도",
    "청포도",
    "골드키위",
    "오렌지",
    "수박",
    "귤",
    "딸기",
    "바나나",
    "복숭아",
    "메론",
    "멜론",

    # 디저트
    "푸딩",
    "아이스크림",
    "케이크",
    "케익",
    "쿠키",
    "머핀",
    "와플",
    "도넛",
    "마카롱",
    "두쫀쿠",
    "감자빵",

    # 음료 / 유제품
    "요구르트",
    "요거트",
    "주스",
    "쥬스",
    "에이드",
    "음료",
    "식혜",
    "수정과",
    "우유",
    "라떼",

    # 기타 후식
    "과일화채"
]


# =========================
# 3. 후식 여부 확인
# =========================

def has_dessert(menu):

    # <br/> 기준으로 메뉴 분리
    foods = menu.replace("<br/>", "\n").split("\n")

    for food in foods:

        food = food.strip()

        # 알레르기 번호 제거
        food = food.split("(")[0].strip()

        for keyword in DESSERT_KEYWORDS:

            if keyword in food:
                return True

    return False


# =========================
# 4. 나이스 API 요청
# =========================

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


# =========================
# 5. 데이터 확인
# =========================

if "mealServiceDietInfo" not in data:

    st.error("급식 데이터를 가져오지 못했습니다.")
    st.write(data)

else:

    rows = data["mealServiceDietInfo"][1]["row"]


    # =========================
    # 6. 요일 설정
    # =========================

    weekday_names = {
        0: "월요일",
        1: "화요일",
        2: "수요일",
        3: "목요일",
        4: "금요일"
    }


    result = []


    # =========================
    # 7. 급식 데이터 분석
    # =========================

    for row in rows:

        ymd = row["MLSV_YMD"]

        meal_date = date(
            int(ymd[:4]),
            int(ymd[4:6]),
            int(ymd[6:8])
        )

        # 토요일, 일요일 제외
        if meal_date.weekday() >= 5:
            continue

        weekday = weekday_names[meal_date.weekday()]

        menu = row["DDISH_NM"]

        dessert = has_dessert(menu)

        result.append({
            "날짜": meal_date,
            "요일": weekday,
            "메뉴": menu,
            "후식": "있음" if dessert else "없음"
        })


    # =========================
    # 8. 데이터프레임 생성
    # =========================

    df = pd.DataFrame(result)


    # =========================
    # 9. 요일별 후식 비율 계산
    # =========================

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

        # 해당 요일의 전체 급식 횟수
        total = len(weekday_df)

        # 후식이 나온 횟수
        dessert_count = len(
            weekday_df[
                weekday_df["후식"] == "있음"
            ]
        )

        # 후식 제공 비율
        if total > 0:
            percentage = dessert_count / total * 100
        else:
            percentage = 0

        summary.append({
            "요일": weekday,
            "전체 급식 횟수": total,
            "후식 제공 횟수": dessert_count,
            "후식 제공 비율": round(percentage, 1)
        })


    summary_df = pd.DataFrame(summary)


    # =========================
    # 10. Streamlit 화면
    # =========================

    st.title("송탄고 급식 후식 분석")

    st.subheader("2026년 6월 ~ 9월 요일별 후식 제공 비율")


    # 요일별 결과 표
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )


    # =========================
    # 11. 막대그래프
    # =========================

    st.subheader("요일별 후식 제공 비율")

    chart_df = summary_df.set_index("요일")

    st.bar_chart(
        chart_df["후식 제공 비율"]
    )


    # =========================
    # 12. 전체 급식 데이터
    # =========================

    with st.expander("6~9월 전체 급식 데이터 확인"):

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
