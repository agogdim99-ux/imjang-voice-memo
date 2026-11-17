"""수도권 지역 정규화 + 토지거래허가구역(토허) 판정 — 2026년 11월 기준.

구분
  A  토허구역      : 갭투자 불가(2년 실거주 의무), 실거주 매수는 허가 필요. 규제지역(LTV 40%)으로 본다.
  B  비대상·비규제 : 갭투자·실거주 모두 가능. LTV 70%.
  C  개별 지정 구역: 인천경제자유구역(송도·청라·영종) 등 별도 고시. 갭투자 불가로 보수 판정, LTV 70%.

한계: 시·군·구(+일부 동 이름) 단위 판정이다. 공공주택지구·재개발 후보지처럼
지번 단위로 지정된 구역은 잡지 못하므로 출력에 항상 '지번 단위 확인 필요'를 붙인다.
"""

SEOUL_GU = [
    "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
    "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구", "금천구",
    "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구",
]

# 2026-07-01 행정체제 개편 후: 9구 2군 (제물포구·영종구·서해구·검단구 출범).
# 녹음에서는 옛 이름(중구·동구·서구)도 흔히 쓰므로 함께 인식한다.
INCHEON_GU = [
    "제물포구", "영종구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서해구", "검단구",
    "강화군", "옹진군",
    "중구", "동구", "서구",  # 개편 전 이름
]

GYEONGGI_SI = [
    "수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시",
    "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시",
    "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "양주시", "포천시",
    "여주시", "연천군", "가평군", "양평군",
]

# 시 아래 일반구 (판정에 필요한 곳 위주)
GYEONGGI_GU = {
    "수원시": ["장안구", "권선구", "팔달구", "영통구"],
    "성남시": ["수정구", "중원구", "분당구"],
    "안양시": ["만안구", "동안구"],
    "용인시": ["처인구", "기흥구", "수지구"],
    "부천시": ["원미구", "소사구", "오정구"],
    "고양시": ["덕양구", "일산동구", "일산서구"],
    "안산시": ["상록구", "단원구"],
    "화성시": ["만세구", "효행구", "병점구", "동탄구"],
}

# A: 2025-10-20 지정(서울 전역 + 경기 12곳) + 2026-07 추가(화성 동탄·구리·용인 기흥)
TOHU_GYEONGGI_WHOLE_CITY = {"과천시", "광명시", "성남시", "의왕시", "하남시", "구리시"}
TOHU_GYEONGGI_GU = {
    ("수원시", "영통구"), ("수원시", "장안구"), ("수원시", "팔달구"),
    ("안양시", "동안구"), ("용인시", "수지구"), ("용인시", "기흥구"), ("화성시", "동탄구"),
}
# 시 이름만 들렸을 때 일부 구만 토허인 도시 → '구 확인 필요'
PARTIAL_TOHU_CITY = {"수원시", "안양시", "용인시", "화성시"}

# C: 인천경제자유구역 (동·지명 키워드)
IFEZ_KEYWORDS = ["송도", "청라", "영종", "운서", "운남", "운북", "중산동"]

SIDO_ALIASES = {
    "서울특별시": ["서울"],
    "인천광역시": ["인천"],
    "경기도": ["경기"],
}


def _strip_suffix(name: str) -> str:
    for suf in ("특별시", "광역시", "도", "시", "군", "구"):
        if name.endswith(suf) and len(name) > len(suf):
            return name[: -len(suf)]
    return name


