@echo off
chcp 65001 >nul
echo ===== 开始构建itch.io游戏iframe提取器 =====
echo.

REM 检查是否安装了必要的库
echo 正在检查必要的库...
python -m pip install cx_Freeze pyinstaller --upgrade

REM 创建必要的文件(如果不存在)
echo 检查必要的文件...
if not exist "LICENSE" (
    echo 创建LICENSE文件...
    echo MIT License > LICENSE
    echo. >> LICENSE
    echo Copyright (c) 2024 xm77233 >> LICENSE
)

echo.
echo 更新pip到最新版本...
python -m pip install --upgrade pip

REM 选择打包方式
echo.
echo 请选择打包方式:
echo 1. 使用cx_Freeze打包 (推荐)
echo 2. 使用PyInstaller打包
echo.
set /p choice=请输入数字选择 (1 或 2): 

if "%choice%"=="1" (
    echo.
    echo === 使用cx_Freeze打包 ===
    
    REM 修改setup.py中的include_files设置
    echo 临时修改setup.py...
    set TEMP_SETUP=setup_temp.py
    
    echo import sys > %TEMP_SETUP%
    echo from cx_Freeze import setup, Executable >> %TEMP_SETUP%
    echo. >> %TEMP_SETUP%
    echo # 依赖项和包 >> %TEMP_SETUP%
    echo build_exe_options = { >> %TEMP_SETUP%
    echo     "packages": ["os", "sys", "json", "time", "threading", "webbrowser", "datetime", "tkinter", "re", "html", "urllib"], >> %TEMP_SETUP%
    echo     "excludes": ["PyQt5", "PyQt6", "PySide6", "notebook"], >> %TEMP_SETUP%
    echo     "include_files": [], >> %TEMP_SETUP%
    echo     "include_msvcr": True, >> %TEMP_SETUP%
    echo } >> %TEMP_SETUP%
    echo. >> %TEMP_SETUP%
    echo # 添加README.md和LICENSE（如果存在） >> %TEMP_SETUP%
    echo import os >> %TEMP_SETUP%
    echo if os.path.exists("README.md"): >> %TEMP_SETUP%
    echo     build_exe_options["include_files"].append("README.md") >> %TEMP_SETUP%
    echo if os.path.exists("LICENSE"): >> %TEMP_SETUP%
    echo     build_exe_options["include_files"].append("LICENSE") >> %TEMP_SETUP%
    echo if os.path.exists("server.py"): >> %TEMP_SETUP%
    echo     build_exe_options["include_files"].append("server.py") >> %TEMP_SETUP%
    echo. >> %TEMP_SETUP%
    echo # 基本信息 >> %TEMP_SETUP%
    echo base = None >> %TEMP_SETUP%
    echo if sys.platform == "win32": >> %TEMP_SETUP%
    echo     base = "Win32GUI"  # 使用窗口应用程序，不显示控制台 >> %TEMP_SETUP%
    echo. >> %TEMP_SETUP%
    echo # 执行文件 >> %TEMP_SETUP%
    echo executables = [ >> %TEMP_SETUP%
    echo     Executable( >> %TEMP_SETUP%
    echo         "iframe_gui.py",  # 脚本文件名 >> %TEMP_SETUP%
    echo         base=base, >> %TEMP_SETUP%
    echo         target_name="IframeExtractor.exe",  # 生成的可执行文件名 >> %TEMP_SETUP%
    echo         shortcut_name="itch.io游戏iframe提取器", >> %TEMP_SETUP%
    echo         shortcut_dir="DesktopFolder", >> %TEMP_SETUP%
    echo     ) >> %TEMP_SETUP%
    echo ] >> %TEMP_SETUP%
    echo. >> %TEMP_SETUP%
    echo setup( >> %TEMP_SETUP%
    echo     name="itch.io游戏iframe提取器", >> %TEMP_SETUP%
    echo     version="1.0.0", >> %TEMP_SETUP%
    echo     description="一款用于提取itch.io游戏iframe源地址的工具", >> %TEMP_SETUP%
    echo     author="xm77233", >> %TEMP_SETUP%
    echo     options={"build_exe": build_exe_options}, >> %TEMP_SETUP%
    echo     executables=executables, >> %TEMP_SETUP%
    echo ) >> %TEMP_SETUP%
    
    echo 使用临时setup.py进行构建...
    python %TEMP_SETUP% build
    
    set BUILD_RESULT=%errorlevel%
    del %TEMP_SETUP%
    
    echo.
    if %BUILD_RESULT% NEQ 0 (
        echo 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%)
    ) else (
        echo 构建成功！
        echo 可执行文件位于 build 目录中
    )
) else if "%choice%"=="2" (
    echo.
    echo === 使用PyInstaller打包 ===
    
    REM 安装PyInstaller
    echo 正在安装PyInstaller...
    python -m pip install pyinstaller --upgrade
    
    REM 创建临时spec文件
    echo 创建临时spec文件...
    set TEMP_SPEC=temp_iframe.spec
    
    echo # -*- mode: python -*- > %TEMP_SPEC%
    echo block_cipher = None >> %TEMP_SPEC%
    echo. >> %TEMP_SPEC%
    echo import os >> %TEMP_SPEC%
    echo datas = [] >> %TEMP_SPEC%
    echo if os.path.exists('README.md'): >> %TEMP_SPEC%
    echo     datas.append(('README.md', '.')) >> %TEMP_SPEC%
    echo if os.path.exists('LICENSE'): >> %TEMP_SPEC%
    echo     datas.append(('LICENSE', '.')) >> %TEMP_SPEC%
    echo if os.path.exists('server.py'): >> %TEMP_SPEC%
    echo     datas.append(('server.py', '.')) >> %TEMP_SPEC%
    echo. >> %TEMP_SPEC%
    echo a = Analysis(['iframe_gui.py'], >> %TEMP_SPEC%
    echo              pathex=['%cd%'], >> %TEMP_SPEC%
    echo              binaries=[], >> %TEMP_SPEC%
    echo              datas=datas, >> %TEMP_SPEC%
    echo              hiddenimports=[], >> %TEMP_SPEC%
    echo              hookspath=[], >> %TEMP_SPEC%
    echo              runtime_hooks=[], >> %TEMP_SPEC%
    echo              excludes=[], >> %TEMP_SPEC%
    echo              win_no_prefer_redirects=False, >> %TEMP_SPEC%
    echo              win_private_assemblies=False, >> %TEMP_SPEC%
    echo              cipher=block_cipher, >> %TEMP_SPEC%
    echo              noarchive=False) >> %TEMP_SPEC%
    echo pyz = PYZ(a.pure, a.zipped_data, >> %TEMP_SPEC%
    echo           cipher=block_cipher) >> %TEMP_SPEC%
    echo exe = EXE(pyz, >> %TEMP_SPEC%
    echo           a.scripts, >> %TEMP_SPEC%
    echo           [], >> %TEMP_SPEC%
    echo           exclude_binaries=True, >> %TEMP_SPEC%
    echo           name='IframeExtractor', >> %TEMP_SPEC%
    echo           debug=False, >> %TEMP_SPEC%
    echo           bootloader_ignore_signals=False, >> %TEMP_SPEC%
    echo           strip=False, >> %TEMP_SPEC%
    echo           upx=True, >> %TEMP_SPEC%
    echo           console=False) >> %TEMP_SPEC%
    echo coll = COLLECT(exe, >> %TEMP_SPEC%
    echo                a.binaries, >> %TEMP_SPEC%
    echo                a.zipfiles, >> %TEMP_SPEC%
    echo                a.datas, >> %TEMP_SPEC%
    echo                strip=False, >> %TEMP_SPEC%
    echo                upx=True, >> %TEMP_SPEC%
    echo                upx_exclude=[], >> %TEMP_SPEC%
    echo                name='IframeExtractor') >> %TEMP_SPEC%
    
    REM 使用临时spec文件进行打包
    echo 开始打包...
    pyinstaller %TEMP_SPEC% --clean --noconfirm
    
    set BUILD_RESULT=%errorlevel%
    del %TEMP_SPEC%
    
    echo.
    if %BUILD_RESULT% NEQ 0 (
        echo 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%)
    ) else (
        echo 构建成功！
        echo 可执行文件位于 dist\IframeExtractor 目录中
    )
) else (
    echo 无效的选择，退出构建流程
    exit /b 1
)

echo.
echo ===== 构建过程已完成 =====
pause 