from typing import Dict, List, Any
from django.db.models import Prefetch, Q
from travel.models import Place, PlaceAnalysis, UserProfile
from datetime import date, datetime, timedelta
from numpy import dot
from numpy.linalg import norm


# 장소 테마에 맞게 사용자 성향 및 선택 테마를 변경
PLACE_THEME_LIST = [
    "힐링/휴식",
    "익스트림/액티비티",
    "역사/문화탐방",
    "SNS/핫플레이스",
    "미식/맛집투어"
]

# 장소 Anaylsis 에 themes_csv 값
THEME_KEYWORDS = {
    "힐링/휴식": [
        "힐링", "휴식", "스파", "명상", "요가",
        "도심 속 휴식처", "산책", "자연", "풍경", "자연경관",
        "산책로", "자연/생태", "자연/환경", "자연체험",
        "자연탐방", "자연/경관"
    ],

    "익스트림/액티비티": [
        "액티비티", "레저", "익스트림", "테마파크", "모험",
        "트레킹", "산책/운동"
    ],

    "역사/문화탐방": [
        "문화", "전시", "역사", "전통", "박물관",
        "전통문화", "전통/역사", "지역문화", "지역문화체험",
        "전통/역사탐방", "지역 체험", "지역 탐방/체험"
    ],

    "SNS/핫플레이스": [
        "핫플", "SNS", "인스타", "카페", "커피",
        "사진", "사진찍기", "여행 사진 촬영"
    ],

    "미식/맛집투어": [
        "맛집", "미식", "식도락", "food",
        "지역 맛집 탐방"
    ]
}


# 여행 동반자 벡터 생성
COMPANION_TYPES = ["solo", "friends", "couple", "family"]

def companion_to_vector(companion):
    vector = []
    for c in COMPANION_TYPES:
        if c == companion:
            vector.append(100)
        else:
            vector.append(0)
    return vector


# 여행 테마 벡터 생성
THEME_LIST = ["cafe", "restaurant", "festival", "nature", "culture", "park", "healing", "hotplace"]

USER_SELECT_TO_PLACE_THEME = {
    "cafe": "SNS/핫플레이스",
    "restaurant": "미식/맛집투어",
    "festival": "SNS/핫플레이스",
    "nature": "힐링/휴식",
    "culture": "역사/문화탐방",
    "park": "익스트림/액티비티",
    "healing": "힐링/휴식",
    "hotplace": "SNS/핫플레이스",
}

def theme_to_vector(selected_themes):
    """
    사용자 선택 테마를 장소 테마 기준 5차원으로 매핑 & 벡터화.
    selected_themes 예: ["카페", "맛집"]
    """

    # 1) 사용자 선택 테마 → 장소 테마로 매핑
    mapped = []
    for t in selected_themes:
        if t in USER_SELECT_TO_PLACE_THEME:
            mapped.append(USER_SELECT_TO_PLACE_THEME[t])
    # print(f"mapped ======== {mapped}")

    # 2) 5차원 벡터 생성
    vector = []
    for place_theme in PLACE_THEME_LIST:
        vector.append(100 if place_theme in mapped else 0)
    # print(f"vector ======== {vector}")
    return vector


# 여행일자로 계절 벡터 생성
SEASONS = ["봄", "여름", "가을", "겨울"]

def build_normalized_season_vector(start_date, end_date):
    # 문자열 → date 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 날짜 리스트 생성
    delta_days = (end_date - start_date).days
    dates = [start_date + timedelta(days=i) for i in range(delta_days + 1)]

    # 계절 카운트 초기화
    season_count = {"봄": 0, "여름": 0, "가을": 0, "겨울": 0}

    # 날짜별 계절 카운트
    for d in dates:
        m = d.month
        if 3 <= m <= 5:
            season = "봄"
        elif 6 <= m <= 8:
            season = "여름"
        elif 9 <= m <= 11:
            season = "가을"
        else:
            season = "겨울"
        season_count[season] += 1

    # 총 여행 일수
    total_days = len(dates)

    # 정규화된 벡터 생성 (0~100 스케일)
    season_vector = []
    for season in SEASONS:
        ratio = season_count[season] / total_days  # 비율 (0~1)
        season_vector.append(int(ratio * 100))     # 0~100 스케일

    return season_vector


# 사용자 성향 및 선택의 테마 벡터 머지
def merge_theme_vectors(pref_v, select_v):
    """
    사용자 성향 테마(pref_v) + 사용자 선택 테마(select_v)를
    장소 테마 기준 5차원 벡터로 결합한다.
    """
    merged = []
    for p, s in zip(pref_v, select_v):
        merged.append(p + s)  # 같은 테마 겹치면 200점으로 강화
    return merged


# 사용자 성향 + 사용자 선택에 대한 벡터 합치기
def build_final_user_vector(
        season_v,          # [4]
        mbti_v,            # [8]
        partner_v,         # [4]
        age_v,             # [4]
        theme_v            # [5]
    ):
    """
    장소 벡터(place_vector)와 동일한 구조로
    사용자 최종 벡터를 하나로 합친다.
    """
    user_vector = []

    # 1) 계절 (4)
    user_vector += season_v

    # 2) MBTI (8)
    user_vector += mbti_v

    # 3) 동반자 (4)
    user_vector += partner_v

    # 4) 나이 (4)
    user_vector += age_v

    # 5) 테마 (5)
    user_vector += theme_v

    return user_vector


def place_theme_to_vector(theme_str):
    if not theme_str:
        return [0, 0, 0, 0, 0]

    theme_str = theme_str.replace(" ", "")

    vector = []

    for theme in PLACE_THEME_LIST:
        keywords = THEME_KEYWORDS[theme]
        matched = any(k in theme_str for k in keywords)
        vector.append(100 if matched else 0)

    return vector


# 장소 대한 벡터 합치기
def build_place_vector(ana):

    vector = []

    # 1) 계절 (4)
    vector += [ana.season_spring, ana.season_summer,
               ana.season_autumn, ana.season_winter]

    # 2) MBTI (8)
    vector += [ana.mbti_E, ana.mbti_I, ana.mbti_S, ana.mbti_N,
               ana.mbti_T, ana.mbti_F, ana.mbti_J, ana.mbti_P]

    # 3) 동반자 (4)
    vector += [ana.group_couple, ana.group_friends,
               ana.group_family, ana.group_solo]

    # 4) 나이대 (3)
    vector += [ana.age_20s, ana.age_30s, ana.age_40s]

    # 5) 테마 (문자열 → 벡터로 변환) (5)
    theme_v = place_theme_to_vector(ana.themes_csv)
    vector += theme_v

    # print(f"장소 계절 벡터 =============== {[ana.season_spring, ana.season_summer, ana.season_autumn, ana.season_winter]}")
    # print(f"장소 mbti 벡터 =============== {[ana.mbti_E, ana.mbti_I, ana.mbti_S, ana.mbti_N, ana.mbti_T, ana.mbti_F, ana.mbti_J, ana.mbti_P]}")
    # print(f"장소 동반자 벡터 =============== {[ana.group_couple, ana.group_friends, ana.group_family, ana.group_solo]}")
    # print(f"장소 나이 벡터 =============== {[ana.age_20s, ana.age_30s, ana.age_40s]}")
    # print(f"장소 테마 벡터 =============== {theme_v}")

    return vector


def cosine_similarity(v1, v2):
    return dot(v1, v2) / (norm(v1) * norm(v2) + 1e-8)