"""Public bookmark shelf, meaningful activity and verified contributor portraits."""
import datetime as dt
import html
import json
import urllib.error
import profile_live as p
from profile_extras import clip


def bookmarks():
    # First 100 recently starred repositories, explicitly a bounded snapshot.
    repos = p.api('users/NagatoBigSeven/starred?sort=created&direction=desc&per_page=100')
    return [{'name': r['full_name'], 'url': r['html_url'], 'language': r.get('language') or 'Other',
             'description': r.get('description') or ''} for r in repos if not r.get('private')]


def meaningful(events):
    result, seen = [], set()
    for event in events:
        kind, payload = event['type'], event.get('payload', {})
        repo = event['repo']['name']
        if repo == p.REPO or repo in seen or '[bot]' in event.get('actor', {}).get('login', ''):
            continue
        item = None
        if kind == 'PullRequestEvent' and payload.get('action') in ('opened', 'closed'):
            pr = payload.get('pull_request', {})
            if payload['action'] == 'closed' and not pr.get('merged'):
                continue
            item = ('Merged PR' if pr.get('merged') else 'Opened PR', pr.get('title', ''), pr.get('html_url'))
        elif kind == 'ReleaseEvent' and payload.get('action') == 'published':
            release = payload.get('release', {})
            if not release.get('draft') and not release.get('prerelease'):
                item = ('Published release', release.get('name') or release.get('tag_name', ''), release.get('html_url'))
        if item and item[2]:
            result.append({'kind': item[0], 'title': item[1], 'url': item[2], 'repository': repo, 'date': event['created_at'][:10]})
            seen.add(repo)
        if len(result) == 5:
            break
    return result


def contributors():
    people = {}
    for repo in ('NagatoBigSeven/AdsMind', 'AI4QC/catdt-gs'):
        for person in p.api(f'repos/{repo}/contributors?per_page=100'):
            if person.get('type') != 'User':
                continue
            login = person['login']
            people.setdefault(login, {'login': login, 'url': person['html_url'], 'avatar': person['avatar_url'], 'repos': []})['repos'].append(repo)
    return sorted(people.values(), key=lambda x: x['login'].casefold())


def card(title, rows, language, now, stale=False):
    cn = language == 'cn'
    height = 120+max(1, len(rows))*64
    out = p.shell(title, height)+p.txt(24, 36, title, 22, weight=600)
    out += '<style>@media(prefers-color-scheme:dark){text{fill:#FFFFFF}rect{fill:#302D40}svg>rect:first-of-type{fill:#252333}}</style>'
    for i, (top, bottom) in enumerate(rows):
        y = 62+i*64
        out += f'<rect x="20" y="{y-12}" width="720" height="58" rx="12" fill="#FFFFFF"/>'
        out += f'<circle cx="40" cy="{y+13}" r="5" fill="{p.PURPLE}"><animate attributeName="opacity" values=".4;1;.4" dur="4s" repeatCount="indefinite"/></circle>'
        out += p.txt(56, y+9, clip(top, 43), 18, weight=600)+p.txt(56, y+32, clip(bottom, 62), 13)
    if not rows:
        out += p.txt(24, 94, '当前公开数据窗口内暂无记录' if cn else 'No records in the current public data window', 19)
    label = ('上次成功快照' if cn else 'Last successful snapshot') if stale else f'{now:%Y-%m-%d} UTC'
    return out+p.txt(24, height-19, label+' · '+('点击打开来源目录' if cn else 'Click to open source directory'), 13)+'</svg>'


