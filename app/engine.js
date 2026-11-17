/* 집노트 엔진 — imjang/regions.py + imjang/extract_rules.py 를 그대로 옮긴 것.
   폰 안에서 받아쓴 글 → 항목표 → 토허 판정을 서버 없이 처리한다.
   Python 결과와 같은지 tools/test_engine.mjs 로 검사한다. */
(function (root) {
  'use strict';

  /* ── 지역 (regions.py) ── */
  const SEOUL_GU = ["종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구","강북구","도봉구","노원구","은평구","서대문구","마포구","양천구","강서구","구로구","금천구","영등포구","동작구","관악구","서초구","강남구","송파구","강동구"];
  const INCHEON_GU = ["제물포구","영종구","미추홀구","연수구","남동구","부평구","계양구","서해구","검단구","강화군","옹진군","중구","동구","서구"];
  const GYEONGGI_SI = ["수원시","성남시","의정부시","안양시","부천시","광명시","평택시","동두천시","안산시","고양시","과천시","구리시","남양주시","오산시","시흥시","군포시","의왕시","하남시","용인시","파주시","이천시","안성시","김포시","화성시","광주시","양주시","포천시","여주시","연천군","가평군","양평군"];
  const GYEONGGI_GU = {"수원시":["장안구","권선구","팔달구","영통구"],"성남시":["수정구","중원구","분당구"],"안양시":["만안구","동안구"],"용인시":["처인구","기흥구","수지구"],"부천시":["원미구","소사구","오정구"],"고양시":["덕양구","일산동구","일산서구"],"안산시":["상록구","단원구"],"화성시":["만세구","효행구","병점구","동탄구"]};
  const TOHU_WHOLE = new Set(["과천시","광명시","성남시","의왕시","하남시","구리시"]);
  const TOHU_GU = new Set(["수원시|영통구","수원시|장안구","수원시|팔달구","안양시|동안구","용인시|수지구","용인시|기흥구","화성시|동탄구"]);
  const PARTIAL = new Set(["수원시","안양시","용인시","화성시"]);
  const IFEZ = ["송도","청라","영종","운서","운남","운북","중산동"];
  const SIDO_ALIASES = [["서울특별시",["서울"]],["인천광역시",["인천"]],["경기도",["경기"]]];
  const CAUTION = "지번 단위 지정 구역(공공주택지구·재개발 후보지 등)은 판정하지 못함 — 거래 전 토지이음·서울부동산정보광장에서 직접 조회";

  /* 동네 이름 → 구 (regions.NEIGHBORHOODS 와 동일) */
  const NEIGHBORHOODS = [
    [["서울특별시",null,"영등포구"],["문래","당산","여의도","신길","대림","양평동"]],
    [["서울특별시",null,"양천구"],["목동","신정","신월"]],
    [["서울특별시",null,"노원구"],["상계","중계","하계","공릉","월계"]],
    [["서울특별시",null,"송파구"],["잠실","문정","가락","방이","오금","거여","마천","풍납"]],
    [["서울특별시",null,"서초구"],["반포","잠원","방배","서초동","양재"]],
    [["서울특별시",null,"강남구"],["대치","압구정","개포","도곡","역삼","청담","삼성동","일원","수서"]],
    [["서울특별시",null,"마포구"],["아현","공덕","상암","합정","망원","연남","성산동","도화동"]],
    [["서울특별시",null,"성동구"],["성수","왕십리","행당","옥수","금호동"]],
    [["서울특별시",null,"용산구"],["이촌","한남","이태원","효창"]],
    [["서울특별시",null,"동작구"],["흑석","사당","상도","노량진","대방"]],
    [["서울특별시",null,"관악구"],["봉천","신림"]],
    [["서울특별시",null,"성북구"],["길음","정릉","장위","석관","돈암"]],
    [["서울특별시",null,"강북구"],["미아","수유","번동"]],
    [["서울특별시",null,"도봉구"],["창동","쌍문","방학"]],
    [["서울특별시",null,"은평구"],["불광","응암","녹번","진관"]],
    [["서울특별시",null,"서대문구"],["홍제","북가좌","남가좌","홍은"]],
    [["서울특별시",null,"강동구"],["고덕","명일","둔촌","천호","암사","길동"]],
    [["서울특별시",null,"중랑구"],["신내","면목","묵동","상봉"]],
    [["서울특별시",null,"동대문구"],["이문","휘경","전농","답십리","청량리","장안동"]],
    [["서울특별시",null,"광진구"],["구의","자양","광장동"]],
    [["서울특별시",null,"강서구"],["화곡","등촌","가양","마곡","발산","염창"]],
    [["서울특별시",null,"구로구"],["개봉","오류동","고척","신도림"]],
    [["서울특별시",null,"금천구"],["독산","가산"]],
    [["경기도","성남시","분당구"],["분당","판교","정자동","서현","수내","야탑"]],
    [["경기도","용인시","수지구"],["수지","죽전","풍덕천"]],
    [["경기도","용인시","기흥구"],["기흥","보정동","구갈"]],
    [["경기도","고양시",null],["일산"]],
    [["인천광역시",null,"연수구"],["송도"]],
    [["인천광역시",null,"서해구"],["청라"]],
    [["인천광역시",null,"검단구"],["검단"]],
  ];
  const NB_INDEX = NEIGHBORHOODS.flatMap(([k, ws]) => ws.map(w => [w, k])).sort((a, b) => b[0].length - a[0].length);

  function stripSuffix(n) {
    for (const s of ["특별시","광역시","도","시","군","구"]) if (n.endsWith(s) && n.length > s.length) return n.slice(0, -s.length);
    return n;
  }

  function normalizeRegion(sido, sigungu, dong, raw) {
    const hay = [sido, sigungu, dong, raw || ""].filter(Boolean).join(" ");
    let found = null;
    for (const [full, al] of SIDO_ALIASES) if (hay.includes(full) || al.some(a => hay.includes(a))) { found = full; break; }
    let city = null, gu = null;
    if (found === null || found === "경기도") {
      for (const si of GYEONGGI_SI) {
        if (hay.includes(si) || hay.includes(stripSuffix(si))) {
          if (si === "광주시" && hay.includes("광주광역시")) continue;
          city = si; found = found || "경기도";
          for (const g of GYEONGGI_GU[si] || []) if (hay.includes(g) || hay.includes(stripSuffix(g))) gu = g;
          break;
        }
      }
      if (city === null) {
        outer: for (const [si, gus] of Object.entries(GYEONGGI_GU)) for (const g of gus) if (hay.includes(g)) { city = si; gu = g; found = found || "경기도"; break outer; }
      }
    }
    if (city === null) {
      let cand = [];
      if (found === null || found === "서울특별시") cand = cand.concat(SEOUL_GU.map(g => ["서울특별시", g]));
      if (found === null || found === "인천광역시") cand = cand.concat(INCHEON_GU.map(g => ["인천광역시", g]));
      cand.sort((a, b) => b[1].length - a[1].length);
      for (const [s, g] of cand) {
        if (["중구","동구","서구"].includes(g) && found === null) continue;
        if (hay.includes(g)) { found = s; gu = g; break; }
      }
    }
    if (gu === null && city === null) {
      for (const [w, [s, c, g]] of NB_INDEX) if (hay.includes(w) && (found === null || found === s)) { found = s; city = c; gu = g; break; }
    }
    return { sido: found, city, gu, dong };
  }

  function classify(r, raw) {
    const { sido, city, gu, dong } = r;
    const hay = [gu, dong, raw || ""].filter(Boolean).join(" ");
    const z = (zone, label, gap, reg, reason) => ({ zone, label, gap_allowed: gap, regulated: reg, reason, caution: CAUTION });
    if (!sido) return z("?", "지역 확인 필요", null, null, "녹음에서 시·도/시·군·구를 찾지 못함");
    if (sido === "서울특별시") return z("A", "A 토허구역", false, true, "서울 25개 자치구 전역 토지거래허가구역 (2026-12-31까지, 연장 미정)");
    if (sido === "인천광역시") {
      if (IFEZ.some(k => hay.includes(k)) || gu === "영종구") return z("C", "C 개별 지정", false, false, "인천경제자유구역(송도·청라·영종) 별도 고시 토허구역 — 구역 경계는 지번 확인");
      return z("B", "B 비대상", true, false, "인천은 일괄 지정 제외 · 2022-11 이후 비규제지역");
    }
    if (!city) return z("?", "시·군 확인 필요", null, null, "경기도 내 시·군을 찾지 못함");
    if (TOHU_WHOLE.has(city) || TOHU_GU.has(city + "|" + gu) || (city === "화성시" && hay.includes("동탄"))) {
      const extra = (city === "구리시" || city === "화성시" || gu === "기흥구") ? " (2026-07 추가 지정, 2027-12-31까지)" : "";
      return z("A", "A 토허구역", false, true, `경기 ${city}${gu ? " " + gu : ""} 토지거래허가구역${extra}`);
    }
    if (PARTIAL.has(city) && !gu) return z("?", "구 확인 필요", null, null, `${city}는 일부 구만 토허구역 — 어느 구인지 녹음에 없음`);
    return z("B", "B 비대상", true, false, `경기 ${city}${gu ? " " + gu : ""}는 토허 지정 목록에 없음 (비규제)`);
  }

  /* ── 규칙 기반 추출 (extract_rules.py) ── */
  const NUM = "\\d[\\d,]*(?:\\.\\d+)?";
  const MONEY = /(?<eok>\d+)\s*억(?:\s*(?<rest>\d[\d,]*)\s*(?<cheon>천)?\s*(?:만)?)?|(?<man>\d[\d,]*)\s*(?<cheon2>천)?\s*만/;
  const num = s => parseFloat(String(s).replace(/,/g, ""));

  function parseMoney(s) {
    const m = MONEY.exec(s); if (!m) return null; const g = m.groups;
    if (g.eok) { let v = parseInt(g.eok, 10) * 10000; if (g.rest) { const r = num(g.rest); v += g.cheon ? Math.trunc(r * 1000) : Math.trunc(r); } return v; }
    const r = num(g.man); return g.cheon2 ? Math.trunc(r * 1000) : Math.trunc(r);
  }
  function after(t, kw, w = 14) { const i = t.indexOf(kw); return i < 0 ? null : t.slice(i + kw.length, i + kw.length + w); }
  const clausesOf = t => t.split(/[.?!,]\s*|\n/).map(c => c.trim()).filter(Boolean);

  /* 단지명 (extract_rules.extract_complex_name) */
  const BRANDS = ["자이","래미안","힐스테이트","아이파크","푸르지오","e편한세상","이편한세상","롯데캐슬","더샵","센트레빌","위브","아크로","하늘채","꿈에그린","스카이뷰","리첸시아","스위첸","데시앙","해링턴","포레나","휴먼시아","베르디움","어울림","캐슬","주공","트리마제","디에이치","써밋","블레스티지","헬리오시티"];
  const NAME_STOP = new Set(["오늘","첫","두","세","네","다섯","번째","번째는","마지막","본","거","거는","건","게","매물","그","뭐지","이번","여기","저기","이","저","하나","집","보러","간","온","곳","일단","음","어","그리고","다음","본거"]);
  const LOCATION_WORDS = new Set(["서울","인천","경기"]);
  function isStop(tok) {
    if (NB_INDEX.some(([w]) => w === tok && !w.endsWith("동"))) return false;   // "송도 더샵", "문래 자이"
    if (NAME_STOP.has(tok) || LOCATION_WORDS.has(tok) || /^\d+(평형?|층|세대)?$/.test(tok)) return true;
    if (/(특별시|광역시|도|시|군|구|동|번째는?|째|에서|이고|인데|는|은)$/.test(tok) && !BRANDS.some(b => tok.includes(b))) return true;
    return GYEONGGI_SI.some(si => tok === si.slice(0, -1));
  }
  function nameBefore(tokens) {
    const picked = [];
    for (const tok of tokens.slice(-3).reverse()) { if (isStop(tok)) break; picked.push(tok); }
    const name = picked.reverse().join(" ").trim();
    return name.length >= 2 ? name : null;
  }
  function extractComplexName(text) {
    const cls = clausesOf(text);
    for (const c of cls) {
      const m = /(아파트|빌라|오피스텔)/.exec(c);
      if (m) { const n = nameBefore(c.slice(0, m.index).split(/\s+/).filter(Boolean)); if (n) return n; }
    }
    for (const c of cls) {
      const toks = c.split(/\s+/).filter(Boolean);
      for (let i = toks.length - 1; i >= 0; i--) {
        if (BRANDS.some(b => toks[i].includes(b))) {
          let n = nameBefore(toks.slice(0, i + 1));
          if (n) {
            const nxt = toks[i + 1] || "";
            if (nxt && !isStop(nxt) && !/\d|(는데|봤|했|고|어|요|다|데|야|서)$/.test(nxt)) n += " " + nxt;
            return n.replace(/(이고|인데|는|은|이야|야)$/, "");
          }
        }
      }
    }
    return null;
  }

  function empty() {
    return { sido:null, sigungu:null, dong:null, complex_name:null, property_type:null, sale_price:null, jeonse_price:null, wolse_deposit:null, wolse_monthly:null,
      seller_loan_exists:null, seller_loan_amount:null, area_pyeong:null, built_year:null, floor:null, facing:null, households:null,
      mgmt_fee:null, parking_per_household:null, elevator:null, mgmt_office:null, station_name:null, station_walk_min:null,
      elementary:null, chopuma:null, middle_high:null, commercial:null, defects:[], uncertain:[] };
  }

  function extract(text) {
    const d = empty(), t = text, cl = clausesOf(t);
    let m = /([가-힣]{1,4}동)(?=[\s,.]|$)/.exec(t);
    const dong = m ? m[1] : null;
    const reg = normalizeRegion(null, null, dong, t);
    d.sido = reg.sido; d.sigungu = [reg.city, reg.gu].filter(Boolean).join(" ") || null; d.dong = dong;
    m = /아파트|빌라|오피스텔|다세대|주택/.exec(t); d.property_type = m ? m[0] : null;
    d.complex_name = extractComplexName(t);

    for (const [key, kw] of [["sale_price", "매매"], ["jeonse_price", "전세"]]) {
      const vals = []; let i = t.indexOf(kw);
      while (i >= 0) { const v = parseMoney(t.slice(i + kw.length, i + kw.length + 14)); if (v) vals.push([i, v]); i = t.indexOf(kw, i + 1); }
      if (vals.length) {
        d[key] = vals[0][1];
        if (vals.length > 1 && /아니|정정|잘못/.test(t.slice(vals[0][0], vals[vals.length - 1][0]))) d[key] = vals[vals.length - 1][1];   // 정정 반영
      }
    }
    let seg = after(t, "월세", 20);
    if (seg) { m = new RegExp(`(${NUM})\\s*에\\s*(${NUM})`).exec(seg); if (m) { d.wolse_deposit = Math.trunc(num(m[1])); d.wolse_monthly = Math.trunc(num(m[2])); } }
    const loan = cl.find(c => c.includes("융자"));
    if (loan) { if (/없/.test(loan)) d.seller_loan_exists = false; else { d.seller_loan_exists = true; d.seller_loan_amount = parseMoney(loan); } }

    m = new RegExp(`(${NUM})\\s*평(?!균)`).exec(t); d.area_pyeong = m ? num(m[1]) : null;
    m = /((?:19|20)\d{2})\s*년\s*식/.exec(t); d.built_year = m ? parseInt(m[1], 10) : null;
    m = /(\d+)\s*층\s*중에\s*(\d+)\s*층/.exec(t);
    if (m) d.floor = `${m[2]}층/${m[1]}층`; else { m = /(\d+)\s*층/.exec(t); d.floor = m ? `${m[1]}층` : null; }
    m = /(남동|남서|북동|북서|남|북|동|서)향/.exec(t); d.facing = m ? m[0] : null;

    m = new RegExp(`(${NUM})\\s*세대(?!당)`).exec(t); d.households = m ? Math.trunc(num(m[1])) : null;
    seg = after(t, "관리비", 12);
    if (seg) { m = new RegExp(`(${NUM})\\s*만`).exec(seg); d.mgmt_fee = m ? num(m[1]) : null; }
    m = new RegExp(`세대당\\s*(${NUM})\\s*대`).exec(t); d.parking_per_household = m ? num(m[1]) : null;
    m = /엘리베이터\s*(?:는|가|도)?\s*(있|없)/.exec(t); d.elevator = m ? m[1] === "있" : null;
    d.mgmt_office = cl.find(c => c.includes("관리사무소")) || null;

    m = /([가-힣]*역)(?:까지|에서)?[^.\d]{0,10}?(\d+)\s*분/.exec(t);
    if (m) { d.station_name = m[1].length > 1 ? m[1] : null; d.station_walk_min = parseInt(m[2], 10); }
    d.elementary = cl.find(c => c.includes("초등") || c.includes("초품아")) || null;
    if (t.includes("초품아")) d.chopuma = true; else if (d.elementary && d.elementary.includes("건너")) d.chopuma = false;
    d.middle_high = cl.find(c => c.includes("중학교") || c.includes("고등학교")) || null;
    d.commercial = cl.find(c => /상가|상권|학원가|마트|시장/.test(c)) || null;

    d.defects = cl.filter(c => /누수|균열|금 간|곰팡이|깨진|결로|녹물|수리|하자/.test(c));
    d.uncertain = cl.filter(c => /것 같|아니다|모르겠|확실히|정도라던데|애매/.test(c));
    return d;
  }

  /* 받아쓴 글 하나 → 앱 매물 하나 */
  function analyze(text) {
    const p = extract(text);
    const r = normalizeRegion(p.sido, p.sigungu, p.dong, text);
    p.sido = r.sido || p.sido;
    p.zone = classify(r, text);
    return p;
  }

  const api = { normalizeRegion, classify, extract, analyze, parseMoney, empty, extractComplexName };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ZipEngine = api;
})(typeof window !== "undefined" ? window : globalThis);
