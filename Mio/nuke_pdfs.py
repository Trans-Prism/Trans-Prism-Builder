import os
import re

# MioMtF Wiki 的 PDF 远程存储地址（如需自定义请修改这里）
REMOTE_PDF_BASE = "https://miomtfwiki.pages.dev/static/documents/"

def fix_pdf_links():
    print("🚀 启动终极 PDF 追踪雷达...")
    replace_count = 0
    
    # 追踪 1：标准的 Markdown 链接 [文字](任何瞎写的路径/文件名.pdf)
    # \1 捕获括号里的文字，\2 捕获最核心的 文件名.pdf
    md_pattern = re.compile(r'\[([^\]]+)\]\([^)]*?([^/)]+\.pdf)\)')
    
    # 追踪 2：HTML <a> 标签 href="任何瞎写的路径/文件名.pdf"
    html_pattern = re.compile(r'href=["\'][^"\']*?([^/"\']+\.pdf)["\']')

    for root, dirs, files in os.walk('docs'):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 暴力替换 Markdown 链接
                new_content, count1 = md_pattern.subn(r'[\1](' + REMOTE_PDF_BASE + r'\2)', content)
                
                # 暴力替换 HTML 链接
                new_content, count2 = html_pattern.subn(r'href="' + REMOTE_PDF_BASE + r'\1"', new_content)

                total_count = count1 + count2
                if total_count > 0:
                    replace_count += total_count
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"🔗 成功重定向了 {total_count} 个链接: {file}")

    if replace_count == 0:
        print("🤔 还是 0 ？？那说明文章里压根就没引用这些 PDF！白赚了几十 MB 空间！")
    else:
        print(f"🎉 搞定！共将 {replace_count} 个狡猾的 PDF 链接全部踢到了云端。")

if __name__ == '__main__':
    fix_pdf_links()
