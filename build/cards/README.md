# 개념 암기 카드 원본

`data/memo-cards.json` 의 원본입니다. 과목별로 나눠 두었습니다.

| 파일 | 과목 | 카드 |
|---|---|---|
| `card1.json` | 1과목 | 13 |
| `card2.json` | 2과목 | 9 |
| `card3.json` | 3과목 | 12 |

## 어떤 개념을 카드로 만들었나

"많이 나온 개념"이 아니라 **"오답 선택지로 많이 쓰인 개념"** 을 골랐습니다.
720문항의 오답 선택지 `refs` 를 집계하면 실제로 헷갈리는 지점이 드러납니다.

```bash
# 헷갈림 유발 개념 순위 뽑기
python - <<'PY'
import json, collections
idx = json.load(open('data/index.json'))
sec = {s['no']: s for s in json.load(open('data/summary.json'))}
Q = [q for e in idx['exams']
       for q in json.load(open('data/exam-%s.json' % e['id']))['questions']]
mis = collections.Counter()
for q in Q:
    for i, o in enumerate(q['options']):
        if i + 1 != q['answer']:
            for r in (o.get('refs') or [])[:2]:
                mis[r] += 1
for r, n in mis.most_common(30):
    if r in sec:
        print(n, sec[r]['title'])
PY
```

## 스키마

```json
{ "id":"C01", "secs":[7,6], "title":"프로세스 상태 전이",
  "key":"한 줄 핵심 (HTML 태그 허용)",
  "visuals":[ … ],
  "compare":[{"a":"준비","b":"대기","d":"차이 설명"}],
  "mnemonic":"암기법" }
```

`secs` 는 이 카드가 덮는 핵심요약 항목 번호입니다. 앱이 이 번호로
사용자의 취약 개념(`S.weak`)과 카드를 이어 붙이므로, **한 항목을 두 카드가
중복해서 다루면 빌드가 실패**합니다. 과목·단원은 첫 `sec` 에서 자동으로 채워집니다.

### 시각 자료 type

| type | 필드 |
|---|---|
| `table` | `label?`, `head[]`, `rows[][]` |
| `calc` | `label?`, `head[]`, `rows[][]`, `foot?` |
| `scale` | `label`, `lo`, `hi`, `items[{t,d}]` — 왼쪽이 약함 |
| `layers` | `label`, `items[{n,t,d}]` — 위에서 아래로 쌓임 |
| `steps` | `label`, `items[{t,d}]` — 화살표로 이어짐 |
| `code` | `label?`, `lang`, `code`, `out?` |
| `tree` | `label`, `nodes[{id,l,x,y}]`, `edges[[a,b]]` — x·y 는 0~100 비율 |
| `note` | `t` — 함정 경고 (노란 박스) |

`key`, `rows`, `d`, `t` 값에는 `<b>` 같은 간단한 HTML 태그를 쓸 수 있습니다.
이 파일은 저장소가 직접 관리하는 1차 데이터라 그대로 렌더링합니다.

## 빌드

```bash
python build/cards/build_cards.py
```

검증 항목: id 중복, `key` 유무, 시각 자료 유무, 모르는 `type`,
`table` 의 rows 누락, `tree` 간선이 없는 노드를 가리키는지,
`sec` 가 실제 요약 항목인지, **한 `sec` 를 두 카드가 중복해서 다루는지**.
