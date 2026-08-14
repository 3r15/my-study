# 빌드 스크립트

PDF → JSON 변환 파이프라인. 문제은행을 다시 만들거나 회차를 추가할 때 씁니다.

- `parse_exam.py` · `parse_summary.py` · `build_data.py` — **필기** (기출 PDF + 핵심요약집 PDF)
- `build_prac.py` · `normalize.py` + `raw/` — **실기** (기사퍼스트 가답안 게시글에서 판독한 회차별 원본)

## 필요 패키지
```bash
pip install pdfplumber --break-system-packages
```

## 실행 순서
```bash
python parse_exam.py      # 기출 PDF → out/YYYY-N.json  (+ out/img/ 크롭 이미지)
python parse_summary.py   # 핵심요약집 PDF → out/summary.json
python build_data.py      # 위 결과 → site/data/*.json + site/img/  (태깅·용어사전 포함)
```

각 스크립트 상단의 경로 상수를 실제 PDF 위치로 맞춰 주세요.

## 회차 추가하기
`parse_exam.py` 맨 아래 파일 필터를 고칩니다.
```python
files = [f for f in files if re.search(r'(2022|2023|2024|2025)년', os.path.basename(f))]
```
2005~2021년 구 체계는 5과목 100문항이라 `SUBJ_CANON`(과목명)과 `UNITS`(단원 범위, `build_data.py`)도 함께 손봐야 합니다.

## 파서가 하는 일
- **2단 조판 분리** — 페이지를 x=297 기준으로 좌/우 컬럼으로 나눠 읽기 순서 복원
- **영역 인식** — 선분/사각형에서 닫힌 박스를 찾아 표(다중 셀) / 보기 박스 / 코드 블록으로 분류
- **그림 크롭** — 텍스트 사이 28pt 이상 빈 공간에 도형·이미지가 있으면 해당 영역만 PNG로 잘라냄 (워터마크 제외)
- **선택지가 그림인 문항** — 선택지 영역을 통째로 크롭
- **문항 분할** — 번호가 `expect`와 정확히 일치할 때만 새 문항으로 인정 (박스 안 숫자에 속지 않음)
- **정답 파싱** — 마지막 "정답" 페이지에서 `1.② 2.④ …` 추출

검증: 12회차 × 60문항 = 720, 정답 720/720, 보기 4개 미달 0건.

---

## 실기 데이터 (`build_prac.py`)

```bash
python build_prac.py ../data      # build/raw/*.json → data/prac-exam.json + prac-index.json
```

`raw/<회차>.json` 12개가 원본입니다. 각 파일은 한 회차(20문항)를 담습니다.

```json
{ "exam":"22-1", "title":"2022년 1회", "date":"2022-05-07", "pass":"합격률 44%",
  "note":"(회차 전체에 붙는 안내. 예: 복원되지 않은 번호 범위)",
  "questions":[ { "no":1, "type":"order", "tags":[…], "unit":"…",
                  "q":"…", "code":"…", "choices":[…],
                  "a":"정답", "alt":[…], "why":"해설", "partial":false } ] }
```

`id`(`22-1-06` 형식)와 `exam`은 빌드 때 자동으로 붙으므로 원본에 적지 않습니다.
스크립트는 `data/prac-note.json`의 `qids`가 실제 문항을 가리키는지도 함께 검사해,
학습노트에서 끊어진 링크가 생기지 않게 합니다.

### 원본 판독에 대해

가답안 게시글 PDF는 **문제 지문과 정답이 벡터 도형으로 렌더링**되어 있어
`pdfplumber`/`pypdfium2`의 텍스트 추출로는 상당 부분이 빠집니다
(특히 붉은 글씨의 정답은 12개 파일 중 3개에서만 추출됨).
그래서 페이지를 이미지로 렌더링해 직접 판독한 결과가 `raw/`입니다.

```python
import pypdfium2 as pdfium
d = pdfium.PdfDocument(path)
d[i].render(scale=2.4).to_pil().save(...)   # 본문 영역만 크롭해서 확인
```

원 게시글에 지문이 실리지 않고 가답안만 있는 문항은 `"partial": true`로 표시했고,
앱에서 "복원 미완 — 참고용"으로 안내하며 랜덤·안 푼 문제 출제에서 제외합니다.

### 표기 통일 (`normalize.py`)

가답안 원문에는 `㉠` `ⓐ` `→` 처럼 키보드로 바로 칠 수 없는 기호가 섞여 있습니다.
답을 직접 타이핑하는 실기 특성상 그대로 두면 정답을 입력할 방법이 없어, 한 번 정리했습니다.

```bash
python normalize.py raw     # raw/*.json 을 제자리에서 수정
python build_prac.py ../data
```

- `㉠㉡㉢…` → `ㄱㄴㄷ…` (한글 자모는 키보드로 쳐집니다), `ⓐⓑⓒ` → `a b c`
- 보기 라벨을 `ㄱ. 내용` 형태로 통일
- 순서 나열 정답의 구분자를 쉼표로 통일
- 칸 번호 `①②③`은 '몇 번째 칸'을 가리키므로 정답 표시에는 남기고, 채점에서만 무시

이미 적용된 상태이므로 회차를 새로 추가할 때만 다시 실행하면 됩니다.
`OVERRIDE` 표에 문항 id를 넣으면 기계적 치환 대신 정답 문자열을 직접 지정할 수 있습니다.
