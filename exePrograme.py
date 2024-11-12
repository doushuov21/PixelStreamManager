import tkinter as tk
from tkinter import ttk, PhotoImage, messagebox, filedialog
import subprocess
import os
import threading
import sys
from PIL import Image, ImageTk
import json
import time
import pystray
import win32event
import win32api
import winerror
import win32gui
import win32con

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("数字孪生系统")
        
        # 获取运行时路径
        self.runtime_path = self.get_runtime_path()
        
        # 初始化配置文件路径
        self.config_file = os.path.join(self.runtime_path, 'config.json')
        self.theme_config = os.path.join(self.runtime_path, 'theme.json')
        
        # 初始化主题
        self.setup_themes()
        self.load_theme()
        
        # 初始化状态标签字典
        self.status_labels = {}
        self.detail_labels = {}
        
        # 从exec-ue.js读取IP和端口
        self.ip_var, self.port_var = self.read_exec_ue_config()
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 设置窗口大小和位置
        window_width = 1280
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        # 先设置最小尺寸，防止闪烁
        self.root.minsize(window_width, window_height)
        self.root.maxsize(window_width, window_height)
        
        # 设置窗口位置和大小
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 创建UI
        self.setup_ui()
        
        # 创建托盘图标
        self.setup_tray_icon()
        
        # 绑定关闭事件
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            ico_path = os.path.join(self.runtime_path, 'cloud.ico')
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
            else:
                print("警告: 未找到ico文件")
        except Exception as e:
            print(f"设置窗口图标失败: {str(e)}")

    def read_exec_ue_config(self):
        """从exec-ue.js读取IP和端口配置"""
        try:
            exec_ue_path = os.path.join(self.runtime_path, 'exec-ue.js')
            if os.path.exists(exec_ue_path):
                with open(exec_ue_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 使用正则表达式提取IP和端口
                import re
                ip_match = re.search(r'signalIp\s*=\s*[\'"]([^\'"]*)[\'"]', content)
                port_match = re.search(r'signalPort\s*=\s*(\d+)', content)
                
                ip = ip_match.group(1) if ip_match else "127.0.0.1"
                port = port_match.group(1) if port_match else "88"
                
                return tk.StringVar(value=ip), tk.StringVar(value=port)
            
        except Exception as e:
            print(f"读取exec-ue.js配置失败: {str(e)}")
        
        return tk.StringVar(value="127.0.0.1"), tk.StringVar(value="88")

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        try:
            # 加载图标
            icon_path = os.path.join(self.runtime_path, 'cloud.ico')
            if not os.path.exists(icon_path):
                icon_path = os.path.join(self.runtime_path, 'cloud.png')
            
            if not os.path.exists(icon_path):
                print(f"找不到图标文件: {icon_path}")
                return False
                
            icon_image = Image.open(icon_path)
            # 确保图标大小合适
            icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
            
            # 创建托盘菜单
            menu = (
                pystray.MenuItem("显示主口", self.show_window),
                pystray.MenuItem("启动全部服务", self.start_all),
                pystray.MenuItem("停止全部服务", self.stop_all),
                pystray.MenuItem("退出程序", self.quit_app)
            )
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                name="digital_twin",
                icon=icon_image,
                title="数字孪生系统",
                menu=menu
            )
            
            # 设置双击事件
            self.tray_icon.on_double_click = self.show_window
            
            # 在新线程中运行托盘图标
            self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True)
            self.tray_thread.start()
            
            # 等待托盘图标创建完成
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"设置系统托盘失败: {str(e)}")
            return False

    def quit_app(self, icon=None):
        """退出应用"""
        try:
            # 停止托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
            
            # 停止所有服务（不等待）
            self.stop_all()
            
            # 直接退出
            self.root.quit()
            
        except Exception as e:
            print(f"退出程序失败: {str(e)}")
            # 强制退出
            self.root.destroy()
            sys.exit(0)

    def get_runtime_path(self):
        """获取程序运行时的路径"""
        try:
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                return os.path.dirname(sys.executable)
            else:
                # 如果是开发环境
                return os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            print(f"获取运行时路径失败: {str(e)}")
            # 返回当前目录作为后备选项
            return os.path.dirname(os.path.abspath(__file__))

    def hide_window(self):
        """隐藏窗口到托盘"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.root.withdraw()  # 隐藏窗口
                # 显示气泡提示
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast("数字孪生系统",
                                     "程序已最小化到系统托盘",
                                     duration=2,
                                     threaded=True)
                except:
                    pass
            else:
                # 如果托盘图标不存在，尝试重新创建
                if self.setup_tray_icon():
                    self.root.withdraw()
                else:
                    # 如果创建失败，提示用户
                    if messagebox.askokcancel("警告", 
                                            "托盘图标创建失败，是否直接退出程序？"):
                        self.quit_app()
                    
        except Exception as e:
            print(f"隐藏窗口失败: {str(e)}")

    def show_window(self, icon=None):
        """显示窗口"""
        try:
            # 使用after方法确保在主线程中执行
            self.root.after(0, lambda: (
                self.root.deiconify(),      # 显示窗口
                self.root.state('normal'),  # 确保窗口不是最小化状态
                self.root.lift(),           # 将窗口提升到顶层
                self.root.focus_force()     # 强制获取焦点
            ))
        except Exception as e:
            print(f"显示窗口失败: {str(e)}")

    def run_tray_icon(self):
        """单独的线程中运行托盘图标"""
        try:
            self.tray_icon.run()
        except Exception as e:
            print(f"托盘图标运行失败: {str(e)}")

    def setup_ui(self):
        """设置主界面"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 创建左侧控制面板
        control_panel = ttk.Frame(self.main_frame)
        control_panel.pack(side='left', fill='y', padx=10)
        
        # Signal.js 控制区域
        signal_section = ttk.LabelFrame(control_panel, text="信令服务")
        signal_section.pack(fill='x', pady=(0, 10))
        
        signal_frame = ttk.Frame(signal_section)
        signal_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(signal_frame, text="启动", width=12,
                  command=lambda: self.start_script('signal')).pack(side='left', padx=5)
        ttk.Button(signal_frame, text="停止", width=12,
                  command=lambda: self.stop_script('signal')).pack(side='left', padx=5)
        
        self.status_labels['signal'] = ttk.Label(signal_frame, text="未运行")
        self.status_labels['signal'].pack(side='left', padx=10)
        
        # Exec-ue.js 控制区域
        exec_section = ttk.LabelFrame(control_panel, text="负载服务")
        exec_section.pack(fill='x', pady=10)
        
        # IP和端口配置
        config_frame = ttk.Frame(exec_section)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(config_frame, text="IP:").pack(side='left')
        self.ip_entry = ttk.Entry(config_frame, textvariable=self.ip_var, width=15)
        self.ip_entry.pack(side='left', padx=5)
        
        ttk.Label(config_frame, text="Port:").pack(side='left')
        self.port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=6)
        self.port_entry.pack(side='left', padx=5)
        
        # 启动停止按钮
        exec_frame = ttk.Frame(exec_section)
        exec_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(exec_frame, text="启动", width=12,
                  command=lambda: self.start_script('exec-ue')).pack(side='left', padx=5)
        ttk.Button(exec_frame, text="停止", width=12,
                  command=lambda: self.stop_script('exec-ue')).pack(side='left', padx=5)
        
        self.status_labels['exec-ue'] = ttk.Label(exec_frame, text="未运行")
        self.status_labels['exec-ue'].pack(side='left', padx=10)
        
        # 全局控制按钮
        global_frame = ttk.Frame(control_panel)
        global_frame.pack(fill='x', pady=10)
        ttk.Button(global_frame, text="启动全部", width=15,
                  command=self.start_all).pack(side='left', padx=5)
        ttk.Button(global_frame, text="停止全部", width=15,
                  command=self.stop_all).pack(side='left', padx=5)
        
        # 右侧输出区域
        output_panel = ttk.Frame(self.main_frame)
        output_panel.pack(side='right', fill='both', expand=True, padx=10)
        
        # Signal.js 输出
        signal_output = ttk.LabelFrame(output_panel, text="信令服务输出")
        signal_output.pack(fill='both', expand=True, pady=(0, 10))
        
        self.detail_labels['signal'] = tk.Text(signal_output, 
                                             height=10,
                                             font=('Consolas', 9),  # 设置小号等宽字体
                                             wrap='none')  # 禁用自动换行
        self.detail_labels['signal'].pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加滚动条
        signal_scroll = ttk.Scrollbar(signal_output, orient="vertical", 
                                    command=self.detail_labels['signal'].yview)
        signal_scroll.pack(side='right', fill='y')
        self.detail_labels['signal'].configure(yscrollcommand=signal_scroll.set)
        
        # Exec-ue.js 输出
        exec_output = ttk.LabelFrame(output_panel, text="负载服务输出")
        exec_output.pack(fill='both', expand=True, pady=(10, 0))
        
        self.detail_labels['exec-ue'] = tk.Text(exec_output, 
                                              height=10,
                                              font=('Consolas', 9),  # 设置小号等宽字体
                                              wrap='none')  # 禁用自动换行
        self.detail_labels['exec-ue'].pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加滚动条
        exec_scroll = ttk.Scrollbar(exec_output, orient="vertical", 
                                  command=self.detail_labels['exec-ue'].yview)
        exec_scroll.pack(side='right', fill='y')
        self.detail_labels['exec-ue'].configure(yscrollcommand=exec_scroll.set)
        
        # 添加主题切换按钮
        theme_frame = ttk.Frame(control_panel)
        theme_frame.pack(fill='x', pady=10)
        ttk.Button(theme_frame, text="切换主题", width=15,
                  command=self.toggle_theme).pack(side='left', padx=5)

    def start_all(self):
        """启动所有服务"""
        self.start_script('signal')
        time.sleep(1)  # 等待信令服务启动
        self.start_script('exec-ue')

    def stop_all(self):
        """停止所有服务"""
        self.stop_script('exec-ue')
        self.stop_script('signal')

    def start_script(self, script_name):
        """启动脚本"""
        try:
            script_path = os.path.join(self.runtime_path, f"{script_name}.js")
            print(f"准备启动脚本: {script_path}")
            
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"找不到脚本文件: {script_path}")

            if script_name == 'exec-ue':
                self.update_exec_ue_config()
            
            # 创建VBS脚本来隐藏运行并重定向输出
            output_file = os.path.join(self.runtime_path, f"{script_name}_output.txt")
            vbs_content = f'''
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{self.runtime_path}"
WshShell.Run "cmd /c node {script_name}.js > {output_file} 2>&1", 0, False
'''
            vbs_path = os.path.join(self.runtime_path, f"run_{script_name}.vbs")
            with open(vbs_path, 'w', encoding='utf-8') as f:
                f.write(vbs_content)
            
            # 运行VBS脚本
            subprocess.run(['cscript', '//Nologo', vbs_path], shell=True)
            
            # 删除VBS脚本
            try:
                os.remove(vbs_path)
            except:
                pass
            
            # 等待进程启动
            time.sleep(1)
            
            # 开始监控输出
            self.start_output_monitor(script_name, output_file)
            
            # 更新状态
            self.status_labels[script_name].config(text="运行中", foreground="green")
            
            if script_name == 'exec-ue':
                self.ip_entry.config(state='disabled')
                self.port_entry.config(state='disabled')
                
        except Exception as e:
            error_msg = f"启动失败: {str(e)}"
            print(error_msg)
            self.status_labels[script_name].config(text=error_msg, foreground="red")

    def start_output_monitor(self, script_name, output_file):
        """监控输出文件"""
        def monitor():
            try:
                last_size = 0
                while True:
                    if os.path.exists(output_file):
                        current_size = os.path.getsize(output_file)
                        if current_size > last_size:
                            with open(output_file, 'r', encoding='utf-8') as f:
                                f.seek(last_size)
                                new_content = f.read()
                                self.root.after(0, lambda: self.update_output(script_name, new_content))
                            last_size = current_size
                    time.sleep(0.1)
            except Exception as e:
                print(f"监控输出失败: {str(e)}")
        
        threading.Thread(target=monitor, daemon=True).start()

    def update_output(self, script_name, content):
        """更新输出显示"""
        if script_name in self.detail_labels:
            text_widget = self.detail_labels[script_name]
            text_widget.config(state='normal')
            text_widget.insert('end', content)
            text_widget.see('end')
            text_widget.config(state='disabled')

    def stop_script(self, script_name):
        """停止脚本"""
        try:
            if script_name == 'signal':
                # 先停止UE5进程
                self.stop_all_exe_processes()
                time.sleep(1)  # 等待UE5进程停止
            
            # 使用更精确的命令查找node进程
            cmd = f'wmic process where "commandline like \'%node%{script_name}.js%\'" get processid,commandline'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.stdout.strip():
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                for line in lines[1:]:  # 跳过标题行
                    if script_name in line:
                        try:
                            pid = line.split()[-1]  # 获取最后一列作为PID
                            print(f"找到进程ID: {pid}")
                            
                            # 终止进程
                            kill_cmd = f'taskkill /F /PID {pid}'
                            subprocess.run(kill_cmd, shell=True)
                            print(f"已终止进程 {pid}")
                        except:
                            continue
                
                # 更新状态
                self.status_labels[script_name].config(text="未运行", foreground="red")
                
                if script_name == 'exec-ue':
                    self.ip_entry.config(state='normal')
                    self.port_entry.config(state='normal')
                
                # 清理输出文件
                output_file = os.path.join(self.runtime_path, f"{script_name}_output.txt")
                try:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                except:
                    pass
                
                # 清空输出框并显示停止信息
                if script_name in self.detail_labels:
                    text_widget = self.detail_labels[script_name]
                    text_widget.config(state='normal')
                    text_widget.delete('1.0', tk.END)
                    text_widget.insert('1.0', f"{script_name}.js 已停止运行\n")
                    text_widget.config(state='disabled')
                    
        except Exception as e:
            error_msg = f"停止失败: {str(e)}"
            print(error_msg)
            self.status_labels[script_name].config(text=error_msg, foreground="red")

    def update_exec_ue_config(self):
        """更新exec-ue.js配置"""
        try:
            script_path = os.path.join(self.runtime_path, 'exec-ue.js')
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"找不到脚本文件: {script_path}")

            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 更新IP和端口
            import re
            content = re.sub(
                r'(signalIp\s*=\s*)[\'"][^\'"]*[\'"]',
                f"\\1'{self.ip_var.get()}'",
                content
            )
            content = re.sub(
                r'signalPort\s*=\s*\d+',
                f'signalPort = {self.port_var.get()}',
                content
            )

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"已更新配置 - IP: {self.ip_var.get()}, Port: {self.port_var.get()}")
            
        except Exception as e:
            print(f"更新配置失败: {str(e)}")
            messagebox.showerror("错误", f"更新配置失败: {str(e)}")

    def stop_all_exe_processes(self):
        """停止所有相关的exe进程"""
        try:
            self.log_to_signal("\n=== 开始停止Windows目录下的所有exe进程 ===\n")
            
            # 获取Windows目录的完整路径
            base_dir = os.path.dirname(self.runtime_path)
            windows_dir = os.path.join(base_dir, 'Windows')
            
            # 创建批处理命令
            batch_cmd = f'''
@echo off
setlocal enabledelayedexpansion
for /r "{windows_dir}" %%f in (*.exe) do (
    echo 发现进程: %%~nxf
    taskkill /F /IM "%%~nxf" >nul 2>&1
    if !errorlevel! equ 0 (
        echo 已停止: %%~nxf
    )
)
'''
            # 创建临时批处理文件
            batch_file = os.path.join(self.runtime_path, 'kill_processes.bat')
            with open(batch_file, 'w', encoding='gbk') as f:
                f.write(batch_cmd)
            
            # 执行批处理文件并捕获输出
            process = subprocess.Popen(batch_file, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    shell=True,
                                    encoding='gbk')
            
            # 实时读取并显示输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log_to_signal(output.strip() + '\n')
            
            # 删除临时批处理文件
            try:
                os.remove(batch_file)
            except:
                pass
            
            self.log_to_signal("=== exe进程停止完成 ===\n")
            
        except Exception as e:
            error_msg = f"停止进程时出错: {str(e)}\n"
            print(error_msg)
            self.log_to_signal(error_msg)

    def log_to_signal(self, message):
        """输出信息到信令服务的输出框"""
        try:
            if 'signal' in self.detail_labels:
                text_widget = self.detail_labels['signal']
                text_widget.config(state='normal')
                text_widget.insert('end', message)
                text_widget.see('end')
                text_widget.config(state='disabled')
            print(message, end='')  # 同时输出到控制台
        except Exception as e:
            print(f"输出到信令窗口失败: {str(e)}")

    def setup_themes(self):
        """设置主题配置"""
        self.themes = {
            "light": {
                'bg': '#ffffff',
                'button_bg': '#f0f0f0',
                'button_active': '#e0e0e0',
                'text_bg': '#1e1e1e',
                'text_fg': '#ffffff',
                'button_fg': '#000000',
                'frame_bg': '#f8f8f8',
                'label_fg': '#000000',
                'output_bg': '#ffffff',
                'output_fg': '#000000',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000'
            },
            "dark": {
                'bg': '#2d2d2d',
                'button_bg': '#404040',
                'button_active': '#505050',
                'text_bg': '#1e1e1e',
                'text_fg': '#ffffff',
                'button_fg': '#e0e0e0',
                'frame_bg': '#363636',
                'label_fg': '#ffffff',
                'output_bg': '#1e1e1e',
                'output_fg': '#ffffff',
                'entry_bg': '#1e1e1e',
                'entry_fg': '#e0e0e0'
            }
        }

    def load_theme(self):
        """加载主题设置"""
        try:
            if os.path.exists(self.theme_config):
                with open(self.theme_config, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', 'light')
            else:
                self.current_theme = 'light'
            self.apply_theme()
        except Exception as e:
            print(f"加载主题失败: {str(e)}")
            self.current_theme = 'light'
            self.apply_theme()

    def save_theme(self):
        """保存主题设置"""
        try:
            with open(self.theme_config, 'w') as f:
                json.dump({'theme': self.current_theme}, f, indent=4)
        except Exception as e:
            print(f"保存主题失败: {str(e)}")

    def toggle_theme(self):
        """切换主题"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme()
        self.save_theme()

    def apply_theme(self):
        """应用主题"""
        theme = self.themes[self.current_theme]
        
        # 应用到主窗口
        self.root.configure(bg=theme['bg'])
        
        # 应用到主框架
        if hasattr(self, 'main_frame'):
            # 设置ttk样式
            style = ttk.Style()
            
            # 配置基本样式
            style.configure('Custom.TFrame', background=theme['frame_bg'])
            style.configure('Custom.TLabelframe', background=theme['frame_bg'])
            style.configure('Custom.TLabelframe.Label', 
                          background=theme['frame_bg'],
                          foreground=theme['label_fg'])
            
            # 配置按钮样式
            style.configure('TButton', 
                          background=theme['button_bg'],
                          foreground=theme['button_fg'])
            style.map('TButton',
                     background=[('active', theme['button_active'])],
                     foreground=[('active', theme['button_fg'])])
            
            # 配置输入框样式
            style.configure('TEntry',
                          fieldbackground=theme['entry_bg'],
                          foreground=theme['entry_fg'])
            
            # 配置标签样式
            style.configure('TLabel',
                          background=theme['frame_bg'],
                          foreground=theme['label_fg'])
            
            # 应用框架样式
            self.main_frame.configure(style='Custom.TFrame')
            
            # 更新所有标签
            for label in self.status_labels.values():
                current_fg = label.cget('foreground')
                if current_fg == 'red':
                    label.configure(background=theme['frame_bg'])
                elif current_fg == 'green':
                    label.configure(background=theme['frame_bg'])
                else:
                    label.configure(background=theme['frame_bg'],
                                  foreground=theme['label_fg'])
            
            # 更新输出区域
            for text_widget in self.detail_labels.values():
                text_widget.configure(
                    background=theme['output_bg'],
                    foreground=theme['output_fg'],
                    insertbackground=theme['output_fg']
                )
            
            # 更新输入框
            if hasattr(self, 'ip_entry'):
                self.ip_entry.configure(style='TEntry')
            if hasattr(self, 'port_entry'):
                self.port_entry.configure(style='TEntry')
            
            # 遍历所有子部件应用主题
            def apply_theme_to_widget(widget):
                if isinstance(widget, ttk.Frame):
                    widget.configure(style='Custom.TFrame')
                elif isinstance(widget, ttk.LabelFrame):
                    widget.configure(style='Custom.TLabelframe')
                elif isinstance(widget, ttk.Label):
                    widget.configure(style='TLabel')
                elif isinstance(widget, ttk.Button):
                    widget.configure(style='TButton')
                elif isinstance(widget, ttk.Entry):
                    widget.configure(style='TEntry')
                
                # 递归处理子部件
                for child in widget.winfo_children():
                    apply_theme_to_widget(child)
            
            # 从主框架开始应用主题
            apply_theme_to_widget(self.main_frame)

def check_single_instance():
    """检查是否已有实例运行"""
    try:
        # 使用具体的互斥量名称
        mutex_name = "Global\\DigitalTwinSystem_SingleInstance_Mutex"
        
        # 尝试创建互斥量
        mutex = win32event.CreateMutex(None, 1, mutex_name)
        last_error = win32api.GetLastError()
        
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            # 查找已存在的窗口
            def find_window_callback(hwnd, _):
                if win32gui.GetWindowText(hwnd) == "数字孪生系统":
                    # 存储找到的窗口句柄
                    find_window_callback.found_hwnd = hwnd
                    return False
                return True
            find_window_callback.found_hwnd = None
            
            # 查找窗口
            win32gui.EnumWindows(find_window_callback, None)
            
            if find_window_callback.found_hwnd:
                # 激活已存在的窗口
                hwnd = find_window_callback.found_hwnd
                if win32gui.IsIconic(hwnd):  # 最小化状态
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                
                print("程序已在运行，已激活现有窗口")
            else:
                print("程序已在运行，但未找到窗口")
            
            return False
            
        # 保存互斥量句柄
        global g_mutex
        g_mutex = mutex
        return True
        
    except Exception as e:
        print(f"单例检查失败: {str(e)}")
        return False

def main():
    if not check_single_instance():
        sys.exit(0)
    
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    