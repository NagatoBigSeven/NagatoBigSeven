"""Polish README-only visual assets; retain facts, links and approved character art."""
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path
from build_showcase import DATES, text
from build_showroom import ROOT, svg


def divider(number):
    body = ['<path d="M20 27 H350 M550 27 H880" class="line" stroke-width="1.5"/>',
            '<path d="M420 27 q12-25 30 0 q18-25 30 0 q-18 25-30 0 q-18 25-30 0" fill="#A4ABD6" opacity=".35"/>',
            text(437,34,f'0{number}',19,'muted',True),
            '<circle cx="386" cy="27" r="3" fill="#C39B65"/><circle cx="514" cy="27" r="3" fill="#A83F55"/>']
    svg(f'chapter-divider-{number}.svg',900,54,f'Chapter {number}',body)


def timeline(lang,mobile):
    cn=lang=='cn';w,h=(420,660) if mobile else (900,350)
    headings=['Planner–Critic PR','社区报告' if cn else 'Community report','CatDT v1','AdsMind v1','CatDT v2']
    types=['上游 PR 已合并','预印本','首次提交','首次提交','修订预印本'] if cn else ['Merged upstream','Preprint','First submission','First submission','Revised preprint']
    body=[text(28,42,'科研里程碑 · 从原型到预印本' if cn else 'RESEARCH SCROLL · prototype to preprint',22,bold=True)]
    body+=['<rect x="16" y="64" width="868" height="205" rx="18" class="panel"/>','<rect x="12" y="64" width="14" height="205" rx="7" fill="#C39B65" opacity=".6"/>','<rect x="874" y="64" width="14" height="205" rx="7" fill="#C39B65" opacity=".6"/>','<path d="M55 146 H845" class="line" stroke-width="3"/>'] if not mobile else ['<rect x="20" y="65" width="380" height="510" rx="18" class="panel"/>','<path d="M44 92 V550" class="line" stroke-width="3"/>','<path d="M30 65 H390 M30 575 H390" stroke="#C39B65" stroke-width="5" stroke-linecap="round" opacity=".65"/>']
    for i in range(5):
        x,y=(44,110+i*95) if mobile else (80+i*180,146)
        tx,ty=(70,y-8) if mobile else (x-42,110)
        body += [f'<circle cx="{x}" cy="{y}" r="8" class="accent"/>',
                 f'<circle cx="{x}" cy="{y}" r="14" class="line {"pulse" if i==4 else ""}" stroke-width="1.5"/>',
                 text(tx,ty,DATES[i],17 if mobile else 14,'muted',True),
                 text(tx,ty+30 if mobile else 188,headings[i],19 if mobile else 16,bold=True),
                 text(tx,ty+55 if mobile else 216,types[i],16 if mobile else 14,'muted')]
    body += [text(28,h-47,'UTC · 节点来源链接见下方' if cn else 'UTC dates · node source links below',16,'muted'),
             text(28,h-22,'预印本版本与软件发布分开标注' if cn else 'Preprint versions are distinct from software releases',14,'muted')]
    svg(f'research-milestones-{lang}{"-mobile" if mobile else ""}.svg',w,h,'Verified research milestones',body)


