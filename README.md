

PixelStream Manager 是一个用于管理 UE5 像素流服务的桌面应用程序。它提供了友好的图形界面来管理信令服务和负载服务，支持多实例配置和系统托盘运行。

## 功能特点

- 图形化管理界面
- 信令服务和负载服务的启动/停止控制
- UE5实例的配置管理
- 系统托盘运行
- 开机自启动
- 支持亮色/暗色主题切换
- 实时日志显示
- 单例运行保护

## 环境要求

- Python 3.8+
- Node.js 14+
- Windows 操作系统

## 依赖库

pip install -r requirements.txt
主要依赖库
tkinter (Python 标准库)
Pillow==10.0.0
pystray==0.19.4
pywin32==306
win10toast==0.9.0
pyinstaller==6.3.0 # 用于打包

## 打包说明

1. 使用 package.py 打包（推荐）   

# 使用 Python 执行打包脚本
python package.py

2. 手动打包（不推荐）：
# 使用 pyinstaller 打包
pyinstaller --onefile --windowed --icon=resources/cloud.ico exePrograme.py

## 启动步骤

1. 开发环境运行：
   # 使用 Python 直接运行
python exePrograme.py


2. 打包后运行：
- 运行 dist 目录下的 exePrograme.exe
- 确保配置文件 (signal.json, theme.json) 在同目录
- 确保资源文件 (cloud.ico/cloud.png) 在 resources 目录

## 目录结构


PyDesktop/
├── exePrograme.py # 主程序
├── package.py # 打包脚本
├── requirements.txt # 依赖库列表
├── signal.json # 信令服务配置
├── theme.json # 主题和参数配置
├── resources/ # 资源文件目录
│ ├── cloud.ico # 程序图标
│ └── cloud.png # 备用图标
└── logs/ # 日志目录


## 配置文件

1. signal.json - 信令服务配置：
   {
"PORT": 10090,
"auth": false,
"one2one": false,
"preload": 0,
"UE5": []
}


2. theme.json - 主题和UE5参数配置：
    {
    "theme": "light",
    "autostart": {
    "signal": false,
    "exec-ue": false
    }
    }   

## 注意事项

1. 程序使用互斥锁确保单例运行
2. 关闭窗口默认最小化到系统托盘
3. 日志文件保存在 logs 目录
4. 支持中文路径
5. 需要管理员权限设置开机启动

## 常见问题

1. 程序无法启动
   - 检查 Python 版本
   - 检查依赖库是否完整
   - 检查配置文件是否存在

2. 无法显示图标
   - 确认 resources 目录中有图标文件
   - 检查图标文件权限

3. 服务启动失败
   - 检查 Node.js 是否安装
   - 检查端口是否被占用
   - 查看日志获取详细错误信息

