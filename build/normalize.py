#!/usr/bin/env python3
"""build/raw/*.json 의 표기를 키보드로 입력 가능한 문자로 통일한다.

- 보기 기호 ㉠㉡㉢… → ㄱㄴㄷ… (한글 자모는 키보드로 바로 쳐진다)
- 동그라미 알파벳 ⓐⓑⓒ → a b c
- 보기 라벨 형식을 'ㄱ. ' 로 통일
- 순서 나열 정답 구분자를 쉼표로 통일
- 괄호 번호 ①②③ 은 '몇 번째 칸' 표시라 정답 표시에는 남기고, 채점은 번호 없이도 통과시킨다
"""
import json, glob, os, re, sys

RAW = sys.argv[1] if len(sys.argv) > 1 else 'build/raw'

SYM = dict(zip('㉠㉡㉢㉣㉤㉥㉦㉧', 'ㄱㄴㄷㄹㅁㅂㅅㅇ'))
SYM.update(dict(zip('ⓐⓑⓒⓓⓔ', 'abcde')))

# 정답 표기를 직접 다시 쓰는 문항 (기호 치환만으로는 정리되지 않는 것들)
OVERRIDE = {
    # 순서 나열 — 구분자를 쉼표로 통일
    '22-1-01': dict(a='ㄴ, ㄷ, ㄱ, ㄹ, ㅁ', alt=['ㄴㄷㄱㄹㅁ', 'ㄴ -> ㄷ -> ㄱ -> ㄹ -> ㅁ']),
    '24-1-02': dict(a='ㄷ, ㄴ, ㄹ, ㅁ, ㄱ', alt=['ㄷㄴㄹㅁㄱ', 'ㄷ -> ㄴ -> ㄹ -> ㅁ -> ㄱ']),
    '23-3-08': dict(a='ㄹ, ㄱ, ㄴ, ㄷ', alt=['ㄹㄱㄴㄷ']),
    '25-3-12': dict(a='ㄹ, ㄱ, ㄴ, ㄷ', alt=['ㄹㄱㄴㄷ']),
    '23-2-07': dict(a='단위 테스트, 통합 테스트, 시스템 테스트, 인수 테스트',
                    alt=['ㄹ, ㄷ, ㄱ, ㄴ', '단위, 통합, 시스템, 인수']),
    '23-1-18': dict(a='1234526', alt=['1 2 3 4 5 2 6']),
    # 연결·분류형 — 기호만 적어도 통과하도록 alt 보강
    '22-2-05': dict(a='① c  ② d  ③ b  ④ a', alt=['c, d, b, a', 'a-4, b-3, c-1, d-2']),
    '23-2-13': dict(a='① 블랙박스 : ㄴ, ㄹ   ② 화이트박스 : ㄱ, ㄷ', alt=['ㄴ, ㄹ, ㄱ, ㄷ']),
    '24-2-12': dict(a='① 블랙박스 : ㄴ, ㅁ, ㅂ   ② 화이트박스 : ㄱ, ㄷ, ㄹ', alt=['ㄴ, ㅁ, ㅂ, ㄱ, ㄷ, ㄹ']),
    '25-3-09': dict(a='ㄱ-2, ㄴ-1, ㄷ-4, ㄹ-3', alt=['2, 1, 4, 3']),
    '23-3-16': dict(a='ㄱ. 동치 분할, ㄴ. 경계값 분석', alt=['ㄱ, ㄴ', '동치 분할, 경계값 분석']),
    '25-3-10': dict(a='ㄱ. 동치 분할, ㄴ. 경계값 커버리지', alt=['ㄱ, ㄴ', '동치 분할, 경계값 커버리지']),
    '23-1-14': dict(a='ㄴ, ㄷ, ㄹ, ㅁ', alt=['순서 제어, 흐름 제어, 오류 처리, 동기화']),
    '23-2-11': dict(a='ㄴ, ㄷ, ㄹ', alt=[]),
    '25-1-05': dict(a='ㄱ, ㄴ', alt=[]),
    '24-1-09': dict(a='ㄴ, ㄷ, ㄹ', alt=[]),
    '25-2-01': dict(a='ㄱ, ㄴ, ㄷ, ㅁ', alt=[]),
    '25-2-17': dict(a='ㄱ', alt=['튜플은 중복되지 않는다']),
}

def sub(s):
    if not isinstance(s, str):
        return s
    return ''.join(SYM.get(ch, ch) for ch in s)

def label(c):
    """보기 라벨을 'ㄱ. 내용' 형태로 통일"""
    c = sub(c)
    m = re.match(r'^\s*([ㄱ-ㅎ])\s*[.)]?\s+(.*)$', c, re.S)
    return '%s. %s' % (m.group(1), m.group(2)) if m else c

changed = 0
for path in sorted(glob.glob(os.path.join(RAW, '*.json'))):
    d = json.load(open(path, encoding='utf-8'))
    for q in d['questions']:
        qid = '%s-%02d' % (d['exam'], q['no'])
        before = json.dumps(q, ensure_ascii=False)
        for k in ('q', 'a', 'why', 'unit'):
            if k in q:
                q[k] = sub(q[k])
        if q.get('choices'):
            q['choices'] = [label(c) for c in q['choices']]
        if q.get('alt'):
            q['alt'] = [sub(x) for x in q['alt']]
        ov = OVERRIDE.get(qid)
        if ov:
            q['a'] = ov['a']
            merged = list(dict.fromkeys([x for x in (q.get('alt') or []) + ov['alt'] if x]))
            q['alt'] = [x for x in merged if x != q['a']]
        if json.dumps(q, ensure_ascii=False) != before:
            changed += 1
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('수정된 문항', changed)
