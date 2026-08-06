# -*- coding: utf-8 -*-
import pdfplumber, re, json, os, sys, glob, hashlib

MID = 297.0
CIRC = "①②③④"
CIRC_RE = re.compile(r'[①②③④]')
QNUM_RE = re.compile(r'^(\d{1,3})\s*[.．]?\s*(.*)$')
SUBJ_RE = re.compile(r'^제\s*([1-5])\s*과목\s*[:：]?\s*(.*)$')

SUBJ_CANON = {1: "정보시스템 기반 기술", 2: "프로그래밍 언어 활용", 3: "데이터베이스 활용"}
def norm_subject(n, raw):
    n = int(n)
    return f"제{n}과목 {SUBJ_CANON.get(n, raw.strip())}"


def col_of(x0, x1):
    return 0 if (x0+x1)/2 < MID else 1

def build_lines(pg):
    words = pg.extract_words(use_text_flow=False, keep_blank_chars=False, extra_attrs=['size'])
    cols = {0: [], 1: []}
    for w in words:
        cols[col_of(w['x0'], w['x1'])].append(w)
    out = []
    for c in (0, 1):
        ws = sorted(cols[c], key=lambda w: (w['top'], w['x0']))
        lines, cur, curtop = [], [], None
        for w in ws:
            if curtop is None or abs(w['top'] - curtop) <= 3.5:
                cur.append(w)
                if curtop is None: curtop = w['top']
            else:
                lines.append(cur); cur = [w]; curtop = w['top']
        if cur: lines.append(cur)
        for ln in lines:
            ln.sort(key=lambda w: w['x0'])
            txt, prev = '', None
            for w in ln:
                if prev is not None and w['x0'] - prev > 1.2: txt += ' '
                txt += w['text']; prev = w['x1']
            out.append(dict(kind='text', col=c, top=min(w['top'] for w in ln),
                            bottom=max(w['bottom'] for w in ln),
                            x0=min(w['x0'] for w in ln), x1=max(w['x1'] for w in ln),
                            size=round(sum(w['size'] for w in ln)/len(ln), 1),
                            text=re.sub(r'\s+', ' ', txt).strip()))
    return out

def rect_regions(pg):
    """closed rectangles from line segments + stroked rects -> (x0,top,x1,bottom, ncells_h)"""
    segs_h, segs_v = [], []
    for l in pg.lines + [dict(x0=r['x0'], x1=r['x1'], top=r['top'], bottom=r['bottom']) for r in pg.rects if r.get('stroke')]:
        if abs(l['bottom'] - l['top']) < 1.5 and l['x1'] - l['x0'] > 20:
            segs_h.append((l['x0'], l['x1'], (l['top']+l['bottom'])/2))
        elif abs(l['x1'] - l['x0']) < 1.5 and l['bottom'] - l['top'] > 6:
            segs_v.append(((l['x0']+l['x1'])/2, l['top'], l['bottom']))
    for r in pg.rects:
        if r.get('stroke') and r['x1']-r['x0'] > 20 and r['bottom']-r['top'] > 6:
            segs_h.append((r['x0'], r['x1'], r['top'])); segs_h.append((r['x0'], r['x1'], r['bottom']))
            segs_v.append((r['x0'], r['top'], r['bottom'])); segs_v.append((r['x1'], r['top'], r['bottom']))
    regs = []
    seen = set()
    for vx, vt, vb in segs_v:
        for vx2, vt2, vb2 in segs_v:
            if vx2 - vx < 25: continue
            if abs(vt2-vt) > 4 or abs(vb2-vb) > 4: continue
            top_ok = any(abs(hy-vt) <= 4 and hx0 <= vx+4 and hx1 >= vx2-4 for hx0,hx1,hy in segs_h)
            bot_ok = any(abs(hy-vb) <= 4 and hx0 <= vx+4 and hx1 >= vx2-4 for hx0,hx1,hy in segs_h)
            if top_ok and bot_ok:
                key = (round(vx), round(vt), round(vx2), round(vb))
                if key in seen: continue
                seen.add(key)
                inner = sorted({round(hy,1) for hx0,hx1,hy in segs_h
                                if vt+3 < hy < vb-3 and hx0 <= vx+4 and hx1 >= vx2-4})
                innerv = sorted({round(x,1) for x,t,b in segs_v if vx+3 < x < vx2-3 and t <= vt+4 and b >= vb-4})
                regs.append(dict(x0=vx, top=vt, x1=vx2, bottom=vb, rows=len(inner)+1, cols=len(innerv)+1))
    # drop nested duplicates (keep outermost)
    regs.sort(key=lambda r: (r['x1']-r['x0'])*(r['bottom']-r['top']), reverse=True)
    keep = []
    for r in regs:
        if any(k['x0']-2 <= r['x0'] and k['x1']+2 >= r['x1'] and k['top']-2 <= r['top'] and k['bottom']+2 >= r['bottom'] for k in keep):
            continue
        keep.append(r)
    return keep

