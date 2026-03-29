---
name: tweet-trend-analyzer
description: "X(트위터) AI/테크 트윗을 수집·분석하여 핵심 트렌드 요약 마크다운을 생성하는 스킬.
트리거: \"트윗 분석\", \"트윗 정리\", \"트렌드 정리\", \"트렌드 요약\", \"타임라인 가져와서 분석해줘\",
\"오늘 트윗 정리해줘\", 또는 tw_*.csv / tw_*.md 파일이 업로드되면서 \"정리해줘\", \"요약해줘\" 등의 요청이 올 때.
Chrome MCP(Claude in Chrome)가 연결되어 있으면 CSV 없이도 타임라인을 직접 수집하여 분석한다.
제외 패턴으로 비-AI 트윗을 걸러내고, 추천 피드의 경우 AI 신호 키워드로 추가 필터링한다.
DuckDB SQL로 고속 분석하며, 출력은 마크다운(.md) 파일이다.
반드시 사용: 트윗/타임라인/트렌드 관련 요청, tw_* 파일 업로드, \"트렌드 분석해줘\" 한 마디 요청.
스케줄 실행 지원: scheduled-tasks로 등록하면 매일 자동 실행 가능."
---

# Tweet Trend Analyzer v6

X(트위터) AI/테크 트윗을 수집하고 분석하여 한국어 트렌드 요약 마크다운을 생성한다.

v6 변경점:
- **전체 트윗 분석** — TOP 80이 아닌 전체 AI 필터링 트윗을 분석
- **브라우저 내 토픽 클러스터링** — 토픽 감지·분류·대표 트윗 선정까지 브라우저에서 완료
- **속도 2배 개선** — 10페이지 배치, 1초 간격, 토픽별 결과 전달(청크 3회 이내)

## 입력 소스 (자동 감지)

우선순위 순서대로 자동 감지:

1. **CSV/MD 파일 업로드** → Phase 0 건너뛰고 Phase 1로
2. **Chrome MCP 연결 + 파일 없음** → Phase 0 수집 실행
3. **둘 다 없음** → 사용자에게 CSV 업로드 요청

CSV 11컬럼: `번호, 이름, 핸들, 텍스트, 시간, URL, 댓글, RT, 좋아요, 조회, 미디어`
MD: 테이블 구간 + Full Texts 구간 병합. `references/md-parsing.md` 참조.

## Phase 0: 타임라인 수집 (Chrome MCP) — 속도 최적화

**조건:** Claude in Chrome MCP 연결 + 파일 미업로드
**전제:** Chrome에서 x.com 로그인 상태

### 수집 절차

1. `tabs_context_mcp(createIfEmpty=true)` → 탭 확인
2. x.com으로 `navigate`
3. ct0 토큰 추출 (`window.__ct0`에 저장, 반환은 길이만)
4. **한 번의 javascript_tool 호출로 fetchPage 함수 + batchFetch 함수 + 파싱 로직 모두 정의**
5. `batchFetch(13)` 실행 → 500개+ 수집 (1회 호출로 13페이지, ~1분)
6. 완료 확인 후 즉시 Phase 1 (브라우저 내 전체 분석)

### GraphQL 호출

`references/graphql-config.md`에 FEATURES 객체 전문, 트윗 파싱 로직 포함.

**핵심 설정:**
- Bearer: `AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA`
- queryId: `c-CzHF1LboFilMpsx4ZCrQ` (변경 가능 — 실패 시 GitHub에서 최신 조회)
- URL: `/i/api/graphql/{queryId}/HomeTimeline?variables=...&features=...`
- Headers: `Authorization: Bearer ...`, `X-Csrf-Token: {ct0}`, `X-Twitter-Auth-Type: OAuth2Session`

**페이지네이션 (v6 최적화):**
- 40개씩 요청, cursor로 다음 페이지, **1초 간격** (v5: 1.5초)
- **13페이지를 1배치로** (v5: 5페이지씩 나눠서 확인 → 불필요한 왕복)
- `promotedMetadata` 있는 항목 자동 스킵
- 수집 완료 확인: `window.__pg.tweets.length` 반환

**javascript_tool 핵심 패턴:**

```
// ❌ async 함수 직접 반환 = undefined
(async () => { ... })()

// ✅ window 전역변수에 저장 후 별도 호출로 읽기
window.__pg = { tweets: [], seen: new Set(), cursor: null, done: false, page: 0 };
```

