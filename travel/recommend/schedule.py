import math
from sklearn.cluster import KMeans
import numpy as np

PLACE_CATEGORY_FIELD = "category"

def get_category(place):
    return getattr(place, PLACE_CATEGORY_FIELD, None)


# # ---------------------
# # 거리 계산 (Haversine)
# # ---------------------
# def _to_float_or_none(x):
#     try:
#         return float(x)
#     except (TypeError, ValueError):
#         return None

# def haversine(lat1, lon1, lat2, lon2):
#     # 문자열(str)로 들어오는 경우를 대비해서 float으로 변환
#     lat1 = _to_float_or_none(lat1)
#     lon1 = _to_float_or_none(lon1)
#     lat2 = _to_float_or_none(lat2)
#     lon2 = _to_float_or_none(lon2)

#     # 하나라도 값이 없으면 "엄청 먼 거리"로 취급해서 경로 최적화에서 밀어내기
#     if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
#         return 9999999.0

#     R = 6371  # km
#     d_lat = math.radians(lat2 - lat1)
#     d_lon = math.radians(lon2 - lon1)
#     a = (
#         math.sin(d_lat / 2) ** 2
#         + math.cos(math.radians(lat1))
#         * math.cos(math.radians(lat2))
#         * math.sin(d_lon / 2) ** 2
#     )
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     return R * c


# # ---------------------
# # N개씩 묶어서 하루 일정 생성 (초기 버전)
# # ---------------------
# def split_days(places, per_day=5):
#     days = []
#     for i in range(0, len(places), per_day):
#         days.append(places[i:i+per_day])
#     return days


# # ---------------------
# # KMeans 기반 클러스터링
# # ---------------------
# def cluster_places(places, n_days=5):
#     """
#     places: Place 객체 리스트
#     n_days: 생성할 일정 수
#     return: {0: [place1, place2...], 1: [...], ...}
#     """

#     # 좌표만 추출
#     coords = []
#     valid_places = []
#     for p in places:
#         try:
#             lat = float(p.lat)
#             lng = float(p.lon)
#             coords.append([lat, lng])
#             valid_places.append(p)
#         except:
#             continue

#     if len(valid_places) == 0:
#         return {}

#     coords = np.array(coords)

#     # KMeans 클러스터링
#     n_clusters = min(n_days, len(valid_places))  # 장소 수보다 클러스터가 많을 수 없게
#     kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
#     labels = kmeans.fit_predict(coords)

#     # 클러스터 dict
#     clusters = {}
#     for label, place in zip(labels, valid_places):
#         clusters.setdefault(label, []).append(place)

#     return clusters


# # ---------------------
# # 하루 내 경로 최적화 (숙소는 무조건 마지막)
# # ---------------------
# def optimize_route(day_places):
#     if not day_places:
#         return []

#     # (1) 숙소(accommodations) 분리
#     accommodations = [p for p in day_places if get_category(p) == "accommodations"]
#     non_accommodations = [p for p in day_places if get_category(p) != "accommodations"]

#     # (2) 기본 경로 체크
#     if len(non_accommodations) == 0:
#         # 전부 숙소인 경우 → 그냥 그대로 반환
#         return accommodations

#     # (3) 숙소 제외 장소들로 Nearest Neighbor TSP 최적화
#     route = [non_accommodations[0]]
#     remaining = non_accommodations[1:]

#     while remaining:
#         last = route[-1]
#         next_place = min(
#             remaining,
#             key=lambda p: haversine(
#                 float(last.lat), float(last.lon),
#                 float(p.lat), float(p.lon)
#             )
#         )
#         route.append(next_place)
#         remaining.remove(next_place)

#     # (4) 숙소가 있다면 마지막에 붙인다.
#     if accommodations:
#         # 가장 가까운 숙소를 선택하는 로직
#         last = route[-1]
#         nearest_acc = min(
#             accommodations,
#             key=lambda p: haversine(
#                 float(last.lat), float(last.lon),
#                 float(p.lat), float(p.lon)
#             )
#         )
#         route.append(nearest_acc)

#     return route


# # ---------------------
# # 하루 경로에 점심/저녁 식사 자동 배치
# # ---------------------
# def assign_meals_for_day(route):
#     """
#     고도화된 일정 배치:
#     - 관광 중심 구조로 자동 정렬
#     - 점심/저녁은 종속되지 않고 자연스럽게 배치
#     """

#     if not route:
#         return []

#     # 1) 카테고리 분리
#     attractions = [p for p in route if get_category(p) == "attractions"]
#     restaurants = [p for p in route if get_category(p) == "restaurants"]
#     accommodations = [p for p in route if get_category(p) == "accommodations"]

#     # 숙소는 가장 마지막 1개만 사용
#     acc = accommodations[0] if accommodations else None

#     # 점심 / 저녁 식당 선택
#     lunch = restaurants[0] if len(restaurants) >= 1 else None
#     dinner = restaurants[1] if len(restaurants) >= 2 else None

#     # 점심/저녁 식당을 제외한 나머지 관광 리스트
#     other_attractions = attractions[:]

#     # 2) 하루 일정 순서 구성
#     final = []

#     # 10:00 관광
#     if other_attractions:
#         final.append((other_attractions.pop(0), "10:00", None))

