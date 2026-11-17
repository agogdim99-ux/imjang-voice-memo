"""자금 계산·판정 — 공개 규정값을 코드에 고정해 계산한다(AI가 숫자를 지어내지 않게).

모든 금액 단위: 만원.  결과는 참고용 개략치이며, 대출 한도는 반드시 은행 상담으로 확인해야 한다.
"""

# ── 시드 구간 (문제정의서 6장) ─────────────────────────────
SEED_BRACKETS = {
    1: ("1억 미만", 0, 10000),
    2: ("1억~3억", 10000, 30000),
    3: ("3억~5억", 30000, 50000),
    4: ("5억~7억", 50000, 70000),
    5: ("7억~10억", 70000, 100000),
    6: ("10억 이상", 100000, None),
}

BUYER_TYPES = {"무주택": "무주택", "생애최초": "생애최초", "다주택": "2주택 이상"}

# 연소득 구간 (DSR 추정용, 선택). 대표값 = 구간 하한(보수적)
INCOME_BRACKETS = {
    0: ("미입력", None),
    1: ("3천만원 미만", 2500),
    2: ("3천~5천만원", 3000),
    3: ("5천~7천만원", 5000),
    4: ("7천만원~1억", 7000),
    5: ("1억 이상", 10000),
}

# ── 2026년 기준 대출 규정값 (문제정의서 3장) ─────────────────
LTV = {  # (규제지역 여부, 구매자 유형) → LTV
    (True, "무주택"): 0.40, (False, "무주택"): 0.70,
    (True, "생애최초"): 0.70, (False, "생애최초"): 0.80,
}
DSR_RATIO = 0.40
ASSUMED_RATE = 0.045      # 연 4.5% (스트레스 금리 감안한 보수적 가정)
ASSUMED_YEARS = 30


def mortgage_cap(price: int) -> int:
    """수도권·규제지역 주택구입 목적 주담대 절대 한도."""
    if price <= 150000:
        return 60000
    if price <= 250000:
        return 40000
    return 20000


def dsr_max_loan(annual_income: int) -> int:
    """연소득 × 40% 를 원리금균등 상환액으로 보고 역산한 최대 대출액."""
    r = ASSUMED_RATE / 12
    n = ASSUMED_YEARS * 12
    monthly = annual_income * DSR_RATIO / 12
    return int(monthly * (1 - (1 + r) ** -n) / r)


def loan_estimate(price: int, regulated: bool, buyer: str, income_key: int = 0) -> dict:
    if buyer == "다주택":
        return {"amount": 0, "basis": "2주택 이상: 수도권 주택구입 목적 주담대 불가"}
    ltv = LTV[(bool(regulated), buyer)]
    by_ltv = int(price * ltv)
    cap = mortgage_cap(price)
    parts = [(by_ltv, f"LTV {int(ltv*100)}% = {won(by_ltv)}"), (cap, f"절대 한도 {won(cap)}")]
    income = INCOME_BRACKETS.get(income_key, ("미입력", None))[1]
    if income:
        d = dsr_max_loan(income)
        parts.append((d, f"DSR 40%(연소득 {won(income)} 가정) = {won(d)}"))
    amount, _ = min(parts, key=lambda p: p[0])
    basis = " · ".join(p[1] for p in parts) + f" → 가장 작은 값 {won(amount)}"
    if not income:
        basis += " (DSR 미반영: 소득이 낮으면 더 줄어듦)"
    return {"amount": amount, "basis": basis}


def judge(need: int, seed_key: int) -> dict:
    """필요자금 vs 시드 구간. 구간 하한(보수적) 기준으로 3단계 판정."""
    name, low, high = SEED_BRACKETS[seed_key]
    short = need - low
    if short <= 0:
        verdict, level = "가능", "ok"
    elif short <= 10000:
        verdict, level = f"조금 부족 ({won(short)})", "warn"
    else:
        verdict, level = f"많이 부족 ({won(short)})", "bad"
    note = ""
    if level != "ok" and (high is None or need <= high):
        note = f"시드가 구간 상단({name})에 가까우면 가능"
    return {"verdict": verdict, "level": level, "shortfall": max(short, 0), "note": note}


