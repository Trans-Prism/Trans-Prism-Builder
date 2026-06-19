import os
import re

def fix_hugo_shortcodes():
    print("🚀 [语法转换引擎] 启动：正在将 Hugo 专属语法翻译为 MkDocs 语法...")
    count = 0
    # MioMtF Wiki 内容在 docs/ 目录下
    content_dir = 'docs'
    
    if not os.path.exists(content_dir):
        print("❌ 找不到 docs 文件夹！")
        return
        
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    original_content = content
                    
                    # 🎯 1. 抢救 Notice (警告框)
                    # 把 {{< notice warning "标题" >}} 内容 {{< /notice >}} 变成 MkDocs 的 !!! warning "标题"
                    def replace_notice(match):
                        type_ = match.group(1)
                        title = match.group(2)
                        inner_text = match.group(3)
                        # MkDocs 的警告框要求内部文字必须缩进 4 个空格
                        indented = "\n".join("    " + line for line in inner_text.split("\n"))
                        return f"!!! {type_} \"{title}\"\n{indented}"
                    
                    content = re.sub(
                        r'\{\{<\s*notice\s+([a-zA-Z0-9_-]+)\s+"([^"]*)"\s*>\}\}(.*?)\{\{<\s*/notice\s*>\}\}',
                        replace_notice, content, flags=re.DOTALL
                    )
                    
                    # 🎯 2. 抢救图片路径 — 处理 Markdown `![alt](path)` 和 Hugo `{{< hiddenphoto >}}`
                    def fix_image_path(path: str) -> str:
                        """将图片路径转为站点根目录绝对路径 /static/...（忽略 URL）"""
                        path = path.strip().lstrip('/')
                        if path.startswith(('http://', 'https://', '#', 'data:')):
                            return path
                        if path.startswith('static/'):
                            return '/' + path
                        return '/static/' + path

                    # 2a. 处理标准 Markdown 图片语法: ![alt](/images/xxx.webp)
                    def replace_md_image(match):
                        alt_text = match.group(1)
                        src = match.group(2)
                        return f'![{alt_text}]({fix_image_path(src)})'

                    content = re.sub(
                        r'!\[([^\]]*)\]\(([^)]+)\)',
                        replace_md_image, content
                    )

                    # 2b. 处理 {{< hiddenphoto "path" "caption" >}} → ![caption](path)
                    def replace_hiddenphoto(match):
                        src = match.group(1)
                        caption = match.group(2).strip() if match.group(2) else ''
                        path = fix_image_path(src)
                        if caption:
                            return f'![{caption}]({path})'
                        else:
                            return f'![]({path})'

                    content = re.sub(
                        r'\{\{<\s*hiddenphoto\s+"([^"]+)"\s*(?:"([^"]*)")?\s*>\}\}',
                        replace_hiddenphoto, content
                    )

                    # 2c. 处理 HTML <img src="..." ...> 标签
                    def replace_html_img(match):
                        before_src = match.group(1)
                        src = match.group(2)
                        after_src = match.group(3)
                        return f'{before_src}{fix_image_path(src)}{after_src}'

                    content = re.sub(
                        r'(<img\s+[^>]*?src=")([^"]+)("[\s\S]*?>)',
                        replace_html_img, content
                    )
                    
                    # 🎯 3. 抢救 Wiki 快捷链接
                    # 把 {{< wiki Novartis en >}} 变成标准的 Markdown 链接 [Novartis](...)
                    def replace_wiki(match):
                        args = match.group(1).strip().split()
                        if not args:
                            return match.group(0)
                        keyword = args[0]
                        lang = args[1] if len(args) > 1 else 'zh'
                        return f'[{keyword}](https://{lang}.wikipedia.org/wiki/{keyword})'
                        
                    content = re.sub(r'\{\{<\s*wiki\s+(.*?)\s*>\}\}', replace_wiki, content)
                    
                    # 🎯 4. 抢救 ref 跨页面引用
                    # 把 {{< ref "risk" >}} 翻译成 [risk](risk.html)
                    def replace_ref(match):
                        target = match.group(1)
                        return f'[{target}]({target}.html)'
                        
                    content = re.sub(r'\{\{<\s*ref\s+"?([^"\s>]+)"?\s*>\}\}', replace_ref, content)
                    
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        count += 1
                except Exception as e:
                    print(f"❌ 警告：处理 {filepath} 时发生错误: {e}")
                    
    print(f"🎉 语法清洗完毕！共拯救了 {count} 个惨遭乱码荼毒的 Markdown 文件！")

if __name__ == '__main__':
    fix_hugo_shortcodes()
