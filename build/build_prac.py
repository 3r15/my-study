#!/usr/bin/env python3
"""raw/<회차>.json → data/prac-exam.json + data/prac-index.json

기사퍼스트 가답안 게시글(12회차)에서 판독한 정보처리산업기사 실기 기출을
학습 사이트가 쓰는 형태로 합친다. prac-note.json 의 qids 도 여기서 검증한다.
"""
import json, glob, os, collections, sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'data'

ORDER = ['22-1','22-2','22-3','23-1','23-2','23-3','24-1','24-2','24-3','25-1','25-2','25-3']
TYPE_LABEL = {'code':'코드 출력','sql':'SQL 작성','short':'단답형','fill':'괄호 채우기','order':'순서 나열'}

exams, questions = [], []
for eid in ORDER:
    d = json.load(open(os.path.join(SRC, eid + '.json'), encoding='utf-8'))
    for q in d['questions']:
        q['id'] = '%s-%02d' % (eid, q['no'])
        q['exam'] = eid
        q.setdefault('lang', None)
        q.setdefault('code', None)
        q.setdefault('choices', None)
        q.setdefault('alt', [])
        q.setdefault('partial', False)
        questions.append(q)
    exams.append({'id': eid, 'title': d['title'], 'date': d['date'],
                  'pass': d['pass'], 'n': len(d['questions']),
                  'note': d.get('note', '')})

def rank(counter):
    return [{'k': k, 'n': n} for k, n in counter.most_common()]

types = collections.Counter(q['type'] for q in questions)
langs = collections.Counter(q['lang'] for q in questions if q['lang'])
tags  = collections.Counter(t for q in questions for t in q.get('tags', []))

index = {
    'n': len(questions),
    'nPartial': sum(1 for q in questions if q['partial']),
    'src': '기사퍼스트 실기 가답안 복원 (2022년 1회 ~ 2025년 3회)',
    'exams': exams,
    'types': [{'k': k, 'label': TYPE_LABEL[k], 'n': n} for k, n in types.most_common()],
    'langs': rank(langs),
    'tags': rank(tags),
}

os.makedirs(OUT, exist_ok=True)
w = lambda name, obj: open(os.path.join(OUT, name), 'w', encoding='utf-8').write(
        json.dumps(obj, ensure_ascii=False, separators=(',', ':')))

w('prac-exam.json', {'exams': exams, 'questions': questions})
w('prac-index.json', index)

# 학습노트가 가리키는 기출 id 가 실제로 있는지 확인
ids = {q['id'] for q in questions}
notep = os.path.join(OUT, 'prac-note.json')
if os.path.exists(notep):
    notes = json.load(open(notep, encoding='utf-8'))
    bad = [(n['id'], i) for n in notes for i in n.get('qids', []) if i not in ids]
    print('학습노트 %d개, 끊어진 기출 링크 %d개%s' % (len(notes), len(bad), bad[:5] if bad else ''))

print('회차 %d · 문항 %d (복원 미완 %d)' % (len(exams), len(questions), index['nPartial']))
print('유형', dict(types), '/ 언어', dict(langs))
