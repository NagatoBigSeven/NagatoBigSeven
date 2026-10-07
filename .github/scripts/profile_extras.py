"""Source-backed notes, anonymous quarterly cloud snapshots and public coding time."""
import base64
import collections
import html
import json
import math
from pathlib import PurePosixPath
import re
import urllib.error
import urllib.parse
import urllib.request

import profile_live as profile

STATE = 'extras-state.json'


def clip(value, units=27):
    result = ''
    for char in value:
        if profile.word_units(result+char) > units:
            return result+'…'
        result += char
    return result


def latest_notes(repositories):
    """One content file per repo, then the three newest repo-level note changes."""
    candidates = []
    for repo in repositories:
        commits = profile.api(f'repos/{repo}/commits?per_page=10')
        for commit in commits:
            detail = profile.api(f'repos/{repo}/commits/{commit["sha"]}')
            files = [file['filename'] for file in detail.get('files', [])
                     if file.get('status') != 'removed'
                     and PurePosixPath(file['filename']).suffix.lower() in ('.md', '.ipynb', '.pdf')
                     and not PurePosixPath(file['filename']).name.lower().startswith(('readme', 'license', 'changelog'))
                     and not any(part.startswith('.') for part in PurePosixPath(file['filename']).parts)]
            if not files:
                continue
            path = sorted(files)[0]
            candidates.append({'repository': repo, 'path': path,
                'title': PurePosixPath(path).stem,
                'updated_at': commit['commit']['committer']['date'],
                'sha': commit['sha'],
                'url': f'https://github.com/{repo}/blob/{commit["sha"]}/'+urllib.parse.quote(path, safe='/')})
            break
    return sorted(candidates, key=lambda item: (item['updated_at'], item['repository']), reverse=True)[:3]


def notes_card(notes, language, now, stale=False, mobile=False):
    cn = language == 'cn'
    height = 90+max(1, len(notes))*156 if mobile else 310
    result = profile.shell('Latest study notes · source-backed bookmarks', height)
    if mobile:
        result = result.replace('width="760"', 'width="360"', 1).replace(f'viewBox="0 0 760 {height}"', f'viewBox="0 0 360 {height}"', 1).replace('width="758"', 'width="358"', 1)
    result += profile.txt(16 if mobile else 24, 35, '最新学习笔记 · 书签' if cn else 'LATEST NOTES · BOOKMARKS', 20 if mobile else 22, weight=600)
    for i, item in enumerate(notes):
        label = item['repository'].split('/')[-1].replace('Nagato-no-', '').replace('-Notes', '')
        label = ({'GenAI': '生成式 AI', 'NLP': '自然语言处理', 'Quantum-Information': '量子信息', 'RDKit': 'RDKit', 'Fine-Tuning': '微调'} if cn else {'Quantum-Information': 'Quantum Info'}).get(label, label)
        if mobile:
            y = 56+i*156
            result += f'<rect x="16" y="{y}" width="328" height="142" rx="14" fill="#FFFFFF"/>'
            result += f'<path d="M304 {y}h24v37l-12-8-12 8Z" fill="{profile.PURPLE}"/>'
            result += profile.txt(32, y+31, clip(label, 12), 20, weight=600)
            result += profile.txt(32, y+64, clip(item['title'], 15), 18)
            result += profile.txt(32, y+94, item['updated_at'][:10]+' UTC', 14)
            result += profile.txt(32, y+122, '打开笔记目录 ↗' if cn else 'Open note directory ↗', 15, color='#696394')
            continue
        x = 20+i*244
        result += f'<rect x="{x}" y="56" width="232" height="211" rx="14" fill="#FFFFFF"/>'
        result += f'<path d="M{x+183} 56h25v48l-12.5-9-12.5 9Z" fill="{profile.PURPLE}"/>'
        result += profile.txt(x+16, 85, f'0{i+1}', 16, color='#696394', weight=600)
        result += profile.txt(x+16, 123, clip(label, 9.5), 20, weight=600)
        result += profile.txt(x+16, 158, clip(item['title'], 10.5), 18)
        result += profile.txt(x+16, 192, item['updated_at'][:10]+' UTC', 14)
        result += profile.txt(x+16, 239, '打开笔记目录 ↗' if cn else 'Open note directory ↗', 15, color='#696394')
    if not notes:
        result += profile.txt(24, 142, '暂无可核实的笔记更新' if cn else 'No verified note updates available', 21)
    label = ('保留上次成功快照' if cn else 'Last successful snapshot retained') if stale else ('每个仓库一篇 · 最近三个更新仓库' if cn else 'One note per repository · three most recently updated')
    if mobile:
        label = ('上次成功快照' if cn else 'Last successful snapshot') if stale else ('每仓库一篇 · 按更新日期排序' if cn else 'One per repository · sorted by update date')
    result += profile.txt(16 if mobile else 24, height-18, label, 13 if mobile else 14)
    return result+'</svg>'


