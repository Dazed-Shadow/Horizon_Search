import sys
import re

def md_to_html(md: str) -> str:
    html = md

    # Blockquote
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # H1-H3
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$',  r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$',   r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Horizontal rule
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

    # Bold + italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*',         r'<em>\1</em>', html)

    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Tables
    def convert_table(m):
        rows = [r.strip() for r in m.group(0).strip().split('\n') if r.strip()]
        out = ['<table>']
        for i, row in enumerate(rows):
            if re.match(r'^[\|\s\-:]+$', row):
                continue
            cells = [c.strip() for c in row.strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            tr = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            out.append(tr)
        out.append('</table>')
        return '\n'.join(out)

    html = re.sub(r'(\|.+\|\n)+', convert_table, html)

    # Unordered lists
    def convert_ul(m):
        items = re.findall(r'^[-*] (.+)$', m.group(0), re.MULTILINE)
        return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
    html = re.sub(r'(^[-*] .+\n?)+', convert_ul, html, flags=re.MULTILINE)

    # Ordered lists
    def convert_ol(m):
        items = re.findall(r'^\d+\. (.+)$', m.group(0), re.MULTILINE)
        return '<ol>' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'
    html = re.sub(r'(^\d+\. .+\n?)+', convert_ol, html, flags=re.MULTILINE)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Paragraphs (lines not already wrapped in a tag)
    lines = html.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('<'):
            result.append(f'<p>{stripped}</p>')
        else:
            result.append(line)
    html = '\n'.join(result)

    return html


def main():
    md_path = sys.argv[1]
    pdf_path = sys.argv[2]

    with open(md_path, 'r') as f:
        md = f.read()

    body = md_to_html(md)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a202c;
    padding: 48px 56px;
    max-width: 820px;
    margin: 0 auto;
  }}

  h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: #1e1b4b;
    border-bottom: 3px solid #4338ca;
    padding-bottom: 10px;
    margin: 0 0 24px;
  }}

  h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: #1e1b4b;
    margin: 32px 0 12px;
    padding-left: 10px;
    border-left: 4px solid #4338ca;
  }}

  h3 {{
    font-size: 12pt;
    font-weight: 600;
    color: #3730a3;
    margin: 22px 0 8px;
  }}

  p {{ margin: 8px 0; }}

  blockquote {{
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 12px 16px;
    margin: 16px 0;
    font-size: 10pt;
    color: #78350f;
    border-radius: 0 6px 6px 0;
  }}

  hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 28px 0;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 10pt;
  }}

  th {{
    background: #1e1b4b;
    color: white;
    padding: 9px 12px;
    text-align: left;
    font-weight: 600;
  }}

  td {{
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
  }}

  tr:nth-child(even) td {{ background: #f8fafc; }}

  ul, ol {{
    margin: 10px 0 10px 22px;
    padding: 0;
  }}

  li {{ margin: 4px 0; }}

  code {{
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 1px 5px;
    font-family: 'Courier New', monospace;
    font-size: 9.5pt;
    color: #0f172a;
  }}

  a {{ color: #4338ca; }}

  strong {{ font-weight: 600; }}

  .footer {{
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #e2e8f0;
    font-size: 9pt;
    color: #94a3b8;
    text-align: center;
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""

    from weasyprint import HTML
    HTML(string=full_html).write_pdf(pdf_path)
    print(f"PDF saved: {pdf_path}")


if __name__ == '__main__':
    main()
