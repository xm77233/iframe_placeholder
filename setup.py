import sys
from cx_Freeze import setup, Executable

# 依赖项和包
build_exe_options = {
    "packages": ["os", "sys", "json", "time", "threading", "webbrowser", "datetime", "tkinter", "re", "html", "urllib"],
    "excludes": ["PyQt5", "PyQt6", "PySide6", "notebook"],
    "include_files": ["README.md", "LICENSE"],
    "include_msvcr": True,
}

# 基本信息
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 使用窗口应用程序，不显示控制台

# 执行文件
executables = [
    Executable(
        "iframe_gui.py",  # 脚本文件名
        base=base,
        target_name="IframeExtractor.exe",  # 生成的可执行文件名
        icon="icon.ico",  # 图标文件（如果有）
        shortcut_name="itch.io游戏iframe提取器",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="itch.io游戏iframe提取器",
    version="1.0.0",
    description="一款用于提取itch.io游戏iframe源地址的工具",
    author="xm77233",
    options={"build_exe": build_exe_options},
    executables=executables,
) 