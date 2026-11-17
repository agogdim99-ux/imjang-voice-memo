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
  const NAME_STOP = new Set(["지금","나는","저는","내가","난","우리","오늘은","방금","여기는","임장","임장하러","왔고","와서","오늘","첫","두","세","네","다섯","번째","번째는","마지막","본","거","거는","건","게","매물","그","뭐지","이번","여기","저기","이","저","하나","집","보러","간","온","곳","일단","음","어","그리고","다음","본거"]);
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
    picked.reverse();
    // "문래 자이" → "문래자이" (동네 + 브랜드 두 단어는 붙여 쓴다)
    if (picked.length === 2 && picked[0].length <= 3 && BRANDS.includes(picked[1])) picked.splice(0, 2, picked[0] + picked[1]);
    const name = picked.join(" ").trim();
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

  /* ── 녹음 정리기: 띄어쓰기·문장부호 없는 혼잣말 → 주제별 메모 ── */
  const SPLIT_MARK = /\s(?=(?:아\s)?(?:그리고|그래서|근데|그런데|무엇보다|왜냐면|왜냐하면|게다가|일단|전반적으로|그리고는)\s)/g;
  // 문장 끝으로 볼 어미 뒤에서 자른다 ('다'는 '베란다'처럼 명사 끝일 수 있어 동사 어간 뒤에서만)
  const END_SPLIT = /(?<=(?:[가-힣](?:고|야|요|어|네|데|음|함|임))|같아|좋아|괜찮아|있어|없어|(?:있|없|좋|같|않|했|됐|된|이|한|많|넓|좁|크|싸)다)\s+/g;
  const FILLERS = [/이거 뭐야/g, /뭐 이런/g, /이런 거(?=[여이]서|\s)/g, /이런 건/g, /(좀\s)?되던지요?/g,
    /\S+\s아니\s(?=\S)/g,                                   // "뒤편으로는 아니 근처로는" → 고쳐 말한 앞말 삭제
    /(^|\s)(음+|어+|그|뭐|막|아|저기|얘가|얘는|이제|그냥|약간 뭐|일단)(?=\s)/g];
  const LEAD = /^(아\s)?(그리고|그래서|근데|그런데|무엇보다|왜냐면|왜냐하면|또|게다가|일단|그리고는)\s+/;
  const ENDINGS = [
    [/(것|거) 같(긴 한데|기도 하고|고|아요|아|네|음|은데|어)$/, '것 같음'],
    [/있(고|어요|어|네|음|는데|다)$/, '있음'], [/없(고|어요|어|네|는데|다)$/, '없음'],
    [/좋(고|아요|아|네|은데|다)$/, '좋음'], [/괜찮(고|아요|아|네|은데|다)$/, '괜찮음'],
    [/가깝(고|네|다)$/, '가까움'], [/편해$|편하고$/, '편함'],
    [/(해|하고|하네|해요|하다)$/, '함'], [/(이야|야|이에요|예요|이네|이다)$/, ''],
    [/(이고|이며|인데|한데|는데|지만)$/, ''], [/있으니까$/, '있음'], [/(으니까|니까)$/, ''],
    [/(많|넓|좁|작|높|낮|싸|않|나쁘지 않)(고|다|아|네)$/, '$1음'], [/크(고|다)$/, '큼'],
  ];
  const CATS = [
    ['price',  '💰 가격',      /억|매매|전세|월세|시세|호가|가격|융자|대출/],
    ['defect', '🔧 하자 · 내부', /누수|곰팡이|균열|금\s?간|결로|하자|수리|녹물|깨진|낡|리모델링|인테리어|공사|방음|소음|층간|내부|구조|화장실|방이|거실|주방|베란다|샷시|창호/],
    ['traffic','🚇 교통 · 입지', /역|호선|지하철|버스|출퇴근|직장|도보|걸어서|여의도|강남|광화문|판교|입지|위치/],
    ['parking','🚗 주차',      /주차/],
    ['manage', '🧹 관리',      /관리|경비|청소|조경|커뮤니티|엘리베이터|관리비/],
    ['school', '🏫 학군',      /초등|중학교|고등학교|학교|학원|초품아|학군/],
    ['life',   '🛒 생활 · 상권', /마트|상가|상권|편의점|시장|병원|공원|산책|카페|백화점|성당|교회|도서관|살기/],
    ['view',   '☀️ 향 · 채광',  /향|채광|햇빛|일조|뷰|조망|전망|밝/],
    ['complex','🏢 단지 · 규모', /단지|세대|평|동\s?수|연식|년식|준공|오래된|신축|구축/],
  ];
  const POS = /좋|괜찮|깔끔|넉넉|편리|편하|가까|저렴|무난|넓|조용|밝|최고|만족|장점|초역세권|역세권|대단지|여유|적당|훌륭|잘\s?돼|잘\s?되|쾌적|깨끗|새것|신축/;
  const NEG = /않|안\s?좋|별로|아쉽|불편|좁|비싸|시끄|어둡|낡|누수|곰팡이|균열|하자|부족|빡빡|멀|단점|걱정|문제|결로|오래돼|오래된|냄새|소음이|노후/;
  const REQUEST = /(넣어|첨부|올려|찾아|알아봐|확인해|물어봐|체크해|해)\s?줘|해\s?주세요|해야\s?(돼|함|겠)|확인\s?필요|물어봐야|알아봐야|봐야\s?돼/;

  const CONNECT = /^(아\s)?(그리고|그래서|근데|그런데|무엇보다|왜냐면|왜냐하면|또|게다가|일단|전반적으로|그리고는|아)$/;
  const TRAIL_CONNECT = /(\s(아\s)?(그리고|그래서|근데|그런데|무엇보다|왜냐면|왜냐하면|또|게다가|일단|아))+$/;
  function tidy(s) {
    let t = ' ' + s + ' ';
    for (const f of FILLERS) t = t.replace(f, ' ');
    t = t.replace(/\s+/g, ' ').trim().replace(TRAIL_CONNECT, '').replace(LEAD, '').replace(/^(나는|저는|내가|난)\s+/, '').replace(/^(여기는|여기)\s+(?=여기)/, '');
    for (const [re, rep] of ENDINGS) { if (re.test(t)) { t = t.replace(re, rep).trim(); break; } }
    return t.replace(/\s+/g, ' ').trim();
  }
  function segment(text) {
    const parts = text.replace(/[.?!]+(?!\d)|,(?!\d)/g, ' . ').split(/\s\.\s|\n+/)
      .flatMap(s => s.split(SPLIT_MARK)).flatMap(s => s.split(END_SPLIT))
      .map(s => s.trim().replace(TRAIL_CONNECT, '').trim()).filter(s => s && !CONNECT.test(s));
    const out = [];
    for (const s of parts) {
      const prev = out[out.length - 1];
      // 너무 짧거나, 앞 문장이 "~해서/~니까/~면"처럼 이어지는 말로 끝나면 합친다
      if (prev && (s.replace(/\s/g, '').length < 5 || (/^(나쁘지\s?않|괜찮|좋|별로|무난)/.test(s) && s.length < 10) || /(어서|아서|해서|라서|니까|으면|면|는데|지만|거여서|이어서)$/.test(prev))) out[out.length - 1] = prev + ' ' + s;
      else out.push(s);
    }
    return out;
  }
  /* 부동산 임장에서 자주 틀리는 음성인식 교정 (앱 녹음에만 적용) */
  const STT_FIX = [
    [/몰래(?=\s?(자이|힐스테이트|아파트|역|동|공원|초등|래미안|푸르지오|아이파크))/g, '문래'], [/주변\s?상관/g, '주변 상권'], [/상관(?=이\s?(좋|나쁘|괜찮))/g, '상권'],
    [/초프마|초품화|초푸마/g, '초품아'], [/메물/g, '매물'], [/메매/g, '매매'], [/맴매/g, '매매'], [/용자(?=[는가도])/g, '융자'],
    [/3대당/g, '세대당'], [/역세고/g, '역세권'], [/동양(?=\.|$|\s)/g, '동향'], [/남양이라/g, '남향이라'], [/체광/g, '채광'],
    [/중계사/g, '중개사'], [/(\d)\s?대구(?=\s)/g, '$1대고'], [/관리 사무소/g, '관리사무소'], [/대규모 되던지요?/g, '대규모 단지'], [/공팡이/g, '곰팡이'],
  ];
  const fixSTT = t => STT_FIX.reduce((s, [re, rep]) => s.replace(re, rep), t);
  const TAGS = [
    [/초역세권/, () => '초역세권'], [/(?<!초)역세권/, () => '역세권'], [/대단지/, () => '대단지'],
    [/([가-힣]+역)(?:이|에서|까지)?\s?바로\s?앞/, m => `${m[1]} 바로 앞`], [/(\d+)\s?호선/, m => `${m[1]}호선`],
    [/화장실(?:이)?\s?(두|2|세|3)\s?개/, m => `화장실 ${({두:2,세:3})[m[1]] || m[1]}개`], [/(\d+)\s?평/, m => `${m[1]}평`],
    [/리모델링/, () => '리모델링 세대'], [/초품아/, () => '초품아'], [/관리비[^.]{0,14}저렴/, () => '관리비 저렴'],
    [/(여의도|강남|광화문|판교|종로)[^.]{0,12}(가깝|가까|직장|출퇴근)/, m => `${m[1]} 출퇴근`], [/조망|뷰가\s?좋/, () => '조망'],
    [/대규모|대단지/, () => '대단지'], [/([가-힣]{2,}초등학교)/, m => `${m[1]} 인근`], [/([가-힣]{2,}공원)/, m => `${m[1]} 인근`],
    [/상권[^.]{0,8}(좋|괜찮|나쁘지\s?않)/, () => '상권 양호'], [/살기[^.]{0,8}좋/, () => '살기 좋음'],
    [/누수/, () => '⚠ 누수'], [/곰팡이/, () => '⚠ 곰팡이'], [/균열|금\s?간/, () => '⚠ 균열'], [/결로/, () => '⚠ 결로'], [/깨진|파손/, () => '⚠ 파손'],
  ];
  const polarityText = s => s.replace(/나쁘지\s?않/g, '괜찮').replace(/(넉넉|넓|크)지\s?않/g, '부족');
  function organize(text, name) {
    const segs = segment(text);
    const groups = {}, todos = [];
    for (let raw of segs) {
      // "…사진은 …첨부해서 넣어 줘" → 앞부분은 메모로, 사진 요청은 할 일로
      const pi = raw.search(/사진/);
      if (pi >= 0 && REQUEST.test(raw.slice(pi))) { if (!todos.includes('사진 첨부하기')) todos.push('사진 첨부하기'); raw = raw.slice(0, pi).trim().replace(/있으니까$/, '있음').replace(/(으니까|니까|으니)$/, '').trim(); if (!raw) continue; }
      else if (REQUEST.test(raw) && /확인|물어|알아|체크|찾아/.test(raw)) {   // 할 일에도 넣고, 메모에도 남긴다
        todos.push(tidy(raw).replace(/\s?(해\s?줘|해\s?주세요)$/, '').replace(/(이|가|도)?\s?(좀\s)?있어서\s?/, ' ').replace(/\s+/g, ' ').trim());
      }
      const line = tidy(raw);
      if (line.replace(/\s/g, '').length < 4 || /^아니\s/.test(line) && line.length < 10) continue;
      // "지금 OO 아파트에 와 있음" 같은 도입부는 뺀다
      const nameRe = name ? new RegExp(name.replace(/\s/g, '').split('').join('\\s?')) : null;
      if (nameRe && nameRe.test(line) && /(와\s?있|왔|임장하러|보러)/.test(line) && !/평|세대|역|단지가|좋|별로/.test(line.replace(nameRe, ''))) continue;
      const cat = (CATS.find(([, , re]) => re.test(raw)) || ['etc', '📝 기타'])[0];
      const pt = polarityText(raw), pos = POS.test(pt), neg = NEG.test(pt);
      const mood = pos && neg ? 'mix' : neg ? 'neg' : pos ? 'pos' : 'neu';
      (groups[cat] = groups[cat] || []).push({ text: line, mood });
    }
    const tags = [];
    for (const [re, fmt] of TAGS) { const m = text.match(re); if (m) { const t = fmt(m); if (!tags.includes(t) && !(t === '역세권' && tags.includes('초역세권'))) tags.push(t); } }
    const all = Object.values(groups).flat();
    const pos = all.filter(x => x.mood === 'pos').length, neg = all.filter(x => x.mood === 'neg').length, mix = all.filter(x => x.mood === 'mix').length;
    const sections = CATS.concat([['etc', '📝 기타']]).filter(([k]) => groups[k]).map(([k, label]) => ({ key: k, label, items: groups[k] }));
    return { sections, tags, todos, counts: { pos, neg, mix }, lines: all.length };
  }

  const api = { normalizeRegion, classify, extract, analyze, parseMoney, empty, extractComplexName, organize, segment, tidy, fixSTT };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ZipEngine = api;
})(typeof window !== "undefined" ? window : globalThis);
