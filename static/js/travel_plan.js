let itinerary = {};
let map;
let markers = [];
let routeLine = null;

$(document).ready(function () {
    // itinerary 데이터 불러오기
    const raw = document.getElementById("itinerary-data").textContent;
    itinerary = JSON.parse(raw);

    // Map 초기화
    initMap();

    // 첫 번째 Day 로딩
    const firstDay = Object.keys(itinerary)[0];
    renderDay(firstDay);

    // Day 탭 클릭 이벤트
    $("#dayTabs .day-tab").on("click", function () {
        $("#dayTabs .day-tab").removeClass("active");
        $(this).addClass("active");

        const dayKey = $(this).data("day");
        renderDay(dayKey);
    });
});

// -------------------------------
// 1) 지도 초기화
// -------------------------------
function initMap() {
    mapboxgl.accessToken = MAPBOX_KEY;

    map = new mapboxgl.Map({
        container: 'map',
        style: "mapbox://styles/mapbox/streets-v12",
        center: [127.0, 37.5],
        zoom: 11
    });
}

// -------------------------------
// 2) Day 일정 렌더링 + 지도 업데이트
// -------------------------------
function renderDay(dayKey) {
    const places = itinerary[dayKey];

    renderScheduleList(places);
    renderMapRoute(places);
}

// -------------------------------
// 3) Sidebar 일정 리스트 출력
// -------------------------------
function renderScheduleList(places) {
    const box = $("#scheduleList");
    box.html("");

    places.forEach((p, idx) => {
        const tag = p.category === "restaurants" ? "🍽️"
                 : p.category === "accommodations" ? "🏨"
                 : "🗺️";

        const meal = p.meal_type === "lunch" ? "🥗 점심"
                  : p.meal_type === "dinner" ? "🍛 저녁"
                  : "";

        box.append(`
            <div class="schedule-item">
                <span class="schedule-time">${p.time}</span>
                <strong>${tag} ${idx+1}. ${p.name}</strong><br>
                <small>${meal}</small>
            </div>
        `);
    });
}

// -------------------------------
// 4) 지도 경로 + 마커 표시
// -------------------------------
function renderMapRoute(places) {
    // 기존 마커 제거
    markers.forEach(m => m.remove());
    markers = [];

    // 기존 라인 제거
    if (map.getLayer("route-line")) {
        map.removeLayer("route-line");
    }
    if (map.getSource("route-line")) {
        map.removeSource("route-line");
    }

    const coords = places.map(p => [p.lng, p.lat]);

    // 지도 bounds 설정
    const bounds = new mapboxgl.LngLatBounds();
    coords.forEach(c => bounds.extend(c));
    map.fitBounds(bounds, { padding: 40 });

    // 마커 추가
    coords.forEach((coord, idx) => {
        const el = document.createElement('div');
        el.style.background = "#2563eb";
        el.style.color = "white";
        el.style.width = "26px";
        el.style.height = "26px";
        el.style.borderRadius = "50%";
        el.style.display = "flex";
        el.style.alignItems = "center";
        el.style.justifyContent = "center";
        el.style.fontSize = "13px";
        el.style.fontWeight = "bold";
        el.innerText = idx + 1;

        const marker = new mapboxgl.Marker(el).setLngLat(coord).addTo(map);
        markers.push(marker);
    });

    // ⭐ 핵심: 스타일이 로딩된 뒤에만 라인 추가 ⭐
    map.once("load", () => {
        map.addSource("route-line", {
            type: "geojson",
            data: {
                type: "Feature",
                geometry: {
                    type: "LineString",
                    coordinates: coords
                }
            }
        });

        map.addLayer({
            id: "route-line",
            type: "line",
            source: "route-line",
            layout: {
                "line-join": "round",
                "line-cap": "round"
            },
            paint: {
                "line-color": "#2563eb",
                "line-width": 5
            }
        });
    });
}

