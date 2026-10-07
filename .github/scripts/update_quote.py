import urllib.request
import json
import re
import sys

def fetch_hitokoto():
    url = "https://v1.hitokoto.cn/?c=d&c=i&c=k"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        quote = data.get('hitokoto', '')
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError('Hitokoto returned no quote; keeping existing content')
        from_who = data.get('from_who', '')
        from_source = data.get('from', '')
        
        author_part = []
        if from_who:
            author_part.append(from_who)
        if from_source:
            author_part.append(f"《{from_source}》")
            
        author_str = " ".join(author_part)
        if author_str:
            return f"> “{quote}”  \n> —— *{author_str}*"
        return f"> “{quote}”"

def fetch_en_quote():
    # Use ZenQuotes for English README
    url = "https://zenquotes.io/api/random"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise ValueError('ZenQuotes returned no quote; keeping existing content')
        quote, author = data[0].get('q'), data[0].get('a')
        if not isinstance(quote, str) or not quote.strip() or not isinstance(author, str) or not author.strip():
            raise ValueError('ZenQuotes returned incomplete attribution')
        return f"> “{quote}”  \n> —— *{author}*"

def update_readme(file_path, quote_md):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(<!-- QUOTE:START -->\n).*?(\n<!-- QUOTE:END -->)'
    new_content = re.sub(pattern, lambda m: f"{m.group(1)}{quote_md}{m.group(2)}", content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    try:
        cn_quote_md = fetch_hitokoto()
        en_quote_md = fetch_en_quote()
        
        update_readme('README.md', en_quote_md)
        update_readme('README_CN.md', cn_quote_md)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