def normalize_region(sido: str | None, sigungu: str | None, dong: str | None, raw_text: str = "") -> dict:
    """LLM/규칙 추출 결과와 원문을 함께 보고 (시·도, 시, 구, 동)을 정규화한다."""
    hay = " ".join(x for x in (sido, sigungu, dong, raw_text) if x)

    found_sido = None
    for full, aliases in SIDO_ALIASES.items():
        if full in hay or any(a in hay for a in aliases):
            found_sido = full
            break

    city = gu = None
    # 경기 시 (이름에서 '시'를 떼고도 찾는다: "부천 원미구", "성남 분당구")
    for si in (GYEONGGI_SI if found_sido in (None, "경기도") else []):
        if si in hay or _strip_suffix(si) in hay:
            if si == "광주시" and "광주광역시" in hay:
                continue
            city = si
            found_sido = found_sido or "경기도"
            for g in GYEONGGI_GU.get(si, []):
                if g in hay or _strip_suffix(g) in hay:
                    gu = g
            break
    if city is None and found_sido in (None, "경기도"):
        # 경기 일반구만 말한 경우 ("분당구 정자동")
        for si, gus in GYEONGGI_GU.items():
            for g in gus:
                if g in hay:
                    city, gu = si, g
                    found_sido = found_sido or "경기도"
                    break
            if city:
                break

    if city is None:
        candidates = []
        if found_sido in (None, "서울특별시"):
            candidates += [("서울특별시", g) for g in SEOUL_GU]
        if found_sido in (None, "인천광역시"):
            candidates += [("인천광역시", g) for g in INCHEON_GU]
        # 긴 이름부터 비교해야 '남동구' 안의 '동구'를 잘못 잡지 않는다
        candidates.sort(key=lambda c: -len(c[1]))
        for s, g in candidates:
            # 중구·동구·서구는 시·도가 없으면 판단하지 않는다(서울/인천 중복)
            if g in ("중구", "동구", "서구") and found_sido is None:
                continue
            if g in hay:
                found_sido, gu = s, g
                break

    return {"sido": found_sido, "city": city, "gu": gu, "dong": dong}


def classify(region: dict, raw_text: str = "") -> dict:
    """정규화된 지역 → 토허 구분(A/B/C/?)과 설명."""
    sido, city, gu, dong = region["sido"], region["city"], region["gu"], region.get("dong")
    hay = " ".join(x for x in (gu, dong, raw_text) if x)
    caution = "지번 단위 지정 구역(공공주택지구·재개발 후보지 등)은 판정하지 못함 — 거래 전 토지이음·서울부동산정보광장에서 직접 조회"

    if sido is None:
        return {"zone": "?", "label": "지역 확인 필요", "gap_allowed": None, "regulated": None,
                "reason": "녹음에서 시·도/시·군·구를 찾지 못함", "caution": caution}

    if sido == "서울특별시":
        return {"zone": "A", "label": "A 토허구역", "gap_allowed": False, "regulated": True,
                "reason": "서울 25개 자치구 전역 토지거래허가구역 (2026-12-31까지, 연장 미정)", "caution": caution}

    if sido == "인천광역시":
        if any(k in hay for k in IFEZ_KEYWORDS) or gu == "영종구":
            return {"zone": "C", "label": "C 개별 지정", "gap_allowed": False, "regulated": False,
                    "reason": "인천경제자유구역(송도·청라·영종) 별도 고시 토허구역 — 구역 경계는 지번 확인", "caution": caution}
        return {"zone": "B", "label": "B 비대상", "gap_allowed": True, "regulated": False,
                "reason": "인천은 일괄 지정 제외 · 2022-11 이후 비규제지역", "caution": caution}

    # 경기
    if city is None:
        return {"zone": "?", "label": "시·군 확인 필요", "gap_allowed": None, "regulated": None,
                "reason": "경기도 내 시·군을 찾지 못함", "caution": caution}
    if city in TOHU_GYEONGGI_WHOLE_CITY or (city, gu) in TOHU_GYEONGGI_GU or (city == "화성시" and "동탄" in hay):
        extra = " (2026-07 추가 지정, 2027-12-31까지)" if city in ("구리시", "화성시") or gu == "기흥구" else ""
        return {"zone": "A", "label": "A 토허구역", "gap_allowed": False, "regulated": True,
                "reason": f"경기 {city}{' ' + gu if gu else ''} 토지거래허가구역{extra}", "caution": caution}
    if city in PARTIAL_TOHU_CITY and gu is None:
        return {"zone": "?", "label": "구 확인 필요", "gap_allowed": None, "regulated": None,
                "reason": f"{city}는 일부 구만 토허구역 — 어느 구인지 녹음에 없음", "caution": caution}
    return {"zone": "B", "label": "B 비대상", "gap_allowed": True, "regulated": False,
            "reason": f"경기 {city}{' ' + gu if gu else ''}는 토허 지정 목록에 없음 (비규제)", "caution": caution}
