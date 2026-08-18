import subprocess
import os
from markdown_it import MarkdownIt

def generate_pdf():
    md_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\PROJECT_JOURNEY_AND_ARCHITECTURE.md"
    html_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\PROJECT_JOURNEY_AND_ARCHITECTURE.html"
    pdf_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\PROJECT_JOURNEY_AND_ARCHITECTURE.pdf"

    with open(md_file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Enable table parsing without linkify dependency
    md = MarkdownIt("commonmark", {"breaks": True, "html": True}).enable("table")
    html_content = md.render(md_text)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Marathi RAG Tutor — Project Journey & Architecture</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 16mm 14mm 16mm 14mm;
        }}
        
        body {{
            font-family: 'Poppins', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1a1a2e;
            background: #ffffff;
            line-height: 1.6;
            font-size: 10pt;
            margin: 0;
            padding: 0;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Poppins', 'Noto Sans Devanagari', sans-serif;
            color: #0f172a;
            font-weight: 700;
            page-break-after: avoid;
        }}

        h1 {{
            font-size: 20pt;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 8px;
            margin-top: 0;
            margin-bottom: 16px;
            color: #1e3a8a;
        }}

        h2 {{
            font-size: 13.5pt;
            border-bottom: 1.5px solid #e2e8f0;
            padding-bottom: 6px;
            margin-top: 22px;
            margin-bottom: 10px;
            color: #1e40af;
        }}

        h3 {{
            font-size: 11pt;
            margin-top: 16px;
            margin-bottom: 6px;
            color: #0f172a;
        }}

        p {{
            margin-top: 0;
            margin-bottom: 10px;
        }}

        strong {{
            color: #0f172a;
            font-weight: 600;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }}

        th, td {{
            padding: 9px 12px;
            border: 1px solid #cbd5e1;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 700;
            border-bottom: 2px solid #94a3b8;
        }}

        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}

        code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 8.8pt;
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            color: #0284c7;
            border: 1px solid #e2e8f0;
        }}

        pre {{
            background: #0f172a;
            color: #f8fafc;
            padding: 14px 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 8.5pt;
            line-height: 1.45;
            margin: 12px 0 16px 0;
            page-break-inside: avoid;
        }}

        pre code {{
            background: transparent;
            color: #f8fafc;
            padding: 0;
            border: none;
        }}

        blockquote {{
            margin: 12px 0;
            padding: 10px 16px;
            background: #f0f9ff;
            border-left: 4px solid #0284c7;
            color: #0369a1;
            border-radius: 0 6px 6px 0;
        }}

        ul, ol {{
            margin-top: 0;
            margin-bottom: 12px;
            padding-left: 22px;
        }}

        li {{
            margin-bottom: 4px;
        }}

        hr {{
            border: none;
            height: 1px;
            background: #e2e8f0;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    browser_exe = chrome_path if os.path.exists(chrome_path) else edge_path
    
    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_file_path}",
        html_file_path
    ]
    
    subprocess.run(cmd, capture_output=True, text=True)
    print(f"SUCCESS: Generated PDF at {pdf_file_path} (Size: {os.path.getsize(pdf_file_path)} bytes)")

if __name__ == "__main__":
    generate_pdf()
