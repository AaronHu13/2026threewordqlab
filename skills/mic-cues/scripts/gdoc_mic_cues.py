#!/usr/bin/env python3
"""
gdoc_mic_cues.py — 读 Google Doc 剧本里的 mic 开关 cue，推演每条之后的全局 mic 状态，
按说话人校验哪句台词的 mic 没开，最后把状态行写回文档（每条 cue 正下方一行，黑色正体）。

依赖只有 google-api-python-client + google-auth；系统 python 被 PEP 668 锁，用 uv 跑：
  uv run --with google-api-python-client --with google-auth python3 gdoc_mic_cues.py <cmd> ...

子命令（按顺序用）：
  dump   <doc_id> --work DIR                 只读：抓文档，打印标题/mic plot 表/所有 mic 行，存 DIR/paras.json、DIR/script.txt
  plan   --work DIR --config CFG             自动把每条 mic 行解析成 on/off/set，写进 CFG.cues 供人工审
  check  --work DIR --config CFG             按 CFG.cues 推演状态、按说话人校验、和文档里已有状态行比对
  apply  --work DIR --config CFG [--refresh] [--dry-run]
                                             写回：确认文档未变 → 套 fixes → 插状态行 → 回读校验。
                                             --refresh：先删掉文档里所有旧状态行再重写（剧本改动后用）

行号 Lnn 一律按“去掉状态行之后”的段落序号计，四个子命令一致。

CFG（json）字段：
  doc_id      文档 id（不要提交到公开仓库）
  mics        {"8":"阿龙","9":"CEO",...}       mic 号 → 状态行里显示的名字
  aliases     {"9":["Ceo","ceo","阿杜"],...}    剧本里台词前会出现的说话人写法（用于校验）
  ignore      ["合","众人","伴舞"]               不校验的说话人
  fixes       {"原文":"改成"}                    写回前要改的 cue 文字（必须在全文唯一）
  cues        plan 生成：[{"line":16,"text":"…","on":[8,9],"off":[11]} | {"line":..,"set":[…]}]
  format      默认 "【当前开：{on} ｜ 关：{off}】"
密钥：环境变量 GDOC_SA_KEY，默认 ~/.slock/tokens/google_docs_sa.json（服务账号；文档要先 Share 给它 Editor）。
"""
import argparse, json, os, re, sys

KEY_PATH = os.path.expanduser(os.environ.get('GDOC_SA_KEY', '~/.slock/tokens/google_docs_sa.json'))
STATE_RE = re.compile(r'^\s*【当前开')
MIC_RE = re.compile(r'mic|麦', re.I)
BRACKET_RE = re.compile(r'（[^（）]*）|【[^【】]*】|\[[^\[\]]*\]|\([^()]*\)')
SPEAKER_RE = re.compile(r'^\s*(?:[（(][^）)]*[）)]\s*)*([^：:（）()\s“"「」]{1,14}?)(?:[（(][^）)]*[）)])?\s*[：:]')


# ---------------------------------------------------------------- Google Docs
def service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    if not os.path.exists(KEY_PATH):
        sys.exit(f'❌ 找不到服务账号密钥 {KEY_PATH}，见 references/google_setup.md')
    creds = service_account.Credentials.from_service_account_file(
        KEY_PATH, scopes=['https://www.googleapis.com/auth/documents'])
    return build('docs', 'v1', credentials=creds)


def fetch(svc, doc_id):
    """→ title, paras [[start,end,text],…], tables [[cells…]…]"""
    from googleapiclient.errors import HttpError
    try:
        doc = svc.documents().get(documentId=doc_id).execute()
    except HttpError as e:
        msg = str(e)
        if 'has not been used in project' in msg or 'is disabled' in msg:
            sys.exit('❌ 这个项目还没开 Google Docs API，把报错里的 console 链接发给文档主人点 Enable：\n' + msg[:400])
        if e.resp.status in (403, 404):
            sys.exit('❌ 读不到文档：请文档主人 Share 给服务账号邮箱（密钥 json 里的 client_email），权限 Editor。\n' + msg[:300])
        raise
    paras, tables = [], []
    for el in doc['body']['content']:
        if 'table' in el:
            rows = []
            for row in el['table']['tableRows']:
                cells = []
                for c in row['tableCells']:
                    t = ''
                    for ce in c['content']:
                        p = ce.get('paragraph')
                        if p:
                            t += ''.join(r.get('textRun', {}).get('content', '') for r in p['elements'])
                    cells.append(t.strip().replace('\n', ' / '))
                rows.append(cells)
            tables.append(rows)
        p = el.get('paragraph')
        if not p:
            continue
        txt = ''.join(r.get('textRun', {}).get('content', '') for r in p['elements']).rstrip('\n')
        paras.append([el['startIndex'], el['endIndex'], txt])
    return doc['title'], paras, tables


