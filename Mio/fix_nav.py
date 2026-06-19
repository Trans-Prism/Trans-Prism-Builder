import os
import re

def fix_navigation():
    print("🚀 [终极导航重构] 启动：正在扫描文档结构...")
    base_dir = 'docs'
    
    # MioMtF Wiki 是单语言简体中文维基，不需要多语言国旗标签
    # 但保留扩展能力

    if not os.path.exists(base_dir):
        print("❌ 找不到 docs 文件夹！")
        return

    # 1. 暴力清除所有旧的 .pages，准备干净的画布
    for root, dirs, files in os.walk(base_dir):
        if '.pages' in files:
            os.remove(os.path.join(root, '.pages'))

    # 2. 深入每个文件夹，重新生成精准的 .pages
    count = 0
    for root, dirs, files in os.walk(base_dir):
        rel_path = os.path.relpath(root, base_dir)
        folder_name = os.path.basename(root)
        
        if rel_path == '.':
            continue
            
        title = None
        
        # 🎯 场景: 所有子目录
        # 寻找子目录的入口文件
        index_files = [f for f in files if f.lower() in ['index.md', '_index.md', 'readme.md']]
        if index_files:
            filepath = os.path.join(root, index_files[0])
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 魔法1：尝试抓取 YAML/TOML 配置里的 title: "xxx" 或 title="xxx"
                    match_meta = re.search(r'^title\s*[:=]\s*[\'"]?([^\n\'"]+)[\'"]?', content, re.MULTILINE | re.IGNORECASE)
                    if match_meta:
                        title = match_meta.group(1).strip()
                    else:
                        # 魔法2：尝试抓取 Markdown 的一级标题 # xxx
                        match_h1 = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if match_h1:
                            title = match_h1.group(1).strip()
                            
            except Exception:
                pass
                    
        # 3. 只有提取到了合法标题，才生成配置文件
        if title:
            pages_path = os.path.join(root, '.pages')
            with open(pages_path, 'w', encoding='utf-8') as f:
                # 防止标题里自带单引号搞崩 YAML
                safe_title = title.replace("'", "''")
                f.write(f"title: '{safe_title}'\n")
            count += 1
            print(f"✅ 生成侧边栏节点: [{folder_name}] -> {title}")
            
    print(f"🎉 侧边栏完美重构！共精准生成了 {count} 个导航配置文件！")
    if count == 0:
        print("🤔 破案雷达：一个都没找到！当前目录下的主文件夹有这些：")
        print([d for d in next(os.walk(base_dir))[1] if not d.startswith('.')])

if __name__ == '__main__':
    fix_navigation()