def directory(stars, events, people):
    lines = ['# Public collection / 公开收藏与贡献', '',
        'Latest 100 publicly starred repositories, grouped by GitHub primary language. Bookmarks are not endorsements or a claim of expertise.',
        '最近 100 个公开 Star 仓库，按 GitHub 主语言归类；收藏不代表背书或熟练掌握。', '']
    for language in sorted({x['language'] for x in stars}):
        lines += ['## '+html.escape(language), '']
        for x in stars:
            if x['language'] == language:
                lines += [f'<p><a href="{html.escape(x["url"], quote=True)}">{html.escape(x["name"])}</a> — {html.escape(x["description"])}</p>']
    lines += ['', '## Meaningful public activity / 公开开源动态', '',
              'At most five opened/merged PRs or published stable releases from the latest 100 public events, one per repository. GitHub events are a limited window, not a full contribution history.', '']
    for x in events:
        lines += [f'<p>{x["date"]} UTC · {x["kind"]} · <a href="{html.escape(x["url"], quote=True)}">{html.escape(x["repository"]+": "+x["title"])}</a></p>']
    if not events:
        lines += ['No qualifying public events in this snapshot / 当前窗口内暂无符合条件的公开事件。']
    lines += ['', '## Repository contributors / 仓库贡献者', '',
        'Public GitHub contributor attribution for AdsMind and CatDT; commit attribution is not paper authorship, collaboration status or endorsement. Bots excluded; at most 100 records per repository.', '']
    for x in people:
        lines += [f'<a href="{html.escape(x["url"], quote=True)}"><img src="{html.escape(x["avatar"], quote=True)}" width="48" height="48" alt="{html.escape(x["login"], quote=True)}" /></a> {html.escape(x["login"])} · '+', '.join(x['repos'])+'<br />']
    return '\n'.join(lines)+'\n'


def build(now):
    try:
        old = p.api(f'repos/{p.REPO}/contents/collection-state.json?ref={p.BRANCH}')
        import base64
        state = json.loads(base64.b64decode(old['content']))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        state = {}
    stale = {}
    for key, fetch in [('stars', bookmarks), ('events', lambda: meaningful(p.api('users/NagatoBigSeven/events/public?per_page=100'))), ('people', contributors)]:
        try:
            state[key] = fetch()
            stale[key] = False
        except (urllib.error.URLError, TimeoutError):
            stale[key] = True
            state.setdefault(key, [])
            print('Collection source unavailable:', key)
    stars, events, people = (state[x] for x in ('stars', 'events', 'people'))
    out = {'collection-state.json': json.dumps(state, ensure_ascii=False, indent=2), 'collection.md': directory(stars, events, people)}
    out['collection.md'] += '\nSnapshot: '+now.isoformat()+' · UTC.\n'
    if any(stale.values()):
        out['collection.md'] += '\nSource unavailable; last successful data retained for: '+', '.join(k for k,v in stale.items() if v)+'\n'
    for language in ('en', 'cn'):
        cn = language == 'cn'
        out[f'bookmarks-{language}.svg'] = card('开源收藏 · 工具书架' if cn else 'OPEN SOURCE · BOOKMARK SHELF', [(x['name'], x['language']+' · '+x['description']) for x in stars[:5]], language, now, stale['stars'])
        out[f'events-{language}.svg'] = card('开源动态 · PR 与发布' if cn else 'OPEN SOURCE · PRs & RELEASES', [(x['repository']+' · '+x['kind'], x['date']+' UTC · '+x['title']) for x in events], language, now, stale['events'])
        jokes = [('实验室里的确定性', '唯一确定的结果：需要再跑一次。'), ('多智能体会议', '大家一致同意：先让另一个 agent 检查。'), ('训练日志', 'Loss 降了，咖啡库存也降了。')] if cn else [('Lab certainty', 'One certain result: run it once more.'), ('Multi-agent meeting', 'Consensus: ask another agent to check.'), ('Training log', 'Loss is down. So is the coffee supply.')]
        joke = jokes[(now.isocalendar().week-1)%len(jokes)]
        out[f'weekend-{language}.svg'] = card('周间彩蛋 · 原创开发者小笑话' if cn else 'WEEKLY EASTER EGG · ORIGINAL DEV HUMOR', [joke], language, now)
    return out
