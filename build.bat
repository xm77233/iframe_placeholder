@echo off
setlocal enabledelayedexpansion

REM 设置UTF-8编码
chcp 65001 >nul

echo ===== 开始构建itch.io游戏iframe提取器 =====
echo.

REM 创建日志文件
set LOG_FILE=build_log.txt
echo 构建日志 - %date% %time% > %LOG_FILE%
echo ================================== >> %LOG_FILE%

REM 捕获错误
set ERROR_OCCURED=0

REM 检查Python是否安装
echo 检查Python环境...
echo 检查Python环境... >> %LOG_FILE%
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中！
    echo [错误] Python未安装或不在PATH中！ >> %LOG_FILE%
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。 >> %LOG_FILE%
    set ERROR_OCCURED=1
    goto end
)

echo Python环境正常
echo Python环境正常 >> %LOG_FILE%
python --version >> %LOG_FILE% 2>&1
echo. >> %LOG_FILE%

REM 创建必要的文件(如果不存在)
echo 检查必要的文件...
echo 检查必要的文件... >> %LOG_FILE%
if not exist "LICENSE" (
    echo 创建LICENSE文件...
    echo 创建LICENSE文件... >> %LOG_FILE%
    echo MIT License > LICENSE
    echo. >> LICENSE
    echo Copyright (c) 2024 xm77233 >> LICENSE
    echo LICENSE文件创建成功
    echo LICENSE文件创建成功 >> %LOG_FILE%
) else (
    echo LICENSE文件已存在
    echo LICENSE文件已存在 >> %LOG_FILE%
)

echo 检查iframe_gui.py文件...
echo 检查iframe_gui.py文件... >> %LOG_FILE%
if not exist "iframe_gui.py" (
    echo [错误] iframe_gui.py文件不存在！
    echo [错误] iframe_gui.py文件不存在！ >> %LOG_FILE%
    set ERROR_OCCURED=1
    goto end
) else (
    echo iframe_gui.py文件存在
    echo iframe_gui.py文件存在 >> %LOG_FILE%
)

REM 创建一个虚拟目录用于构建
if not exist "build_env" mkdir build_env
cd build_env

REM 安装必要的库（分开安装，以便于查看哪一步出错）
echo 正在安装必要的库...
echo 正在安装必要的库... >> ..\%LOG_FILE%
echo 安装pip...
echo 安装pip... >> ..\%LOG_FILE%
python -m pip install --upgrade pip >> ..\%LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 更新pip失败，但将继续...
    echo [警告] 更新pip失败，但将继续... >> ..\%LOG_FILE%
)

echo 安装cx_Freeze...
echo 安装cx_Freeze... >> ..\%LOG_FILE%
python -m pip install cx_Freeze >> ..\%LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 安装cx_Freeze失败，但将尝试继续...
    echo [警告] 安装cx_Freeze失败，但将尝试继续... >> ..\%LOG_FILE%
)

echo 安装PyInstaller...
echo 安装PyInstaller... >> ..\%LOG_FILE%
python -m pip install pyinstaller >> ..\%LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 安装PyInstaller失败，但将尝试继续...
    echo [警告] 安装PyInstaller失败，但将尝试继续... >> ..\%LOG_FILE%
)

cd ..

REM 选择打包方式
echo. >> %LOG_FILE%
echo.
echo 请选择打包方式:
echo 1. 使用cx_Freeze打包 (推荐)
echo 2. 使用PyInstaller打包
echo.
set /p choice=请输入数字选择 (1 或 2): 
echo 用户选择: %choice% >> %LOG_FILE%

if "%choice%"=="1" (
    echo.
    echo === 使用cx_Freeze打包 ===
    echo. >> %LOG_FILE%
    echo === 使用cx_Freeze打包 === >> %LOG_FILE%
    
    REM 修改setup.py中的include_files设置
    echo 临时修改setup.py...
    echo 临时修改setup.py... >> %LOG_FILE%
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
    echo 使用临时setup.py进行构建... >> %LOG_FILE%
    echo 执行命令: python %TEMP_SETUP% build >> %LOG_FILE%
    python %TEMP_SETUP% build >> %LOG_FILE% 2>&1
    
    set BUILD_RESULT=%errorlevel%
    echo 构建结果代码: %BUILD_RESULT% >> %LOG_FILE%
    
    del %TEMP_SETUP%
    
    echo.
    echo. >> %LOG_FILE%
    if %BUILD_RESULT% NEQ 0 (
        echo [错误] 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%)
        echo [错误] 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%) >> %LOG_FILE%
        echo 详细信息请查看日志文件: %LOG_FILE%
        set ERROR_OCCURED=1
    ) else (
        echo 构建成功！
        echo 可执行文件位于 build 目录中
        echo 构建成功！ >> %LOG_FILE%
        echo 可执行文件位于 build 目录中 >> %LOG_FILE%
    )
) else if "%choice%"=="2" (
    echo.
    echo === 使用PyInstaller打包 ===
    echo. >> %LOG_FILE%
    echo === 使用PyInstaller打包 === >> %LOG_FILE%
    
    REM 创建临时spec文件
    echo 创建临时spec文件...
    echo 创建临时spec文件... >> %LOG_FILE%
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
    echo 开始打包... >> %LOG_FILE%
    echo 执行命令: pyinstaller %TEMP_SPEC% --clean --noconfirm >> %LOG_FILE%
    pyinstaller %TEMP_SPEC% --clean --noconfirm >> %LOG_FILE% 2>&1
    
    set BUILD_RESULT=%errorlevel%
    echo 构建结果代码: %BUILD_RESULT% >> %LOG_FILE%
    
    del %TEMP_SPEC%
    
    echo.
    echo. >> %LOG_FILE%
    if %BUILD_RESULT% NEQ 0 (
        echo [错误] 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%)
        echo [错误] 构建失败，请检查错误信息 (错误代码: %BUILD_RESULT%) >> %LOG_FILE%
        echo 详细信息请查看日志文件: %LOG_FILE%
        set ERROR_OCCURED=1
    ) else (
        echo 构建成功！
        echo 可执行文件位于 dist\IframeExtractor 目录中
        echo 构建成功！ >> %LOG_FILE%
        echo 可执行文件位于 dist\IframeExtractor 目录中 >> %LOG_FILE%
    )
) else (
    echo 无效的选择，退出构建流程
    echo 无效的选择，退出构建流程 >> %LOG_FILE%
    set ERROR_OCCURED=1
)

:end
echo.
echo. >> %LOG_FILE%
echo ===== 构建过程已完成 ===== >> %LOG_FILE%
echo ===== 构建过程已完成 =====

if %ERROR_OCCURED% equ 1 (
    echo.
    echo [警告] 构建过程中发生错误，请查看日志文件: %LOG_FILE%
    echo. >> %LOG_FILE%
    echo [警告] 构建过程中发生错误，请查看日志文件: %LOG_FILE% >> %LOG_FILE%
)

echo.
echo 请按任意键继续...
pause > nul

endlocal 