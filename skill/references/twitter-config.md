# Twitter/X GraphQL 수집 설정

## 인증

- **Bearer Token:** `AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA`
- **queryId:** `c-CzHF1LboFilMpsx4ZCrQ` (변경될 수 있음 — 실패 시 GitHub에서 최신 queryId 조회)
- **URL:** `/i/api/graphql/{queryId}/HomeTimeline?variables=...&features=...`
- **Headers:**
  - `Authorization: Bearer {위 토큰}`
  - `X-Csrf-Token: {ct0}` (브라우저 쿠키에서 추출)
  - `X-Twitter-Auth-Type: OAuth2Session`

## ct0 토큰 추출

Chrome MCP `javascript_tool`로 실행:
```javascript
// ct0 쿠키 추출 → window.__ct0에 저장
document.cookie.split(';').forEach(c => {
  const [k,v] = c.trim().split('=');
  if(k === 'ct0') window.__ct0 = v;
});
window.__ct0.length  // 길이만 반환 (전체 문자열은 BLOCKED)
```

## 페이지네이션

- 40개씩 요청, cursor로 다음 페이지
- **1초 간격** (rate limit 방지)
- **18페이지를 1배치로** (500+ 트윗)
- `promotedMetadata` 있는 항목은 자동 스킵 (광고)

## javascript_tool 핵심 패턴

```javascript
// ❌ async 함수 직접 반환 = undefined
(async () => { ... })()

// ✅ window 전역변수에 저장 후 별도 호출로 읽기
window.__pg = { tweets: [], seen: new Set(), cursor: null, done: false, page: 0 };

// ✅ 결과는 반드시 JSON.stringify()로 반환 (raw string은 차단됨)
JSON.stringify({ stats: window.__aiStats, kwTop: window.__kwTop })
```

## 트윗 추출 경로

- 텍스트: `tw.note_tweet.note_tweet_results.result.text` || `tw.legacy.full_text`
- 이름: `tw.core.user_results.result.legacy.name`
- 핸들: `tw.core.user_results.result.legacy.screen_name`
- 좋아요: `tw.legacy.favorite_count`
- RT: `tw.legacy.retweet_count`
- 댓글: `tw.legacy.reply_count`
- 조회: `tw.views.count` (parseInt)
- 미디어: `tw.legacy.extended_entities.media[].media_url_https`
- URL: `https://x.com/${handle}/status/${tw.legacy.id_str}`

## 필터링 패턴

### 제외 패턴 (비-AI/테크 트윗)
```javascript
const exclude = /(K-?pop|아이돌|컴백|앨범|드라마|예능|웹툰|만화|야구|축구|농구|배구|올림픽|선거|대통령|국회|정당|탄핵|치킨|피자|배달|쿠폰|경품|화장품|뷰티|패션|다이어트|헬스장)/i;
```

### 포함 패턴 (AI 신호 키워드)
```javascript
const include = /(AI|GPT|LLM|Claude|Anthropic|OpenAI|Gemini|Google|DeepMind|Meta|agent|MCP|model|coding|code|developer|dev|API|SDK|GPU|NVIDIA|AMD|Intel|prompt|Cursor|Copilot|GitHub|Cowork|Codex|Supabase|React|Vercel|Next\.js|deploy|frontend|backend|browser.use|token|context|benchmark|chip|semiconductor|TSMC|compute|cloud|AWS|GCP|Azure|CLI|terminal|IDE|Figma|Docker|Kubernetes|startup|funding|YC|open.source|OSS|ML|NLP|transformer|neural|inference|training|finetun|RAG|embedding|vector|multimodal|vision|robotics|autonomous|agentic|workflow|automat|pipeline|Rust|Python|TypeScript|JavaScript|programming|software|engineer|tech|SaaS|infra|database|serverless|Cloudflare|Deno|Bun|Vite|npm|crypto|blockchain|Gemma|Llama|Mistral|Qwen|DeepSeek|Grok|xAI|Perplexity|Midjourney|Hugging.Face|LangChain|CrewAI|Devin|Replit|Windsurf|Bolt|Lovable|Trae)/i;
```

### 피드 종류별 전략
- 팔로잉 피드 (AI 계정 위주): EXCLUDE만 적용
- 추천 피드 (노이즈 다수): EXCLUDE + INCLUDE 양방향 필터
- 자동 판단: 필터 후 AI 비율 50% 미만 → 추천 피드로 간주

## 14개 토픽 클러스터 정의

```javascript
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
```

## Engagement 계산
```
engagement = likes + rt * 2 + comments * 1.5
```

## 토픽 데이터 전달 (브라우저 → Claude)

토픽 클러스터링 완료 후, `window.__getTopicChunk(start, end)`로 전달:
- 1회: `(0, 4)` — 상위 4개 토픽
- 2회: `(4, 8)` — 다음 4개 토픽
- 3회(선택): `(8, 12)` — 나머지
- BLOCKED 시: 범위를 2개로 축소

총 API 호출: 수집 확인 2회 + 분석 1회 + 토픽 전달 2~3회 = 5~6회

## 수집 실패 처리

- Chrome MCP 미연결 → [수집 실패] 표시, 다른 Part 계속 진행
- X 로그인 안 됨 → [수집 실패]
- queryId 변경 → GitHub에서 최신 queryId 검색 후 재시도
- Rate limit → 배치 간격 늘리기 (1초 → 2초)
