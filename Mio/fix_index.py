import os

def fix_index_names():
    print("🚀 [全盘雷达] 启动：正在全项目进行无差别地毯式扫描...")
    count = 0
    # MioMtF Wiki 内容在 docs/ 目录下
    scan_dir = 'docs'

    if not os.path.exists(scan_dir):
        print(f"❌ 找不到 {scan_dir} 文件夹！")
        return

    for root, dirs, files in os.walk(scan_dir):
        # 避开生成的 .vitepress 缓存文件夹，防止误伤
        if '.vitepress' in root:
            continue
            
        for filename in files:
            lower_name = filename.lower()
            
            # 精准狙击 _index.md 和 readme.md
            if lower_name == '_index.md' or lower_name == 'readme.md':
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, 'index.md')
                
                try:
                    if old_path == new_path:
                        continue
                    if os.path.exists(new_path):
                        os.remove(new_path)
                        
                    os.rename(old_path, new_path)
                    print(f"✅ 成功斩杀并正名: {old_path} -> index.md")
                    count += 1
                except Exception as e:
                    print(f"❌ 警告：处理 {old_path} 时发生错误: {e}")
                    
    print(f"🎉 扫描结束！共成功为 {count} 个源文件正名！")
    
    if count == 0:
        print("🤔 破案雷达：一个都没找到！当前目录下的主文件夹有这些：")
        print([d for d in next(os.walk(scan_dir))[1] if not d.startswith('.')])

if __name__ == '__main__':
    fix_index_names()