def is_state(t):
    return bool(STATE_RE.match(t))


def is_mic_line(t):
    return bool(MIC_RE.search(t)) and 'Plot' not in t and not is_state(t)


def strip_states(paras):
    """去掉状态行；每段附带“它下面紧跟的旧状态行文字”（没有则 None），用于 check 比对。"""
    out = []
    for i, p in enumerate(paras):
        if is_state(p[2]):
            continue
        nxt = paras[i + 1][2] if i + 1 < len(paras) and is_state(paras[i + 1][2]) else None
        out.append([p[0], p[1], p[2], nxt])
    return out


# ---------------------------------------------------------------- parsing
def nums_in(s, mics):
    """'5-7' '8，9，11' '9.11-14' → mic 号集合（只保留 plot 里有的）"""
    s = s.replace('－', '-').replace('—', '-').replace('～', '-')
    out = set()
    for a, b in re.findall(r'(\d+)\s*-\s*(\d+)', s):
        out |= set(range(int(a), int(b) + 1))
    out |= {int(x) for x in re.findall(r'\d+', re.sub(r'\d+\s*-\s*\d+', ' ', s))}
    return {x for x in out if x in mics}


def auto_parse(text, mics):
    """把一条 mic 行解析成 {'on':[..],'off':[..]} 或 {'set':[..]}；返回 (op, note)。启发式，结果必须人工审。"""
    segs = [m.group(0) for m in BRACKET_RE.finditer(text) if MIC_RE.search(m.group(0))] or [text]
    on, off, notes, mode = set(), set(), [], None   # mode: None | all_off | all_on | complement
    for seg in segs:
        low = seg.lower()
        if re.search(r'all\s*mics?\s*off|all\s*off|全关|全部关', low):
            mode = 'all_off'; notes.append('all off'); continue
        if re.search(r'open\s*all|all\s*on|所有人|全开|全部开', low):
            mode = 'all_on'; notes.append('all on'); continue
        if re.search(r'其他人?\s*(off|关)|others?\s*off|rest\s*off', low):
            mode = 'complement'; notes.append('其他人 off → set')
        # \b 对中英混排无效（“人off”里没有词边界），用字母 lookaround；keep 视作 on
        kws = [(m.start(), 'off' if m.group(0).lower() in ('off', '关') else 'on')
               for m in re.finditer(r'(?<![a-z])(?:on|off|keep)(?![a-z])|开|关', seg, re.I)]
        if not kws:
            notes.append('无 on/off 关键词'); continue
        for m in re.finditer(r'\d+(?:\s*[-－—~～.,，、/ ]\s*\d+)*', seg):
            ns = nums_in(m.group(0), mics)
            if ns:
                kind = min(kws, key=lambda k: abs(k[0] - m.start()))[1]
                (on if kind == 'on' else off).update(ns)
    if mode == 'all_off':
        return {'set': []}, '; '.join(notes)
    if mode == 'all_on':
        return {'set': sorted(mics)}, '; '.join(notes)
    if mode == 'complement':
        return {'set': sorted(on)}, '; '.join(notes)
    if not on and not off:
        return {'on': [], 'off': []}, '⚠ 没解析出任何 mic 号，请手改'
    return {'on': sorted(on), 'off': sorted(off)}, '; '.join(notes)


# ---------------------------------------------------------------- state machine
def fix_text(t, fixes):
    for k, v in fixes.items():
        t = t.replace(k, v)
    return t


def run_states(paras, cues, mics, fmt, fixes):
    """paras 已去状态行。→ [(line, cue_text, state_set, state_line), …]"""
    by_line = {c['line']: c for c in cues}
    state, out = set(), []
    for i, p in enumerate(paras, 1):
        t = fix_text(p[2], fixes)
        if not is_mic_line(t):
            continue
        c = by_line.get(i)
        if c is None:
            sys.exit(f'❌ L{i} 是 mic 行但 config.cues 里没有规则（重新 plan）：{t}')
        if c.get('text') is not None and fix_text(c['text'], fixes) != t:
            sys.exit(f'❌ L{i} 文字和 config 记录的不一致，重新 dump/plan：\n  doc: {t}\n  cfg: {c["text"]}')
        if 'set' in c:
            state = set(c['set'])
        else:
            state |= set(c.get('on', [])); state -= set(c.get('off', []))
        on = ' '.join(f'{n}{mics[n]}' for n in sorted(state)) or '无'
        off = ' '.join(str(n) for n in sorted(set(mics) - state)) or '无'
        out.append((i, t, set(state), fmt.format(on=on, off=off)))
    return out


