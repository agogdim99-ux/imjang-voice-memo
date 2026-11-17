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

  function empty() {
    return { sido:null, sigungu:null, dong:null, property_type:null, sale_price:null, jeonse_price:null, wolse_deposit:null, wolse_monthly:null,
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

  const api = { normalizeRegion, classify, extract, analyze, parseMoney, empty };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ZipEngine = api;
})(typeof window !== "undefined" ? window : globalThis);
