import os
import shutil

def prepare_static():
    print("🚀 [自动化构建链] 启动：正在将 static 资源目录合并到 docs 中...")
    
    source = 'static'
    destination = os.path.join('docs', 'static')
    
    # 确保 docs 文件夹存在
    if not os.path.exists('docs'):
        print("❌ 致命错误：找不到 docs 文件夹，请确认在项目根目录运行！")
        return

    try:
        # 场景 A: 如果 docs 里面已经有 static 了（比如上次流水线跑完留下的）
        if os.path.exists(destination):
            print("🧹 发现 docs/static 中已有旧数据，正在清理以防冲突...")
            shutil.rmtree(destination)
            
        # 场景 B: 根目录下有 static，执行标准的移动操作
        if os.path.exists(source):
            shutil.move(source, 'docs/')
            print("✅ 转移成功：static 文件夹已完美并入 docs/static！")
        else:
            # 场景 C: 根目录和 docs 里都没有 static (防弹处理)
            if not os.path.exists(destination):
                print("⚠️ 警告：到处都找不到 static 文件夹，请确认源码是否完整！")
            else:
                print("✅ 检查通过：static 已经在 docs 里面了，无需重复移动！")
                
    except Exception as e:
        print(f"❌ 移动 static 文件夹时发生底层错误: {e}")

if __name__ == '__main__':
    prepare_static()