def speaker_check(paras, states, mics, aliases, ignore):
    """→ (violations[(line,name,mic,text)], unknown{name:line})：谁在 mic 关着的时候说了话"""
    name2mic = {}
    for n, names in aliases.items():
        for a in names:
            name2mic[a.lower()] = int(n)
    for n, name in mics.items():
        name2mic.setdefault(str(name).lower(), n)
    cue_at = {i: st for i, _, st, _ in states}
    state, viol, unknown = set(), [], {}
    for i, p in enumerate(paras, 1):
        if i in cue_at:
            state = cue_at[i]; continue
        m = SPEAKER_RE.match(p[2])
        if not m:
            continue
        for raw in re.split(r'[，,、/和及]', m.group(1)):
            raw = raw.strip()
            if not raw or raw in ignore:
                continue
            mic = name2mic.get(raw.lower())
            if mic is None:
                unknown.setdefault(raw, i); continue
            if mic not in state:
                viol.append((i, raw, mic, p[2][:60]))
    return viol, unknown


# ---------------------------------------------------------------- commands
def load_work(work):
    with open(os.path.join(work, 'paras.json'), encoding='utf-8') as f:
        return json.load(f)


def load_cfg(path):
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    cfg['mics'] = {int(k): v for k, v in cfg['mics'].items()}
    cfg.setdefault('aliases', {}); cfg.setdefault('ignore', ['合', '众人', '伴舞', '合唱', '众', '全体'])
    cfg.setdefault('fixes', {}); cfg.setdefault('format', '【当前开：{on} ｜ 关：{off}】'); cfg.setdefault('cues', [])
    return cfg


