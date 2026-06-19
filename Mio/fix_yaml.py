import os
import re

def fix_yaml_hide():
    print("🚀 启动排雷：正在全盘清洗致命的 hide 布尔值...")
    # MioMtF Wiki 内容在 docs/ 目录下
    content_dir = 'docs'
    count = 0
    
    if not os.path.exists(content_dir):
        print(f"❌ 找不到 {content_dir} 文件夹！")
        return
    
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 正则大杀器：匹配独占一行的 hide: true 或 hide: false (忽略大小写)
                    new_content = re.sub(r'^hide:\s*(true|false)\s*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
                    
                    if content != new_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"✅ 成功拆除炸弹: {filepath}")
                        count += 1
                except Exception as e:
                    print(f"❌ 警告：处理 {filepath} 时发生错误: {e}")
                    
    print(f"🎉 排雷完毕！共成功拆除了 {count} 颗会导致构建工具猝死的炸弹！")

if __name__ == '__main__':
    fix_yaml_hide()
