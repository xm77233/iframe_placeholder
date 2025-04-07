@echo off
chcp 65001 >nul
echo ===== itch.io游戏iframe提取器环境测试 =====
echo.

REM 检查Python是否安装
echo 1. 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中！
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。
    goto end
) else (
    echo Python环境正常
)

echo.
echo 2. 检查必要的库是否安装...

echo 检查tkinter...
python -c "import tkinter" 2>nul
if %errorlevel% neq 0 (
    echo [警告] tkinter库可能未安装！GUI界面将无法运行。
    echo 请确保安装了带有tkinter的Python版本。
) else (
    echo tkinter正常
)

echo.
echo 3. 检查项目文件是否存在...

echo 检查iframe_gui.py...
if not exist "iframe_gui.py" (
    echo [错误] iframe_gui.py文件不存在！主程序无法运行。
) else (
    echo iframe_gui.py存在
)

echo 检查server.py...
if not exist "server.py" (
    echo [警告] server.py文件不存在！将使用内置爬虫备份。
) else (
    echo server.py存在
)

echo.
echo 4. 测试启动GUI应用...
echo (这将尝试打开GUI窗口，请稍候几秒钟)
echo 如果没有显示GUI窗口，可能存在兼容性问题。
echo.
echo 按任意键开始测试，或关闭窗口退出...
pause > nul

start /b python iframe_gui.py

echo.
echo 5. 环境测试已完成
echo 如果GUI窗口成功打开，则说明环境正常，可以继续构建可执行文件。
echo 如果有错误或警告，请先解决后再尝试打包。

:end
echo.
echo ===== 测试结束 =====
echo 按任意键退出...
pause > nul 