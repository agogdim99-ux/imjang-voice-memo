"""규칙 기반(정규식) 추출기 — API 키 없이 돌아가는 기본 추출기이자, LLM과 비교할 기준선.

기본은 '키워드 뒤 첫 번째 숫자'. v1에서는 "3억 8천, 아 아니다 3억 6천"처럼 말을 고친 경우 첫 값을 잡아 틀렸고(실패 사례),
v2에서 가격에 한해 '같은 키워드를 다시 말하고 그 사이에 아니다/정정이 있으면 마지막 값' 규칙을 추가했다.
"""
import re

from .regions import normalize_region
from .schema import empty

NUM = r"\d[\d,]*(?:\.\d+)?"
MONEY = re.compile(
    rf"(?P<eok>\d+)\s*억(?:\s*(?P<rest>\d[\d,]*)\s*(?P<cheon>천)?\s*(?:만)?)?"
    rf"|(?P<man>\d[\d,]*)\s*(?P<cheon2>천)?\s*만"
)


def _to_int(s: str) -> float:
    return float(s.replace(",", ""))


def parse_money(s: str) -> int | None:
    """'7억 2천' → 72000, '5천만' → 5000, '4억' → 40000 (단위: 만원)."""
    m = MONEY.search(s)
    if not m:
        return None
    if m.group("eok"):
        v = int(m.group("eok")) * 10000
        if m.group("rest"):
            r = _to_int(m.group("rest"))
            v += int(r * 1000) if m.group("cheon") else int(r)
        return v
    r = _to_int(m.group("man"))
    return int(r * 1000) if m.group("cheon2") else int(r)


def _after(text: str, keyword: str, window: int = 14) -> str | None:
    i = text.find(keyword)
    if i < 0:
        return None
    return text[i + len(keyword): i + len(keyword) + window]


def _clauses(text: str) -> list[str]:
    return [c.strip() for c in re.split(r"[.?!,]\s*|\n", text) if c.strip()]


def extract(text: str) -> dict:
    d = empty()
    t = text
    clauses = _clauses(t)

    # 지역
    m = re.search(r"([가-힣]{1,4}동)(?=[\s,.]|$)", t)
    dong = m.group(1) if m else None
    reg = normalize_region(None, None, dong, t)
    d["sido"] = reg["sido"]
    d["sigungu"] = " ".join(x for x in (reg["city"], reg["gu"]) if x) or None
    d["dong"] = dong

    m = re.search(r"아파트|빌라|오피스텔|다세대|주택", t)
    d["property_type"] = m.group(0) if m else None

    # 가격: 키워드 뒤 첫 금액. 단, 같은 키워드로 다시 말하고 그 사이에 "아니다/정정"이 있으면 마지막 값(정정 반영)
    for key, kw in (("sale_price", "매매"), ("jeonse_price", "전세")):
        vals, i = [], t.find(kw)
        while i >= 0:
            v = parse_money(t[i + len(kw): i + len(kw) + 14])
            if v:
                vals.append((i, v))
            i = t.find(kw, i + 1)
        if vals:
            d[key] = vals[0][1]
            if len(vals) > 1 and re.search(r"아니|정정|잘못", t[vals[0][0]:vals[-1][0]]):
                d[key] = vals[-1][1]
    seg = _after(t, "월세", 20)
    if seg:
        m = re.search(rf"({NUM})\s*에\s*({NUM})", seg)
        if m:
            d["wolse_deposit"], d["wolse_monthly"] = int(_to_int(m.group(1))), int(_to_int(m.group(2)))

    loan_clause = next((c for c in clauses if "융자" in c), None)
    if loan_clause:
        if re.search(r"없", loan_clause):
            d["seller_loan_exists"] = False
        else:
            d["seller_loan_exists"] = True
            d["seller_loan_amount"] = parse_money(loan_clause)

    # 물건
    m = re.search(rf"({NUM})\s*평(?!균)", t)
    d["area_pyeong"] = _to_int(m.group(1)) if m else None
    m = re.search(r"((?:19|20)\d{2})\s*년\s*식", t)
    d["built_year"] = int(m.group(1)) if m else None
    m = re.search(r"(\d+)\s*층\s*중에\s*(\d+)\s*층", t)
    if m:
        d["floor"] = f"{m.group(2)}층/{m.group(1)}층"
    else:
        m = re.search(r"(\d+)\s*층", t)
        d["floor"] = f"{m.group(1)}층" if m else None
    m = re.search(r"(남동|남서|북동|북서|남|북|동|서)향", t)
    d["facing"] = m.group(0) if m else None

    # 단지·관리
    m = re.search(rf"({NUM})\s*세대(?!당)", t)
    d["households"] = int(_to_int(m.group(1))) if m else None
    seg = _after(t, "관리비", 12)
    if seg:
        m = re.search(rf"({NUM})\s*만", seg)
        d["mgmt_fee"] = _to_int(m.group(1)) if m else None
    m = re.search(rf"세대당\s*({NUM})\s*대", t)
    d["parking_per_household"] = _to_int(m.group(1)) if m else None
    m = re.search(r"엘리베이터\s*(?:는|가|도)?\s*(있|없)", t)
    d["elevator"] = (m.group(1) == "있") if m else None
    d["mgmt_office"] = next((c for c in clauses if "관리사무소" in c), None)

    # 입지
    m = re.search(r"([가-힣]*역)(?:까지|에서)?[^.\d]{0,10}?(\d+)\s*분", t)
    if m:
        d["station_name"] = m.group(1) if len(m.group(1)) > 1 else None
        d["station_walk_min"] = int(m.group(2))
    d["elementary"] = next((c for c in clauses if "초등" in c or "초품아" in c), None)
    if "초품아" in t:
        d["chopuma"] = True
    elif d["elementary"] and "건너" in d["elementary"]:
        d["chopuma"] = False
    d["middle_high"] = next((c for c in clauses if "중학교" in c or "고등학교" in c), None)
    d["commercial"] = next((c for c in clauses if re.search(r"상가|상권|학원가|마트|시장", c)), None)

    # 하자 / 헷갈린 부분
    d["defects"] = [c for c in clauses if re.search(r"누수|균열|금 간|곰팡이|깨진|결로|녹물|수리|하자", c)]
    d["uncertain"] = [c for c in clauses if re.search(r"것 같|아니다|모르겠|확실히|정도라던데|애매", c)]
    return d
