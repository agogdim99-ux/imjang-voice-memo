# 항목 추출 정확도

정답표: `data/ground_truth.json` (매물 5건 × 15항목 = 75칸). 녹음에 없는 항목은 '확인 필요'로 비워야 정답.

| 결과 파일 | 추출 | 받아쓰기 입력 | 정확도 | 누락 표시(확인 필요) 정확도 | 1건 평균 처리 시간 |
|---|---|---|---|---|---|
| extracted_qwen_scripts.json | Qwen/Qwen2.5-7B-Instruct (오픈소스 LLM) | `data/scripts.json` | **73/75 (97%)** | 17/17 | 19.5초 |
| extracted_qwen_small_noisy_noprompt.json | Qwen/Qwen2.5-7B-Instruct (오픈소스 LLM) | `data/transcripts/small_noisy_noprompt.json` | **65/75 (87%)** | 17/17 | 21.7초 |
| extracted_qwen_turbo_noisy_prompt.json | Qwen/Qwen2.5-7B-Instruct (오픈소스 LLM) | `data/transcripts/turbo_noisy_prompt.json` | **69/75 (92%)** | 17/17 | 20.8초 |
| extracted_rules_scripts.json | 규칙 기반 | `data/scripts.json` | **75/75 (100%)** | 17/17 | 0.0초 |
| extracted_rules_small_clean_noprompt.json | 규칙 기반 | `data/transcripts/small_clean_noprompt.json` | **65/75 (87%)** | 17/17 | 3.2초 |
| extracted_rules_small_clean_prompt.json | 규칙 기반 | `data/transcripts/small_clean_prompt.json` | **70/75 (93%)** | 17/17 | 2.8초 |
| extracted_rules_small_noisy_noprompt.json | 규칙 기반 | `data/transcripts/small_noisy_noprompt.json` | **64/75 (85%)** | 17/17 | 2.8초 |
| extracted_rules_small_noisy_prompt.json | 규칙 기반 | `data/transcripts/small_noisy_prompt.json` | **68/75 (91%)** | 17/17 | 2.7초 |
| extracted_rules_turbo_clean_noprompt.json | 규칙 기반 | `data/transcripts/turbo_clean_noprompt.json` | **70/75 (93%)** | 17/17 | 1.8초 |
| extracted_rules_turbo_clean_prompt.json | 규칙 기반 | `data/transcripts/turbo_clean_prompt.json` | **74/75 (99%)** | 17/17 | 1.6초 |
| extracted_rules_turbo_noisy_noprompt.json | 규칙 기반 | `data/transcripts/turbo_noisy_noprompt.json` | **69/75 (92%)** | 17/17 | 2.0초 |
| extracted_rules_turbo_noisy_prompt.json | 규칙 기반 | `data/transcripts/turbo_noisy_prompt.json` | **74/75 (99%)** | 17/17 | 1.7초 |

## 틀린 칸 — extracted_qwen_scripts.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s3 | 관리비 | 7 | 70.0 |
| s5 | 동 | 정자동 | None |

## 틀린 칸 — extracted_qwen_small_noisy_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 동 | 당산동 | 방산동 |
| s1 | 융자 유무 | False | None |
| s2 | 동 | 부평동 | None |
| s3 | 매매가 | 28000 | None |
| s3 | 관리비 | 7 | 70000.0 |
| s3 | 역 도보(분) | 5 | None |
| s4 | 전세가 | 40000 | None |
| s4 | 평형 | 27 | 127.0 |
| s5 | 시·군·구 | ['성남', '분당'] | 분당구 |
| s5 | 융자 유무 | True | None |

## 틀린 칸 — extracted_qwen_turbo_noisy_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s2 | 동 | 부평동 | None |
| s3 | 관리비 | 7 | 8.0 |
| s4 | 동 | 송도동 | None |
| s4 | 전세가 | 40000 | None |
| s4 | 평형 | 27 | 21.9 |
| s5 | 동 | 정자동 | None |

## 틀린 칸 — extracted_rules_scripts.json

없음

## 틀린 칸 — extracted_rules_small_clean_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 매매가 | 72000 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 초품아 | True | None |
| s1 | 융자 유무 | False | None |
| s3 | 매매가 | 28000 | None |
| s4 | 평형 | 27 | None |
| s5 | 매매가 | 99000 | None |
| s5 | 연식 | 1995 | None |
| s5 | 융자 유무 | True | None |

## 틀린 칸 — extracted_rules_small_clean_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 평형 | 24 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s4 | 평형 | 27 | None |
| s5 | 연식 | 1995 | None |

## 틀린 칸 — extracted_rules_small_noisy_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 동 | 당산동 | 방산동 |
| s1 | 매매가 | 72000 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 초품아 | True | None |
| s1 | 융자 유무 | False | True |
| s3 | 매매가 | 28000 | None |
| s4 | 평형 | 27 | None |
| s5 | 매매가 | 99000 | None |
| s5 | 연식 | 1995 | None |
| s5 | 융자 유무 | True | None |

## 틀린 칸 — extracted_rules_small_noisy_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 동 | 당산동 | 방산동 |
| s1 | 평형 | 24 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 융자 유무 | False | True |
| s4 | 평형 | 27 | None |
| s5 | 연식 | 1995 | None |

## 틀린 칸 — extracted_rules_turbo_clean_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 주차(1대 기준) | 1대 이상 | None |
| s1 | 초품아 | True | None |
| s2 | 주차(1대 기준) | 1대 이상 | None |
| s3 | 주차(1대 기준) | 1대 미만 | None |
| s4 | 평형 | 27 | None |

## 틀린 칸 — extracted_rules_turbo_clean_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s4 | 평형 | 27 | None |

## 틀린 칸 — extracted_rules_turbo_noisy_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 주차(1대 기준) | 1대 이상 | None |
| s1 | 초품아 | True | None |
| s2 | 주차(1대 기준) | 1대 이상 | None |
| s3 | 주차(1대 기준) | 1대 미만 | None |
| s4 | 평형 | 27 | None |
| s5 | 엘리베이터 | True | None |

## 틀린 칸 — extracted_rules_turbo_noisy_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s4 | 평형 | 27 | None |