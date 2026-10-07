"""Offline artwork and bilingual README blocks from curated public sources."""
import json
import re
from pathlib import Path
from build_showcase import text, svg as base_svg, STORIES

ROOT = Path(__file__).resolve().parents[2]
FACTS = json.loads((ROOT / '.github/profile-showroom.json').read_text(encoding='utf-8'))


def svg(name, w, h, title, body):
    """Theme only showroom artwork; never regenerate approved character art."""
    flourish = [f'<path d="M{w-48} 13 q-16 15 2 26 q-27 4-20-21" fill="#C39B65" opacity=".55"/>',
                f'<path d="M{w-24} {h-24} q-12-10-12 0 q0 8 12 0 q12-10 12 0 q0 8-12 0 m-3 2-4 7 m10-7 4 7" fill="none" stroke="#A83F55" stroke-width="1.5" opacity=".5"/>',
                f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="23" fill="none" stroke="#A4ABD6" opacity=".3"/>'] if h>100 else []
    base_svg(name,w,h,title,body+flourish)
    path = ROOT/'assets'/name
    skin = '<style>.bg{fill:#ECE9E0}.panel{fill:#FFFEFA}.ink{fill:#353247}.muted{fill:#575166}.pulse{animation:pulse 6s ease-in-out infinite}@media(prefers-color-scheme:dark){.bg{fill:#22212D}.panel{fill:#343145}.ink{fill:#FFFFFF}.muted{fill:#DED9EB}.line{stroke:#B9BEE5}}@media(prefers-reduced-motion:reduce){.pulse{animation:none}}</style>'
    content=path.read_text(encoding='utf-8').replace('</style>','</style>'+skin,1)
    path.write_text(content,encoding='utf-8')


def book_covers():
    for i, post in enumerate(FACTS['posts']):
        body = [
            '<rect x="22" y="25" width="264" height="180" rx="12" fill="#353247" opacity=".14"/>',
            '<rect x="28" y="27" width="254" height="168" rx="8" fill="#FFFEFA"/>',
            '<path d="M44 185 H279 M44 189 H279 M44 193 H279" stroke="#D8D0C2" stroke-width="1"/>',
            '<rect x="16" y="18" width="262" height="166" rx="10" class="panel"/>',
            '<path d="M30 28 V176" class="line" stroke-width="7"/>',
            '<path d="M38 28 V176" stroke="#C39B65" stroke-width="1" opacity=".55"/>',
            '<path d="M250 18 v44 l-12 -9 -12 9 V18" class="accent"/>',
            text(46, 55, f'VOL. 0{i+1} / CHEMISTRY', 14, 'muted'),
            text(46, 107, post['title'], 17, bold=True),
            text(46, 144, post['date'], 17, 'muted'),
            text(46, 172, 'READ THE ORIGINAL →', 12, 'muted')]
        svg(f'blog-cover-{i+1}.svg', 300, 220, post['title']+' · '+post['date'], body)


def navigation(lang):
    labels = [('RESEARCH', '科研'), ('NOTES', '笔记'), ('BLOG', '随笔'), ('AFTER HOURS', '科研之外'), ('NAGATO', '长门')]
    icons = ['✧', '≡', '▤', '◇', '❀']
    for i, (en, cn) in enumerate(labels):
        body = [f'<path d="M12 45 H168" class="line" stroke-width="2"/>',
                '<circle cx="167" cy="15" r="2" class="accent pulse"/>',
                text(12, 31, f'0{i+1}', 14, 'muted'),
                text(40, 31, icons[i], 19, 'muted'),
                text(65, 31, cn if lang == 'cn' else en, 14, bold=True)]
        svg(f'nav-{i+1}-{lang}.svg', 180, 54, cn if lang == 'cn' else en, body)


def project_card(project, lang, mobile):
    cn = lang == 'cn'
    w, h = (420, 530) if mobile else (900, 360)
    name = 'AdsMind' if project == 'adsmind' else 'CatDT'
    number = '01' if project == 'adsmind' else '02'
    story = STORIES[project][lang]
    body = [text(24, 35, number+' / RESEARCH SHOWCASE', 14, 'muted'),
            text(24, 77, name, 34, bold=True),
            text(24, 111, story[1][1], 20, bold=True)]
    # Repository coordinates for AdsMind; a labeled schematic for CatDT.
    x, y = (70, 140) if mobile else (590, 30)
    if project == 'adsmind':
        source = (ROOT/'assets/pt111-example.svg').read_text(encoding='utf-8')
        defs = re.search(r'<defs>.*?</defs>', source, re.S).group(0)
        circles = ''.join(re.findall(r'<circle [^>]+/>', source))
        body += [defs, f'<ellipse cx="{x+135}" cy="{y+75}" rx="130" ry="110" class="panel" opacity=".65"/>',
                 f'<g transform="translate({x-110} {y-31}) scale(.54)">{circles}</g>',
                 f'<circle cx="{x+260}" cy="{y+10}" r="4" class="accent pulse"/>',
                 text(x+12, y+168, 'Pt(111) · repository coordinates', 13, 'muted')]
    else:
        body += [f'<path d="M{x+135} {y+74} L{x+45} {y+26} M{x+135} {y+74} L{x+225} {y+26} M{x+135} {y+74} L{x+45} {y+122} M{x+135} {y+74} L{x+225} {y+122}" class="line" stroke-width="3"/>']
        for nx,ny,label in [(135,74,'Hub'),(45,26,'Surface'),(225,26,'Pathway'),(45,122,'Memory'),(225,122,'Kinetics')]:
            body += [f'<rect x="{x+nx-40}" y="{y+ny-16}" width="80" height="32" rx="12" class="panel"/>',text(x+nx-31,y+ny+5,label,13,'muted')]
        body += [f'<circle cx="{x+135}" cy="{y+74}" r="23" class="line pulse" stroke-width="2"/>',
                 text(x+35,y+168,'Agent coordination · schematic',13,'muted')]
    my = (['主导闭环架构开发', '构建基准与跨后端评估'] if cn else ['Led closed-loop architecture', 'Benchmarks & cross-backend evaluation']) if project == 'adsmind' else (['共同作者 · 参与 CatDT 研究'] if cn else ['Co-author · CatDT research contributor'])
    sy = 355 if mobile else 167
    body += [f'<rect x="20" y="{sy-24}" width="{w-40 if mobile else 540}" height="{96 if mobile else 78}" rx="14" class="panel"/>',
             text(34,sy+6,story[2][1],36,bold=True)]
    if mobile:
        body += [text(34,sy+34+j*22,line,14,'muted') for j,line in enumerate(story[2][2])]
    else:
        body += [text(34,sy+34,' · '.join(story[2][2]),14,'muted')]
    cy = 457 if mobile else 277
    body += [text(24,cy,'我的贡献 / '+my[0] if cn else 'MY WORK / '+my[0],16,bold=True)]
    if len(my)>1:body += [text(24,cy+25,my[1],16,'muted')]
    body += [text(24,h-15,'arXiv:2606.19152v1 · reported results' if project=='adsmind' else 'arXiv:2606.05050v2 · reported results',13,'muted')]
    svg(f'{project}-showcase-{lang}{"-mobile" if mobile else ""}.svg',w,h,name+' · reported results and contribution',body)


def bookshelf(lang, mobile):
    w, h = (420, 610) if mobile else (900, 290)
    body = [text(24, 40, 'CHEMISTRY ARCHIVE · 2021' if lang == 'en' else '化学随笔书架 · 2021', 24, bold=True)]
    for i, post in enumerate(FACTS['posts']):
        x, y, bw, bh = (24, 64+i*164, 372, 146) if mobile else (24+i*290, 66, 270, 160)
        body += [f'<rect x="{x+4}" y="{y+6}" width="{bw}" height="{bh}" rx="12" fill="#A4ABD6" opacity=".25"/>',
                 f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="12" class="panel"/>',
                 f'<path d="M{x+15} {y+8} V{y+bh-8}" class="line" stroke-width="5"/>',
                 f'<path d="M{x+bw-45} {y} v36 l-10 -8 -10 8 V{y}" fill="#A4ABD6"/>',
                 text(x+30, y+35, f'VOL. 0{i+1}', 16, 'muted'),
                 text(x+30, y+79, post['title'], 19, bold=True),
                 text(x+30, y+113, post['date'], 16, 'muted')]
    body += [text(24, h-22, 'Selected Chinese study posts · original cover artwork' if lang == 'en' else '中文学习随笔选读 · 封面为原创装饰图', 14, 'muted')]
    svg(f'blog-bookshelf-{lang}{"-mobile" if mobile else ""}.svg', w, h, 'Chemistry blog archive', body)


def structure():
    lines = (ROOT / 'assets/pt111-example.xyz').read_text(encoding='utf-8').splitlines()
    atoms = [line.split() for line in lines[2:] if line.strip()]
    assert len(atoms) == int(lines[0]) == 54 and all(a[0] == 'Pt' for a in atoms)
    points = []
    for atom in atoms:
        x, y, z = map(float, atom[1:4])
        points.append((.8*x-.4*y, .25*x+.3*y-.8*z))
    xmin, xmax = min(x for x,y in points), max(x for x,y in points)
    ymin, ymax = min(y for x,y in points), max(y for x,y in points)
    scale = min(600/(xmax-xmin), 220/(ymax-ymin))
    body = [text(24, 40, 'Pt(111) · 54 Pt · repository coordinates', 23, bold=True),
            '<defs><radialGradient id="pt" cx="30%" cy="25%"><stop stop-color="#fff"/><stop offset=".45" stop-color="#A4ABD6"/><stop offset="1" stop-color="#514C63"/></radialGradient></defs>']
    for x,y in sorted(points, key=lambda p:p[1]):
        cx, cy = 450+(x-(xmin+xmax)/2)*scale, 185+(y-(ymin+ymax)/2)*scale
        body.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="13" fill="url(#pt)" stroke="#514C63" stroke-width="1"/>')
    body += [text(24, 346, 'Coordinate projection · not a new optimization result', 17, 'muted')]
    svg('pt111-example.svg', 900, 370, 'Projection of 54 Pt atoms from the AdsMind repository', body)


def picture(stem, lang, alt):
    return f'<picture><source media="(max-width: 600px)" srcset="./assets/{stem}-{lang}-mobile.svg" /><img src="./assets/{stem}-{lang}.svg" width="100%" alt="{alt}" /></picture>'


def research(lang):
    cn = lang == 'cn'
    heading = '成果入口 · 论文、代码与公开样例' if cn else 'Research entry points · papers, code & public examples'
    columns = '| 项目 | 论文 | 代码 | 数据 / 样例 | 我的工作 |' if cn else '| Project | Paper | Code | Data / examples | My work |'
    rows = [columns, '|:--|:--|:--|:--|:--|']
    for p in FACTS['projects']:
        code = f"[GitHub]({p['code']})" if p['code'] else '—'
        examples = f"[{'公开目录' if cn else 'Public directory'}]({p['examples']})" if p['examples'] else '—'
        work = f"[{'项目介绍' if cn else 'Project overview'}](#{p['anchor']})" if p['anchor'] else f"[{'论文署名' if cn else 'Paper authors'}]({p['paper']})"
        rows.append(f"| **{p['name']}** | [arXiv]({p['paper']}) | {code} | {examples} | {work} |")
    base = FACTS['catdt_example_base']
    caption = '公开仓库案例 · 点击展开' if cn else 'Public repository examples · click to open'
    explanation = ('AdsMind：按已提交的 54 个 Pt 原子坐标生成投影，属于公开输入结构展示，不是本轮优化结果。' if cn else 'AdsMind: a projection of 54 committed Pt coordinates, showing a public input structure rather than a new optimization result.')
    catdt = ('CatDT：以下图片来自仓库中的 AdsorbDiff 模块示例，分别为初始结构与采样后结构；不是本轮运行，也不代表完整 CatDT 端到端验证。' if cn else 'CatDT: committed AdsorbDiff module example images, showing the initial and diffused structures. These are not a new run or an end-to-end validation of CatDT.')
    return '\n\n'.join([
        f'<a id="research-entry-points"></a>\n\n### 🗂️ {heading}', '\n'.join(rows),
        f'<details>\n<summary><b>🔬 {caption}</b></summary>',
        f'<a href="{FACTS["pt_source"]}"><img src="./assets/pt111-example.svg" width="100%" alt="54 Pt atoms · repository coordinate projection" /></a>',
        f'{explanation} [Source]({FACTS["pt_source"]}) · [XYZ](./assets/pt111-example.xyz)',
        f'<a href="{FACTS["catdt_example_source"]}"><img src="{base}initial_structure.png" width="46%" alt="AdsorbDiff Cu111_CO · initial structure" /> <img src="{base}diffused_structure.png" width="46%" alt="AdsorbDiff Cu111_CO · diffused structure" /></a>',
        f'{catdt} [Source]({FACTS["catdt_example_source"]})', '</details>',
        f"[💬 {'公开科研交流' if cn else 'Ask a public research question'}](https://github.com/NagatoBigSeven/NagatoBigSeven/issues/new?template=research-question.yml) · [✉️ {'私密合作联系' if cn else 'Private collaboration'}](mailto:zzmhkust@gmail.com)"
    ])


def blog(lang):
    cn = lang == 'cn'
    return '\n\n'.join([
        '<a id="blog-bookshelf"></a>',
        '### 📖 化学随笔书架' if cn else '### 📖 Chemistry blog bookshelf',
        '<p align="center">'+ '\n'.join(f'<a href="{p["url"]}" title="{p["title"]}"><img src="./assets/blog-cover-{i+1}.svg" width="260" alt="{p["title"]} · {p["date"]}" /></a>' for i,p in enumerate(FACTS['posts']))+'</p>',
        '\n'.join(f"- [{p['title']}]({p['url']}) · {p['date']}" for p in FACTS['posts']),
        ('2021 年中文学习随笔选读；封面为原创装饰图，不是原文缩略图。' if cn else 'Selected Chinese study notes from 2021; the decorative covers are original artwork, not article thumbnails.'),
        f"[{'浏览博客归档' if cn else 'Browse the blog archive'}]({FACTS['blog']})"
    ])


def update(path, marker, block, anchor):
    content = path.read_text(encoding='utf-8')
    wrapped = f'<!-- {marker}:START -->\n{block}\n<!-- {marker}:END -->'
    pattern = rf'<!-- {marker}:START -->.*?<!-- {marker}:END -->'
    if re.search(pattern, content, flags=re.S):
        content = re.sub(pattern, lambda _: wrapped, content, flags=re.S)
    else:
        assert content.count(anchor) == 1
        content = content.replace(anchor, anchor+'\n\n'+wrapped) if marker == 'SHOWROOM' else content.replace(anchor, wrapped+'\n\n'+anchor)
    path.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    structure()
    book_covers()
    for lang, name in [('en', 'README.md'), ('cn', 'README_CN.md')]:
        navigation(lang)
        for mobile in (False, True):
            bookshelf(lang, mobile)
            for project in ['adsmind','catdt']:
                project_card(project, lang, mobile)
        update(ROOT/name, 'SHOWROOM', research(lang), '<!-- PAPERS:END -->')
        update(ROOT/name, 'BLOG-BOOKSHELF', blog(lang), '<a id="geek-after-hours"></a>')
        path = ROOT/name
        content = path.read_text(encoding='utf-8')
        for project in ['adsmind','catdt']:
            pattern = rf'<p align="center"><picture><source media="\(max-width: 600px\)" srcset="\./assets/{project}-(?:story|showcase)-{lang}-mobile.svg" /><img src="\./assets/{project}-(?:story|showcase)-{lang}.svg" width="100%" alt="[^"]*" /></picture></p>'
            content, count = re.subn(pattern, lambda _: '<p align="center">'+picture(project+'-showcase',lang,project+' · reported results, public structure or schematic, and personal contribution')+'</p>', content)
            assert count == 1
            paper = next(p['paper'] for p in FACTS['projects'] if p['anchor']==project)
            buttons = re.search(r'<p>\s*<a href="'+re.escape(paper)+r'"[^>]*><img src="\./assets/badges/project-paper-'+lang+r'.*?</p>',content,re.S)
            assert buttons is not None
            button_block = buttons.group(0)
            end = buttons.end()+2 if content[buttons.end():].startswith('\n\n') else buttons.end()
            content = content[:buttons.start()]+content[end:]
            card = re.search(pattern,content).group(0)
            content = content.replace(card,card+'\n\n'+button_block,1)
        nav = '<p align="center">'+ '\n'.join(f'<a href="#{anchor}"><img src="./assets/nav-{i+1}-{lang}.svg" width="160" alt="0{i+1} · {label}" /></a>' for i,(anchor,label) in enumerate([('-代表项目与开源' if lang=='cn' else '-featured-work--open-source','科研' if lang=='cn' else 'Research'),('-学习笔记' if lang=='cn' else '-study-notes','笔记' if lang=='cn' else 'Notes'),('-化学随笔书架' if lang=='cn' else '-chemistry-blog-bookshelf','随笔' if lang=='cn' else 'Blog'),('-科研之外' if lang=='cn' else '-geek-after-hours','科研之外' if lang=='cn' else 'After hours'),('-角色柜' if lang=='cn' else '-character-cabinet','长门' if lang=='cn' else 'Nagato')]))+'</p>'
        marker = r'<!-- VISUAL-NAV:START -->.*?<!-- VISUAL-NAV:END -->'
        block = '<!-- VISUAL-NAV:START -->\n'+nav+'\n<!-- VISUAL-NAV:END -->'
        if re.search(marker,content,re.S):
            content = re.sub(marker,lambda _:block,content,flags=re.S)
        else:
            anchor = '<p align="center"><a href="#research-milestones">'
            start = content.index(anchor)
            end = content.index('</p>', start)+len('</p>')
            content = content[:end]+'\n\n'+block+content[end:]
        heading = '### 🌸 角色柜' if lang=='cn' else '### 🌸 Character cabinet'
        if heading not in content:
            content = content.replace('<a id="character-cabinet"></a>',heading+'\n\n<a id="character-cabinet"></a>')
        path.write_text(content,encoding='utf-8')
