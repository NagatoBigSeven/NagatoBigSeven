"""Build bilingual README artwork. Run locally with Pillow; no network inputs."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[2] / 'assets'
FONT_DIR = Path('C:/Windows/Fonts')
STYLE = '''<style>
.bg{fill:#ECE9E0}.panel{fill:#fff}.ink{fill:#353247}.muted{fill:#514C63}
.accent{fill:#A4ABD6}.line{stroke:#A4ABD6;fill:none}.petal{fill:#A4ABD6;opacity:.25}
@media(prefers-color-scheme:dark){.bg{fill:#22212D}.panel{fill:#302E40}.ink{fill:#fff}.muted{fill:#D8D5E5}}
.pulse{animation:pulse 3s ease-in-out infinite}@keyframes pulse{50%{opacity:.4}}
@media(prefers-reduced-motion:reduce){.pulse{animation:none}}
text{font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif}
</style>'''


def text(x, y, value, size=20, cls='ink', bold=False):
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>'


def svg(name, w, h, title, body):
    ASSETS.joinpath(name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
        f'<title>{escape(title)}</title>{STYLE}<rect width="{w}" height="{h}" rx="24" class="bg"/>'
        f'<path d="M{w-78} 12 Q{w-28} 40 {w-38} 82 Q{w-94} 65 {w-78} 12" class="petal"/>'
        + ''.join(body) + '</svg>', encoding='utf-8')


STORIES = {
 'adsmind': {
  'en': [('PROBLEM', 'Where should it bind?', ['Many adsorption configurations.', 'Trial-and-error search is costly.']),
         ('METHOD', 'Propose → relax → verify', ['LLM proposals + MLFF feedback.', 'Revise invalid configurations.']),
         ('RESULT', '100% / 98.8%', ['AA20 / OCD-GMAE62 success.', '≈14× fewer MLFF relaxations.'])],
  'cn': [('问题', '吸附物应放在哪里？', ['候选吸附构型多，', '反复试错的搜索成本高。']),
         ('方法', '提议 → 松弛 → 验证', ['LLM 提议结合 MLFF 反馈，', '修正不符合约束的构型。']),
         ('结果', '100% / 98.8%', ['AA20 / OCD-GMAE62 成功率，', '松弛预算：约为枚举法的 1/14。'])]},
 'catdt': {
  'en': [('PROBLEM', 'Connect the workflow', ['Surface, pathways, microkinetics:', 'coordinate scientific tools.']),
         ('METHOD', 'A multi-agent digital twin', ['Specialist agents + memory.', 'Learn from workflow feedback.']),
         ('RESULT', '41% → 84%', ['Barrier-calculation success.', 'Evaluated on 600 surfaces.'])],
  'cn': [('问题', '如何串联催化研究？', ['从表面到反应路径与微观动力学，', '协调多种科学工具。']),
         ('方法', '多智能体数字孪生', ['专用智能体协作，', '结合记忆与工作流反馈自演化。']),
         ('结果', '41% → 84%', ['能垒计算成功率提升，', '在 600 个催化表面上评估。'])]}}


def story(project, lang, mobile):
    w, h = (420, 680) if mobile else (900, 350)
    title = 'AdsMind' if project == 'adsmind' else 'CatDT'
    body = [text(24, 42, title + (' · RESEARCH STORY' if lang == 'en' else ' · 科研叙事'), 25, bold=True)]
    for i, (label, headline, lines) in enumerate(STORIES[project][lang]):
        x, y, pw, ph = (20, 68+i*180, 380, 160) if mobile else (20+i*294, 70, 272, 208)
        body += [f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" rx="16" class="panel"/>',
                 f'<circle cx="{x+26}" cy="{y+27}" r="6" class="accent pulse"/>',
                 text(x+42, y+33, f'0{i+1} / {label}', 16, cls='muted', bold=True),
                 text(x+16, y+75, headline, 24 if mobile else (22 if lang == 'cn' else 19), bold=True)]
        body += [text(x+16, y+108+j*27, line, 19 if mobile else 16, 'muted') for j, line in enumerate(lines)]
        if not mobile:
            body += [f'<path d="M{x+18} {y+176} H{x+pw-18}" class="line" stroke-width="2"/>']
    foot = ('Preprint results · workflow success, not optimality' if lang == 'en' else '预印本报告结果 · 工作流成功率不等于全局最优')
    if project == 'catdt':
        foot = 'Preprint v2 · memory-augmented reinforcement' if lang == 'en' else '预印本 v2 · 结合记忆的强化循环'
    body += [text(22, h-40, foot, 15 if mobile else 17, 'muted'),
             text(22, h-16, 'arXiv:2606.19152v1' if project == 'adsmind' else 'arXiv:2606.05050v2', 15, 'muted')]
    svg(f'{project}-story-{lang}{"-mobile" if mobile else ""}.svg', w, h, title, body)


DATES = ['2026-01-28', '2026-05-04', '2026-06-03', '2026-06-17', '2026-07-09']
def timeline(lang, mobile):
    w, h = (420, 640) if mobile else (900, 400)
    headings = ['Planner–Critic PR', 'Community report', 'CatDT v1', 'AdsMind v1', 'CatDT v2'] if lang == 'en' else ['Planner–Critic PR', '社区报告', 'CatDT v1', 'AdsMind v1', 'CatDT v2']
    types = ['Merged upstream', 'Preprint', 'First submission', 'First submission', 'Revised preprint'] if lang == 'en' else ['上游 PR 已合并', '预印本', '首次提交', '首次提交', '修订预印本']
    body = [text(24, 43, 'FROM PROTOTYPE TO PREPRINT' if lang == 'en' else '从原型贡献到科研预印本', 23, bold=True)]
    body += [f'<path d="M40 95 V{h-90}" class="line" stroke-width="3"/>'] if mobile else ['<path d="M72 152 H828" class="line" stroke-width="3"/>']
    for i in range(5):
        x, y = (40, 100+i*98) if mobile else (72+i*184, 152)
        body += [f'<circle cx="{x}" cy="{y}" r="10" class="accent"/>']
        tx, ty = (68, y-5) if mobile else (max(22,x-46), y-33)
        body += [text(tx, ty, DATES[i], 18 if mobile else 15, 'muted', True),
                 text(tx, ty+29 if mobile else y+40, headings[i], 20 if mobile else 17, bold=True),
                 text(tx, ty+55 if mobile else y+68, types[i], 17 if mobile else 15, 'muted')]
    body += [text(24,h-48,'Submission dates in UTC · links below' if lang == 'en' else '提交日期按 UTC · 每个节点的证据链接见下方',16,'muted'),
             text(24,h-22,'Preprint versions are not software releases' if lang == 'en' else '预印本版本与软件 Release 分开标注',16,'muted')]
    svg(f'research-milestones-{lang}{"-mobile" if mobile else ""}.svg',w,h,'Verified research milestones',body)


def comic(lang,mobile):
    w,h=(420,430) if mobile else (900,230)
    dialogues = [('AGENT','One more candidate?'),('VERIFIER','Check the constraints.'),('DEVELOPER','Save the provenance.')] if lang=='en' else [('智能体','再试一个候选构型？'),('验证器','先检查物理约束。'),('开发者','记得保存溯源记录。')]
    body=[text(24,38,'ONE MORE CANDIDATE' if lang=='en' else '再试一个候选构型',23,bold=True)]
    for i,(role,line) in enumerate(dialogues):
        x,y,pw=(20,58+i*103,380) if mobile else (20+i*294,62,272)
        body += [f'<rect x="{x}" y="{y}" width="{pw}" height="88" rx="16" class="panel"/>',text(x+16,y+27,role,15,'muted',True),text(x+16,y+62,line,21 if mobile else 18,bold=True)]
    body += [text(24,h-24,'Original vignette · illustrative dialogue' if lang=='en' else '原创开发者小剧场 · 虚构示意对话',16,'muted')]
    svg(f'developer-vignette-{lang}{"-mobile" if mobile else ""}.svg',w,h,'Original developer vignette',body)


def font(size,lang,bold=False):
    return ImageFont.truetype(str(FONT_DIR / ('msyhbd.ttc' if bold else 'msyh.ttc') if lang=='cn' else FONT_DIR / ('segoeuib.ttf' if bold else 'segoeui.ttf')),size)


def animation(lang,mobile):
    w,h=(420,430) if mobile else (900,320)
    phases=['Propose candidates','Relax with MLFF','Check physical constraints','Reject → revise → retry'] if lang=='en' else ['提出候选构型','使用 MLFF 松弛','检查物理约束','拒绝 → 修正 → 重试']
    frames=[]
    for phase in range(4):
      for step in range(4):
        im=Image.new('RGB',(w,h),'#ECE9E0');d=ImageDraw.Draw(im)
        d.text((20,15),'AdsMind / CLOSED LOOP' if lang=='en' else 'AdsMind / 自纠错闭环',font=font(23,lang,True),fill='#353247')
        d.rounded_rectangle((20,60,w-20,h-60),radius=20,fill='white')
        sx=38;sy=130 if not mobile else 178; spacing=(w-100)/7
        for row in range(2):
          for col in range(8):
            x=sx+col*spacing;y=sy+row*24
            d.ellipse((x-7,y-7,x+7,y+7),fill='#A4ABD6',outline='#514C63')
        positions=[(w*.30,sy-44),(w*.66,sy-56)]
        for i,(x,y) in enumerate(positions):
          if phase==1:y+=step*3
          if phase==3 and i==0:x+=step*5
          d.line((x,y,x+18,y-14),fill='#514C63',width=3)
          d.ellipse((x-9,y-9,x+9,y+9),fill='#C75165')
          d.ellipse((x+11,y-21,x+25,y-7),fill='#C5AA7F')
          if phase==2:d.ellipse((x-15,y-15,x+15,y+15),outline='#514C63' if i else '#C75165',width=3)
        label_y=205 if not mobile else 255
        d.text((38,label_y),phases[phase],font=font(21,lang,True),fill='#353247')
        footer='Conceptual animation; not a recorded run' if lang=='en' else '概念动画 · 非实验录像或实测耗时'
        d.text((20,h-34),footer,font=font(16,lang),fill='#514C63')
        for i in range(4):
          x=38+i*35;d.ellipse((x, h-91,x+12,h-79),fill='#353247' if i==phase else '#A4ABD6')
        frames.append(im)
    frames[0].save(ASSETS/f'adsmind-loop-{lang}{"-mobile" if mobile else ""}.gif',save_all=True,append_images=frames[1:],duration=450,loop=0,optimize=True)


if __name__=='__main__':
    for lang in ['en','cn']:
        for mobile in [False,True]:
            for project in STORIES:story(project,lang,mobile)
            timeline(lang,mobile)
            comic(lang,mobile)
            animation(lang,mobile)
    print('Built 20 bilingual desktop/mobile showcase assets.')
