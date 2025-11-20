# 장소 테마에 맞게 사용자 성향 및 선택 테마를 변경
PLACE_THEME_LIST = [
    "힐링/휴식",
    "익스트림/액티비티",
    "역사/문화탐방",
    "SNS/핫플레이스",
    "미식/맛집투어"
]

# =============== 성별 컬럼 벡터 =====================
def gender_to_vector(gender):
    if gender == "남성":
        return [100, 0]
    elif gender == "여성":
        return [0, 100]
    return [0, 0]  # 미입력

# =============== 나이 컬럼 벡터 =====================
def age_range_to_vector(age_range):
    mapping = {
        "10대": [100, 0, 0],
        "20대": [100, 0, 0],
        "30대": [0, 100, 0],
        "40대 이상": [0, 0, 100],
    }
    return mapping.get(age_range, [0,0,0])

# =============== 여행 스타일 컬럼 벡터 =====================
USER_PREF_TO_PLACE_THEME = {
    "휴양": "힐링/휴식",
    "액티비티": "익스트림/액티비티",
    "문화탐방": "역사/문화탐방",
    "미식": "미식/맛집투어",
    "핫플레이스": "SNS/핫플레이스",
}

def style_to_vector(styles):
    """
    사용자 성향(styles)을 장소 테마 기준 5차원 벡터로 변환한다.
    styles: ["휴양", "미식"] 이런 리스트
    """
    # 1) 사용자 성향을 장소 테마로 매핑
    mapped = [USER_PREF_TO_PLACE_THEME[s] 
              for s in styles 
              if s in USER_PREF_TO_PLACE_THEME]

    # 2) 장소 테마 5차원 벡터 생성
    vector = []
    for theme in PLACE_THEME_LIST:
        vector.append(100 if theme in mapped else 0)

    return vector


# =============== MBTI 컬럼 벡터 =====================
def mbti_to_vector(mbti):
    mbti = mbti.upper()
    return [
        100 if "E" in mbti else 0,
        100 if "I" in mbti else 0,
        100 if "S" in mbti else 0,
        100 if "N" in mbti else 0,
        100 if "T" in mbti else 0,
        100 if "F" in mbti else 0,
        100 if "J" in mbti else 0,
        100 if "P" in mbti else 0,
    ]

# =============== 계절 벡터 =====================
def season_to_vector(season):
    seasons = ["봄", "여름", "가을", "겨울"]

    vector = []
    for se in season:
        vector.append(100 if se in seasons else 0)

    return vector


def build_user_vector(dataDic):
    v_gender = gender_to_vector(dataDic["gender"])
    v_age = age_range_to_vector(dataDic["age_range"])
    v_style = style_to_vector(dataDic["travel_style"])
    v_mbti = mbti_to_vector(dataDic["mbti"])
    v_season = season_to_vector(dataDic["season"])

    analysis = ({
        "gender" : v_gender,
        "age" : v_age,
        "style" : v_style,
        "mbti" : v_mbti,
        "season" : v_season,
    })

    return analysis