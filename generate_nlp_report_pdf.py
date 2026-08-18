import subprocess
import os
from markdown_it import MarkdownIt

def generate_academic_pdf():
    md_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\NLP_PROJECT_REPORT.md"
    html_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\NLP_PROJECT_REPORT.html"
    pdf_file_path = r"c:\Users\USER\Desktop\NLP\marathi-rag\NLP_PROJECT_REPORT.pdf"

    with open(md_file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    md = MarkdownIt("commonmark", {"breaks": True, "html": True}).enable("table")
    html_content = md.render(md_text)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NLP Technical Project Report</title>
    <style>
        @page {{
            size: A4;
            margin: 18mm 16mm 18mm 16mm;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Noto Sans Devanagari', Arial, sans-serif;
            color: #111827;
            background: #ffffff;
            line-height: 1.6;
            font-size: 10pt;
            margin: 0;
            padding: 0;
        }}

        h1, h2, h3, h4 {{
            color: #0f172a;
            page-break-after: avoid;
        }}

        h1 {{
            font-size: 18pt;
            font-weight: 700;
            border-bottom: 2.5px solid #1e3a8a;
            padding-bottom: 8px;
            margin-top: 0;
            margin-bottom: 12px;
            color: #1e3a8a;
            text-align: center;
            line-height: 1.3;
        }}

        h2 {{
            font-size: 13.5pt;
            font-weight: 700;
            border-bottom: 1.5px solid #cbd5e1;
            padding-bottom: 4px;
            margin-top: 22px;
            margin-bottom: 10px;
            color: #1e40af;
        }}

        h3 {{
            font-size: 11.5pt;
            font-weight: 600;
            margin-top: 16px;
            margin-bottom: 6px;
            color: #1e293b;
        }}

        h4 {{
            font-size: 10.5pt;
            font-weight: 600;
            margin-top: 12px;
            margin-bottom: 4px;
            color: #334155;
        }}

        p {{
            margin-top: 0;
            margin-bottom: 10px;
        }}

        strong {{
            color: #0f172a;
            font-weight: 700;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }}

        th, td {{
            padding: 8px 10px;
            border: 1px solid #94a3b8;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 700;
            border-bottom: 2px solid #475569;
        }}

        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}

        code {{
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 8.8pt;
            background: #f1f5f9;
            padding: 2px 5px;
            border-radius: 3px;
            color: #0f766e;
            border: 1px solid #e2e8f0;
        }}

        pre {{
            background: #0f172a;
            color: #f8fafc;
            padding: 12px 14px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 8.5pt;
            line-height: 1.4;
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
            padding: 8px 14px;
            background: #f8fafc;
            border-left: 3.5px solid #1e3a8a;
            color: #334155;
            font-style: italic;
            border-radius: 0 4px 4px 0;
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
            background: #cbd5e1;
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
    if os.path.exists(pdf_file_path):
        print(f"SUCCESS: Generated PDF at {pdf_file_path} (Size: {os.path.getsize(pdf_file_path)} bytes)")

if __name__ == "__main__":
    generate_academic_pdf()
