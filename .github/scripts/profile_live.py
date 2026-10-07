"""Render public profile widgets; publish atomically to an asset-only branch.

Issue text is data, never code. No personal access token or third-party service.
"""
import collections
import base64
import datetime as dt
import html
import json
import math
import os
from pathlib import Path
import random
import subprocess
import tempfile
import re
import time
import unicodedata
import urllib.error
import urllib.request

REPO = 'NagatoBigSeven/NagatoBigSeven'
BRANCH = 'profile-live'
ROOT = Path(__file__).resolve().parents[2]
PURPLE, CREAM, INK = '#A4ABD6', '#ECE9E0', '#353247'


def api(path, method='GET', data=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-live',
               'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request('https://api.github.com/' + path, method=method,
        headers=headers, data=None if data is None else json.dumps(data).encode())
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in [429, 500, 502, 503, 504] or attempt == 2:
                raise
            time.sleep(2 ** attempt)


def topics(issues):
    # One active vote per account; newest valid issue wins. Closed issues withdraw votes.
    votes, seen = {}, set()
    for issue in sorted(issues, key=lambda item: item['number'], reverse=True):
        if 'pull_request' in issue:
            continue
        if issue.get('title') != '[Research word]':
            continue
        match = re.search(r'^### Research topic\s*\n+([^\n]+)', issue.get('body') or '', re.M)
        if not match:
            continue
        word = ' '.join(match.group(1).strip().split())
        if not 1 <= len(word) <= 30 or not re.fullmatch(r'[\w .+/-]+', word, re.UNICODE):
            continue
        user = issue['user']['login']
        if user in seen:
            continue
        seen.add(user)
        if issue.get('state') == 'open':
            votes[user] = unicodedata.normalize('NFC', word.casefold())
    return collections.Counter(votes.values()), len(votes)


def txt(x, y, value, size=18, color=INK, weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Segoe UI,Microsoft YaHei,Arial,sans-serif" font-size="{size}" font-weight="{weight}">{html.escape(str(value))}</text>'


def shell(title, height):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}" role="img"><title>{html.escape(title)}</title><rect x="1" y="1" width="758" height="{height-2}" rx="18" fill="{CREAM}" stroke="{PURPLE}"/>'


def cloud(issues, language):
    counts, participants = topics(issues)
    # Shuffle requests change arrangement without altering votes or counts.
    seed = max((i['number'] for i in issues if i.get('title') == '[Shuffle research cloud]' and i.get('state') == 'open' and 'pull_request' not in i), default=0)
    return cloud_from_counts(counts, participants, seed, language)


def cloud_from_counts(counts, participants, seed, language):
    cn = language == 'cn'
    words = [word for word, _ in counts.most_common(18)]
    examples = not words
    if examples:
        words = ['AI for Science', 'Catalysis', 'AutoResearch', 'Multi-Agent', 'Lab Safety', 'Materials']
    layout = cloud_layout(words, counts, seed)
    title = '你希望 AI 解决什么科学问题？' if cn else 'What science should AI help solve?'
    height = max(440, math.ceil(max(y+size*1.35 for _, _, y, _, size in layout))+49)
    result = shell(title, height) + txt(24, 36, title, 23, weight=600)
    result += txt(24, 64, f'{participants} participants · {len(counts)} topics · one active vote per account' if not cn else f'{participants} 位参与者 · {len(counts)} 个主题 · 每个账号一票', 15)
    result += '<ellipse cx="380" cy="244" rx="340" ry="140" fill="#FFFFFF" opacity=".52"/>'
    for i, (word, x, y, width, size) in enumerate(layout):
        result += txt(round(x, 1), round(y+size, 1), word, size, color=[INK, '#696394', '#595C84'][i%3], weight=600)
    result += txt(24, height-24, ('示例词 · 等待你的第一个真实投稿' if cn else 'Example words · waiting for the first real submission') if examples else ('词语大小随票数变化 · 前 18 个主题' if cn else 'Size reflects votes · top 18 topics'), 15)
    return result + '</svg>'


def word_units(word):
    # Bounds cover wide Latin glyphs and CJK fallback fonts, including W-only input.
    return sum(1.15 if ord(char)>127 else 1.05 if char in 'MWmw@#%&' else .82 if char.isupper() else .38 if char in "ilIjtf.,'|:! " else .74 for char in word)


