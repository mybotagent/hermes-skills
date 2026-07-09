# 논문 코드 구현 검증 가이드

> **발생 계기**: TradingAgents(2412.20138) 논문 분석 중, 논문 본문에는 LangGraph 언급이 없었으나 실제 GitHub 코드에는 `langgraph>=0.4.8` 의존성이 명시되어 있었음.

## 교훈

학술 논문은 **방법론(methodology)**과 **아이디어**만 설명하고,  
구현 디테일(프레임워크, 라이브러리, 구체적 코드 구조)은 GitHub에 담는 것이 일반적인 관행.

## 검증 절차

1. 논문 본문에서 프레임워크/라이브러리명 검색
2. GitHub 레포의 `pyproject.toml` / `requirements.txt` / `go.mod` 확인
3. 실제 코드 구조 확인 (`graph/`, `agents/`, `dataflows/` 등 디렉토리명)
4. 논문의 아키텍처 다이어그램과 코드 구조 매핑 확인

## 적용 사례: TradingAgents

| 확인 항목 | 논문 본문 | GitHub 코드 |
|:---------|:---------|:-----------|
| LangGraph | 언급 없음 | `langgraph>=0.4.8` ✅ |
| ReAct | 언급 있음 | ReAct 프롬프팅 패턴 사용 |
| GPT-4o/o1 | 언급 있음 | LangChain ChatModel 래퍼 |
| Agent 구조 | 7개 역할 설명 | `agents/` 디렉토리에 각각 파일 |

## 주의

- 논문이 특정 프레임워크를 **언급하지 않는다고** 사용하지 않는 것은 아님
- "llm.call()" 같은 메서드는 특정 프레임워크가 아닌 일반적인 API 호출 패턴
- **의심되면 GitHub 코드를 직접 확인**할 것 (pyproject.toml이 가장 정확)
