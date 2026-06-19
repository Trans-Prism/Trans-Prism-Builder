import os
from PIL import Image

# 🚀 核心破解：关闭防解压炸弹限制，允许读取一亿像素的巨图
Image.MAX_IMAGE_PIXELS = None

# MioMtF Wiki 使用 VitePress，图片放在 docs/images 和 docs/public 下
folders = ['docs']

def do_surgery():
    print("🚀 开始给 MioMtF Wiki 抽脂...")
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(root, file)
                    webp_path = os.path.splitext(img_path)[0] + '.webp'
                    
                    try:
                        with Image.open(img_path) as img:
                            # 🚀 核心瘦身：如果是巨型图片，进行物理缩放 (限制最大宽度 1600)
                            max_width = 1600
                            if img.width > max_width:
                                ratio = max_width / img.width
                                new_height = int(img.height * ratio)
                                # 使用 LANCZOS 算法保证缩放后的清晰度
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                                
                            # 对于 RGBA (带透明度的图) 转 WebP 可能需要转为 RGB
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            
                            # 狠狠压缩并保存
                            img.save(webp_path, 'webp', quality=75)
                            
                        os.remove(img_path) 
                        print(f'✅ 压缩并替换: {file} -> .webp')
                    except Exception as e:
                        print(f'❌ 处理失败 {img_path}: {e}')

    # 2. 遍历所有 md 文件，把里面的图片链接后缀替换掉
    for root, dirs, files in os.walk('docs'):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单暴力的文本替换
                content = content.replace('.png', '.webp') \
                                 .replace('.jpg', '.webp') \
                                 .replace('.jpeg', '.webp') \
                                 .replace('.PNG', '.webp') \
                                 .replace('.JPG', '.webp')
                
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    print("🎉 抽脂完成！你可以右键看看文件夹现在有多大了。")

if __name__ == '__main__':
    do_surgery()