#     # 12:00 점심
#     if lunch:
#         final.append((lunch, "12:00", "lunch"))

#     # 14:00 관광
#     if other_attractions:
#         final.append((other_attractions.pop(0), "14:00", None))

#     # 16:00 관광/식당/카페
#     if other_attractions:
#         final.append((other_attractions.pop(0), "16:00", None))

#     # 18:00 저녁
#     if dinner:
#         final.append((dinner, "18:00", "dinner"))

#     # 20:00 관광/마무리 코스
#     if other_attractions:
#         final.append((other_attractions.pop(0), "20:00", None))

#     # 21:30 숙소
#     if acc:
#         final.append((acc, "21:30", None))

#     # place/time/meal_type dict 반환
#     result = []
#     for place, t, meal in final:
#         result.append({
#             "place": place,
#             "time": t,
#             "meal_type": meal
#         })

#     return result


# # ---------------------
# # KMeans 기반 일정 생성
# # ---------------------
# def generate_itinerary(places, n_days):
#     # 1) KMeans로 가까운 장소끼리 묶기
#     clusters = cluster_places(places, n_days)
#     print("clusters ==================== ", clusters)

#     itinerary = {}

#     # 2) 각 클러스터(=하루 일정)에 대해 경로 최적화 + 식사 자동 배치
#     for day_idx, (cluster_id, day_places) in enumerate(clusters.items(), start=1):

#         # (1) 하루 경로 최적화
#         optimized_route = optimize_route(day_places)

#         # (2) 점심/저녁 배치
#         day_plan = assign_meals_for_day(optimized_route)

#         # (3) JSON-friendly로 변환
#         itinerary[f"day{day_idx}"] = [
#             {
#                 "id": item["place"].id,
#                 "name": item["place"].name,
#                 "lat": float(item["place"].lat),
#                 "lng": float(item["place"].lon),
#                 "time": item["time"],
#                 "category": get_category(item["place"]),
#                 "meal_type": item["meal_type"]
#             }
#             for item in day_plan
#         ]

#     return itinerary


def place_to_item(place, time_str, meal_type=None):
    """Place 객체를 itinerary용 dict로 변환"""
    return {
        "id": place.id,
        "name": place.name,
        "lat": place.lat,
        "lng": place.lon,
        "time": time_str,
        "category": get_category(place),
        "meal_type": meal_type,
    }


def generate_itinerary_pattern(act_top, res_top, acc_top, total_days):
    """
    패턴 기반 일정 생성:
    - 하루 기준:
      10:00 관광
      12:00 점심 (식당1)
      14:00 관광
      16:00 관광
      18:00 저녁 (식당2)
      20:00 관광/마무리
      21:30 숙소
    """

    # 추천 결과에서 Place만 뽑기
    act_places = [x["place"] for x in act_top]
    res_places = [x["place"] for x in res_top]
    acc_places = [x["place"] for x in acc_top]

    def safe_get(lst, idx):
        return lst[idx] if idx < len(lst) else None

    itinerary = {}

    for day_idx in range(total_days):
        day_key = f"day{day_idx + 1}"
        day_list = []

        a_base = day_idx * 3      # 관광 3개씩 배분
        r_base = day_idx * 2      # 식당 2개씩 배분
        acc_idx = day_idx         # 숙소 1개씩 배분

        a1 = safe_get(act_places, a_base)
        a2 = safe_get(act_places, a_base + 1)
        a3 = safe_get(act_places, a_base + 2)

        r1 = safe_get(res_places, r_base)
        r2 = safe_get(res_places, r_base + 1)

        acc = safe_get(acc_places, acc_idx)

        # 10:00 관광
        if a1:
            day_list.append(place_to_item(a1, "10:00"))

        # 12:00 점심 (식당1 있으면 식당, 없으면 관광으로 대체)
        if r1:
            day_list.append(place_to_item(r1, "12:00", "lunch"))
        elif a2:
            day_list.append(place_to_item(a2, "12:00"))
            a2 = None  # 이미 사용

        # 14:00 관광
        if a2:
            day_list.append(place_to_item(a2, "14:00"))
        elif a3:
            day_list.append(place_to_item(a3, "14:00"))
            a3 = None

        # 16:00 관광
        if a3:
            day_list.append(place_to_item(a3, "16:00"))

        # 18:00 저녁 (식당2 있으면 식당, 없으면 식당1 재사용)
        if r2:
            day_list.append(place_to_item(r2, "18:00", "dinner"))
        elif r1:
            # 식당이 하나밖에 없으면 같은 식당을 저녁으로 한 번 더 사용
            day_list.append(place_to_item(r1, "18:00", "dinner"))

        # 20:00 남는 관광/식당 아무거나 하나 더
        # 아직 쓰지 않은 관광이 남으면 관광 우선
        extra = None
        extra_idx = a_base + 3
        extra = safe_get(act_places, extra_idx)
        if extra:
            day_list.append(place_to_item(extra, "20:00"))
        # 그래도 없으면 남는 식당이라도 한 번 더
        elif len(res_places) > r_base + 2:
            day_list.append(place_to_item(res_places[r_base + 2], "20:00"))

        # 21:30 숙소
        if acc:
            day_list.append(place_to_item(acc, "21:30"))

        itinerary[day_key] = day_list

    return itinerary