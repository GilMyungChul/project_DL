import math
from sklearn.cluster import KMeans
import numpy as np

PLACE_CATEGORY_FIELD = "category"

def get_category(place):
    return getattr(place, PLACE_CATEGORY_FIELD, None)


# ---------------------
# 거리 계산 (Haversine)
# ---------------------
def _to_float_or_none(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def haversine(lat1, lon1, lat2, lon2):
    # 문자열(str)로 들어오는 경우를 대비해서 float으로 변환
    lat1 = _to_float_or_none(lat1)
    lon1 = _to_float_or_none(lon1)
    lat2 = _to_float_or_none(lat2)
    lon2 = _to_float_or_none(lon2)

    # 하나라도 값이 없으면 "엄청 먼 거리"로 취급해서 경로 최적화에서 밀어내기
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999999.0

    R = 6371  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ---------------------
# N개씩 묶어서 하루 일정 생성 (초기 버전)
# ---------------------
def split_days(places, per_day=5):
    days = []
    for i in range(0, len(places), per_day):
        days.append(places[i:i+per_day])
    return days


# ---------------------
# KMeans 기반 클러스터링
# ---------------------
def cluster_places(places, n_days=3):
    """
    places: Place 객체 리스트
    n_days: 생성할 일정 수
    return: {0: [place1, place2...], 1: [...], ...}
    """

    # 좌표만 추출
    coords = []
    valid_places = []
    for p in places:
        try:
            lat = float(p.latitude)
            lng = float(p.longitude)
            coords.append([lat, lng])
            valid_places.append(p)
        except:
            continue

    if len(valid_places) == 0:
        return {}

    coords = np.array(coords)

    # KMeans 클러스터링
    n_clusters = min(n_days, len(valid_places))  # 장소 수보다 클러스터가 많을 수 없게
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(coords)

    # 클러스터 dict
    clusters = {}
    for label, place in zip(labels, valid_places):
        clusters.setdefault(label, []).append(place)

    return clusters


# ---------------------
# 하루 내 경로 최적화 (숙소는 무조건 마지막)
# ---------------------
def optimize_route(day_places):
    if not day_places:
        return []

    # (1) 숙소(accommodations) 분리
    accommodations = [p for p in day_places if get_category(p) == "accommodations"]
    non_accommodations = [p for p in day_places if get_category(p) != "accommodations"]

    print("non_accommodations ============================", non_accommodations)
    print("accommodations ============================", accommodations)

    # (2) 기본 경로 체크
    if len(non_accommodations) == 0:
        # 전부 숙소인 경우 → 그냥 그대로 반환
        return accommodations

    # (3) 숙소 제외 장소들로 Nearest Neighbor TSP 최적화
    route = [non_accommodations[0]]
    remaining = non_accommodations[1:]

    while remaining:
        last = route[-1]
        next_place = min(
            remaining,
            key=lambda p: haversine(
                float(last.latitude), float(last.longitude),
                float(p.latitude), float(p.longitude)
            )
        )
        route.append(next_place)
        remaining.remove(next_place)

    # (4) 숙소가 있다면 마지막에 붙인다.
    if accommodations:
        # 가장 가까운 숙소를 선택하는 로직
        last = route[-1]
        nearest_acc = min(
            accommodations,
            key=lambda p: haversine(
                float(last.latitude), float(last.longitude),
                float(p.latitude), float(p.longitude)
            )
        )
        route.append(nearest_acc)

    return route


# ---------------------
# 하루 경로에 점심/저녁 식사 자동 배치
# ---------------------
def assign_meals_for_day(route):
    """
    route: Place 객체 리스트 (optimize_route() 결과)
    return: [{"place": Place, "time": "HH:MM", "meal_type": "lunch"/"dinner"/None}, ...]
    """

    n = len(route)
    if n == 0:
        return []

    # 1) 식당 위치 찾기
    restaurant_indices = [
        i for i, p in enumerate(route)
        if get_category(p) == "restaurants"
    ]

    # 식당이 하나도 없으면 그냥 시간만 배치
    lunch_idx = dinner_idx = None
    if restaurant_indices:
        # 대략 1/3 지점 = 점심, 2/3 지점 = 저녁 타겟
        lunch_target = n // 3
        dinner_target = (2 * n) // 3 if n > 2 else n - 1

        # 점심용 식당 index
        lunch_idx = min(restaurant_indices, key=lambda i: abs(i - lunch_target))

        # 저녁용 식당 index (점심과 다른 식당이면 좋음)
        remaining = [i for i in restaurant_indices if i != lunch_idx]
        if remaining:
            dinner_idx = min(remaining, key=lambda i: abs(i - dinner_target))

    # 2) 시간/meal_type 채우기
    day_plan = []
    start_hour = 10   # 하루 시작 10:00 가정
    slot_minutes = 120  # 한 장소당 2시간 가정

    cur_hour = start_hour
    cur_min = 0

    for i, place in enumerate(route):
        time_str = f"{cur_hour:02d}:{cur_min:02d}"
        meal_type = None

        if i == lunch_idx:
            time_str = "12:00"
            meal_type = "lunch"
        elif i == dinner_idx:
            time_str = "18:00"
            meal_type = "dinner"

        day_plan.append({
            "place": place,
            "time": time_str,
            "meal_type": meal_type,
        })

        # 마지막 장소가 아니면 다음 시간으로 이동
        if i != n - 1:
            cur_min += slot_minutes
            while cur_min >= 60:
                cur_min -= 60
                cur_hour += 1

    return day_plan


# ---------------------
# 전체 일정 생성
# ---------------------
# ---------------------
# KMeans 기반 일정 생성
# ---------------------
def generate_itinerary(places, n_days=3):
    # 1) KMeans로 가까운 장소끼리 묶기
    clusters = cluster_places(places, n_days=n_days)
    print("clusters ==================== ", clusters)

    itinerary = {}

    # 2) 각 클러스터(=하루 일정)에 대해 경로 최적화 + 식사 자동 배치
    for day_idx, (cluster_id, day_places) in enumerate(clusters.items(), start=1):

        # (1) 하루 경로 최적화
        optimized_route = optimize_route(day_places)

        # (2) 점심/저녁 배치
        day_plan = assign_meals_for_day(optimized_route)

        # (3) JSON-friendly로 변환
        itinerary[f"day{day_idx}"] = [
            {
                "id": item["place"].id,
                "name": item["place"].name,
                "lat": float(item["place"].latitude),
                "lng": float(item["place"].longitude),
                "time": item["time"],
                "category": get_category(item["place"]),
                "meal_type": item["meal_type"]
            }
            for item in day_plan
        ]

    return itinerary