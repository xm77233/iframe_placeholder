@echo off
chcp 65001 >nul
echo ===== 安装itch.io游戏iframe提取器所需依赖 =====
echo.

REM 创建日志文件
set LOG_FILE=install_deps_log.txt
echo 安装日志 - %date% %time% > %LOG_FILE%
echo ================================== >> %LOG_FILE%

REM 检查Python是否安装
echo 检查Python环境...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中！ | tee -a %LOG_FILE%
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。
    echo 您可以从 https://www.python.org/downloads/ 下载Python。
    echo 安装时请勾选"Add Python to PATH"选项。
    goto end
)

echo Python环境正常 | tee -a %LOG_FILE%
python --version >> %LOG_FILE% 2>&1

echo.
echo 开始安装必要的依赖... | tee -a %LOG_FILE%

echo 1. 更新pip... | tee -a %LOG_FILE%
python -m pip install --upgrade pip >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 更新pip失败，但将继续尝试安装其他依赖。 | tee -a %LOG_FILE%
) else (
    echo pip更新成功 | tee -a %LOG_FILE%
)

echo 2. 安装必要的Python库... | tee -a %LOG_FILE%

echo 安装cx_Freeze... | tee -a %LOG_FILE%
python -m pip install cx_Freeze >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 安装cx_Freeze失败 | tee -a %LOG_FILE%
) else (
    echo cx_Freeze安装成功 | tee -a %LOG_FILE%
)

echo 安装PyInstaller... | tee -a %LOG_FILE%
python -m pip install pyinstaller >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [警告] 安装PyInstaller失败 | tee -a %LOG_FILE%
) else (
    echo PyInstaller安装成功 | tee -a %LOG_FILE%
)

echo.
echo 安装完成 | tee -a %LOG_FILE%

echo.
echo 您可以通过以下步骤测试环境是否正常：
echo 1. 运行 test_environment.bat 测试环境
echo 2. 如果测试正常，运行 build.bat 构建可执行文件

:end
echo.
echo 详细日志已保存至: %LOG_FILE%
echo.
echo ===== 安装过程已完成 =====
echo 按任意键退出...
pause > nul 