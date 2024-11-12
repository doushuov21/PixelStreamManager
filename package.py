import os
import sys
from PIL import Image
import PyInstaller.__main__
import base64

def create_ico_from_png():
    """从PNG创建ICO文件"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, 'resources')
        
        png_path = os.path.join(resource_dir, 'cloud.png')
        ico_path = os.path.join(resource_dir, 'cloud.ico')
        
        if os.path.exists(png_path):
            img = Image.open(png_path)
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            img.save(ico_path, format='ICO', sizes=icon_sizes)
            print(f"成功创建图标文件: {ico_path}")
            return ico_path
        else:
            print(f"未找到PNG文件: {png_path}")
            return None
    except Exception as e:
        print(f"创建图标文件失败: {str(e)}")
        return None

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建ICO文件
    ico_path = create_ico_from_png()
    if not ico_path:
        print("警告: 将使用默认图标")
        ico_path = os.path.join(current_dir, 'resources', 'cloud.ico')
    
    # 运行PyInstaller
    PyInstaller.__main__.run([
        'exePrograme.py',                      # 主程序文件
        '--name=数字孪生系统',                  # 生成的exe名称
        '--windowed',                          # 使用GUI模式
        '--onefile',                           # 打包成单个exe
        '--clean',                             # 清理临时文件
        f'--icon={ico_path}',                  # 设置图标
        '--noconfirm',                         # 覆盖现有文件
        '--add-binary=resources/cloud.png;.',  # 直接添加到根目录
        '--add-binary=resources/background.png;.',
        '--add-binary=resources/cloud.ico;.',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=watchdog.observers.winapi',
        '--hidden-import=watchdog.observers.polling'
    ])
    
    print("打包完成！")

if __name__ == "__main__":
    main()