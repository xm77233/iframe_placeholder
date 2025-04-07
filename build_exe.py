#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将itch.io游戏iframe提取器打包为可执行文件
"""

import sys
import os
import shutil
import subprocess
import platform

def main():
    """主函数"""
    print("=== itch.io游戏iframe提取器打包工具 ===")
    print("本工具将帮助您将应用打包为可执行文件")
    print()
    
    # 检查是否安装了PyInstaller
    print("正在检查PyInstaller...")
    try:
        import PyInstaller
        print("PyInstaller已安装 √")
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
            print("PyInstaller安装成功 √")
        except Exception as e:
            print(f"安装PyInstaller失败: {e}")
            print("请手动安装PyInstaller: pip install PyInstaller")
            input("按Enter键退出...")
            return
    
    # 检查必要的文件是否存在
    required_files = ["iframe_scraper.py", "iframe_scraper_gui.py"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"错误: 缺少以下必要文件: {', '.join(missing_files)}")
        input("按Enter键退出...")
        return
    
    # 创建打包目录
    build_dir = "build"
    dist_dir = "dist"
    
    # 清理旧的构建文件
    for dir_to_clean in [build_dir, dist_dir]:
        if os.path.exists(dir_to_clean):
            print(f"清理{dir_to_clean}目录...")
            try:
                shutil.rmtree(dir_to_clean)
                print(f"{dir_to_clean}目录已清理 √")
            except Exception as e:
                print(f"清理{dir_to_clean}目录失败: {e}")
    
    # 检测系统类型
    system = platform.system()
    icon_option = []
    
    if system == "Windows":
        icon_file = "icon.ico"
        if not os.path.exists(icon_file):
            print("未找到图标文件(icon.ico)，将使用默认图标")
        else:
            icon_option = ["--icon", icon_file]
    elif system == "Darwin":  # macOS
        icon_file = "icon.icns"
        if not os.path.exists(icon_file):
            print("未找到图标文件(icon.icns)，将使用默认图标")
        else:
            icon_option = ["--icon", icon_file]
    
    # 创建临时的hooks文件，确保urllib.request模块被正确包含
    hooks_dir = "hooks"
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)
    
    with open(os.path.join(hooks_dir, "hook-urllib.py"), "w") as f:
        f.write("""
# 确保urllib的所有子模块都被包含
hiddenimports = [
    'urllib.request',
    'urllib.error',
    'urllib.parse',
    'urllib.robotparser'
]
""")
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--additional-hooks-dir={hooks_dir}",
        "--name", "itch.io游戏iframe提取器",
        "--add-data", f"iframe_scraper.py{os.pathsep}.",
        "--hidden-import", "urllib.request",
        "--hidden-import", "urllib.error",
        "--hidden-import", "urllib.parse",
        "--hidden-import", "html.parser",
        "--hidden-import", "json",
        "--hidden-import", "os",
        "--hidden-import", "time",
        "--hidden-import", "re",
        "--hidden-import", "logging",
    ]
    
    # 添加图标选项
    cmd.extend(icon_option)
    
    # 添加主脚本
    cmd.append("iframe_scraper_gui.py")
    
    print("\n开始构建...")
    print("运行命令:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        
        # 清理临时hooks目录
        if os.path.exists(hooks_dir):
            shutil.rmtree(hooks_dir)
        
        print("\n构建成功! √")
        
        # 获取生成的可执行文件路径
        if system == "Windows":
            exe_path = os.path.join(dist_dir, "itch.io游戏iframe提取器.exe")
        else:
            exe_path = os.path.join(dist_dir, "itch.io游戏iframe提取器")
        
        print(f"\n可执行文件位置: {os.path.abspath(exe_path)}")
        
        # 提示打开目录
        print("\n您可以:")
        print(f"1. 打开输出目录: {os.path.abspath(dist_dir)}")
        print("2. 直接运行程序")
        print("3. 退出")
        
        choice = input("\n请选择 (1/2/3): ")
        
        if choice == "1":
            # 打开输出目录
            if system == "Windows":
                os.startfile(os.path.abspath(dist_dir))
            elif system == "Darwin":  # macOS
                subprocess.call(["open", os.path.abspath(dist_dir)])
            else:  # Linux
                subprocess.call(["xdg-open", os.path.abspath(dist_dir)])
        elif choice == "2":
            # 运行程序
            print("正在启动程序...")
            if system == "Windows":
                subprocess.Popen([exe_path])
            else:
                subprocess.Popen([exe_path])
    
    except Exception as e:
        print(f"\n构建失败: {e}")
        input("按Enter键退出...")
        return
    
    print("\n感谢使用构建工具!")

if __name__ == "__main__":
    main() 