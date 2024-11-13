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
import re
import traceback
import logging
import datetime
import uuid
import winreg
import win32com.client

# 在文件开头添加全局变量
_MUTEX = None
_MUTEX_NAME = "Global\\PixelStreamManager_SingleInstance"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelStream Manager")
        
        # 获取运行时路径
        self.runtime_path = self.get_runtime_path()
        
        # 初始化配置文件路径
        self.config_file = os.path.join(self.runtime_path, 'config.json')
        self.signal_json = os.path.join(self.runtime_path, 'signal.json')
        self.theme_json = os.path.join(self.runtime_path, 'theme.json')
        
        # 首先设置日志
        self.setup_logger()
        self.logger.info("程序启动")
        self.logger.info(f"运行时路径: {self.runtime_path}")
        
        # 然后设置图标路径
        self.icon_path = self.get_resource_path('cloud.ico')
        self.png_path = self.get_resource_path('cloud.png')
        
        # 设置窗口图标
        self.set_window_icon(self.root)
        
        # 注册数字验证函数
        self._validate_number_registered = self.root.register(self.validate_number)
        
        # 初始化状态标签字典
        self.status_labels = {}
        self.detail_labels = {}
        
        # 加载UE5参数配置
        self.load_ue5_params()
        
        # 加载UE5实例配置
        self.load_ue5_configs()
        
        # 从exec-ue.js读取IP和端口
        self.ip_var, self.port_var = self.read_exec_ue_config()
        
        # 设置主题
        self.setup_themes()
        self.current_theme = 'light'
        self.apply_theme()
        
        # 设置窗口大小和位置
        window_width = 1280
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 创建UI
        self.setup_ui()
        
        # 创建托盘图标
        self.setup_tray_icon()
        
        # 绑定关闭事件
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        
        # 加载自动启动配置
        self.load_autostart_config()
        
        # 检查开机启动状态
        self.autostart_enabled = self.check_autostart()
        
        # 确保托盘图标创建成功
        if not self.setup_tray_icon():
            self.logger.error("托盘图标创建失败")
            messagebox.showerror("错误", "托盘图标创建失败，程序可能无法正常工作")
        
        # 检查资源文件
        self.check_resources()

    def setup_logger(self):
        """设置日志"""
        try:
            # 创建日志文件名：年月日_时分秒_GUID.log
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            guid = str(uuid.uuid4())[:8]  # 使用UUID的前8位
            log_filename = f"{current_time}_{guid}.log"
            
            # 创建logs目录（如果不存在）
            logs_dir = os.path.join(self.runtime_path, 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            log_path = os.path.join(logs_dir, log_filename)
            
            # 配置日志
            self.logger = logging.getLogger('PixelStreamManager')
            self.logger.setLevel(logging.DEBUG)
            
            # 文件处理器
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            print(f"日志文件创建成功: {log_path}")
            
        except Exception as e:
            print(f"设置日志失败: {str(e)}")

    def load_ue5_configs(self):
        """加载UE5配置"""
        try:
            if os.path.exists(self.signal_json):
                with open(self.signal_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'UE5' in data:
                        self.ue5_configs = data['UE5']
                        self.logger.info(f"成功加载UE5配置: {len(self.ue5_configs)}个实例")
                        for i, config in enumerate(self.ue5_configs):
                            self.logger.debug(f"实例 {i+1}: {config}")
                    else:
                        self.logger.warning("signal.json中未找到UE5配置")
                        self.ue5_configs = []
            else:
                self.logger.error(f"配置文件不存在: {self.signal_json}")
                self.ue5_configs = []
        except Exception as e:
            self.logger.error("加载UE5配置失败", exc_info=True)
            self.ue5_configs = []

    def refresh_ue5_list(self):
        """刷新UE5实例列表"""
        try:
            if not hasattr(self, 'instance_listbox'):
                self.logger.warning("列表控件未初始化")
                return
                
            self.instance_listbox.delete(0, tk.END)
            
            if hasattr(self, 'ue5_configs') and self.ue5_configs:
                self.logger.debug(f"刷新列表，当前有 {len(self.ue5_configs)} 个配置")
                for i, config in enumerate(self.ue5_configs):
                    if isinstance(config, str):
                        parts = config.split()
                        exe_path = None
                        start_ip = ""
                        
                        # 查找exe路径和启动IP
                        for j, part in enumerate(parts):
                            if part == 'start':
                                # 检查start前面是否有IP
                                if j > 0 and parts[j-1].replace('.', '').isdigit():
                                    start_ip = f"[{parts[j-1]}] "
                            elif '.exe' in part:
                                exe_path = part
                                break
                        
                        display_text = f"实例 {i+1}: {start_ip}{os.path.basename(exe_path) if exe_path else '未知'}"
                        self.instance_listbox.insert(tk.END, display_text)
                        self.logger.debug(f"添加列表项: {display_text}")
            else:
                self.logger.warning("没有UE5配置或配置未初始化")
                
        except Exception as e:
            self.logger.error("刷新UE5列表失败", exc_info=True)

    def save_ue5_configs(self):
        """保存UE5配置"""
        try:
            # 读取完整的signal.json内容
            with open(self.signal_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.debug("原始配置: %s", data)
            self.logger.debug("要更新的UE5配置: %s", self.ue5_configs)
            
            # 更新UE5配置
            data['UE5'] = self.ue5_configs
            
            # 强制关闭文件并重新打开写入
            with open(self.signal_json, 'w', encoding='utf-8') as f:
                f.seek(0)  # 移动到文件开头
                f.truncate()  # 清空文件
                json.dump(data, f, indent='\t')  # 写入新内容
                f.flush()  # 强制刷新缓冲区
                os.fsync(f.fileno())  # 强磁盘
            
            self.logger.info("配置已保存到: %s", self.signal_json)
            self.logger.debug("保存后的完整配置: %s", data)
            
            # 验证保存结果
            with open(self.signal_json, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                if verify_data['UE5'] != self.ue5_configs:
                    raise Exception("配置保存验证失败")
                
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            messagebox.showerror("错误", error_msg)

    def set_window_icon(self, window):
        """设置窗口图标"""
        try:
            self.logger.debug("开始设置窗口图标")
            self.logger.debug(f"ICO路径: {self.icon_path}")
            self.logger.debug(f"PNG路径: {self.png_path}")
            
            if os.path.exists(self.icon_path):
                window.iconbitmap(default=self.icon_path)
                window.iconbitmap(self.icon_path)
                self.logger.info(f"使用ICO设置窗口图标成功: {self.icon_path}")
            elif os.path.exists(self.png_path):
                icon = PhotoImage(file=self.png_path)
                window.iconphoto(True, icon)
                if not hasattr(self, '_icon_images'):
                    self._icon_images = []
                self._icon_images.append(icon)
                self.logger.info(f"使用PNG设置窗口图标成功: {self.png_path}")
            else:
                self.logger.warning("未找到任何图标文件")
                # 列出resources目录内容
                try:
                    resources_dir = os.path.join(self.runtime_path, 'resources')
                    if os.path.exists(resources_dir):
                        files = os.listdir(resources_dir)
                        self.logger.debug(f"Resources目录内容: {files}")
                    else:
                        self.logger.warning(f"Resources目录不存在: {resources_dir}")
                except Exception as e:
                    self.logger.error(f"列出Resources目录内容失败: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"设置窗口图标失败: {str(e)}")

    def read_exec_ue_config(self):
        """从exec-ue.js读取IP和端口配"""
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
            icon_path = self.get_resource_path('cloud.ico')
            if not os.path.exists(icon_path):
                icon_path = self.get_resource_path('cloud.png')
            
            if not os.path.exists(icon_path):
                self.logger.error(f"找不到图标文件: {icon_path}")
                return False
            
            icon_image = Image.open(icon_path)
            icon_image = icon_image.resize((128, 128), Image.Resampling.LANCZOS)
            
            # 创建托盘菜单
            menu = (
                pystray.MenuItem("显示主窗口", self.show_window),
                pystray.MenuItem("启动全部服务", self.start_all),
                pystray.MenuItem("停止全部服务", self.stop_all),
                pystray.MenuItem("开机启动", 
                               self.toggle_autostart, 
                               checked=lambda _: self.autostart_enabled),
                pystray.MenuItem("退出程序", self.quit_app)
            )
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                name="pixel_stream",
                icon=icon_image,
                title="PixelStream Manager",
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
            self.logger.error(f"设置系统托盘失败: {str(e)}")
            return False

    def quit_app(self, icon=None):
        """退出应用"""
        try:
            # 停止托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
            
            # 停止所有服务，但不更新配置
            if hasattr(self, 'status_labels'):
                for script_name in self.status_labels.keys():
                    self.stop_script(script_name, manual=False)
            
            # 清理互斥锁
            cleanup_mutex()
            
            # 直接退出
            self.root.quit()
            
        except Exception as e:
            self.logger.error(f"退出程序失败: {str(e)}")
            # 强制退出
            self.root.destroy()
            sys.exit(0)

    def get_runtime_path(self):
        """获取程序运行时的路径"""
        try:
            if getattr(sys, 'frozen', False):
                return os.path.dirname(sys.executable)
            else:
                return os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            print(f"获取运行时路径失败: {str(e)}")
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
                    toaster.show_toast("PixelStream Manager",
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
            self.logger.error(f"隐藏窗口失败: {str(e)}")

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
            self.logger.error(f"显示窗口失败: {str(e)}")

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
        
        # 在控制面板中添加UE5配置按钮
        ue5_frame = ttk.Frame(control_panel)
        ue5_frame.pack(fill='x', pady=10)
        ttk.Button(ue5_frame, text="UE5配置", width=15,
                  command=self.show_ue5_config).pack(side='left', padx=5)

    def start_all(self):
        """启动所有服务"""
        self.start_script('signal')
        time.sleep(1)  # 等待信令服务启动
        self.start_script('exec-ue')

    def stop_all(self, manual=True):
        """停止所有服务"""
        try:
            # 先停止exec-ue
            if 'exec-ue' in self.status_labels:
                self.stop_script('exec-ue', manual=manual)
                time.sleep(0.5)
            
            # 再停止signal
            if 'signal' in self.status_labels:
                self.stop_script('signal', manual=manual)
            
        except Exception as e:
            error_msg = f"停止所有服务失败: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("错误", error_msg)

    def start_script(self, script_name, manual=True):
        """启动脚本
        manual: 是否是手动启动，只有手动启动才更新配置
        """
        try:
            script_path = os.path.join(self.runtime_path, f"{script_name}.js")
            self.logger.info(f"准备启动脚本: {script_path}")
            
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"找不到脚本文件: {script_path}")

            if script_name == 'exec-ue':
                self.update_exec_ue_config()
            
            # 设置输出文件路径
            output_file = os.path.join(self.runtime_path, f"{script_name}_output.txt")
            
            # 构建命令
            cmd = f'cmd /c chcp 65001 & node "{script_path}" > "{output_file}" 2>&1'
            
            # 在当前目录下启动进程
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=self.runtime_path,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待进程启动
            time.sleep(1)
            
            # 开始监控输出
            self.start_output_monitor(script_name, output_file)
            
            # 更新状态
            self.status_labels[script_name].config(text="运行中", foreground="green")
            
            if script_name == 'exec-ue':
                self.ip_entry.config(state='disabled')
                self.port_entry.config(state='disabled')
                
            # 只有手动启动才更新配置
            if manual:
                self.update_autostart_config(script_name, True)
                self.logger.info(f"手动启动，更新自动启动配置: {script_name} = True")
            
        except Exception as e:
            error_msg = f"启动失败: {str(e)}"
            self.logger.error(error_msg)
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

    def stop_script(self, script_name, manual=True):
        """停止脚本
        manual: 是否是手动停止，只有手动停止才更新配置
        """
        try:
            if script_name == 'signal':
                # 先停止signal.js
                self.stop_node_process(script_name)
                # 等待进程完全停止
                time.sleep(1)
                # 然后停止所有Windows目录下的exe进程
                self.stop_all_exe_processes_with_progress()
            else:
                self.stop_node_process(script_name)
            
            # 只有手动停止才更新配置
            if manual:
                self.update_autostart_config(script_name, False)
                self.logger.info(f"手动停止，更新自动启动配置: {script_name} = False")
            
        except Exception as e:
            error_msg = f"停止失败: {str(e)}"
            self.logger.error(error_msg)
            self.status_labels[script_name].config(text=error_msg, foreground="red")
            
            # 显示错误信息在输出框
            if script_name in self.detail_labels:
                text_widget = self.detail_labels[script_name]
                text_widget.config(state='normal')
                text_widget.delete('1.0', tk.END)
                text_widget.insert('1.0', error_msg + '\n')
                text_widget.config(state='disabled')

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

    def stop_all_exe_processes_with_progress(self):
        """停止所有UE5进程并显示进度"""
        try:
            self.log_to_signal("\n=== 开始停止UE5进程 ===\n")
            
            # 从signal.json读取UE5配置
            if not os.path.exists(self.signal_json):
                self.log_to_signal("未找到signal.json配置文件\n")
                return
                
            with open(self.signal_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ue5_configs = data.get('UE5', [])
            
            if not ue5_configs:
                self.log_to_signal("未找到UE5配置\n")
                return
            
            # 收集所有Windows目录
            windows_dirs = set()
            for config in ue5_configs:
                try:
                    parts = config.split()
                    for part in parts:
                        if '.exe' in part:
                            if '../Windows/' in part:
                                # 相对路径
                                base_dir = os.path.dirname(self.runtime_path)
                                windows_dir = os.path.join(base_dir, 'Windows')
                                windows_dirs.add(windows_dir)
                            else:
                                # 绝对路径或其他路
                                exe_dir = os.path.dirname(part)
                                if os.path.exists(exe_dir):
                                    windows_dirs.add(exe_dir)
                except Exception as e:
                    self.log_to_signal(f"解析配置失败: {str(e)}\n")
            
            if not windows_dirs:
                self.log_to_signal("未找到有效的exe目录\n")
                return
            
            self.log_to_signal(f"找到 {len(windows_dirs)} 个目录:\n")
            for dir_path in windows_dirs:
                self.log_to_signal(f"- {dir_path}\n")
            
            # 为每个目录创建批处理命令
            batch_cmd = "@echo off\nsetlocal enabledelayedexpansion\n\n"
            
            for dir_path in windows_dirs:
                batch_cmd += f'''
echo 正在检查目录: {dir_path}
for /r "{dir_path}" %%f in (*.exe) do (
    echo Found .exe: "%%~nxf"
    taskkill /F /IM "%%~nxf" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Successfully killed: "%%~nxf"
    ) else (
        echo [FAILED] Failed to kill: "%%~nxf"
    )
)
echo.
'''
            
            # 创建临时批处理文件
            batch_file = os.path.join(self.runtime_path, 'kill_processes.bat')
            with open(batch_file, 'w', encoding='gbk') as f:
                f.write(batch_cmd)
            
            self.log_to_signal("\n开始执行停止操作...\n")
            
            # 执行批处理文件并捕获输出
            process = subprocess.Popen(
                batch_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding='gbk'
            )
            
            # 实时读取并显示输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if '正在检查目录:' in line:
                        self.log_to_signal(f"\n{line}\n")
                    elif 'Found .exe:' in line:
                        exe_name = line.split('"')[1]
                        self.log_to_signal(f"发现进程: {exe_name}\n")
                    elif '[SUCCESS]' in line:
                        exe_name = line.split('"')[1]
                        self.log_to_signal(f"✓ 成功停止: {exe_name}\n")
                    elif '[FAILED]' in line:
                        exe_name = line.split('"')[1]
                        self.log_to_signal(f"× 停止失败: {exe_name}\n")
            
            # 删除临时批处理文件
            try:
                os.remove(batch_file)
            except:
                pass
            
            self.log_to_signal("\n=== UE5进程停止完成 ===\n")
            
        except Exception as e:
            error_msg = f"停止进程时出错: {str(e)}\n"
            self.logger.error(error_msg)
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
        """存主题设置"""
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
            
            # 更新输出区
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
            
            # 从主框架开应用主题
            apply_theme_to_widget(self.main_frame)

    def show_ue5_config(self):
        """显示UE5配置窗口"""
        try:
            config_window = tk.Toplevel(self.root)
            config_window.title("UE5配置")
            config_window.transient(self.root)
            
            # 设置窗口图标
            self.set_window_icon(config_window)
            
            # 设置窗口大小和位置
            width = 800
            height = 600
            self.center_window(config_window, width, height)
            
            # 创建框架
            main_frame = ttk.Frame(config_window)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # 创建左右分栏
            left_frame = ttk.Frame(main_frame)
            left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
            
            right_frame = ttk.Frame(main_frame)
            right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
            
            # 左侧：UE5实例列表
            list_frame = ttk.LabelFrame(left_frame, text="UE5实例列表")
            list_frame.pack(fill='both', expand=True, pady=5)
            
            self.instance_listbox = tk.Listbox(list_frame, width=40, height=15)
            self.instance_listbox.pack(fill='both', expand=True, padx=5, pady=5)
            self.instance_listbox.bind('<Double-Button-1>', self.edit_ue5_instance)
            
            # 按钮框架
            btn_frame = ttk.Frame(list_frame)
            btn_frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Button(btn_frame, text="添加实例", 
                      command=self.add_ue5_instance).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="删除实例",
                      command=self.remove_ue5_instance).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="编辑实例",
                      command=lambda: self.edit_ue5_instance(None)).pack(side='left', padx=5)
            
            # 右侧：其他配置
            config_frame = ttk.LabelFrame(right_frame, text="信令服务配置")
            config_frame.pack(fill='both', expand=True, pady=5)
            
            # 端口配置
            port_frame = ttk.Frame(config_frame)
            port_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(port_frame, text="端口:").pack(side='left')
            self.port_var = tk.StringVar(value="10090")
            ttk.Entry(port_frame, textvariable=self.port_var, width=6).pack(side='left', padx=5)
            
            # 认证配置
            auth_frame = ttk.Frame(config_frame)
            auth_frame.pack(fill='x', padx=5, pady=5)
            self.auth_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(auth_frame, text="启用认证", variable=self.auth_var).pack(side='left')
            
            # 一对一配置
            one2one_frame = ttk.Frame(config_frame)
            one2one_frame.pack(fill='x', padx=5, pady=5)
            self.one2one_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(one2one_frame, text="一对一模式", variable=self.one2one_var).pack(side='left')
            
            # 预加载配置
            preload_frame = ttk.Frame(config_frame)
            preload_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(preload_frame, text="预加载数量:").pack(side='left')
            self.preload_var = tk.StringVar(value="0")
            ttk.Entry(preload_frame, textvariable=self.preload_var, width=3).pack(side='left', padx=5)
            
            # 冷却时间配置
            cooltime_frame = ttk.Frame(config_frame)
            cooltime_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(cooltime_frame, text="冷却时间(秒):").pack(side='left')
            self.cooltime_var = tk.StringVar(value="60")
            ttk.Entry(cooltime_frame, textvariable=self.cooltime_var, width=4).pack(side='left', padx=5)
            
            # UE版本配置
            version_frame = ttk.Frame(config_frame)
            version_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(version_frame, text="UE版本:").pack(side='left')
            self.version_var = tk.StringVar(value="5")
            ttk.Entry(version_frame, textvariable=self.version_var, width=2).pack(side='left', padx=5)
            
            # 开机启动配置
            boot_frame = ttk.Frame(config_frame)
            boot_frame.pack(fill='x', padx=5, pady=5)
            self.boot_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(boot_frame, text="开机启动", variable=self.boot_var).pack(side='left')
            
            # 加载当前配置
            self.load_signal_config()
            
            # 底部按钮
            bottom_frame = ttk.Frame(config_window)
            bottom_frame.pack(side='bottom', fill='x', padx=10, pady=10)
            
            def save_and_close():
                self.save_ue5_configs()
                config_window.destroy()  # 保存后关闭窗口
            
            ttk.Button(bottom_frame, text="保存并关闭",
                      command=save_and_close).pack(side='right', padx=5)
            ttk.Button(bottom_frame, text="取消",
                      command=config_window.destroy).pack(side='right', padx=5)
            
            # 刷新列表
            self.refresh_ue5_list()
            self.logger.info("已打开UE5配置窗口")
            
        except Exception as e:
            self.logger.error("显示UE5配置窗口失败", exc_info=True)
            messagebox.showerror("错误", f"显示配置窗口失败: {str(e)}")

    def load_signal_config(self):
        """加载signal.json配置"""
        try:
            if os.path.exists(self.signal_json):
                with open(self.signal_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.port_var.set(str(data.get('PORT', 10090)))
                    self.auth_var.set(data.get('auth', False))
                    self.one2one_var.set(data.get('one2one', False))
                    self.preload_var.set(str(data.get('preload', 0)))
                    self.cooltime_var.set(str(data.get('exeUeCoolTime', 60)))
                    self.version_var.set(str(data.get('UEVersion', 5)))
                    self.boot_var.set(data.get('boot', False))
                    
                    self.logger.info("成功加载signal.json配置")
                    
        except Exception as e:
            self.logger.error("加载signal.json配置失败", exc_info=True)

    def save_signal_config(self):
        """保存signal.json配置"""
        try:
            with open(self.signal_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新配置
            data['PORT'] = int(self.port_var.get())
            data['auth'] = self.auth_var.get()
            data['one2one'] = self.one2one_var.get()
            data['preload'] = int(self.preload_var.get())
            data['exeUeCoolTime'] = int(self.cooltime_var.get())
            data['UEVersion'] = int(self.version_var.get())
            data['boot'] = self.boot_var.get()
            
            # 保存配置
            with open(self.signal_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent='\t')
            
            self.logger.info("成功保存signal.json配置")
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            self.logger.error("保存signal.json配置失败", exc_info=True)
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def add_ue5_instance(self):
        """添加UE5实例"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("添加UE5实例")
            dialog.transient(self.root)
            
            # 设置窗口图标
            self.set_window_icon(dialog)
            
            # 设置窗口大小和位置
            width = 800
            height = 800
            self.center_window(dialog, width, height)
            
            # 创建主滚动框架
            main_canvas = tk.Canvas(dialog)
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
            scrollable_frame = ttk.Frame(main_canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            )
            
            main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            main_canvas.configure(yscrollcommand=scrollbar.set)
            
            # EXE配置
            path_frame = ttk.LabelFrame(scrollable_frame, text="EXE配置")
            path_frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(path_frame, text="EXE路径:").pack(side='left', padx=5)
            exe_path = tk.StringVar()
            path_entry = ttk.Entry(path_frame, textvariable=exe_path, width=50)
            path_entry.pack(side='left', padx=5)
            
            def browse_exe():
                filename = filedialog.askopenfilename(
                    title="选择UE5程序",
                    filetypes=[("EXE files", "*.exe")]
                )
                if filename:
                    base_dir = os.path.dirname(self.runtime_path)
                    rel_path = os.path.relpath(filename, base_dir)
                    exe_path.set(rel_path)
            
            ttk.Button(path_frame, text="浏览", command=browse_exe).pack(side='left', padx=5)
            
            # 网络配置
            net_frame = ttk.LabelFrame(scrollable_frame, text="网络配置")
            net_frame.pack(fill='x', padx=10, pady=5)
            
            # 启动IP配置
            start_ip_frame = ttk.Frame(net_frame)
            start_ip_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(start_ip_frame, text="启动IP:").pack(side='left')
            start_ip = tk.StringVar()
            ttk.Entry(start_ip_frame, textvariable=start_ip, width=15).pack(side='left', padx=5)
            ttk.Label(start_ip_frame, text="(可选)").pack(side='left')
            
            # WebSocket配置
            ws_frame = ttk.Frame(net_frame)
            ws_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(ws_frame, text="WebSocket IP:").pack(side='left')
            ws_ip = tk.StringVar(value="127.0.0.1")
            ttk.Entry(ws_frame, textvariable=ws_ip, width=15).pack(side='left', padx=5)
            ttk.Label(ws_frame, text="Port:").pack(side='left')
            ws_port = tk.StringVar(value="10090")
            ttk.Entry(ws_frame, textvariable=ws_port, width=6).pack(side='left', padx=5)
            
            # UE5参数配置
            params_frame = ttk.LabelFrame(scrollable_frame, text="UE5参数配置")
            params_frame.pack(fill='x', padx=10, pady=5)
            
            # 创建参数选择框和输入框
            param_vars = {}
            param_entries = {}
            
            for param_config in self.ue5_params:
                param = param_config['param']
                desc = param_config['desc']
                default = param_config['default']
                editable = param_config['editable']
                input_type = param_config['input_type']
                
                # 为每个参数创建一个框架
                param_frame = ttk.Frame(params_frame)
                param_frame.pack(fill='x', padx=5, pady=2)
                
                if editable:
                    # 可编辑参数
                    var = tk.BooleanVar(value=True)
                    entry_var = tk.StringVar(value=str(default))
                    
                    # 复选框和标签
                    cb_frame = ttk.Frame(param_frame)
                    cb_frame.pack(side='left')
                    cb = ttk.Checkbutton(cb_frame, text=desc, variable=var)
                    cb.pack(side='left')
                    
                    # 输入框
                    if input_type == "number":
                        vcmd = (self.root.register(self.validate_number), '%P')
                        entry = ttk.Entry(param_frame, textvariable=entry_var, width=10,
                                        validate='key', validatecommand=vcmd)
                    else:
                        entry = ttk.Entry(param_frame, textvariable=entry_var, width=10)
                    entry.pack(side='right', padx=5)
                    
                    param_vars[param] = var
                    param_entries[param] = entry_var
                else:
                    # 不可编辑参数
                    var = tk.BooleanVar(value=default)
                    ttk.Checkbutton(param_frame, text=desc, variable=var).pack(side='left')
                    param_vars[param] = var
            
            # 打包滚动组件
            main_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
            
            # 底部按钮
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(side='bottom', fill='x', padx=10, pady=10)
            
            def save_instance():
                try:
                    if not exe_path.get():
                        messagebox.showerror("错误", "请选择EXE文件")
                        return
                    
                    # 收集参数
                    selected_params = []
                    for param, var in param_vars.items():
                        if var.get():
                            if param in param_entries:
                                # 可编辑参数
                                value = param_entries[param].get()
                                selected_params.append(f"{param}{value}")
                            else:
                                # 不可编辑参数
                                selected_params.append(param)
                    
                    # 构建命令
                    start_prefix = f"{start_ip.get()} " if start_ip.get() else ""
                    cmd = f'{start_prefix}start {exe_path.get()} {" ".join(selected_params)} ' \
                          f'-PixelStreamingURL=ws://{ws_ip.get()}:{ws_port.get()}/'
                    
                    self.logger.debug(f"新增配置: {cmd}")
                    
                    # 更新配置
                    if not hasattr(self, 'ue5_configs'):
                        self.ue5_configs = []
                    self.ue5_configs.append(cmd)
                    
                    # 保存配置
                    self.save_ue5_configs()
                    self.refresh_ue5_list()
                    dialog.destroy()
                    
                except Exception as e:
                    self.logger.error("存配置失败", exc_info=True)
                    messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
            ttk.Button(btn_frame, text="保存", command=save_instance).pack(side='right', padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='right')
            
        except Exception as e:
            self.logger.error("创建配置窗口失败", exc_info=True)
            messagebox.showerror("错误", f"创建配置窗口失败: {str(e)}")

    def remove_ue5_instance(self):
        """删除UE5实例"""
        selection = self.instance_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的实例")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的实例吗？"):
            try:
                index = selection[0]
                
                # 读取当前配置
                with open(self.signal_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 删除选中的配置
                if 'UE5' in data and 0 <= index < len(data['UE5']):
                    removed_config = data['UE5'].pop(index)
                    print(f"删除配置: {removed_config}")
                    
                    # 保存到文件
                    with open(self.signal_json, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)
                    print(f"配置已保到: {self.signal_json}")
                    
                    # 更新内存中的配置
                    self.ue5_configs = data['UE5']
                    
                    # 刷新列表
                    self.refresh_ue5_list()
                    
            except Exception as e:
                error_msg = f"删除实例失败: {str(e)}"
                print(error_msg)
                messagebox.showerror("错误", error_msg)

    def edit_ue5_instance(self, event=None):
        """编辑UE5实例"""
        try:
            selection = self.instance_listbox.curselection()
            if not selection:
                return
                
            index = selection[0]
            if index >= len(self.ue5_configs):
                return
                
            config = self.ue5_configs[index]
            self.logger.debug(f"正在编辑配置: {config}")
            
            dialog = tk.Toplevel(self.root)
            dialog.title("编辑UE5实例")
            dialog.transient(self.root)
            
            # 设窗口图标
            self.set_window_icon(dialog)
            
            # 设置窗口大小和位置
            width = 800
            height = 800
            self.center_window(dialog, width, height)
            
            # 创建主滚动框架
            main_canvas = tk.Canvas(dialog)
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
            scrollable_frame = ttk.Frame(main_canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            )
            
            main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            main_canvas.configure(yscrollcommand=scrollbar.set)
            
            # 解析当前配置
            parts = config.split()
            start_ip_value = ""
            exe_path_value = ""
            ws_ip_value = "127.0.0.1"
            ws_port_value = "10090"
            
            # 提取启动IP和exe路径
            for i, part in enumerate(parts):
                if part == "start":
                    if i > 0 and parts[i-1].replace('.', '').isdigit():
                        start_ip_value = parts[i-1]
                    if i+1 < len(parts):
                        exe_path_value = parts[i+1]
                elif "-PixelStreamingURL=ws://" in part:
                    url = part.replace("-PixelStreamingURL=ws://", "").replace("/", "")
                    if ":" in url:
                        ws_ip_value, ws_port_value = url.split(":")
            
            # EXE配置
            path_frame = ttk.LabelFrame(scrollable_frame, text="EXE配置")
            path_frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(path_frame, text="EXE路径:").pack(side='left', padx=5)
            exe_path = tk.StringVar(value=exe_path_value)
            path_entry = ttk.Entry(path_frame, textvariable=exe_path, width=50)
            path_entry.pack(side='left', padx=5)
            
            def browse_exe():
                filename = filedialog.askopenfilename(
                    title="选择UE5程",
                    filetypes=[("EXE files", "*.exe")]
                )
                if filename:
                    base_dir = os.path.dirname(self.runtime_path)
                    rel_path = os.path.relpath(filename, base_dir)
                    exe_path.set(rel_path)
            
            ttk.Button(path_frame, text="浏览", command=browse_exe).pack(side='left', padx=5)
            
            # 网络配置
            net_frame = ttk.LabelFrame(scrollable_frame, text="网络配置")
            net_frame.pack(fill='x', padx=10, pady=5)
            
            # 启动IP配置
            start_ip_frame = ttk.Frame(net_frame)
            start_ip_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(start_ip_frame, text="启动IP:").pack(side='left')
            start_ip = tk.StringVar(value=start_ip_value)
            ttk.Entry(start_ip_frame, textvariable=start_ip, width=15).pack(side='left', padx=5)
            ttk.Label(start_ip_frame, text="(可选)").pack(side='left')
            
            # WebSocket配置
            ws_frame = ttk.Frame(net_frame)
            ws_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(ws_frame, text="WebSocket IP:").pack(side='left')
            ws_ip = tk.StringVar(value=ws_ip_value)
            ttk.Entry(ws_frame, textvariable=ws_ip, width=15).pack(side='left', padx=5)
            ttk.Label(ws_frame, text="Port:").pack(side='left')
            ws_port = tk.StringVar(value=ws_port_value)
            ttk.Entry(ws_frame, textvariable=ws_port, width=6).pack(side='left', padx=5)
            
            # UE5参数配置
            params_frame = ttk.LabelFrame(scrollable_frame, text="UE5参数配置")
            params_frame.pack(fill='x', padx=10, pady=5)
            
            # 创建参数选择框和输入框
            param_vars = {}
            param_entries = {}
            
            # 解析当前参数值
            current_params = {}
            for part in parts:
                if part.startswith('-'):
                    param_name = part.split('=')[0] + ('=' if '=' in part else '')
                    param_value = part.split('=')[1] if '=' in part else None
                    current_params[param_name] = param_value
            
            self.logger.debug(f"当前参数值: {current_params}")
            
            for param_config in self.ue5_params:
                param = param_config['param']
                desc = param_config['desc']
                default = param_config['default']
                editable = param_config['editable']
                input_type = param_config['input_type']
                
                # 为每个参数创建一个框架
                param_frame = ttk.Frame(params_frame)
                param_frame.pack(fill='x', padx=5, pady=2)
                
                # 检查参数是否存在于当前配置中
                is_enabled = param in current_params
                param_value = current_params.get(param.rstrip('='), str(default))
                
                if editable:
                    # 可编辑参数
                    var = tk.BooleanVar(value=is_enabled)
                    entry_var = tk.StringVar(value=param_value)
                    
                    # 复选框和标签
                    cb_frame = ttk.Frame(param_frame)
                    cb_frame.pack(side='left')
                    cb = ttk.Checkbutton(cb_frame, text=desc, variable=var)
                    cb.pack(side='left')
                    
                    # 输入框
                    if input_type == "number":
                        vcmd = (self.root.register(self.validate_number), '%P')
                        entry = ttk.Entry(param_frame, textvariable=entry_var, width=10,
                                        validate='key', validatecommand=vcmd)
                    else:
                        entry = ttk.Entry(param_frame, textvariable=entry_var, width=10)
                    entry.pack(side='right', padx=5)
                    
                    param_vars[param] = var
                    param_entries[param] = entry_var
                else:
                    # 不可编辑参数
                    var = tk.BooleanVar(value=is_enabled)
                    ttk.Checkbutton(param_frame, text=desc, variable=var).pack(side='left')
                    param_vars[param] = var
            
            # 打包滚动组件
            main_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
            
            # 底部按钮
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(side='bottom', fill='x', padx=10, pady=10)
            
            def save_changes():
                try:
                    # 收集参数
                    selected_params = []
                    for param, var in param_vars.items():
                        if var.get():
                            if param in param_entries:
                                # 可编辑参数
                                value = param_entries[param].get()
                                selected_params.append(f"{param}{value}")
                            else:
                                # 不可编辑参数
                                selected_params.append(param)
                    
                    # 构建命令
                    start_prefix = f"{start_ip.get()} " if start_ip.get() else ""
                    cmd = f'{start_prefix}start {exe_path.get()} {" ".join(selected_params)} ' \
                          f'-PixelStreamingURL=ws://{ws_ip.get()}:{ws_port.get()}/'
                    
                    self.logger.debug(f"更新配置: {cmd}")
                    
                    # 更新配置
                    self.ue5_configs[index] = cmd
                    
                    # 保存配置
                    self.save_ue5_configs()
                    self.refresh_ue5_list()
                    dialog.destroy()
                    
                except Exception as e:
                    self.logger.error("保存配置失败", exc_info=True)
                    messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
            ttk.Button(btn_frame, text="保存", command=save_changes).pack(side='right', padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='right')
            
        except Exception as e:
            self.logger.error("编辑配置失败", exc_info=True)
            messagebox.showerror("错误", f"编辑配置失败: {str(e)}")

    def load_ue5_params(self):
        """加载UE5参数配置"""
        try:
            if os.path.exists(self.theme_json):
                with open(self.theme_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'ue5_params' in data:
                        self.ue5_params = data['ue5_params']
                        self.logger.info(f"成功加载UE5参数配置: {len(self.ue5_params)}个参数")
                        for param in self.ue5_params:
                            self.logger.debug(f"参数: {param['desc']} ({param['param']})")
                    else:
                        self.logger.warning("theme.json中未找到ue5_params配置")
                        self.ue5_params = []
            else:
                self.logger.error(f"配置文件不存在: {self.theme_json}")
                # 使用默认参数配置
                self.ue5_params = [
                    {
                        "param": "-Unattended",
                        "desc": "无人值守模式",
                        "default": True,
                        "editable": False,
                        "input_type": None
                    },
                    # ... 其他默认参数 ...
                ]
        except Exception as e:
            self.logger.error("加载UE5参数配置失败", exc_info=True)
            self.ue5_params = []

    def create_default_theme_json(self):
        """创建默认的theme.json"""
        default_config = {
            "theme": "light",
            "autostart": {
                "signal": False,
                "exec-ue": False
            },
            "ue5_params": [
                {
                    "param": "-Unattended",
                    "desc": "无人值守模式",
                    "default": True,
                    "editable": False,
                    "input_type": None
                },
                {
                    "param": "-RenderOffScreen",
                    "desc": "离屏渲染",
                    "default": True,
                    "editable": False,
                    "input_type": None
                },
                {
                    "param": "-GraphicsAdapter=",
                    "desc": "显卡序号(0,1,2...)",
                    "default": "0",
                    "editable": True,
                    "input_type": "number"
                },
                # ... 其他参数 ...
            ]
        }
        
        try:
            with open(self.theme_json, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            self.logger.info(f"创建默认theme.json成功")
        except Exception as e:
            self.logger.error(f"创建默认theme.json失败: {str(e)}")

    def validate_number(self, value):
        """验证数字输入"""
        try:
            if value == "":
                return True
            if value.startswith('-'):  # 允许负数
                value = value[1:]
            if value.count('.') <= 1:  # 允许小数点
                # 移除小数点后尝试转换
                test_value = value.replace('.', '')
                if test_value.isdigit() or test_value == "":
                    return True
            return False
        except Exception as e:
            self.logger.error(f"数字验证失败: {str(e)}")
            return False

    def load_autostart_config(self):
        """加载自动启动配置"""
        try:
            if os.path.exists(self.theme_json):
                with open(self.theme_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    autostart = data.get('autostart', {})
                    
                    # 自动启动配置的服务
                    if autostart.get('signal', False):
                        self.root.after(1000, lambda: self.start_script('signal'))
                    if autostart.get('exec-ue', False):
                        self.root.after(2000, lambda: self.start_script('exec-ue'))
                        
                    self.logger.info(f"加载自动启动配置: {autostart}")
        except Exception as e:
            self.logger.error(f"加载自动启动配置失败: {str(e)}")

    def update_autostart_config(self, script_name, status):
        """更新自动启动配置"""
        try:
            with open(self.theme_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'autostart' not in data:
                data['autostart'] = {}
            
            data['autostart'][script_name] = status
            
            with open(self.theme_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            self.logger.info(f"更新自动启动配置: {script_name} = {status}")
            
        except Exception as e:
            self.logger.error(f"更新自动启动配置失: {str(e)}")

    def stop_node_process(self, script_name):
        """停止Node进程"""
        try:
            self.logger.info(f"正在停止 {script_name}.js")
            
            # 查找进程ID
            find_pid_cmd = f'wmic process where "commandline like \'%node%{script_name}.js%\'" get processid'
            result = subprocess.run(find_pid_cmd, capture_output=True, text=True, shell=True)
            
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            if len(lines) > 1:  # 跳过标题行
                for line in lines[1:]:  # 处理所有匹配的进程
                    if line:
                        pid = line
                        self.logger.debug(f"找到进程ID: {pid}")
                        
                        # 终止进程
                        kill_cmd = f'taskkill /F /PID {pid}'
                        subprocess.run(kill_cmd, shell=True)
                        self.logger.info(f"已终止进程 {pid}")
                
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
                except Exception as e:
                    self.logger.error(f"清理输出文件失败: {str(e)}")
                
                # 清空输出框并显示停止信息
                if script_name in self.detail_labels:
                    text_widget = self.detail_labels[script_name]
                    text_widget.config(state='normal')
                    text_widget.delete('1.0', tk.END)
                    text_widget.insert('1.0', f"{script_name}.js 已停止运行\n")
                    text_widget.config(state='disabled')
                    
            else:
                self.logger.info(f"未找到运行中的 {script_name}.js")
                self.status_labels[script_name].config(text="未运行", foreground="red")
                
                # 清空输出框
                if script_name in self.detail_labels:
                    text_widget = self.detail_labels[script_name]
                    text_widget.config(state='normal')
                    text_widget.delete('1.0', tk.END)
                    text_widget.insert('1.0', f"{script_name}.js 未在运行\n")
                    text_widget.config(state='disabled')
                
        except Exception as e:
            error_msg = f"停止进程失败: {str(e)}"
            self.logger.error(error_msg)
            self.status_labels[script_name].config(text=error_msg, foreground="red")
            
            # 显示错误信息在输出框
            if script_name in self.detail_labels:
                text_widget = self.detail_labels[script_name]
                text_widget.config(state='normal')
                text_widget.delete('1.0', tk.END)
                text_widget.insert('1.0', error_msg + '\n')
                text_widget.config(state='disabled')

    def center_window(self, window, width, height):
        """窗口居中显示"""
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 获取主窗口位置
        if window.master:
            master = window.master
            master_x = master.winfo_x()
            master_y = master.winfo_y()
            master_width = master.winfo_width()
            master_height = master.winfo_height()
            
            # 相对于主窗口居中
            x = master_x + (master_width - width) // 2
            y = master_y + (master_height - height) // 2
        else:
            # 相对于屏幕居中
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        
        # 确保窗口不会超出屏幕边界
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        window.geometry(f'{width}x{height}+{x}+{y}')

    def get_resource_path(self, relative_path):
        """获取资源文件的路径"""
        try:
            # 判断是否是打包后的exe
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                if hasattr(self, 'logger'):
                    self.logger.debug(f"使用打包路径: {base_path}")
            else:
                # 开发环境下，从resources目录获取
                base_path = os.path.join(self.runtime_path, 'resources')
                if hasattr(self, 'logger'):
                    self.logger.debug(f"使用开发路径: {base_path}")
            
            full_path = os.path.join(base_path, relative_path)
            if hasattr(self, 'logger'):
                self.logger.debug(f"完整资源路径: {full_path}")
            
            # 检查文件是否存在
            if os.path.exists(full_path):
                if hasattr(self, 'logger'):
                    self.logger.info(f"找到资源文件: {full_path}")
            else:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"资源文件不存在: {full_path}")
                # 列出目录内容
                try:
                    dir_path = os.path.dirname(full_path)
                    if os.path.exists(dir_path):
                        files = os.listdir(dir_path)
                        if hasattr(self, 'logger'):
                            self.logger.debug(f"目录内容: {files}")
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"列出目录内容失败: {str(e)}")
            
            return full_path
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"获取资源路径失败: {str(e)}")
            return os.path.join(self.runtime_path, relative_path)

    def check_autostart(self):
        """检查开机启动状态"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "PixelStream Manager"
            
            # 尝试打开注册表键
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                
                # 检查路径是否匹配
                if getattr(sys, 'frozen', False):
                    current_path = f'"{sys.executable}"'
                else:
                    current_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                
                return value == current_path
                
            except WindowsError:
                return False
                
        except Exception as e:
            self.logger.error(f"检查开机启动状态失败: {str(e)}")
            return False

    def set_autostart(self, enable=True):
        """设置开机启动"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "PixelStream Manager"
            
            if enable:
                # 添加到开机启动
                key = None
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                       winreg.KEY_WRITE)
                    
                    if getattr(sys, 'frozen', False):
                        # 打包后的exe路径
                        exe_path = f'"{sys.executable}"'
                    else:
                        # 开发环境路径
                        exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                    
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                    self.logger.info(f"已添加到开机启动: {exe_path}")
                    return True
                except Exception as e:
                    self.logger.error(f"添加开机启动失败: {str(e)}")
                    return False
                finally:
                    if key:
                        winreg.CloseKey(key)
            else:
                # 从开机启动移除
                key = None
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                       winreg.KEY_WRITE)
                    winreg.DeleteValue(key, app_name)
                    self.logger.info("已从开机启动移除")
                    return True
                except WindowsError:
                    return True  # 如果键不存在，视为移除成功
                except Exception as e:
                    self.logger.error(f"移除开机启动失败: {str(e)}")
                    return False
                finally:
                    if key:
                        winreg.CloseKey(key)
                    
        except Exception as e:
            self.logger.error(f"设置开机启动失败: {str(e)}")
            return False

    def toggle_autostart(self, icon=None):
        """切换开机启动状态"""
        try:
            # 切换状态
            new_state = not self.autostart_enabled
            
            # 更新注册表
            if self.set_autostart(new_state):
                self.autostart_enabled = new_state
                
                # 显示提示
                if new_state:
                    message = "已添加到开机启动"
                else:
                    message = "已从开机启动移除"
                
                # 使用气泡提示
                if sys.platform == 'win32':
                    try:
                        from win10toast import ToastNotifier
                        toaster = ToastNotifier()
                        toaster.show_toast("PixelStream Manager",
                                         message,
                                         duration=2,
                                         threaded=True)
                    except:
                        pass
                
                self.logger.info(f"开机启动状态已更新: {new_state}")
            
        except Exception as e:
            self.logger.error(f"切换开机启动状态失败: {str(e)}")

    def check_resources(self):
        """检查资源文件"""
        try:
            resources = [
                ('cloud.ico', '图标文件'),
                ('cloud.png', '图标文件')
            ]
            
            missing_files = []
            for filename, desc in resources:
                path = self.get_resource_path(filename)
                if not os.path.exists(path):
                    missing_files.append(f"{desc} ({filename})")
                else:
                    self.logger.info(f"找到资源文件: {path}")
                    # 打印文件信息
                    file_stat = os.stat(path)
                    self.logger.info(f"  大小: {file_stat.st_size} bytes")
                    self.logger.info(f"  修改时间: {time.ctime(file_stat.st_mtime)}")
            
            if missing_files:
                error_msg = "缺少以下资源文件:\n" + "\n".join(missing_files)
                self.logger.error(error_msg)
                messagebox.showwarning("警告", error_msg)
                
        except Exception as e:
            self.logger.error(f"检查资源文件失败: {str(e)}")

    def on_closing(self):
        """处理窗口关闭事件"""
        try:
            self.hide_window()  # 隐藏到托盘
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"隐藏窗口失败: {str(e)}")
            self.quit_app()  # 如果隐藏失败，则退出程序

def check_single_instance():
    """检查是否已有实例运行，确保只有一个实例"""
    global _MUTEX
    try:
        # 尝试创建互斥锁，第二个参数设为True表示立即获取所有权
        _MUTEX = win32event.CreateMutex(None, True, _MUTEX_NAME)
        last_error = win32api.GetLastError()
        
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            # 找到并激活现有窗口
            def find_window(hwnd, _):
                if win32gui.GetWindowText(hwnd) == "PixelStream Manager":
                    try:
                        # 恢复最小化的窗口
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        # 显示窗口并置顶
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        win32gui.BringWindowToTop(hwnd)
                        win32gui.SetForegroundWindow(hwnd)
                    except Exception as e:
                        print(f"激活窗口失败: {str(e)}")
                    return False
                return True

            win32gui.EnumWindows(find_window, None)
            
            # 释放互斥锁
            if _MUTEX:
                win32api.CloseHandle(_MUTEX)
                _MUTEX = None
            return False
            
        return True

    except Exception as e:
        print(f"检查单例失败: {str(e)}")
        if _MUTEX:
            win32api.CloseHandle(_MUTEX)
            _MUTEX = None
        return False

def cleanup_mutex():
    """清理互斥锁"""
    global _MUTEX
    if _MUTEX:
        try:
            win32api.CloseHandle(_MUTEX)
            _MUTEX = None
        except Exception as e:
            print(f"清理互斥锁失败: {str(e)}")

def main():
    """主函数"""
    try:
        # 检查是否已有实例运行
        if not check_single_instance():
            # 已有实例运行，显示通知并退出
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast("PixelStream Manager",
                                 "程序已在运行中",
                                 duration=2,
                                 threaded=True)
            except:
                try:
                    import tkinter.messagebox as messagebox
                    messagebox.showinfo("提示", "程序已在运行中")
                except:
                    print("程序已在运行中")
            
            time.sleep(1)  # 确保通知显示
            return  # 直接返回，不使用sys.exit()
        
        # 创建主窗口
        root = tk.Tk()
        app = App(root)
        root.mainloop()
        
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", error_msg)
        except:
            pass
    finally:
        # 确保清理互斥锁
        cleanup_mutex()

if __name__ == "__main__":
    main()
    