**트윗 추출 경로:**
- 텍스트: `tw.note_tweet.note_tweet_results.result.text` || `tw.legacy.full_text`
- 이름: `tw.core.user_results.result.legacy.name`
- 핸들: `tw.core.user_results.result.legacy.screen_name`
- 조회: `tw.views.count` (parseInt)
- 미디어: `tw.legacy.extended_entities.media[].media_url_https`

**CSV 다운로드:** BOM(`\uFEFF`) 포함 UTF-8, 파일명 `tw_timeline_YYYYMMDD.csv`

## Phase 1: 브라우저 내 전체 분석 + 토픽 클러스터링 (v6 핵심)

> **v6의 핵심 변경: 전체 트윗을 분석하고, 토픽 클러스터링까지 브라우저에서 완료한다.**
> 이전 v5에서는 TOP 80만 추출 → 청크 전달 → Claude가 분석하는 3단계였지만,
> v6에서는 **전체 AI 트윗 → 키워드 기반 토픽 분류 → 토픽별 대표 트윗 선정**을 모두 브라우저 JS에서 수행.
> Claude에게는 토픽별 요약 데이터만 전달하므로 API 호출이 3회 이내로 줄어든다.

### 1-1. 전체 AI/테크 필터링 + 토픽 클러스터링 (단일 JS 호출)

수집 완료 후, 같은 탭에서 javascript_tool로 실행:

```javascript
// === STEP 1: 필터링 (전체 트윗 대상) ===
const exclude = /(K-?pop|아이돌|컴백|앨범|드라마|예능|웹툰|만화|야구|축구|농구|배구|올림픽|선거|대통령|국회|정당|탄핵|치킨|피자|배달|쿠폰|경품|화장품|뷰티|패션|다이어트|헬스장)/i;
const include = /(AI|GPT|LLM|Claude|Anthropic|OpenAI|...)/i;

const all = window.__pg.tweets;
const ai = all.filter(t => !exclude.test(t.text) && include.test(t.text));
ai.forEach(t => { t.engagement = t.likes + t.rt*2 + t.comments*1.5; });

// === STEP 2: 키워드 기반 토픽 클러스터 정의 ===
const topicDefs = [
  { name: 'Claude/Anthropic', keywords: /claude|anthropic|sonnet|opus|haiku|mcp|cowork/i },
  { name: 'OpenAI/GPT/Codex', keywords: /openai|gpt|codex|chatgpt|o1|o3|dall-?e|sora/i },
  { name: 'Google/Gemini/DeepMind', keywords: /google|gemini|deepmind|gemma|bard/i },
  { name: 'AI Agent/자율화', keywords: /agent|agentic|autonomous|workflow|automat|crew|devin|browser.use/i },
  { name: '바이브코딩/개발도구', keywords: /vibe.?cod|cursor|copilot|windsurf|bolt|lovable|replit|trae|ide|coding|code.?editor/i },
  { name: 'LLM/모델/벤치마크', keywords: /llm|model|benchmark|inference|training|fine.?tun|rlhf|transformer|neural|reasoning/i },
  { name: 'AI인프라/GPU/클라우드', keywords: /gpu|nvidia|amd|tsmc|chip|semiconductor|cloud|aws|gcp|azure|infra|compute|server/i },
  { name: '오픈소스/GitHub', keywords: /open.?source|oss|github|git|hugging.?face|llama|mistral|qwen|deepseek/i },
  { name: 'AI규제/법률/사회', keywords: /regulat|law|legal|copyright|lawsuit|safety|alignment|agi|asi|policy|govern|trump|congress/i },
  { name: 'AI크리에이티브/멀티모달', keywords: /image|video|3d|generat|multimodal|vision|art|design|midjourney|interior|voice|tts|music/i },
  { name: '프론트엔드/웹개발', keywords: /react|next\.?js|vercel|frontend|backend|supabase|stripe|saas|deploy|tailwind|vite/i },
  { name: '스타트업/비즈니스', keywords: /startup|funding|yc|unicorn|acquisition|ipo|valuation|series|venture|founder/i },
  { name: 'xAI/Grok', keywords: /xai|grok|elon/i },
  { name: 'Perplexity/검색AI', keywords: /perplexity|search|rag|embedding|vector|retrieval/i }
];

// === STEP 3: 전체 AI 트윗을 토픽별 분류 (중복 허용) ===
const topics = topicDefs.map(td => {
  const matched = ai.filter(t => td.keywords.test(t.text));
  matched.sort((a,b) => b.engagement - a.engagement);
  return {
    name: td.name,
    count: matched.length,
    totalEng: Math.round(matched.reduce((s,t) => s + t.engagement, 0)),
    totalViews: matched.reduce((s,t) => s + t.views, 0),
    // 토픽별 대표 트윗 TOP 10 (전체 필드)
    top: matched.slice(0, 10).map(t => ({
      name: t.name, h: t.handle, likes: t.likes, rt: t.rt,
      comments: t.comments, views: t.views, url: t.url,
      eng: Math.round(t.engagement),
      txt: (t.text||'').substring(0,200)
    }))
  };
});

// 트윗 3건 이상인 토픽만, engagement 합 기준 정렬
topics.sort((a,b) => b.totalEng - a.totalEng);
window.__topics = topics.filter(t => t.count >= 3);

// === STEP 4: 전체 통계 ===
const totalLikes = ai.reduce((s,t) => s + t.likes, 0);
const totalViews = ai.reduce((s,t) => s + t.views, 0);
window.__aiStats = {
  totalAll: all.length, totalAI: ai.length,
  aiRatio: Math.round(ai.length / all.length * 100),
  avgLikes: Math.round(totalLikes / ai.length),
  avgViews: Math.round(totalViews / ai.length),
  topicCount: window.__topics.length
};

// === STEP 5: 키워드 빈도 (전체 AI 트윗 대상) ===
const kwList = ['AI','Claude','OpenAI','GPT','Gemini','agent','MCP','model','code','API','GPU','prompt','Cursor','GitHub','Codex','LLM','RAG','Vercel','Supabase','React','deploy','Docker','startup','crypto','Grok','xAI','Perplexity','Llama','DeepSeek','Windsurf','Bolt','NVIDIA','TSMC'];
const kwCount = {};
const allTexts = ai.map(t => t.text.toLowerCase());
kwList.forEach(w => {
  const wl = w.toLowerCase();
  let c = 0; allTexts.forEach(txt => { if(txt.includes(wl)) c++; });
  if(c >= 2) kwCount[w] = c;
});
window.__kwTop = Object.entries(kwCount).sort((a,b) => b[1]-a[1]).slice(0,10);

// 작성자 TOP 20 (전체 AI 트윗 기준)
const aMap = {};
ai.forEach(t => {
  if(!aMap[t.handle]) aMap[t.handle] = {h:t.handle, n:t.name, tw:0, eng:0, views:0};
  aMap[t.handle].tw++; aMap[t.handle].eng += t.engagement; aMap[t.handle].views += t.views;
});
window.__topAuthors = Object.values(aMap).sort((a,b) => b.eng - a.eng).slice(0,20);

// 반환: 통계 + 키워드 + 토픽 수 (소량, BLOCKED 안 됨)
JSON.stringify({ stats: window.__aiStats, kwTop: window.__kwTop, topicNames: window.__topics.map(t => t.name + '(' + t.count + ')') })
```

