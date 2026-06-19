import os
import shutil

def clean_miomtfwiki_repo():
    print("🚀 [MioMtF Wiki 净化协议] 启动：正在执行物理级大清洗...")
    
    # 🛡️ 核心白名单：MioMtF.wiki 专属护城河
    whitelist = [
        'docs',         # 核心 Markdown 源码库（VitePress 约定）
        'mkdocs.yml',   # 配置文件（如果保留）
        'LICENSE',      # 尊重开源协议的护身符
    ]

    deleted_count = 0
    root_items = os.listdir('.')

    for item in root_items:
        # 🔐 绝对安全锁：
        # 1. 在白名单里的直接放过
        # 2. 所有的 .py 流水线脚本必须活下来（你的雇佣兵军团）
        # 3. 所有的 .md 说明文档 (如 README.md, index.md) 给予保留
        # 4. 所有 .yml 配置文件
        # 5. package.json 等 node 项目文件
        if item in whitelist or item.endswith('.py') or item.endswith('.md') or item.endswith('.yml') or item == 'package.json' or item == 'package-lock.json' or item == '.gitattributes' or item == '.gitignore' or item.startswith('.'):
            continue

        try:
            if os.path.isdir(item):
                shutil.rmtree(item)
                print(f"💣 摧毁无用/残留文件夹: {item}/")
            else:
                os.remove(item)
                print(f"💥 摧毁无用/残留文件: {item}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ 警告：无法删除 {item}, 错误: {e}")

    print(f"🎉 净化完成！共粉碎了 {deleted_count} 个电子垃圾和历史残留构建！")
    print("👉 现在的 MioMtF Wiki 已经是一块极致纯净的画布，随时准备重构！")

if __name__ == '__main__':
    clean_miomtfwiki_repo()
