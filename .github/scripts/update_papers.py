import urllib.request
import xml.etree.ElementTree as ET
import re
import ssl
import sys

# 绕过本地某些环境可能存在的 SSL 证书问题（在 GitHub Actions Ubuntu 中其实不需要，但为了保险起见保留）
ssl._create_default_https_context = ssl._create_unverified_context

def parse_existing(content):
    """解析现有的 README，提取已经手动填写的论文状态（例如 Under review）"""
    pattern = r'<!-- PAPERS:START -->(.*?)<!-- PAPERS:END -->'
    match = re.search(pattern, content, flags=re.DOTALL)
    statuses = {}
    if match:
        table_lines = match.group(1).strip().split('\n')
        if len(table_lines) > 2:
            for line in table_lines[2:]:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    status_col = parts[3]
                    # 提取 arXiv ID 作为唯一标识符
                    m = re.search(r'arXiv:(\d{4}\.\d{5})', status_col)
                    if m:
                        # 提取链接前面的纯状态文本（以间隔号 · 为界）
                        pure_status = status_col.split('·')[0].strip() if '·' in status_col else ''
                        # 排除没写状态只写了链接的情况
                        if pure_status and "arXiv:" not in pure_status:
                            statuses[m.group(1)] = pure_status
    return statuses

def build_table(papers, existing_statuses, is_cn=False):
    """根据抓取到的论文列表和保存的状态重新构建 Markdown 表格"""
    lines = []
    header_title = "论文标题" if is_cn else "Paper"
    header_status = "状态" if is_cn else "Status"
    lines.append(f"| # | {header_title} | {header_status} |")
    lines.append("|:-:|:------|:------|")
    
    for idx, p in enumerate(papers, 1):
        title = p['title']
        # 为了美观，将冒号前面的主标题加粗
        if ':' in title:
            parts = title.split(':', 1)
            title_md = f"**{parts[0].strip()}:** {parts[1].strip()}"
        else:
            title_md = f"**{title}**"
        
        arxiv_id = p['arxiv_id']
        pure_status = existing_statuses.get(arxiv_id, "")
        link_md = f"[arXiv:{arxiv_id}](https://arxiv.org/abs/{arxiv_id})"
        
        # 组装状态列
        if pure_status:
            status_md = f"{pure_status} · {link_md}"
        else:
            status_md = link_md
            
        lines.append(f"| {idx} | {title_md} | {status_md} |")
    return "\n".join(lines) + "\n"

def update_file(filepath, is_cn=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 提取旧状态
    existing_statuses = parse_existing(content)
    
    # 2. 查询 arXiv API
    url = 'http://export.arxiv.org/api/query?search_query=au:%22Zongmin%20Zhang%22&sortBy=submittedDate&sortOrder=descending'
    # arXiv API 官方建议使用描述性 User-Agent
    req = urllib.request.Request(url, headers={'User-Agent': 'NagatoBigSeven-GithubProfile/1.0 (mailto:zzmhkust@gmail.com)'})
    with urllib.request.urlopen(req, timeout=10) as response:
        root = ET.fromstring(response.read())
    
    papers = []
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    # 学术领域的关键词过滤，防止同名学者（如做音频、图像加密的 Zongmin Zhang）的论文混入
    keywords = ["catalyst", "adsorption", "chemistry", "materials", "language model", "agent", "molecule", "dft", "physical"]
    
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
        summary = entry.find('atom:summary', ns).text.replace('\n', ' ').strip().lower()
        
        # 关键词匹配，确保是该作者研究领域的论文
        text_to_check = title.lower() + " " + summary
        if not any(kw in text_to_check for kw in keywords):
            continue
            
        id_url = entry.find('atom:id', ns).text
        arxiv_id = id_url.split('/abs/')[-1].split('v')[0]
        papers.append({'title': title, 'arxiv_id': arxiv_id, 'url': id_url})
    
    # 如果没查到数据（可能 API 故障），不覆写文件
    if not papers:
        print(f"No papers found for {filepath}, skipping.")
        return

    # 3. 构建新表格
    table_md = "\n" + build_table(papers, existing_statuses, is_cn)
    
    # 4. 替换内容
    pattern = r'(<!-- PAPERS:START -->).*?(<!-- PAPERS:END -->)'
    new_content = re.sub(pattern, lambda m: f"{m.group(1)}{table_md}{m.group(2)}", content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    try:
        update_file('README.md', False)
        update_file('README_CN.md', True)
        print("Papers updated successfully.")
    except Exception as e:
        print(f"Error updating papers: {e}")
        sys.exit(0)