### 1-2. 토픽별 대표 트윗 전달 (2~3회 호출)

**v6 핵심: 토픽별로 이미 구조화된 데이터를 전달하므로 청크 수가 대폭 감소.**

```javascript
// 토픽 0~3 한번에 전달
window.__getTopicChunk = function(start, end) {
  const result = [];
  for (let i = start; i < Math.min(end, window.__topics.length); i++) {
    const tp = window.__topics[i];
    const tweets = tp.top.map(t => {
      const txt = (t.txt||'').replace(/~/g,' ').replace(/[\n\r]/g,' ')
        .replace(/[^\x20-\x7Ea-zA-Z0-9\uAC00-\uD7AF\u3041-\u30F6\u4E00-\u9FFF .,!?@#$%&*:;()\-\/'"+=<>{}\[\]]/g,'');
      return t.h + '|' + t.likes + '|' + t.rt + '|' + t.views + '|' + t.url + '|' + txt.substring(0,150);
    }).join('\n  ');
    result.push('TOPIC:' + tp.name + '|count=' + tp.count + '|eng=' + tp.totalEng + '\n  ' + tweets);
  }
  return result.join('\n---\n');
};
```

**전달 규칙:**
- 1회: `window.__getTopicChunk(0, 4)` — 상위 4개 토픽
- 2회: `window.__getTopicChunk(4, 8)` — 다음 4개 토픽
- 3회(선택): `window.__getTopicChunk(8, 12)` — 나머지 토픽 (있으면)
- BLOCKED 시: 범위를 2개로 축소 (`0,2` → `2,4` → ...)

**총 API 호출 예상: 수집 확인 2회 + 분석 1회 + 토픽 전달 2~3회 = 5~6회 (v5: 15회+)**

### 1-3. 작성자 TOP 20 + 미분류 트윗 확인