def page_elements(pg, pageno, imgdir, imgprefix):
    lines = build_lines(pg)
    H = pg.height
    regs = [r for r in rect_regions(pg)
            if r['bottom'] - r['top'] > 8 and r['x1'] - r['x0'] > 25
            and r['top'] > 60 and r['bottom'] < H - 45
            and r['x1'] - r['x0'] < 275]           # inside one column only
    tbl_objs = pg.find_tables({"vertical_strategy":"lines","horizontal_strategy":"lines",
                               "intersection_tolerance":3,"snap_tolerance":3})
    tbl_map = {}
    for t in tbl_objs:
        tbl_map[(round(t.bbox[0]), round(t.bbox[1]))] = t

    els = []
    consumed = [False]*len(lines)
    for r in regs:
        c = col_of(r['x0'], r['x1'])
        for i, L in enumerate(lines):
            if L['col'] == c and r['top']-2 <= L['top'] and L['bottom'] <= r['bottom']+3 \
               and L['x0'] >= r['x0']-3 and L['x1'] <= r['x1']+3:
                consumed[i] = True
        inner = [L for i, L in enumerate(lines)
                 if L['col'] == c and r['top']-2 <= L['top'] and L['bottom'] <= r['bottom']+3
                 and L['x0'] >= r['x0']-3 and L['x1'] <= r['x1']+3]
        inner.sort(key=lambda L: L['top'])
        # vector graphics inside region?
        ncur = sum(1 for cu in pg.curves if r['x0'] <= cu['x0'] and cu['x1'] <= r['x1'] and r['top'] <= cu['top'] and cu['bottom'] <= r['bottom'])
        t = tbl_map.get((round(r['x0']), round(r['top'])))
        if t is None:
            for (kx, ky), tv in tbl_map.items():
                if abs(kx - r['x0']) <= 3 and abs(ky - r['top']) <= 3: t = tv; break
        if t is not None and r['rows'] >= 2 and r['cols'] >= 2:
            grid = [[(c2 or '').replace('\n', ' ').strip() for c2 in row] for row in t.extract()]
            els.append(dict(kind='table', col=c, top=r['top'], grid=grid))
        else:
            txt = [L['text'] for L in inner]
            el = dict(kind='box', col=c, top=r['top'], lines=txt,
                      xs=[round(L['x0']-r['x0'], 1) for L in inner])
            if ncur > 4 or (not txt and (r['bottom']-r['top']) > 20):
                el['kind'] = 'figure'
            els.append(el)
    # ---- whitespace gaps that hold non-text content (images / vector diagrams) -> figure crop
    for col in (0, 1):
        occ = []
        for i, L in enumerate(lines):
            if L['col'] == col and not consumed[i] and 58 < L['top'] and L['bottom'] < H - 42:
                occ.append((L['top'], L['bottom']))
        for r in regs:
            if col_of(r['x0'], r['x1']) == col:
                occ.append((r['top'], r['bottom']))
        for e in els:
            if e['col'] == col and e['kind'] in ('table', 'box', 'figure'):
                pass
        if not occ: continue
        occ.sort()
        merged = [list(occ[0])]
        for a, b in occ[1:]:
            if a <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        x0 = 40 if col == 0 else 300
        x1 = 296 if col == 0 else 558
        for k in range(len(merged) - 1):
            gtop, gbot = merged[k][1], merged[k+1][0]
            if not (28 < gbot - gtop < 360): continue
            objs = [o for o in list(pg.curves) + list(pg.lines) + list(pg.rects) + list(pg.images)
                    if gtop - 2 < (o['top'] + o['bottom']) / 2 < gbot + 2
                    and x0 - 4 < (o['x0'] + o['x1']) / 2 < x1 + 4
                    and (o['x1'] - o['x0']) < 280
                    and not (o['object_type'] == 'image' and (o['x1']-o['x0']) > 150
                             and abs((o['x1']-o['x0']) - (o['bottom']-o['top'])) < 25)]
            if not objs: continue
            ox0 = max(x0, min(o['x0'] for o in objs) - 5)
            ox1 = min(x1, max(o['x1'] for o in objs) + 5)
            if ox1 - ox0 < 25: continue
            name = f"{imgprefix}_p{pageno}_{int(gtop)}.png"
            try:
                pg.crop((ox0, gtop + 1, ox1, gbot - 1)).to_image(resolution=200).save(os.path.join(imgdir, name)) if imgdir else None
            except Exception:
                continue
            els.append(dict(kind='figure_img', col=col, top=gtop + 1, src=name,
                            w=round(ox1 - ox0, 1), h=round(gbot - gtop - 2, 1)))

    for i, L in enumerate(lines):
        if not consumed[i]:
            els.append(L)
    els.sort(key=lambda e: (e['col'], e['top']))
    return els