def cloud_layout(words, counts, seed, area_height=300):
    """Deterministic spiral packing with conservative glyph bounds; no overlaps."""
    rng = random.Random(seed)
    order = list(words)
    rng.shuffle(order)
    order.sort(key=lambda word: counts.get(word, 1), reverse=True)
    maximum = max(counts.values(), default=1)
    placed = []
    for word in order:
        units = word_units(word)
        requested = min(44, 18+int(26*math.sqrt(counts.get(word, 1)/maximum)))
        phase = rng.uniform(0, math.tau)
        found = None
        for size in range(min(requested, int(690/max(units, 1))), 11, -2):
            width, height = units*size, size*1.35
            for step in range(1800):
                angle = step*.37 + phase
                radius = 7*math.sqrt(step)
                x = 380 + math.cos(angle)*radius - width/2
                y = 91+area_height/2 + math.sin(angle)*radius*(area_height/510) - height/2
                if x<24 or x+width>736 or y<91 or y+height>91+area_height:
                    continue
                if any(not (x+width+8<px or px+pw+8<x or y+height+6<py or py+ps*1.35+6<y) for _, px, py, pw, ps in placed):
                    continue
                found = (word, x, y, width, size)
                break
            if found:
                break
        if not found:
            if area_height<660:
                return cloud_layout(words, counts, seed, area_height+120)
            # Extreme long-word inputs still render completely, using loose staggered rows.
            fallback, cursor = [], 91
            for item in order:
                fallback_size = 12+int(4*math.sqrt(counts.get(item, 1)/maximum))
                fallback_size = min(fallback_size, 690/max(word_units(item), 1))
                fallback_width = word_units(item)*fallback_size
                fallback.append((item, 24+rng.uniform(0, 712-fallback_width), cursor, fallback_width, fallback_size))
                cursor += fallback_size*1.35+9
            return fallback
        placed.append(found)
    return placed


def release_summary(release):
    """Use the first meaningful release-note line, never an invented changelog."""
    for line in (release.get('body') or '').splitlines():
        line = line.strip()
        if not line or line.startswith(('#', '![', '<!--', 'http')):
            continue
        line = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', line)
        line = re.sub(r'<[^>]*>', '', line)
        line = re.sub(r'^(?:[-*+]\s+|\d+[.)]\s+)', '', line)
        line = re.sub(r'(`+)(.*?)\1', r'\2', line)
        line = re.sub(r'(\*\*|__)(.*?)\1', r'\2', line).strip()
        if line:
            return line
    return ''


