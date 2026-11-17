"""고정 항목표 — 규칙 기반·LLM 추출기가 모두 이 모양으로 결과를 낸다. null = 녹음에 없음."""

FIELDS = [
    # key, 표시 이름, 분류, JSON 타입
    ("sido", "시·도", "지역", "string"),
    ("sigungu", "시·군·구", "지역", "string"),
    ("dong", "동", "지역", "string"),
    ("complex_name", "단지명", "물건", "string"),
    ("property_type", "유형", "물건", "string"),
    ("sale_price", "매매가", "가격", "integer"),
    ("jeonse_price", "전세가", "가격", "integer"),
    ("wolse_deposit", "월세 보증금", "가격", "integer"),
    ("wolse_monthly", "월세", "가격", "integer"),
    ("seller_loan_exists", "융자 유무", "가격", "boolean"),
    ("seller_loan_amount", "융자 금액", "가격", "integer"),
    ("area_pyeong", "평형", "물건", "number"),
    ("built_year", "연식", "물건", "integer"),
    ("floor", "층", "물건", "string"),
    ("facing", "향", "물건", "string"),
    ("households", "단지 세대수", "단지", "integer"),
    ("mgmt_fee", "관리비(만원)", "관리", "number"),
    ("parking_per_household", "세대당 주차", "관리", "number"),
    ("elevator", "엘리베이터", "관리", "boolean"),
    ("mgmt_office", "관리사무소 상태", "관리", "string"),
    ("station_name", "역 이름", "입지", "string"),
    ("station_walk_min", "역 도보(분)", "입지", "integer"),
    ("elementary", "초등학교", "입지", "string"),
    ("chopuma", "초품아", "입지", "boolean"),
    ("middle_high", "중·고등학교", "입지", "string"),
    ("commercial", "상권", "입지", "string"),
]
LIST_FIELDS = [
    ("defects", "하자·수리 필요"),
    ("uncertain", "말한 사람도 헷갈린 부분"),
]


def json_schema() -> dict:
    props = {k: {"type": [t, "null"]} for k, _, _, t in FIELDS}
    for k, _ in LIST_FIELDS:
        props[k] = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": props,
        "required": [k for k, *_ in FIELDS] + [k for k, _ in LIST_FIELDS],
        "additionalProperties": False,
    }


def empty() -> dict:
    d = {k: None for k, *_ in FIELDS}
    for k, _ in LIST_FIELDS:
        d[k] = []
    return d