HDR_JUNK = re.compile(
    r'^(\s*-\s*\d*\s*-?\s*'
    r'|\d+회.*|기출문제.*정답.*|정보처리산업기사.*필기.*|저작권 안내|이 자료는.*|다른 매체에.*'
    r'|개인적인 용도.*|없습니다\.|상업적.*|\d{4}년.*|※.*|답란\(.*|제\s*[1-5]\s*과목.*|)$')

def parse(path):
    base = os.path.basename(path)
    m = re.search(r'(20\d\d|0[5-9])\s*년\s*(\d)\s*회', base)
    if m:
        y = m.group(1); y = ('20'+y) if len(y) == 2 else y
        year, sess = int(y), int(m.group(2))
    else:
        raise ValueError(base)
    eid = f"{year}-{sess}"
    els = []
    imgdir = "/tmp/w/out/img"
    os.makedirs(imgdir, exist_ok=True)
    pdf = pdfplumber.open(path)
    for i, pg in enumerate(pdf.pages):
        for e in page_elements(pg, i+1, imgdir, eid):
            e['page'] = i+1
            els.append(e)
    els.sort(key=lambda e: (e['page'], e['col'], e['top']))

    # ---- split off answer section
    ans_idx = None
    for i, e in enumerate(els):
        if e['kind'] == 'text' and re.fullmatch(r'정답(\s*및\s*해설)?', e['text']) and e.get('size', 0) >= 11:
            ans_idx = i; break
    body = els[:ans_idx] if ans_idx is not None else els
    tail = els[ans_idx:] if ans_idx is not None else []

    answers = {}
    for e in tail:
        if e['kind'] != 'text': continue
        for qn, ch in re.findall(r'(\d{1,2})\s*\.\s*([①②③④])', e['text']):
            answers[int(qn)] = CIRC.index(ch)+1

    # ---- segment questions
    qs = []
    cur = None
    subject = None
    expect = 1
    for e in body:
        if e['kind'] in ('table', 'box', 'figure'):
            probe = ' '.join(sum(e['grid'], []) if e['kind'] == 'table' else e.get('lines', []))
            sm2 = SUBJ_RE.match(probe.strip())
            if sm2:
                subject = norm_subject(sm2.group(1), sm2.group(2)); continue
        if e['kind'] == 'text':
            t = e['text']
            sm = SUBJ_RE.match(t)
            if sm and e.get('size',0) >= 9.5:
                subject = norm_subject(sm.group(1), sm.group(2)); continue
            if HDR_JUNK.fullmatch(t): continue
            qm = QNUM_RE.match(t)
            if qm and int(qm.group(1)) == expect and e['size'] >= 8.5:
                if cur: qs.append(cur)
                cur = dict(no=expect, subject=subject, stem=[], options=[], page=e['page'])
                expect += 1
                rest = qm.group(2).strip()
                if rest: cur['stem'].append(dict(type='text', text=rest))
                cur['_qx'] = e['x0']
                cur['_geo'] = [(e['page'], e['col'], e['top'], e.get('bottom', e['top']+10))]
                cur['_optgeo'] = None
                continue
        if cur is None: continue
        cur['_geo'].append((e['page'], e['col'], e['top'], e.get('bottom', e['top']+12)))
        if e['kind'] == 'text' and CIRC_RE.match(e['text']) and cur['_optgeo'] is None:
            cur['_optgeo'] = (e['page'], e['col'], e['top'])
        og = cur.get('_optgeo')
        if og and e['kind'] in ('table', 'box', 'figure', 'figure_img') \
           and e['page'] == og[0] and e['col'] == og[1] and e['top'] >= og[2] - 14:
            cur['_gfxopt'] = cur.get('_gfxopt', 0) + 1
            cur['_gfxtop'] = min(cur.get('_gfxtop', 1e9), e['top'])
        add_element(cur, e)
    if cur: qs.append(cur)

    for q in qs:
        finalize(q, answers.get(q['no']))
    render_option_images(pdf, qs, imgdir, eid)
    for q in qs:
        q.pop('_qx', None); q.pop('_optx', None); q.pop('_geo', None); q.pop('_optgeo', None); q.pop('_gfxopt', None); q.pop('_gfxtop', None)
        for b in q['stem']: b.pop('_g', None)
    return dict(id=eid, year=year, session=sess, title=f"{year}년 {sess}회", source=base,
                questions=qs), answers