```javascript
JSON.stringify({
  authors: window.__topAuthors.slice(0, 10),
  // 어떤 토픽에도 속하지 않은 고 engagement 트윗 (놓친 트렌드 방지)
  uncategorized: ai.filter(t => !window.__topics.some(tp => tp.top.some(tt => tt.url === t.url)))
    .sort((a,b) => b.engagement - a.engagement)
    .slice(0, 5)
    .map(t => ({ h: t.handle, txt: t.text.substring(0,100), eng: Math.round(t.engagement), url: t.url }))
})
```

## Phase 1-B: DuckDB 분석 (CSV 파일이 있는 경우)

CSV가 업로드되었거나 로컬에 존재하면, DuckDB SQL로 분석한다.

**DuckDB CLI 사용.** 없으면 설치:
```bash
curl -fsSL https://install.duckdb.org | sh
export PATH="/root/.duckdb/cli/latest:$PATH"
```

### AI/테크 필터링 (전체 대상)

```sql
WITH ai AS (
    SELECT *, 좋아요 + RT*2 + 댓글*1.5 AS engagement
    FROM 'INPUT_FILE'
    WHERE NOT regexp_matches(텍스트,
        '(K-?pop|아이돌|컴백|앨범|드라마|예능|웹툰|만화|야구|축구|농구|배구|올림픽|선거|대통령|국회|정당|탄핵|치킨|피자|배달|쿠폰|경품|화장품|뷰티|패션|다이어트|헬스장)')
      AND regexp_matches(텍스트,
        '(?i)(AI|GPT|LLM|Claude|Anthropic|OpenAI|Gemini|Google|DeepMind|Meta|agent|MCP|model|coding|code|developer|dev|API|SDK|GPU|NVIDIA|AMD|Intel|prompt|Cursor|Copilot|GitHub|Cowork|Codex|Supabase|React|Vercel|Next\.js|deploy|frontend|backend|browser.use|token|context|benchmark|chip|semiconductor|TSMC|compute|cloud|AWS|GCP|Azure|CLI|terminal|IDE|Figma|Docker|Kubernetes|startup|funding|YC|open.source|OSS|ML|NLP|transformer|neural|inference|training|finetun|RAG|embedding|vector|multimodal|vision|robotics|autonomous|agentic|workflow|automat|pipeline|Rust|Python|TypeScript|JavaScript|programming|software|engineer|tech|SaaS|infra|database|serverless|Cloudflare|Deno|Bun|Vite|npm|crypto|blockchain|Gemma|Llama|Mistral|Qwen|DeepSeek|Grok|xAI|Perplexity|Midjourney|Hugging.Face|LangChain|CrewAI|Devin|Replit|Windsurf|Bolt|Lovable|Trae)')
)
```

### 전체 분석 쿼리 (v6: TOP 80 제한 없음)

```sql
-- 전체 AI 트윗 (제한 없음)
SELECT 번호, 이름, 핸들, 텍스트[1:200] AS preview,
       좋아요, RT, 댓글, 조회, round(engagement,0) AS eng, URL
FROM ai ORDER BY engagement DESC;

-- 작성자 TOP 20
SELECT 핸들, count() AS tweets,
       round(sum(engagement),0) AS total_eng,
       sum(조회) AS total_views
FROM ai GROUP BY ALL ORDER BY total_eng DESC LIMIT 20;

-- 기본 통계
SELECT count() AS total_ai,
       round(avg(좋아요),0) AS avg_likes,
       round(avg(조회),0) AS avg_views
FROM ai;
```

**출력 형식:** `-json` (Claude 분석용) 또는 `-csv` (사람 확인용)

**피드 종류별 전략:**
- 팔로잉 피드 (이미 AI 계정 위주): EXCLUDE만 적용, AI_SIGNAL 생략 가능
- 추천 피드 (노이즈 다수): 양방향 필터 필수
- 자동 판단: 필터 후 AI 비율 50% 미만이면 추천 피드로 간주

## Phase 2: 토픽별 상세 분석 + 리포트 작성

> **v6에서는 Phase 1에서 토픽 클러스터링이 이미 완료되었으므로, Phase 2에서는 즉시 리포트 작성에 들어간다.**

각 토픽에 대해:
1. 해당 토픽의 **전체** 트윗 수, 총 engagement, 대표 트윗 확인
2. 핵심 소식/주장 추출
3. 찬성/반대/냉소적 시각 균형 포함
4. `> **시사점:**` 블록으로 토픽 의미 요약
5. 미디어 활용: `article`=기사, `img`/`vid`=시각자료 표시
6. 모든 인용에 `[🔗](URL)` 링크 포함
7. **미분류 고 engagement 트윗도 확인** — 놓친 트렌드 방지

