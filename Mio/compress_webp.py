import os
from PIL import Image

# 再次关闭防解压炸弹限制
Image.MAX_IMAGE_PIXELS = None

# MioMtF Wiki 使用 VitePress，图片在 docs 目录下
folders = ['docs']
# 手机端 2K 级别绝对够用了
MAX_EDGE = 2000 

def smash_webp():
    print("🚀 开始对巨型 WebP 进行二次物理降维...")
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.webp'):
                    img_path = os.path.join(root, file)
                    
                    try:
                        with Image.open(img_path) as img:
                            width, height = img.size
                            
                            # 只要有一边超过咱们的限制，就抓出来打
                            if width > MAX_EDGE or height > MAX_EDGE:
                                print(f"⚠️ 抓获巨型 WebP: {file} ({width} x {height})")
                                
                                # 计算缩放比例，按最长边等比缩小
                                ratio = MAX_EDGE / max(width, height)
                                new_width = int(width * ratio)
                                new_height = int(height * ratio)
                                
                                # 使用 LANCZOS 高质量重采样
                                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                
                                # 直接覆盖原文件
                                resized_img.save(img_path, 'webp', quality=75)
                                print(f"✅ 已暴力拍扁为 {new_width} x {new_height}")
                                
                    except Exception as e:
                        print(f'❌ 处理失败 {img_path}: {e}')

    print("🎉 WebP 二次抽脂完成！这下安装包彻底老实了。")

if __name__ == '__main__':
    smash_webp()
