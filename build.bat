@echo off
echo ===== 开始构建itch.io游戏iframe提取器 =====
echo.

REM 检查是否安装了必要的库
echo 正在检查必要的库...
python -m pip install cx_Freeze pyinstaller --upgrade

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
    python setup.py build
    
    echo.
    if errorlevel 1 (
        echo 构建失败，请检查错误信息
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
    
    REM 使用PyInstaller打包
    echo 开始打包...
    pyinstaller --name="IframeExtractor" ^
                --windowed ^
                --add-data="README.md;." ^
                --add-data="LICENSE;." ^
                --clean ^
                --noconfirm ^
                iframe_gui.py
    
    echo.
    if errorlevel 1 (
        echo 构建失败，请检查错误信息
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