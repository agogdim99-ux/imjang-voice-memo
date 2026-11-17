"""비교표·자금 판정 카드를 Markdown 과 HTML 로 만든다."""
import html

from .finance import BUYER_TYPES, INCOME_BRACKETS, SEED_BRACKETS, won

NEED = "확인 필요"


def _yn(v, yes="있음", no="없음"):
    return NEED if v is None else (yes if v else no)


def derived_rows(p: dict) -> list[tuple[str, str, str]]:
    """(분류, 항목, 값) — 문제정의서 항목표 순서. 값이 없으면 '확인 필요'."""
    pk = p.get("parking_per_household")
    st = p.get("station_walk_min")
    hh = p.get("households")
    hh_label = None if hh is None else ("대단지" if hh >= 1000 else "중단지" if hh >= 300 else "소단지")
    loan = p.get("seller_loan_exists")
    loan_s = NEED if loan is None else (f"있음 ({won(p['seller_loan_amount'])})" if loan and p.get("seller_loan_amount") else "있음" if loan else "없음")
    region = " ".join(x for x in (p.get("sido"), p.get("sigungu"), p.get("dong")) if x) or NEED
    return [
        ("지역", "위치", region),
        ("지역", "토허 구분", p["_zone"]["label"]),
        ("가격", "매매가", won(p.get("sale_price"))),
        ("가격", "전세가", won(p.get("jeonse_price"))),
        ("가격", "월세", NEED if p.get("wolse_monthly") is None else f"{won(p.get('wolse_deposit'))} / 월 {p['wolse_monthly']}만원"),
        ("가격", "매도인 융자", loan_s),
        ("물건", "유형", p.get("property_type") or NEED),
        ("물건", "평형", NEED if p.get("area_pyeong") is None else f"{p['area_pyeong']:g}평"),
        ("물건", "연식", NEED if p.get("built_year") is None else f"{p['built_year']}년 (약 {2026 - p['built_year']}년차)"),
        ("물건", "층", p.get("floor") or NEED),
        ("물건", "향", p.get("facing") or NEED),
        ("단지", "세대수", NEED if hh is None else f"{hh:,}세대 · {hh_label}"),
        ("관리", "관리비", NEED if p.get("mgmt_fee") is None else f"{p['mgmt_fee']:g}만원"),
        ("관리", "주차", NEED if pk is None else f"{'1대 이상' if pk >= 1 else '1대 미만'} ({pk:g}대)"),
        ("관리", "엘리베이터", _yn(p.get("elevator"))),
        ("관리", "관리사무소", p.get("mgmt_office") or NEED),
        ("하자", "하자·수리", " / ".join(p.get("defects") or []) or NEED),
        ("입지", "역세권", NEED if st is None else f"{'역세권' if st <= 10 else '비역세권'} (도보 {st}분{', ' + p['station_name'] if p.get('station_name') else ''})"),
        ("입지", "초등학교", NEED if p.get("chopuma") is None and not p.get("elementary") else (("초품아 ✓" if p.get("chopuma") else "초품아 아님" if p.get("chopuma") is False else "") + (f" — {p['elementary']}" if p.get("elementary") else ""))),
        ("입지", "중·고등학교", p.get("middle_high") or NEED),
        ("입지", "상권", p.get("commercial") or NEED),
    ]


def missing_count(rows) -> int:
    return sum(1 for _, _, v in rows if v == NEED)


def to_markdown(props: list[dict], settings: dict) -> str:
    seed = SEED_BRACKETS[settings["seed"]][0]
    out = [f"# 임장 매물 비교표\n",
           f"- 추출 방식: **{settings['method']}** · 받아쓰기: `{settings['source']}`",
           f"- 내 조건: 시드 **{seed}** · {BUYER_TYPES[settings['buyer']]} · 연소득 {INCOME_BRACKETS[settings['income']][0]}",
           "- 모든 수치는 참고용 개략치. 세금·실제 대출 한도는 반영하지 않음.\n",
           "## 1. 항목 비교\n"]
    rows_all = [derived_rows(p) for p in props]
    head = "| 분류 | 항목 | " + " | ".join(p["_title"] for p in props) + " |"
    out += [head, "|" + "---|" * (len(props) + 2)]
    for i, (cat, name, _) in enumerate(rows_all[0]):
        cells = []
        for rows in rows_all:
            v = rows[i][2].replace("|", "/")
            cells.append(f"⚠️ {v}" if v == NEED else v)
        out.append(f"| {cat} | {name} | " + " | ".join(cells) + " |")
    out.append("| — | **확인 필요 개수** | " + " | ".join(str(missing_count(r)) for r in rows_all) + " |\n")

    out.append("## 2. 내 자금으로 가능한가\n")
    for p in props:
        f = p["_finance"]
        out.append(f"### {p['_title']}  ·  {p['_zone']['label']}")
        out.append(f"> {p['_zone']['reason']}  \n> ℹ️ {p['_zone']['caution']}\n")
        out.append("| 방식 | 필요자금 | 판정 | 계산 |")
        out.append("|---|---|---|---|")
        for s in f["scenarios"]:
            icon = {"ok": "🟢", "warn": "🟡", "bad": "🔴"}.get(s["level"], "⚪")
            note = f" — {s['note']}" if s.get("note") else ""
            out.append(f"| {s['name']} | {won(s['need']) if s['need'] is not None else '—'} | {icon} {s['verdict']}{note} | {s['detail']} |")
        for s in f["scenarios"]:
            if s.get("loan_basis"):
                out.append(f"\n- 주담대 추정 근거: {s['loan_basis']}")
        for c in f["comments"]:
            out.append(f"- 💬 {c}")
        if f.get("fee"):
            out.append(f"- 중개보수(매매) {f['fee']}")
        if p.get("uncertain"):
            out.append(f"- ❓ 헷갈린 부분: {' / '.join(p['uncertain'])}")
        out.append("")
    return "\n".join(out)


CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1f;--sub:#6b6b70;--line:#e4e4e0;--need:#b45309;--needbg:#fff4e0;
--ok:#15803d;--okbg:#e8f6ec;--warn:#a16207;--warnbg:#fdf6d8;--bad:#b91c1c;--badbg:#fde8e8;--na:#6b6b70;--nabg:#efefec;--a:#1d4ed8}
@media (prefers-color-scheme:dark){:root{--bg:#141415;--card:#1e1e20;--ink:#ececec;--sub:#a0a0a6;--line:#333336;--need:#fbbf24;--needbg:#3a2a0c;
--ok:#4ade80;--okbg:#12301c;--warn:#facc15;--warnbg:#332a08;--bad:#f87171;--badbg:#3a1414;--na:#a0a0a6;--nabg:#2a2a2c;--a:#93b4ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 12px}
.meta{color:var(--sub);font-size:13px}.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{position:sticky;top:0;background:var(--card);font-weight:600}td.cat{color:var(--sub);white-space:nowrap}td.name{font-weight:600;white-space:nowrap}
td.need{color:var(--need);background:var(--needbg);font-weight:600}tr.total td{font-weight:700}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}.card h3{margin:0 0 2px;font-size:16px}
.zone{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;background:var(--nabg);margin-bottom:6px}
.sc{display:flex;justify-content:space-between;gap:8px;padding:8px 10px;border-radius:8px;margin:6px 0}
.sc b{display:block}.sc small{color:var(--sub)}.ok{background:var(--okbg)}.ok .v{color:var(--ok)}.warn{background:var(--warnbg)}.warn .v{color:var(--warn)}
.bad{background:var(--badbg)}.bad .v{color:var(--bad)}.na{background:var(--nabg)}.na .v{color:var(--na)}.v{font-weight:700;text-align:right;white-space:nowrap}
ul{padding-left:18px;margin:8px 0 0}li{margin:2px 0;font-size:13.5px}.small{color:var(--sub);font-size:12.5px}
"""


def to_html(props: list[dict], settings: dict) -> str:
    e = html.escape
    seed = SEED_BRACKETS[settings["seed"]][0]
    rows_all = [derived_rows(p) for p in props]
    th = "".join(f"<th>{e(p['_title'])}</th>" for p in props)
    body = []
    for i, (cat, name, _) in enumerate(rows_all[0]):
        tds = "".join(f'<td class="need">{NEED}</td>' if r[i][2] == NEED else f"<td>{e(r[i][2])}</td>" for r in rows_all)
        body.append(f'<tr><td class="cat">{cat}</td><td class="name">{name}</td>{tds}</tr>')
    body.append('<tr class="total"><td></td><td>확인 필요 개수</td>' + "".join(f"<td>{missing_count(r)}</td>" for r in rows_all) + "</tr>")

    cards = []
    for p in props:
        f = p["_finance"]
        sc = "".join(
            f'<div class="sc {s["level"]}"><div><b>{e(s["name"])}</b><small>{e(s["detail"])}</small></div>'
            f'<div class="v">{e(won(s["need"])) if s["need"] is not None else "—"}<br>{e(s["verdict"])}</div></div>'
            + (f'<div class="small">↳ {e(s["note"])}</div>' if s.get("note") else "")
            for s in f["scenarios"])
        lis = "".join(f"<li>{e(c)}</li>" for c in f["comments"])
        if f.get("fee"):
            lis += f"<li>중개보수(매매) {e(f['fee'])}</li>"
        if p.get("uncertain"):
            lis += f"<li>❓ 헷갈린 부분: {e(' / '.join(p['uncertain']))}</li>"
        basis = next((s["loan_basis"] for s in f["scenarios"] if s.get("loan_basis")), "")
        cards.append(
            f'<div class="card"><h3>{e(p["_title"])}</h3><span class="zone">{e(p["_zone"]["label"])}</span>'
            f'<div class="small">{e(p["_zone"]["reason"])}</div>{sc}'
            + (f'<div class="small">주담대 추정: {e(basis)}</div>' if basis else "")
            + f'<ul>{lis}</ul><div class="small" style="margin-top:8px">ℹ️ {e(p["_zone"]["caution"])}</div></div>')

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>임장 매물 비교표</title><style>{CSS}</style></head>
<body><main><h1>임장 매물 비교표</h1>
<div class="meta">추출: <b>{e(settings['method'])}</b> · 받아쓰기: {e(settings['source'])} · 시드 <b>{e(seed)}</b> · {e(BUYER_TYPES[settings['buyer']])} · 연소득 {e(INCOME_BRACKETS[settings['income']][0])}<br>
모든 수치는 참고용 개략치입니다. 세금·실제 대출 한도는 반영하지 않으며, 은행 상담이 필요합니다.</div>
<h2>1. 항목 비교</h2><div class="wrap"><table><thead><tr><th>분류</th><th>항목</th>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div>
<h2>2. 내 자금으로 가능한가</h2><div class="cards">{''.join(cards)}</div></main></body></html>"""