def note_directory(notes):
    lines = ['# Latest study notes / 最新学习笔记', '',
             'One note from each of the three most recently updated study repositories. Dates are Git commit times, not reading times.',
             '每个笔记仓库选取最近一次内容更新中的一篇，展示最近更新的三个仓库；日期为 Git 提交时间。', '']
    for index, item in enumerate(notes, 1):
        # HTML links keep arbitrary source filenames from changing Markdown structure.
        lines += [f'## {index}. {html.escape(item["title"])}', '',
                  f'<a href="{html.escape(item["url"], quote=True)}">打开笔记 / Open note</a>', '',
                  f'Repository: `{item["repository"]}` · {item["updated_at"][:10]} UTC', '']
    return '\n'.join(lines)+'\n'


def update_history(previous, issues, now):
    counts, participants = profile.topics(issues)
    period = f'{now.year}-Q{(now.month-1)//3+1}'
    records = {item['period']: item for item in previous}
    if participants:
        seed = max((i['number'] for i in issues if i.get('title') == '[Shuffle research cloud]' and i.get('state') == 'open' and 'pull_request' not in i), default=0)
        current = {'period': period, 'counts': dict(counts), 'participants': participants,
                   'seed': seed, 'prompt': 'What science should AI help solve?'}
        old = records.get(period, {})
        current['updated_at'] = old.get('updated_at', now.isoformat()) if all(old.get(k) == current[k] for k in current) else now.isoformat()
        records[period] = current
    else:
        # Withdrawal clears this quarter's active snapshot instead of preserving stale votes.
        records.pop(period, None)
    return [records[key] for key in sorted(records)[-8:]]


def history_card(history, language):
    cn = language == 'cn'
    shown = list(reversed(history))[:8]
    height = 248 if not shown else 80+math.ceil(len(shown)/2)*240
    result = profile.shell('Quarterly research cloud gallery · real submissions only', height)
    result += profile.txt(24, 34, '词云历史画廊 · 季度快照' if cn else 'RESEARCH CLOUD · QUARTERLY GALLERY', 22, weight=600)
    if not shown:
        for i in range(3):
            x = 24+i*244
            result += f'<rect x="{x}" y="65" width="220" height="107" rx="14" fill="#FFFFFF" stroke="{profile.PURPLE}" stroke-dasharray="5 6"/>'
            result += f'<path d="M{x+66} 126h80a15 15 0 0 0 0-30 24 24 0 0 0-43-8 18 18 0 0 0-37 38Z" fill="{profile.PURPLE}" opacity=".28"/>'
        result += profile.txt(24, 205, '等待真实投稿 · 示例词不会进入历史' if cn else 'Waiting for real submissions · example words are never archived', 17)
    for i, item in enumerate(shown):
        x, y = 20+(i%2)*370, 62+(i//2)*240
        result += f'<rect x="{x}" y="{y}" width="350" height="225" rx="13" fill="#FFFFFF"/>'
        svg = profile.cloud_from_counts(collections.Counter(item['counts']), item['participants'], item['seed'], language)
        encoded = base64.b64encode(svg.encode()).decode()
        result += f'<image href="data:image/svg+xml;base64,{encoded}" x="{x+10}" y="{y+10}" width="330" height="157"/>'
        result += profile.txt(x+14, y+189, item['period']+' · '+item['updated_at'][:10], 17, weight=600)
        result += profile.txt(x+14, y+211, f'{item["participants"]} participants · {len(item["counts"])} topics' if not cn else f'{item["participants"]} 位参与者 · {len(item["counts"])} 个主题', 14)
    result += profile.txt(24, height-16, '历史快照不代表当前票数 · 最近八个有投稿季度' if cn else 'Historical snapshots are not current votes · last eight submitted quarters', 13)
    return result+'</svg>'


def fetch_activity(username):
    if not username:
        return {'status': 'not_connected'}
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', username):
        raise ValueError('Invalid public WakaTime username')
    request = urllib.request.Request(f'https://api.wakatime.com/api/v1/users/{username}/stats/last_7_days', headers={'User-Agent': 'public-profile-widgets'})
    # This public request never receives the GitHub token or a private WakaTime key.
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response).get('data', {})
    if data.get('is_up_to_date') is not True:
        return {'status': 'pending', 'username': username}
    return {'status': 'ready', 'username': username, 'start': data['start'], 'end': data['end'],
            'timezone': data.get('timezone', 'UTC'), 'languages': data.get('languages', []),
            'editors': data.get('editors', [])}