def add_element(q, e):
    if e['kind'] == 'table':
        tgt = q['options'] if q['options'] else q['stem']
        blk = dict(type='table', grid=e['grid'], _g=(e['page'], e['col'], e['top']))
        (q['options'][-1]['blocks'] if q['options'] else q['stem']).append(blk) if q['options'] else q['stem'].append(blk)
        return
    if e['kind'] == 'figure_img':
        q['stem'].append(dict(type='image', src=e['src'], w=e['w'], h=e['h'], _g=(e['page'], e['col'], e['top']))); return
    if e['kind'] in ('box', 'figure'):
        blk = dict(type='code' if e['kind']=='box' and looks_code(e['lines']) else ('figure' if e['kind']=='figure' else 'note'),
                   lines=e.get('lines', []), indents=e.get('xs', []), _g=(e['page'], e['col'], e['top']))
        q['stem'].append(blk); return
    t = e['text']
    if HDR_JUNK.fullmatch(t): return
    marks = [mm.start() for mm in CIRC_RE.finditer(t)]
    if marks and marks[0] == 0:
        parts = []
        for i, p in enumerate(marks):
            end = marks[i+1] if i+1 < len(marks) else len(t)
            parts.append(t[p:end].strip())
        for p in parts:
            idx = CIRC.index(p[0])
            txt = p[1:].strip()
            while len(q['options']) <= idx:
                q['options'].append(dict(no=len(q['options'])+1, text='', blocks=[]))
            q['options'][idx]['text'] = (q['options'][idx]['text'] + ' ' + txt).strip()
        q['_optx'] = e['x0']
        return
    if q['options']:
        q['options'][-1]['text'] = (q['options'][-1]['text'] + ' ' + t).strip()
    else:
        if q['stem'] and q['stem'][-1]['type'] == 'text':
            q['stem'][-1]['text'] = (q['stem'][-1]['text'] + ' ' + t).strip()
        else:
            q['stem'].append(dict(type='text', text=t))

CODE_HINT = re.compile(r'[{};]|<\w+>|printf|scanf|System\.|public |void |int |char |def |print\(|function|var |let |const |#include|SELECT|CREATE|UPDATE|DELETE|INSERT')
def looks_code(lines):
    if not lines: return False
    s = ' '.join(lines)
    return bool(CODE_HINT.search(s))

