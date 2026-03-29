# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

6개 소스(GitHub TrendShift, Product Hunt, X, Reddit, Hacker News, Polymarket)에서 AI/개발 트렌드를 병렬 수집하여 일일 브리핑 마크다운을 생성하는 Claude Code 스킬.

## 폴더 구조

```
├── skill/                           # 스킬 정의
│   ├── SKILL.md                     # daily-trend-briefing 메인 스킬
│   ├── evals/                       # 스킬 평가 데이터
│   └── references/                  # 트위터 GraphQL 설정 등 참조 문서
```

수집 결과는 프로젝트 루트에 `trending-YYYY-MM-DD/` (파트별) + `trending-YYYY-MM-DD.md` (합본)으로 생성된다. `.gitignore`로 추적하지 않음.

## 스킬 설치

```bash
# daily-trend-briefing 스킬 설치
cp -r skill/ ~/.claude/skills/daily-trend-briefing/
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

## 실행

```bash
# 1. Chrome 디버그 프로필로 실행
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"

# 2. Claude Code에서 실행
# "트렌드 브리핑 해줘" 또는 /daily-trend-briefing
```