def activity_card(activity, language):
    cn = language == 'cn'
    ready = activity.get('status') == 'ready'
    rows = [(kind, item) for kind in ('languages', 'editors') for item in sorted(activity.get(kind, []), key=lambda item: item['total_seconds'], reverse=True)[:4]] if ready else []
    height = 160 if not rows else 118+len(rows)*42
    result = profile.shell('Weekly coding time · WakaTime public data only', height)
    result += profile.txt(24, 34, '每周编程活动 · 真实时间记录' if cn else 'WEEKLY CODING · TRACKED TIME', 22, weight=600)
    if not ready:
        result += '<path d="M47 61v16l10 7" fill="none" stroke="#696394" stroke-width="3"/><circle cx="47" cy="78" r="24" fill="none" stroke="#A4ABD6" stroke-width="3"/>'
        result += profile.txt(89, 83, ('公开数据暂不可用' if cn else 'Public data temporarily unavailable') if activity.get('status') == 'unavailable' else ('统计正在生成' if cn else 'Statistics are being prepared') if activity.get('status') == 'pending' else ('等待连接公开 WakaTime 数据' if cn else 'Awaiting public WakaTime data'), 20)
        result += profile.txt(24, 137, '未显示虚构时长；仓库语言占比不等于编程时间。' if cn else 'No invented hours · repository language shares are not coding time', 15)
    else:
        result += profile.txt(24, 61, f'{activity["start"][:10]} — {activity["end"][:10]} · {activity["timezone"]}', 14)
        for i, (kind, item) in enumerate(rows):
            y = 91+i*42
            group_total = sum(x['total_seconds'] for x in activity[kind])
            percent = item['total_seconds']/group_total if group_total else 0
            label = ('语言' if kind == 'languages' else '编辑器') if cn else ('Language' if kind == 'languages' else 'Editor')
            result += profile.txt(24, y, label+' · '+clip(item['name'], 17), 15)
            result += f'<rect x="256" y="{y-14}" width="330" height="16" rx="8" fill="#FFFFFF"/>'
            result += f'<rect x="256" y="{y-14}" width="{330*percent:.2f}" height="16" rx="8" fill="{profile.PURPLE}"><animate attributeName="opacity" values=".6;1;.6" dur="4s" repeatCount="indefinite"/></rect>'
            result += profile.txt(607, y, f'{item["total_seconds"]/3600:.1f} h · {percent:.0%}', 15)
        result += profile.txt(24, height-15, 'WakaTime · 过去七天 · 语言与编辑器各自归一化' if cn else 'WakaTime · last 7 days · language/editor shares normalized separately', 13)
    return result+'</svg>'


def load_state():
    try:
        result = profile.api(f'repos/{profile.REPO}/contents/{STATE}?ref={profile.BRANCH}')
        return json.loads(base64.b64decode(result['content']))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return {}
        raise


def build(issues, now):
    config = json.loads((profile.ROOT/'.github/profile-widgets.json').read_text(encoding='utf-8'))
    state = load_state()
    stale = False
    try:
        notes = latest_notes(config['note_repositories'])
    except (urllib.error.URLError, TimeoutError):
        notes, stale = state.get('notes', []), True
        print('Note source unavailable; retaining last successful snapshot.')
    history = update_history(state.get('history', []), issues, now)
    try:
        activity = fetch_activity(config.get('wakatime_username'))
    except (urllib.error.URLError, TimeoutError):
        activity = {'status': 'unavailable'}
        print('Public coding-time data unavailable; no hours shown.')
    result = {STATE: json.dumps({'notes': notes, 'history': history}, ensure_ascii=False, indent=2),
              'notes.md': note_directory(notes)}
    for language in ('en', 'cn'):
        result[f'notes-{language}.svg'] = notes_card(notes, language, now, stale)
        result[f'notes-{language}-mobile.svg'] = notes_card(notes, language, now, stale, mobile=True)
        result[f'history-{language}.svg'] = history_card(history, language)
        result[f'activity-{language}.svg'] = activity_card(activity, language)
    lines = ['# Quarterly research cloud snapshots / 词云季度快照', '', 'Historical anonymous vote counts, not current votes. Example words are never archived.', '历史匿名票数不代表当前票数；示例词不会归档。', '']
    for item in reversed(history):
        lines += [f'## {item["period"]}', '', f'{item["updated_at"]} · {item["participants"]} participants', '']
        for language in ('en', 'cn'):
            name = f'history/{item["period"]}-{language}.svg'
            result[name] = profile.cloud_from_counts(collections.Counter(item['counts']), item['participants'], item['seed'], language)
        lines += [f'![Quarterly cloud](./history/{item["period"]}-en.svg)', '']
    if not history:
        lines += ['Waiting for the first real submission / 等待首次真实投稿。', '']
    result['history.md'] = '\n'.join(lines)
    return result