def cmd_dump(a):
    title, raw, tables = fetch(service(), a.doc_id)
    paras = strip_states(raw)
    os.makedirs(a.work, exist_ok=True)
    with open(os.path.join(a.work, 'paras.json'), 'w', encoding='utf-8') as f:
        json.dump({'doc_id': a.doc_id, 'title': title, 'paras': paras}, f, ensure_ascii=False)
    with open(os.path.join(a.work, 'script.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(f'L{i}: {p[2]}' for i, p in enumerate(paras, 1)))
    n_state = len(raw) - len(paras)
    print(f'title: {title} | paragraphs: {len(paras)} (+{n_state} 行已有状态行) | tables: {len(tables)}')
    for rows in tables:
        if rows and any('mic' in c.lower() for c in rows[0]):
            print('mic plot table:')
            for r in rows:
                print('  | ' + ' | '.join(r))
    print('mic lines:')
    for i, p in enumerate(paras, 1):
        if is_mic_line(p[2]):
            print(f'  L{i}: {p[2][:100]}')
    if n_state:
        print(f'⚠ 文档里已有 {n_state} 行状态行；剧本若改过，apply 时用 --refresh 整体重写')
    print(f'saved {a.work}/paras.json, {a.work}/script.txt（整段剧本，按行号分段读它来复核）')


def cmd_plan(a):
    w = load_work(a.work); cfg = load_cfg(a.config)
    cues = []
    for i, p in enumerate(w['paras'], 1):
        if not is_mic_line(p[2]):
            continue
        op, note = auto_parse(fix_text(p[2], cfg['fixes']), cfg['mics'])
        c = {'line': i, 'text': p[2], **op}
        if note:
            c['note'] = note
        cues.append(c)
    raw = json.load(open(a.config, encoding='utf-8')); raw['cues'] = cues
    with open(a.config, 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)
    print(f'wrote {len(cues)} cues into {a.config} — 逐条人工审 on/off/set，尤其带 ⚠ 的')
    for c in cues:
        op = f"set {c['set']}" if 'set' in c else f"on {c['on']} off {c['off']}"
        print(f"  L{c['line']}: {c['text'][:60]}\n        → {op}   {c.get('note', '')}")


def cmd_check(a):
    w = load_work(a.work); cfg = load_cfg(a.config); paras = w['paras']
    states = run_states(paras, cfg['cues'], cfg['mics'], cfg['format'], cfg['fixes'])
    print('状态表：')
    stale = 0
    for i, t, st, line in states:
        old = paras[i - 1][3]
        cmp = ''
        if old is not None:
            cmp = '  ✅ 与文档已有状态行一致' if old == line else f'  ❌ 文档里是：{old}'
            stale += old != line
        elif any(p[3] for p in paras):
            cmp = '  ❌ 文档里这条下面没有状态行'; stale += 1
        print(f'L{i} {t[:70]}\n    {line}{cmp}')
    viol, unknown = speaker_check(paras, states, cfg['mics'], cfg['aliases'], set(cfg['ignore']))
    print(f'\n说话人校验：{len(viol)} 处 mic 未开就说话')
    for i, name, mic, t in viol:
        print(f'  ❌ L{i} {name}（mic {mic} 关着）：{t}')
    if unknown:
        print('未识别的说话人（真有词的加进 aliases，标题/杂项加 ignore 或忽略）：' + '、'.join(f'{k}(L{v})' for k, v in unknown.items()))
    if stale:
        print(f'⚠ {stale} 条状态行已过期或缺失 → apply --refresh')
    if states and states[-1][2]:
        print(f'提示：结尾状态仍有 mic 开着 {sorted(states[-1][2])}，考虑在最后加一条 all off。')


def cmd_apply(a):
    w = load_work(a.work); cfg = load_cfg(a.config)
    svc = service(); doc_id = cfg.get('doc_id') or w['doc_id']
    _, raw, _ = fetch(svc, doc_id)
    cur = strip_states(raw)
    if [p[2] for p in cur] != [p[2] for p in w['paras']]:
        d = [(x[2], y[2]) for x, y in zip(w['paras'], cur) if x[2] != y[2]]
        print(f'❌ 文档自 dump 后已变（{len(w["paras"])}→{len(cur)} 段，{len(d)} 段不同），重新 dump/plan/check：')
        for x, y in d[:5]:
            print('  was:', x[:60], '\n  now:', y[:60])
        sys.exit(1)
    old_states = [p for p in raw if is_state(p[2])]
    if old_states and not a.refresh:
        sys.exit(f'❌ 文档里已有 {len(old_states)} 行状态行。要整体重写加 --refresh，否则不动。')
    alltext = '\n'.join(p[2] for p in cur)
    for k in cfg['fixes']:
        if alltext.count(k) != 1:
            sys.exit(f'❌ fix 原文出现 {alltext.count(k)} 次，必须唯一：{k}')
    states = run_states(cur, cfg['cues'], cfg['mics'], cfg['format'], cfg['fixes'])   # 先算一遍，规则有问题就在写之前退出
    if a.dry_run:
        print(f'[dry-run] 会删 {len(old_states)} 行旧状态、改 {len(cfg["fixes"])} 处文字、插 {len(states)} 行状态；不写。'); return
    if old_states:
        svc.documents().batchUpdate(documentId=doc_id, body={'requests': [
            {'deleteContentRange': {'range': {'startIndex': s, 'endIndex': e}}}
            for s, e, _ in sorted(old_states, key=lambda p: -p[0])]}).execute()
        print(f'deleted {len(old_states)} old state lines')
    if cfg['fixes']:
        svc.documents().batchUpdate(documentId=doc_id, body={'requests': [
            {'replaceAllText': {'containsText': {'text': k, 'matchCase': True}, 'replaceText': v}}
            for k, v in cfg['fixes'].items()]}).execute()
        print(f'fixes applied: {len(cfg["fixes"])}')
    _, paras, _ = fetch(svc, doc_id)
    assert not any(is_state(p[2]) for p in paras)
    states = run_states(paras, cfg['cues'], cfg['mics'], cfg['format'], {})
    black = {'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}, 'italic': False, 'bold': False}
    reqs = []
    for i, t, st, line in sorted(states, key=lambda x: -x[0]):
        pos = paras[i - 1][1] - 1                      # 该段换行符之前
        reqs.append({'insertText': {'location': {'index': pos}, 'text': '\n' + line}})
        reqs.append({'updateTextStyle': {'range': {'startIndex': pos + 1, 'endIndex': pos + 1 + len(line)},
                                         'textStyle': black, 'fields': 'foregroundColor,italic,bold'}})
    svc.documents().batchUpdate(documentId=doc_id, body={'requests': reqs}).execute()
    print(f'inserted {len(states)} state lines')
    # 回读校验
    _, after, _ = fetch(svc, doc_id)
    ok = 0
    for j, p in enumerate(after):
        if is_mic_line(p[2]):
            nxt = after[j + 1][2] if j + 1 < len(after) else ''
            good = is_state(nxt); ok += good
            print(('  ✅ ' if good else '  ❌ ') + p[2][:60] + '\n       ' + (nxt if good else 'MISSING STATE LINE'))
    rest = [p[2] for p in after if not is_state(p[2])]
    expect = [fix_text(p[2], cfg['fixes']) for p in w['paras']]
    print(f'cues with state: {ok}/{len(states)} ; other paragraphs identical to original(+fixes): {rest == expect} ; paragraphs {len(raw)}→{len(after)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('dump'); p.add_argument('doc_id'); p.add_argument('--work', required=True); p.set_defaults(f=cmd_dump)
    for name, fn in (('plan', cmd_plan), ('check', cmd_check), ('apply', cmd_apply)):
        p = sub.add_parser(name); p.add_argument('--work', required=True); p.add_argument('--config', required=True)
        if name == 'apply':
            p.add_argument('--dry-run', action='store_true'); p.add_argument('--refresh', action='store_true')
        p.set_defaults(f=fn)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