def progress(now, language):
    start = dt.datetime(now.year, 1, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(now.year+1, 1, 1, tzinfo=dt.timezone.utc)
    fraction = (now-start)/(end-start)
    cn = language == 'cn'
    label = f'{now.year} · 日历年度进度' if cn else f'{now.year} · calendar year progress'
    return shell(label, 106) + txt(24, 30, label, 18, weight=600) + txt(628, 30, f'{fraction:.1%}', 20, weight=600) + '<rect x="24" y="45" width="712" height="16" rx="8" fill="#FFFFFF"/>' + f'<rect x="24" y="45" width="{712*fraction:.2f}" height="16" rx="8" fill="{PURPLE}"/>' + txt(24, 88, f'Updated {now:%Y-%m-%d %H:%M} UTC · calendar only, not research completion' if not cn else f'更新于 {now:%Y-%m-%d %H:%M} UTC · 仅表示时间流逝，不表示科研完成度', 14) + '</svg>'


def updates(releases, language, now):
    cn = language == 'cn'
    result = shell('Research & releases', 366)
    result += txt(24, 34, '研究动态' if cn else 'Research updates', 22, weight=600)
    result += txt(402, 34, '项目发布' if cn else 'Project releases', 22, weight=600)
    result += f'<path d="M380 24V325" stroke="{PURPLE}"/>'
    events = [('2026-07-09', 'CatDT v2'), ('2026-06-17', 'AdsMind v1'), ('2026-06-03', 'CatDT v1'), ('2026-05-04', 'LLM Hackathon report')]
    for index, (date, label) in enumerate(events):
        y = 73 + index*56
        result += txt(24, y, date, 14) + txt(24, y+23, label, 19, weight=600)
    for index, (name, release) in enumerate(releases):
        y = 73 + index*129
        result += txt(402, y, name, 21, weight=600)
        if release:
            tag = release['tag_name']
            result += txt(402, y+28, tag if len(tag)<29 else tag[:26]+'…', 18)
            result += txt(402, y+51, release['published_at'][:10], 14)
            summary = release_summary(release)
            limit = 19 if any(ord(char)>127 for char in summary) else 36
            label = (summary[:limit-1]+'…' if len(summary)>limit else summary) or ('发布说明未提供' if cn else 'No release notes supplied')
            result += txt(402, y+76, label, 14)
        else:
            result += txt(402, y+28, '尚无正式 GitHub Release' if cn else 'No published GitHub release', 17)
            result += txt(402, y+51, '源代码已公开' if cn else 'Source code is public', 14)
    result += txt(24, 346, f'GitHub releases checked {now:%Y-%m-%d} UTC · summaries from release notes' if not cn else f'GitHub 发布核查：{now:%Y-%m-%d} UTC · 摘要来自原始发布说明', 14)
    return result + '</svg>'


def metrics(user, repositories, language, now):
    cn = language == 'cn'
    values = [len(repositories), sum(repo['stargazers_count'] for repo in repositories if not repo['fork']), user['followers']]
    labels = ['公开仓库', '自有公开仓库 Stars', 'GitHub 关注者'] if cn else ['Public repositories', 'Stars · owned public repos', 'GitHub followers']
    result = shell('Public GitHub metrics · animated constellation', 236)
    result += txt(24, 33, '公开 GitHub 数据 · 星轨' if cn else 'PUBLIC GITHUB · CONSTELLATION', 21, weight=600)
    for i in range(22):
        x, y = 18+i*34, 60+int(23*math.sin(i*.9))
        result += f'<circle cx="{x}" cy="{y}" r="2.5" fill="#696394"><animate attributeName="opacity" values=".15;.8;.15" dur="{3+i%4}s" begin="-{i%5}s" repeatCount="indefinite"/></circle>'
        if i:
            result += f'<path d="M{x-34} {60+int(23*math.sin((i-1)*.9))}L{x} {y}" stroke="{PURPLE}" stroke-width="1" opacity=".45"/>'
    for i, (value, label) in enumerate(zip(values, labels)):
        x = 20+i*244
        result += f'<rect x="{x}" y="86" width="232" height="110" rx="14" fill="#FFFFFF" fill-opacity=".92"/>'
        result += txt(x+16, 144, value, 43, weight=600)+txt(x+16, 176, label, 16)
    result += txt(24, 220, f'GitHub REST API · {now:%Y-%m-%d %H:%M} UTC · public data only' if not cn else f'GitHub REST API · {now:%Y-%m-%d %H:%M} UTC · 仅公开数据', 14)
    return result+'</svg>'


def render(issues, releases, now, user=None, repositories=None):
    files = {f'{kind}-{language}.svg': content for language in ['en', 'cn']
        for kind, content in [('community', cloud(issues, language)), ('year', progress(now, language)), ('updates', updates(releases, language, now))]}
    if user is not None and repositories is not None:
        files.update({f'metrics-{language}.svg': metrics(user, repositories, language, now) for language in ['en', 'cn']})
    return files


def publish(files):
    # Git push commits the widgets atomically. main and its protection are untouched.
    try:
        api(f'repos/{REPO}/git/ref/heads/'+BRANCH)
        exists = True
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        exists = False
    token = os.environ['GH_TOKEN']
    environment = os.environ.copy()
    environment['GIT_CONFIG_COUNT'] = '2'
    environment['GIT_CONFIG_KEY_0'] = 'http.https://github.com/.extraheader'
    environment['GIT_CONFIG_VALUE_0'] = 'AUTHORIZATION: basic ' + base64.b64encode(('x-access-token:'+token).encode()).decode()
    environment['GIT_CONFIG_KEY_1'] = 'credential.helper'
    environment['GIT_CONFIG_VALUE_1'] = ''
    environment['GIT_TERMINAL_PROMPT'] = '0'
    with tempfile.TemporaryDirectory(prefix='profile-assets-') as directory:
        def git(*arguments):
            result = subprocess.run(['git', *arguments], cwd=directory, env=environment,
                                    capture_output=True, text=True)
            if result.returncode:
                message = result.stderr.replace(token, '[redacted]').replace(environment['GIT_CONFIG_VALUE_0'], '[redacted]')
                raise RuntimeError('Asset-branch Git operation failed: '+arguments[0]+'\n'+message)
            return result.stdout.strip()
        git('init', '--initial-branch='+BRANCH)
        git('remote', 'add', 'origin', 'https://github.com/'+REPO+'.git')
        if exists:
            git('fetch', '--depth=1', 'origin', BRANCH)
            git('checkout', '-B', BRANCH, 'FETCH_HEAD')
        git('rm', '-r', '--cached', '--ignore-unmatch', '.')
        for name, content in files.items():
            target = Path(directory)/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        git('add', '--', *files.keys())
        if not git('diff', '--cached', '--name-only'):
            return
        git('config', 'user.name', 'github-actions[bot]')
        git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
        git('commit', '-m', 'chore: refresh public profile widgets')
        git('push', 'origin', 'HEAD:refs/heads/'+BRANCH)


def main():
    issues = []
    page = 1
    while True:
        batch = api(f'repos/{REPO}/issues?state=all&per_page=100&page={page}')
        issues.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    releases = []
    for repository in ['NagatoBigSeven/AdsMind', 'AI4QC/catdt-gs']:
        try:
            release = api('repos/'+repository+'/releases/latest')
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            release = None
        releases.append((repository.split('/')[-1], release))
    user = api('users/NagatoBigSeven')
    repositories, page = [], 1
    while True:
        batch = api(f'users/NagatoBigSeven/repos?type=owner&per_page=100&page={page}')
        repositories.extend(repo for repo in batch if not repo.get('private', False))
        if len(batch)<100:
            break
        page += 1
    now = dt.datetime.now(dt.timezone.utc)
    files = render(issues, releases, now, user, repositories)
    import profile_extras
    files.update(profile_extras.build(issues, now))
    import profile_collection
    files.update(profile_collection.build(now))
    if '--publish' in __import__('sys').argv:
        publish(files)
    else:
        output = ROOT/'assets'/'live'
        output.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            target = output/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    main()