def brokerage_fee(price: int) -> str:
    """매매 중개보수 상한(법정 상한요율). 실제 금액은 협의."""
    if price < 5000:
        return f"상한 0.6% (최대 25만원) ≈ {won(min(price*0.006, 25))}"
    if price < 20000:
        return f"상한 0.5% (최대 80만원) ≈ {won(min(price*0.005, 80))}"
    for limit, rate in ((90000, 0.004), (120000, 0.005), (150000, 0.006)):
        if price < limit:
            return f"상한 {rate*100:.1f}% ≈ {won(price*rate)}"
    return f"상한 0.7% ≈ {won(price*0.007)}"


def comments(price: int, zone: dict, buyer: str, loan: dict, seller_loan: int | None) -> list[str]:
    out = []
    if buyer == "다주택":
        out.append("다주택자는 수도권 주담대가 막혀 있어 현금·전세 레버리지 외 방법이 없음")
    elif buyer == "생애최초":
        out.append("생애최초 LTV 우대 적용 — 디딤돌(주택가격 5억·소득 요건)·보금자리론(6억 이하) 해당 여부 은행 확인")
    elif price <= 60000:
        out.append("주택가격 6억 이하 → 보금자리론 대상 가능성, 시중은행 주담대와 금리 비교 권장")
    else:
        out.append("시중은행 주담대 기준 — 한도는 LTV·절대 한도·DSR 중 가장 작은 값으로 결정")
    if zone["zone"] in ("A", "C"):
        out.append("토허구역: 허가 후 4개월 내 입주·2년 실거주 의무 → 전세 끼고 매수 불가")
    if seller_loan:
        out.append(f"매도인 융자 {won(seller_loan)} — 잔금 때 말소(상환) 조건을 계약서에 명시")
    return out


def won(v) -> str:
    """만원 단위 숫자 → '4억 5,000만원' 식 표기."""
    if v is None:
        return "확인 필요"
    v = int(round(v))
    sign = "-" if v < 0 else ""
    v = abs(v)
    eok, man = divmod(v, 10000)
    if eok and man:
        return f"{sign}{eok}억 {man:,}만원"
    if eok:
        return f"{sign}{eok}억원"
    return f"{sign}{man:,}만원"


def evaluate_property(p: dict, zone: dict, seed_key: int, buyer: str, income_key: int = 0) -> dict:
    """한 매물에 대해 시나리오(갭투자/실거주)별 필요자금과 판정을 만든다."""
    price, jeonse = p.get("sale_price"), p.get("jeonse_price")
    res = {"scenarios": [], "comments": [], "fee": None}
    if price is None:
        res["scenarios"].append({"name": "판정 불가", "need": None,
                                 "verdict": "매매가 확인 필요", "level": "na", "detail": "녹음에 매매가가 없음"})
        return res

    regulated = bool(zone.get("regulated"))
    loan = loan_estimate(price, regulated, buyer, income_key)

    # 갭투자: B 지역만
    if zone.get("gap_allowed"):
        if jeonse is None:
            res["scenarios"].append({"name": "갭투자", "need": None, "verdict": "전세가 확인 필요",
                                     "level": "na", "detail": "녹음에 전세가가 없음"})
        else:
            need = price - jeonse
            j = judge(need, seed_key)
            res["scenarios"].append({"name": "갭투자", "need": need, **j,
                                     "detail": f"매매 {won(price)} − 전세 {won(jeonse)}"})
    elif zone.get("gap_allowed") is False:
        res["scenarios"].append({"name": "갭투자", "need": None, "verdict": "불가 (토허구역)",
                                 "level": "na", "detail": zone["reason"]})

    # 실거주 매수: 모든 지역
    need = price - loan["amount"]
    j = judge(need, seed_key)
    res["scenarios"].append({"name": "실거주 매수", "need": need, **j,
                             "detail": f"매매 {won(price)} − 주담대 추정 {won(loan['amount'])}",
                             "loan_basis": loan["basis"]})

    seller_loan = p.get("seller_loan_amount") if p.get("seller_loan_exists") else None
    res["comments"] = comments(price, zone, buyer, loan, seller_loan)
    res["fee"] = brokerage_fee(price)
    return res
