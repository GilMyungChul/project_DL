import numpy as np
import tensorflow as tf
from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from .model import create_recommend_model

from travel.models import (
    Place,    
    PlaceAnalysis,
    UserProfile,
    UserAnalysis,
)

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


# ------------------------------
# 코사인 유사도
# ------------------------------
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ------------------------------
# 자동 label 생성 (상위 20% = 1, 하위 20% = 0)
# ------------------------------
def auto_label_top_bottom(user_vector, places):
    similarities = []

    for place in places:
        analysis = place.analyses.first()
        if not analysis :
            continue
        
        place_vec = build_place_vector(analysis)

        sim = cosine_similarity(user_vector, place_vec)

        similarities.append((place_vec, sim))

    if not similarities:
        return []

    similarities.sort(key=lambda x: x[1], reverse=True)

    n = len(similarities)
    top_k = max(1, int(n * 0.2))
    bottom_k = max(1, int(n * 0.2))

    train_data = []

    # positive
    for p_vec, sim in similarities[:top_k]:
        train_data.append((user_vector, p_vec, 1))

    # negative
    for p_vec, sim in similarities[-bottom_k:]:
        train_data.append((user_vector, p_vec, 0))

    return train_data



# ------------------------------
# train_data → X, y 변환
# ------------------------------
def make_feature(user_vec, place_vec):
    u = np.array(user_vec, dtype=np.float32)
    p = np.array(place_vec, dtype=np.float32)

    abs_diff = np.abs(u - p)
    prod = u * p

    return np.concatenate([u, p, abs_diff, prod])  # 100차원


def build_training_dataset(train_data):
    X = []
    y = []

    for u_vec, p_vec, label in train_data:
        feat = make_feature(u_vec, p_vec)
        X.append(feat)
        y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

# ------------------------------
# 장소 성향 벡터 합치기
# ------------------------------
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

    return vector

# ------------------------------
# 유저 성향 벡터 합치기
# ------------------------------
def build_final_user_vector(userV):
    
    mbti_v = userV.mbti_vector
    style_v = userV.style_vector
    age_v = userV.age_vector
    gender_v = userV.gender_vector

    user_vector = []

    # 2) MBTI (8)
    user_vector += mbti_v

    # 3) 성별 (4)
    user_vector += gender_v

    # 4) 나이 (4)
    user_vector += age_v

    # 5) 테마 (5)
    user_vector += style_v

    return user_vector


# ------------------------------
# 대표 유저로 학습 실행
# ------------------------------
def train_recommend_model(request):
    print("🚀 [Training] 추천 모델 학습을 시작합니다...")

    User = get_user_model()

    # (1) 대표 유저 1명 가져오기
    sample_user = User.objects.get(username="qkqh")
    if not sample_user:
        print("❌ 유저가 존재하지 않음.")
        return False

    user_vector = build_final_user_vector(sample_user.userprofile.analysis)
    if not user_vector:
        print("❌ 대표 유저의 벡터가 없습니다.")
        return False
    
    # (2) 모든 장소 가져오기
    places = Place.objects.all().prefetch_related(
        Prefetch("analyses")
    )

    # (3) auto-label 기반 학습 데이터 생성
    train_data = auto_label_top_bottom(user_vector, places)

    if not train_data:
        print("❌ train 데이터가 생성되지 않았습니다.")
        return False

    # (4) X, y 생성
    X, y = build_training_dataset(train_data)

    # (5) 모델 생성
    model = create_recommend_model(input_dim=X.shape[1])

    # (6) 학습 수행
    model.fit(
        X, y,
        epochs=20,
        batch_size=16,
        validation_split=0.1
    )

    # (7) 모델 저장
    model.save("myapp/recommend/saved_model.h5")

    print("✅ 추천 모델 학습 완료! saved_model.h5 저장됨")
    return True