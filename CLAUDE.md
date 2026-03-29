# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

AI/개발 트렌드 브리핑 스킬 테스트 및 운영 폴더. 6개 소스에서 데이터를 수집하여 일일 트렌드 브리핑 마크다운을 생성한다.

## 폴더 구조

```
trend-briefing-test/
├── skill/                          # 스킬 정의 (다른 곳에 복사하여 사용 가능)
│   ├── SKILL.md                    # daily-trend-briefing 6-in-1 스킬 (메인)
│   ├── tweet-trend-analyzer-SKILL.md  # 트위터 단독 분석 스킬 (참고용)
│   ├── evals/                      # 스킬 평가 데이터
│   └── references/                 # 트위터 GraphQL 설정 등 참조 문서
├── autoresearch/                   # 필터 최적화 autoresearch 구조
│   ├── eval/                       # Frozen Metric (benchmark.py, test_tweets.json)
│   ├── target/                     # 최적화 대상 (filter_config.json)
│   └── outer/                      # 전략 (program.md)
├── trending-YYYY-MM-DD/            # 일별 수집 결과 (6개 파트)
│   ├── part1-github.md
│   ├── part2-producthunt.md
│   ├── part3-twitter.md
│   ├── part4-reddit.md
│   ├── part5-hackernews.md
│   └── part6-polymarket.md
└── trending-YYYY-MM-DD.md          # 종합 합본 (6소스 교차 분석)
```

## 스킬 설치 방법

이 폴더의 스킬을 다른 환경에서 사용하려면:

```bash
# daily-trend-briefing 스킬 설치
cp -r skill/ ~/.claude/skills/daily-trend-briefing/

# tweet-trend-analyzer 스킬 설치 (선택)
mkdir -p ~/.claude/skills/tweet-trend-analyzer/
cp skill/tweet-trend-analyzer-SKILL.md ~/.claude/skills/tweet-trend-analyzer/SKILL.md
```

## 필수 도구

```bash
# dev-browser (X, Reddit, HN, Polymarket DOM 수집)
npm install -g dev-browser
dev-browser install

# Chrome 디버그 프로필 (최초 1회)
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
# → X 수동 로그인 + Reddit 캡차 통과
```

## 6개 소스와 수집 방법

| Part | 소스 | 수집 방법 | 차단 여부 |
|:----:|------|----------|:---------:|
| 1 | GitHub TrendShift | WebFetch | 없음 |
| 2 | Product Hunt | WebFetch / Chrome MCP | 없음 |
| 3 | X(트위터) | dev-browser DOM 스크롤 (`--connect`) | 로그인 필요 |
| 4 | Reddit | dev-browser DOM (`--connect`) | 캡차 1회 |
| 5 | Hacker News | dev-browser DOM | 없음 |
| 6 | Polymarket | dev-browser DOM | 없음 |

## 수집 실행

```bash
# Chrome 디버그 프로필로 실행 (Part 3~6 공유)
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"

# dev-browser 연결
dev-browser --connect http://localhost:9222

# 스킬 실행 (Claude Code에서)
# "트렌드 브리핑 해줘" 또는 /daily-trend-briefing
```

## 출력 스타일

내러티브 스타일 (AI_trend_summary 참고):
- 토픽별 이야기체 도입부 + engagement 수치 + 원문 링크 [🔗](URL)
- 시사점 + 해시태그 `#키워드`
- 감정/온도 분석 (🔴과열 🟢성장 🟡주의 🔵전환)
- 바이브 코딩 시사점 (사용자 맞춤 액션)

## 필터 최적화

`autoresearch/` 폴더에 autoresearch 40회 실험 결과가 있다:
- 베이스라인 0.9304 → 최종 0.9370 (+0.71%)
- noise_ratio 15.3% → 7.4% (절반 감소)
- 최적화된 필터: `autoresearch/target/filter_config.json`