## Phase 3: 이전 회차 대비 변화 감지

**사용자가 명시적으로 요청할 때만 수행.**

## 출력

파일명: `AI_trend_summary_YYYY-MM-DD.md` (영문 필수)

```markdown
# 🔥 AI 트윗 트렌드 핵심 요약 (YYYY.MM.DD)

> **데이터:** N개 트윗 분석 (AI/테크 M개 필터링) | **주요 키워드 TOP 5:** A(n), B(n), C(n), D(n), E(n)

오늘의 타임라인에서 가장 눈에 띄는 흐름은 [핵심 트렌드 한줄 요약을 순수 한국어로 작성]. [두번째 주요 흐름도 한국어로 이어서 서술].

---

## 1. [토픽명] — [한줄 요약]

[2~3문단 서술 — 반드시 한국어 문장으로, 첫 문장은 조사와 어미를 포함한 완전한 한국어 문장이어야 한다]

주요 소식들:
- **[소식1]** — 상세 설명 (@핸들, N만 조회) [🔗](https://x.com/핸들/status/ID)
- **[소식2]** — 상세 설명 (@핸들, N만 조회) [🔗](https://x.com/핸들/status/ID)

> **시사점:** [1~2문장]
>
> `#한글해시태그1` `#한글해시태그2` — 한국어 해시태그 2~3개, 공백 없이 **한글만으로 10자 이상** 작성. 예: `#오픈소스생태계수직통합` `#에이전트아키텍처표준화확산` `#반도체공급망지정학리스크`

---
(5~7개 토픽 반복)

---

## 📊 오늘의 감정/온도 분석

- **🔴 과열 신호:** [토픽]
- **🟢 실질적 성장:** [토픽]
- **🟡 주의 필요:** [토픽]
- **🔵 패러다임 전환:** [토픽]

---

## 🎯 바이브 코딩 시사점

1. **[시사점1]** — [활용법]
2. **[시사점2]** — [활용법]
3. **[시사점3]** — [활용법]
```

## 작성 원칙 (필수 — 반드시 준수)

- 모든 출력 **한국어** — 각 토픽 서술은 최소 2~3문장의 한국어 문장으로 작성 (영어 나열 금지, 한국어 문장으로 풀어서 설명)
  - **중요:** 토픽 서술의 첫 문장은 반드시 순수 한국어로 시작해야 한다 (예: "오늘 가장 뜨거운 소식은 클로드 코드 생태계의 급성장이다")
  - 영어 고유명사는 한국어 문장 속에 자연스럽게 삽입 (예: "OpenAI가 Astral을 인수하면서 파이썬 생태계에 큰 변화가 예상된다")
- **링크 필수:** 모든 트윗 인용에 반드시 `[🔗](https://x.com/핸들/status/ID)` 형식의 링크를 포함해야 한다
  - URL을 모르면 `https://x.com/핸들` 로 대체 가능하지만, `[🔗](https://...)` 형태는 반드시 유지
  - 예시: `(@steipete, 7.8만 조회) [🔗](https://x.com/steipete/status/2035023659849720265)`
  - 링크 없는 인용은 금지
- 숫자: 한글 단위 사용 (25만, 2.5천, 3,556만) — 영문 단위(K, M) 금지
- 과장 없이 재미있게, 비판적 시각도 균형있게
- 감정/온도: 데이터 기반 (조회 대비 좋아요율, 반박 존재 여부)
- 바이브 코딩 시사점: 새 도구, 워크플로우 패턴, 보안/비용, 에이전트 생태계
- 건설업 시사점 제외

## v5 대비 v6 API 호출 비교

| 단계 | v5 호출 수 | v6 호출 수 |
|------|-----------|-----------|
| 수집 (navigate+ct0+batch) | 5~6 | 3~4 |
| 배치 확인 | 3~4 | 1~2 |
| 필터링+통계 | 2 | 1 (필터+토픽+키워드 통합) |
| 데이터 전달 (청크) | 6~8 | 2~3 (토픽별 구조화) |
| 작성자/추가 | 2 | 1 |
| **합계** | **18~22** | **8~11** |

## 스케줄 실행 참고

`scheduled-tasks`로 등록 시:
- 전제: Chrome에서 x.com 로그인 유지
- 프롬프트: "tweet-trend-analyzer 스킬로 오늘 트윗 트렌드를 분석해서 AI_trend_summary_YYYY-MM-DD.md로 저장해줘"
- 출력 경로: workspace 폴더 (매일 트윗 정리)