def badges():
    ns={'s':'http://www.w3.org/2000/svg'}
    for p in (ROOT/'assets/badges').glob('*.svg'):
        if p.name=='views-snapshot.svg':continue
        source=p.read_text(encoding='utf-8')
        if p.name.startswith('project-'):
            source=re.sub(r'<style id="badge-theme">.*?</style>','',source,flags=re.S)
            style='<style id="badge-theme">rect{rx:10;stroke-width:1.2}@media(prefers-color-scheme:dark){rect[fill="#ECE9E0"]{fill:#343145}rect[fill="#A4ABD6"]{fill:#484563}text{fill:#FFFFFF}g{stroke:#FFFFFF}}</style>'
            p.write_text(source.replace('</svg>',style+'</svg>'),encoding='utf-8');continue
        # Existing brand logos are retained; labels and destinations stay unchanged.
        root=ET.fromstring(source)
        texts=root.findall('.//s:text',ns)
        if len(texts)!=2:continue
        label,value=[t.text or '' for t in texts]
        def units(s):return sum(1.8 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)
        lw=round(units(label)*6.6+28);vw=round(units(value)*6.6+16);width=lw+vw
        image=root.find('.//s:image',ns)
        logo=''
        if image is not None:
            href=image.get('href') or image.get('{http://www.w3.org/1999/xlink}href')
            if href:logo=f'<image x="7" y="3" width="14" height="14" href="{escape(href,quote=True)}"/>'
        style='<style>.label{fill:#514C63}.value{fill:#ECE9E0}.value-text{fill:#353247}@media(prefers-color-scheme:dark){.label{fill:#343145}.value{fill:#484563}.value-text{fill:#FFFFFF}}</style>'
        result=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" viewBox="0 0 {width} 20" role="img"><title>{escape(label+": "+value)}</title>{style}<defs><clipPath id="round"><rect width="{width}" height="20" rx="6"/></clipPath></defs><g clip-path="url(#round)"><rect width="{lw}" height="20" class="label"/><rect x="{lw}" width="{vw}" height="20" class="value"/></g>{logo}<text x="24" y="14" fill="#FFFFFF" font-family="Segoe UI,Microsoft YaHei,Arial,sans-serif" font-size="11">{escape(label)}</text><text x="{lw+8}" y="14" class="value-text" font-family="Segoe UI,Microsoft YaHei,Arial,sans-serif" font-size="11">{escape(value)}</text></svg>'
        p.write_text(result,encoding='utf-8')


def chapters(lang):
    p=ROOT/('README_CN.md' if lang=='cn' else 'README.md');content=p.read_text(encoding='utf-8')
    headings=['## ✨ 代表项目与开源','## 📚 学习笔记','### 📖 化学随笔书架','## 🎮 科研之外','### 🌸 角色柜'] if lang=='cn' else ['## ✨ Featured Work & Open Source','## 📚 Study Notes','### 📖 Chemistry blog bookshelf','## 🎮 Geek After Hours','### 🌸 Character cabinet']
    for i,heading in enumerate(headings):
        image=f'<p align="center"><img src="./assets/chapter-divider-{i+1}.svg" width="100%" alt="Chapter 0{i+1}" /></p>'
        assert content.count(heading)==1
        if image+'\n\n'+heading not in content:content=content.replace(heading,image+'\n\n'+heading)
    # Keep individually clickable source links in chronological order.
    old=r'\[2026-01-28 · (?:Merged Planner–Critic PR|[^\]]+)\]\(https://github.com/schwallergroup/llm_adsorbate/pull/1\).*?(?=\n\n)'
    labels=['上游 Planner–Critic PR' if lang=='cn' else 'Merged Planner–Critic PR','社区报告' if lang=='cn' else 'Community report','CatDT v1','AdsMind v1','CatDT v2']
    urls=['https://github.com/schwallergroup/llm_adsorbate/pull/1','https://arxiv.org/abs/2605.03205v1','https://arxiv.org/abs/2606.05050v1','https://arxiv.org/abs/2606.19152v1','https://arxiv.org/abs/2606.05050v2']
    content,count=re.subn(old,lambda _: ' · '.join(f'[{date} · {label}]({url})' for date,label,url in zip(DATES,labels,urls)),content,flags=re.S)
    assert count==1
    p.write_text(content,encoding='utf-8')


if __name__=='__main__':
    subprocess.run([sys.executable,str(ROOT/'.github/scripts/build_showroom.py')],check=True)
    for i in range(1,6):divider(i)
    badges()
    for lang in ['en','cn']:
        for mobile in [False,True]:timeline(lang,mobile)
        chapters(lang)
