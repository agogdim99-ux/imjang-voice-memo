/* 집노트 AI — Claude로 ① 단지 찾기 ② 웹 검색(단지 정보·최근 실거래가) ③ 임장 내용 정리.
   API 키는 사용자의 폰(localStorage)에만 저장되고, Anthropic API로만 전송된다. */
(function (root) {
  'use strict';
  const SDK_URL = 'https://cdn.jsdelivr.net/npm/@anthropic-ai/sdk@0.136.0/+esm';
  const MODEL = 'claude-opus-5-5';

  const S = t => ({ type: [t, 'null'] });
  const STR_LIST = { type: 'array', items: { type: 'string' } };
  const obj = (props) => ({ type: 'object', properties: props, required: Object.keys(props), additionalProperties: false });

  // 결과 양식 — Claude는 이 도구를 한 번 호출해 결과를 넘긴다 (strict: 양식이 항상 맞음)
  const REPORT_TOOL = {
    name: 'save_report',
    description: '검색과 정리를 마친 뒤 결과를 저장한다. 마지막에 정확히 한 번 호출한다.',
    strict: true,
    input_schema: obj({
      complex: obj({
        name: S('string'),            // 공식 단지명 (예: 문래자이)
        heard_as: S('string'),        // 녹음에서 들린 표현 (예: 문래 자이)
        address: S('string'),         // 도로명 또는 지번 주소
        sido: S('string'), sigungu: S('string'), dong: S('string'),
        households: S('integer'), buildings: S('integer'), built_year: S('integer'),
        floors_max: S('integer'), parking_per_household: S('number'),
        nearest_station: S('string'), station_walk_min: S('integer'),
        builder: S('string'), heating: S('string'),
        confidence: { type: 'string', enum: ['높음', '보통', '낮음', '못 찾음'] },
      }),
      market: obj({
        area_pyeong: S('number'),     // 시세 기준 평형 (녹음에서 말한 평형 우선)
        sale_recent: S('integer'),    // 최근 매매 실거래가 (만원)
        sale_date: S('string'),
        jeonse_recent: S('integer'),  // 최근 전세 (만원)
        jeonse_date: S('string'),
        note: S('string'),            // 시세에 대한 한 줄 설명
      }),
      sources: { type: 'array', items: obj({ title: { type: 'string' }, url: { type: 'string' } }) },
      visit: obj({
        summary: { type: 'string' },  // 2~3문장 요약
        said_area_pyeong: S('number'),
        said_sale: S('integer'), said_jeonse: S('integer'),   // 녹음에서 직접 말한 가격 (만원)
        pros: STR_LIST, cons: STR_LIST, defects: STR_LIST,
        management: STR_LIST, location: STR_LIST, to_check: STR_LIST,
      }),
    }),
  };

  const SYSTEM = `너는 한국 수도권 아파트 임장(현장 방문)을 돕는 부동산 비서다. 사용자는 상업용 부동산 PM 출신 투자 준비자다.
입력은 휴대폰 음성인식으로 받아쓴 임장 혼잣말이다. 띄어쓰기·문장부호가 없고 인식 오류가 섞여 있다 (예: "문래 자이" = 문래자이, "아파" = 아파트).

할 일
1. 녹음에서 단지명과 지역을 알아낸다. 확실하지 않으면 지역 단서(역 이름, 동네)로 웹 검색해 가장 그럴듯한 단지를 고른다.
2. web_search로 그 단지의 기본 정보(주소, 세대수, 동 수, 준공연도, 최고층, 세대당 주차, 가까운 역과 도보 시간, 시공사, 난방)를 찾는다.
3. web_search로 최근 실거래가를 찾는다. 녹음에서 말한 평형(없으면 대표 평형)의 최근 매매가·전세가와 거래 시점을 적는다. 국토부 실거래가·호갱노노·아실·네이버 부동산 등 출처를 쓴다.
4. 녹음 내용을 정리한다: 요약 2~3문장, 좋았던 점, 아쉬운 점, 하자·수리, 관리 상태, 입지(역·학교·상권·직장 접근), 다시 확인할 것.
   - 말한 내용만 정리하고 지어내지 않는다. 검색 정보는 complex/market에만 넣는다.
   - 녹음에서 직접 말한 가격·평형은 visit.said_* 에 만원 단위로 넣는다 (7억 2천 → 72000). 말하지 않았으면 null.
5. 마지막에 save_report 도구를 정확히 한 번 호출한다.

규칙
- 금액은 모두 만원 단위 정수.
- 찾지 못한 값은 null. 추측한 숫자를 넣지 않는다. 단지를 특정하지 못했으면 confidence를 '못 찾음'으로.
- sido는 '서울특별시' / '인천광역시' / '경기도' 중 하나.
- 검색은 4번 이내로 끝낸다.`;

  let client = null, clientKey = null;
  async function getClient(apiKey) {
    if (client && clientKey === apiKey) return client;
    const mod = await import(SDK_URL);
    const Anthropic = mod.default || mod.Anthropic;
    client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true, maxRetries: 2, timeout: 180000 });
    clientKey = apiKey;
    return client;
  }

  function friendlyError(e) {
    const s = e && (e.status || (e.error && e.error.status));
    if (s === 401) return 'API 키가 올바르지 않아요. 내 기록 → AI 설정에서 키를 확인해 주세요.';
    if (s === 402 || /credit|billing/i.test(String(e && e.message))) return 'API 크레딧이 부족해요. console.anthropic.com에서 충전해 주세요.';
    if (s === 429) return '요청이 많아요. 잠시 후 다시 시도해 주세요.';
    if (s === 529 || s >= 500) return 'Claude 서버가 바빠요. 잠시 후 다시 시도해 주세요.';
    if (e && /fetch|network/i.test(String(e.message))) return '인터넷 연결을 확인해 주세요.';
    return '정리 중 문제가 생겼어요: ' + (e && e.message ? e.message.slice(0, 120) : '알 수 없는 오류');
  }

  /* 요청 옵션 중 하나가 거절(400)되면 더 단순한 요청으로 한 번씩 다시 시도한다 */
  let mode = 0;   // 0: beta+fallbacks+strict, 1: 일반+strict, 2: 일반+strict 없음
  async function create(c, body) {
    for (;;) {
      try {
        if (mode === 0) return await c.beta.messages.create({ ...body, betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' });
        if (mode === 1) return await c.messages.create(body);
        const tools = body.tools.map(t => t.strict ? { ...t, strict: undefined } : t);
        return await c.messages.create({ ...body, tools });
      } catch (e) {
        if (e && e.status === 400 && mode < 2) { console.warn('집노트: 요청 단순화 후 재시도', e.message); mode++; continue; }
        throw e;
      }
    }
  }

  /* 받아쓴 글 → 보고서. onStep(문구)로 진행 상황을 알린다. */
  async function analyze(apiKey, transcript, onStep) {
    const c = await getClient(apiKey);
    const messages = [{ role: 'user', content: `임장 녹음 받아쓰기:\n\n${transcript}` }];
    onStep && onStep('단지를 찾고 있어요');
    for (let turn = 0; turn < 6; turn++) {
      const res = await create(c, {
        model: MODEL,
        max_tokens: 16000,
        system: SYSTEM,
        messages,
        tools: [{ type: 'web_search_20260209', name: 'web_search', max_uses: 4, user_location: { type: 'approximate', country: 'KR', timezone: 'Asia/Seoul' } }, REPORT_TOOL],
        tool_choice: { type: 'auto' },
        output_config: { effort: 'medium' },
      });
      if (res.stop_reason === 'refusal') throw new Error('요청이 거절됐어요');
      const searches = res.content.filter(b => b.type === 'server_tool_use').length;
      if (searches) onStep && onStep(`단지 정보·시세 검색 중 (${searches}번)`);
      const call = res.content.find(b => b.type === 'tool_use' && b.name === 'save_report');
      if (call) {
        const r = call.input;
        r._usage = res.usage; r._model = res.model; r._at = Date.now();
        return r;
      }
      if (res.stop_reason === 'pause_turn') { messages.push({ role: 'assistant', content: res.content }); continue; }
      if (res.stop_reason === 'max_tokens') throw new Error('응답이 너무 길어 잘렸어요');
      // 도구를 안 부르고 끝났으면 한 번 더 요청
      messages.push({ role: 'assistant', content: res.content });
      messages.push({ role: 'user', content: 'save_report 도구로 결과를 저장해 주세요.' });
      onStep && onStep('정리를 마무리하고 있어요');
    }
    throw new Error('결과를 받지 못했어요');
  }

  /* 키 확인용 아주 짧은 호출 */
  async function testKey(apiKey) {
    const c = await getClient(apiKey);
    await c.messages.create({ model: MODEL, max_tokens: 16, messages: [{ role: 'user', content: 'ok' }], output_config: { effort: 'low' } });
    return true;
  }

  /* ── 키 없이: Claude·ChatGPT 앱에 넘겨주고 답을 붙여넣기 ── */
  const TEMPLATE = {
    complex: { name: '공식 단지명', heard_as: '녹음에서 들린 표현', address: '주소', sido: '서울특별시|인천광역시|경기도', sigungu: '구/시', dong: '동',
      households: 0, buildings: 0, built_year: 0, floors_max: 0, parking_per_household: 0.0, nearest_station: '역 이름', station_walk_min: 0,
      builder: '시공사', heating: '난방', confidence: '높음|보통|낮음|못 찾음' },
    market: { area_pyeong: 0, sale_recent: 0, sale_date: '거래 시점', jeonse_recent: 0, jeonse_date: '거래 시점', note: '시세 한 줄 설명' },
    sources: [{ title: '출처 제목', url: 'https://...' }],
    visit: { summary: '2~3문장 요약', said_area_pyeong: 0, said_sale: 0, said_jeonse: 0,
      pros: ['좋았던 점'], cons: ['아쉬운 점'], defects: ['하자'], management: ['관리 상태'], location: ['입지'], to_check: ['다시 확인할 것'] },
  };
  function handoffPrompt(transcript) {
    return `${SYSTEM.replace('5. 마지막에 save_report 도구를 정확히 한 번 호출한다.', '5. 마지막에 아래 형식의 JSON을 코드블록 하나로 출력한다.').replace('web_search로', '웹 검색으로').replace('web_search로', '웹 검색으로')}
- 숫자 칸은 숫자만(따옴표 없이), 모르면 null. 금액은 만원 단위 (15억 → 150000).
- JSON 앞에 짧게 설명해도 되지만, JSON 코드블록은 반드시 하나만.

JSON 형식:
\`\`\`json
${JSON.stringify(TEMPLATE)}
\`\`\`

임장 녹음 받아쓰기:
"""
${transcript}
"""`;
  }
  // 붙여넣은 답에서 JSON을 꺼내 보고서 모양으로 맞춘다
  function parseHandoff(text) {
    const block = (text.match(/```(?:json)?\s*([\s\S]*?)```/) || [])[1] || text;
    const i = block.indexOf('{'), j = block.lastIndexOf('}');
    if (i < 0 || j <= i) throw new Error('답에서 JSON을 찾지 못했어요. Claude 답 전체를 복사해 붙여넣어 주세요.');
    let r;
    try { r = JSON.parse(block.slice(i, j + 1)); }
    catch (e) { throw new Error('JSON 형식이 깨져 있어요. 코드블록 부분을 다시 복사해 주세요.'); }
    const num = v => (v === '' || v === null || v === undefined || isNaN(Number(String(v).replace(/,/g, '')))) ? null : Number(String(v).replace(/,/g, ''));
    const str = v => (v === '' || v == null) ? null : String(v);
    const arr = v => Array.isArray(v) ? v.map(String).filter(Boolean) : (v ? [String(v)] : []);
    const c = r.complex || {}, m = r.market || {}, v = r.visit || {};
    const out = {
      complex: { name: str(c.name), heard_as: str(c.heard_as), address: str(c.address), sido: str(c.sido), sigungu: str(c.sigungu), dong: str(c.dong),
        households: num(c.households), buildings: num(c.buildings), built_year: num(c.built_year), floors_max: num(c.floors_max),
        parking_per_household: num(c.parking_per_household), nearest_station: str(c.nearest_station), station_walk_min: num(c.station_walk_min),
        builder: str(c.builder), heating: str(c.heating), confidence: str(c.confidence) || '보통' },
      market: { area_pyeong: num(m.area_pyeong), sale_recent: num(m.sale_recent), sale_date: str(m.sale_date), jeonse_recent: num(m.jeonse_recent), jeonse_date: str(m.jeonse_date), note: str(m.note) },
      sources: Array.isArray(r.sources) ? r.sources.filter(s => s && s.url).map(s => ({ title: String(s.title || s.url), url: String(s.url) })) : [],
      visit: { summary: str(v.summary) || '', said_area_pyeong: num(v.said_area_pyeong), said_sale: num(v.said_sale), said_jeonse: num(v.said_jeonse),
        pros: arr(v.pros), cons: arr(v.cons), defects: arr(v.defects), management: arr(v.management), location: arr(v.location), to_check: arr(v.to_check) },
      _via: 'handoff', _at: Date.now(),
    };
    // 템플릿의 0을 그대로 둔 값은 '모름'으로 본다
    for (const sec of ['complex', 'market', 'visit']) for (const k in out[sec]) if (out[sec][k] === 0) out[sec][k] = null;
    if (!out.complex.name && !out.visit.summary) throw new Error('단지명과 요약이 비어 있어요. 답을 다시 확인해 주세요.');
    return out;
  }

  root.ZipAI = { analyze, testKey, friendlyError, MODEL, handoffPrompt, parseHandoff };
})(window);
