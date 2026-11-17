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


# 단지명: "문래자이아파트", "당산 센트럴 아이파크" 처럼 유형어(아파트 등)나 브랜드 앞의 1~3단어
BRANDS = ["자이", "래미안", "힐스테이트", "아이파크", "푸르지오", "e편한세상", "이편한세상", "롯데캐슬", "더샵", "센트레빌",
          "위브", "아크로", "하늘채", "꿈에그린", "스카이뷰", "리첸시아", "스위첸", "데시앙", "해링턴", "포레나", "휴먼시아",
          "베르디움", "어울림", "캐슬", "주공", "트리마제", "디에이치", "써밋", "블레스티지", "헬리오시티"]
NAME_STOP = {"지금", "나는", "저는", "내가", "난", "우리", "오늘은", "방금", "여기는", "임장", "임장하러", "왔고", "와서", "오늘", "첫", "두", "세", "네", "다섯", "번째", "번째는", "마지막", "본", "거", "거는", "건", "게", "매물", "그", "뭐지",
             "이번", "여기", "저기", "이", "저", "하나", "집", "보러", "간", "온", "곳", "일단", "음", "어", "그리고", "다음", "본거"}
LOCATION_WORDS = {"서울", "인천", "경기"}


def _is_stop(tok: str) -> bool:
    from .regions import NEIGHBORHOODS
    if any(tok == w for ws in NEIGHBORHOODS.values() for w in ws if not w.endswith("동")):
        return False  # "송도 더샵", "문래 자이"처럼 동네 이름은 단지명 앞부분으로 쓴다
    if tok in NAME_STOP or tok in LOCATION_WORDS or re.fullmatch(r"\d+(평형?|층|세대)?", tok):
        return True
    if re.search(r"(특별시|광역시|도|시|군|구|동|번째는?|째|에서|이고|인데|는|은)$", tok) and not any(b in tok for b in BRANDS):
        return True
    from .regions import GYEONGGI_SI
    return any(tok == si[:-1] for si in GYEONGGI_SI)


def _name_before(tokens: list[str]) -> str | None:
    picked = []
    for tok in reversed(tokens[-3:]):
        if _is_stop(tok):
            break
        picked.append(tok)
    picked.reverse()
    if len(picked) == 2 and len(picked[0]) <= 3 and picked[1] in BRANDS:  # "문래 자이" → "문래자이"
        picked = [picked[0] + picked[1]]
    name = " ".join(picked).strip()
    return name if len(name) >= 2 else None


def extract_complex_name(text: str) -> str | None:
    for c in _clauses(text):
        m = re.search(r"(아파트|빌라|오피스텔)", c)
        if m:
            name = _name_before(c[: m.start()].split())
            if name:
                return name
    for c in _clauses(text):
        toks = c.split()
        for i in range(len(toks) - 1, -1, -1):
            if any(b in toks[i] for b in BRANDS):
                name = _name_before(toks[: i + 1])
                if name:
                    # 브랜드 뒤 수식어 1개까지 ("래미안 에스티움")
                    nxt = toks[i + 1] if i + 1 < len(toks) else ""
                    if nxt and not _is_stop(nxt) and not re.search(r"\d|(는데|봤|했|고|어|요|다|데|야|서)$", nxt):
                        name += " " + nxt
                    return re.sub(r"(이고|인데|는|은|이야|야)$", "", name)
    return None


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
    d["complex_name"] = extract_complex_name(t)

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
