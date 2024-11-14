import os
import sys
from PIL import Image
import PyInstaller.__main__
import base64
import psutil
import time

def kill_existing_process():
    """终止已存在的程序进程"""
    target_name = "数字孪生系统.exe"
    killed = False
    
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == target_name:
                    proc.kill()
                    killed = True
                    print(f"已终止现有进程: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            # 等待进程完全终止
            time.sleep(2)
            print("等待进程终止完成")
    except Exception as e:
        print(f"终止进程时出错: {str(e)}")

def clean_dist_folder():
    """清理dist文件夹"""
    try:
        dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
        target_exe = os.path.join(dist_path, "数字孪生系统.exe")
        
        if os.path.exists(target_exe):
            try:
                os.remove(target_exe)
                print(f"已删除现有文件: {target_exe}")
            except Exception as e:
                print(f"删除文件失败: {str(e)}")
                return False
        return True
    except Exception as e:
        print(f"清理dist文件夹失败: {str(e)}")
        return False

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
    try:
        # 先终止已存在的进程
        kill_existing_process()
        
        # 清理dist文件夹
        if not clean_dist_folder():
            print("清理失败，打包终止")
            return
        
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
            '--add-binary=resources/cloud.ico;.',
            '--hidden-import=PIL._tkinter_finder',
            '--hidden-import=watchdog.observers.winapi',
            '--hidden-import=watchdog.observers.polling'
        ])
        
        print("打包完成！")
        
    except Exception as e:
        print(f"打包失败: {str(e)}")

if __name__ == "__main__":
    main()