def render_option_images(pdf, qs, imgdir, eid):
    for i, q in enumerate(qs):
        if 'optionsImage' in q: continue
        if sum(1 for o in q['options'] if not o['text']) < 2 and q.get('_gfxopt', 0) < 2: continue
        og = q.get('_optgeo')
        if not og:
            g = q.get('_geo') or []
            if len(g) < 2: continue
            og = (g[0][0], g[0][1], g[0][2])
            q['stem'] = [b for b in q['stem'] if b['type'] == 'text'][:1]
            q['fullCrop'] = True
        pg = pdf.pages[og[0]-1]
        col = og[1]
        top = min(og[2], q.get('_gfxtop', 1e9)) - 4
        bot = max(g[3] for g in q['_geo'] if g[0] == og[0] and g[1] == col) + 4
        nxt = qs[i+1] if i+1 < len(qs) else None
        if nxt and nxt['_geo'] and nxt['_geo'][0][0] == og[0] and nxt['_geo'][0][1] == col:
            bot = min(bot, nxt['_geo'][0][2] - 4)
        else:
            bot = min(bot, pg.height - 45)
        x0 = 40 if col == 0 else 300
        x1 = 295 if col == 0 else 558
        if bot - top < 12: continue
        name = f"{eid}_opt{q['no']}.png"
        try:
            pg.crop((x0, top, x1, bot)).to_image(resolution=200).save(os.path.join(imgdir, name))
            q['optionsImage'] = name
            if q.pop('fullCrop', None): q['optionsImageIsFull'] = True
            cut = min(og[2], q.get('_gfxtop', 1e9)) - 6
            q['stem'] = [b for b in q['stem']
                         if not (b.get('_g') and b['_g'][0] == og[0] and b['_g'][1] == og[1] and b['_g'][2] >= cut)]
            for o in q['options']: o['text'] = ''
            # 선택지 그림에 포함된 자투리 note 블록 제거
            while q['stem'] and q['stem'][-1]['type'] in ('note', 'table'):
                b = q['stem'][-1]
                txt = ' '.join(b.get('lines', []) if b['type'] == 'note' else sum(b.get('grid', []), []))
                digits = sum(c.isdigit() for c in txt)
                if len(txt) < 60 or (txt and digits / len(txt) > 0.45):
                    q['stem'].pop()
                else:
                    break
        except Exception:
            pass


def finalize(q, ans):
    st = []
    for b in q['stem']:
        if b['type'] == 'text' and not b['text']: continue
        if b['type'] in ('code', 'note', 'figure') and not [x for x in b.get('lines', []) if x.strip()]: continue
        st.append(b)
    q['stem'] = st
    q['answer'] = ans
    for o in q['options']:
        o.pop('blocks', None)
        o['text'] = re.sub(r'\s+', ' ', o['text']).strip()
    empt = sum(1 for o in q['options'] if not o['text'])
    imgs = [b for b in q['stem'] if b['type'] == 'image']
    if empt >= 2 and imgs:
        q['optionsImage'] = imgs[-1]['src']
        q['stem'] = [b for b in q['stem'] if b is not imgs[-1]]

if __name__ == '__main__':
    files = sorted(glob.glob("/sessions/relaxed-dreamy-brahmagupta/mnt/산업기사필기/*.pdf"))
    files = [f for f in files if re.search(r'(2022|2023|2024|2025)년', os.path.basename(f))]
    for f in files:
        try:
            data, ans = parse(f)
        except Exception as ex:
            print("FAIL", os.path.basename(f), ex); continue
        n = len(data['questions'])
        noans = [q['no'] for q in data['questions'] if not q['answer']]
        noopt = [q['no'] for q in data['questions'] if len(q['options']) != 4]
        print(f"{data['id']}: q={n} ans={len(ans)} missing_ans={noans[:8]} bad_opts={noopt[:12]}")
        json.dump(data, open(f"/tmp/w/out/{data['id']}.json","w"), ensure_ascii=False, indent=1)
