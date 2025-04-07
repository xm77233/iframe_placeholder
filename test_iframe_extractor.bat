@echo off
chcp 65001 >nul
echo ===== 测试itch.io游戏iframe提取器 =====
echo.

REM 设置日志文件
set LOG_FILE=test_extractor_log.txt
echo 测试日志 - %date% %time% > %LOG_FILE%
echo ================================== >> %LOG_FILE%

REM 检查Python是否安装
echo 检查Python环境...
echo 检查Python环境... >> %LOG_FILE%
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中！
    echo [错误] Python未安装或不在PATH中！ >> %LOG_FILE%
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。
    echo 请安装Python 3.6或更高版本并确保添加到PATH环境变量。 >> %LOG_FILE%
    goto end
)

echo Python环境正常
echo Python环境正常 >> %LOG_FILE%
python --version >> %LOG_FILE% 2>&1
echo. >> %LOG_FILE%

REM 检查必要的文件是否存在
echo 检查必要的文件...
echo 检查必要的文件... >> %LOG_FILE%

echo 检查iframe_gui.py...
echo 检查iframe_gui.py... >> %LOG_FILE%
if not exist "iframe_gui.py" (
    echo [错误] iframe_gui.py文件不存在！
    echo [错误] iframe_gui.py文件不存在！ >> %LOG_FILE%
    goto end
) else (
    echo iframe_gui.py文件存在
    echo iframe_gui.py文件存在 >> %LOG_FILE%
)

REM 创建简单的测试脚本
echo 创建临时测试脚本...
echo 创建临时测试脚本... >> %LOG_FILE%
set TEMP_SCRIPT=temp_test_script.py

echo import os > %TEMP_SCRIPT%
echo import sys >> %TEMP_SCRIPT%
echo import json >> %TEMP_SCRIPT%
echo from datetime import datetime >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%

echo # 尝试导入爬虫类 >> %TEMP_SCRIPT%
echo try: >> %TEMP_SCRIPT%
echo     # 首先尝试从server模块导入 >> %TEMP_SCRIPT%
echo     try: >> %TEMP_SCRIPT%
echo         from server import FastItchIoScraper >> %TEMP_SCRIPT%
echo         print("从server.py导入FastItchIoScraper成功") >> %TEMP_SCRIPT%
echo     except ImportError: >> %TEMP_SCRIPT%
echo         # 然后尝试从iframe_gui模块导入 >> %TEMP_SCRIPT%
echo         sys.path.append(os.path.abspath('.')) >> %TEMP_SCRIPT%
echo         from iframe_gui import FastItchIoScraper >> %TEMP_SCRIPT%
echo         print("从iframe_gui.py导入FastItchIoScraper成功") >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo     # 创建爬取器实例 >> %TEMP_SCRIPT%
echo     print("创建爬取器实例...") >> %TEMP_SCRIPT%
echo     scraper = FastItchIoScraper(max_games=2, start_offset=0, delay=1.0) >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo     # 开始爬取 >> %TEMP_SCRIPT%
echo     print("开始爬取...") >> %TEMP_SCRIPT%
echo     start_time = datetime.now() >> %TEMP_SCRIPT%
echo     results, stats = scraper.scrape() >> %TEMP_SCRIPT%
echo     end_time = datetime.now() >> %TEMP_SCRIPT%
echo     elapsed = (end_time - start_time).total_seconds() >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo     # 显示结果 >> %TEMP_SCRIPT%
echo     print("\n==== 爬取结果 ====") >> %TEMP_SCRIPT%
echo     print(f"总处理游戏: {stats['total_processed']}") >> %TEMP_SCRIPT%
echo     print(f"成功提取iframe: {stats['successful_extractions']}") >> %TEMP_SCRIPT%
echo     print(f"耗时: {elapsed:.2f}秒") >> %TEMP_SCRIPT%
echo     print() >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo     # 显示查找到的iframe >> %TEMP_SCRIPT%
echo     if results: >> %TEMP_SCRIPT%
echo         print("提取到的iframe:") >> %TEMP_SCRIPT%
echo         for i, result in enumerate(results, 1): >> %TEMP_SCRIPT%
echo             print(f"{i}. {result['title']}") >> %TEMP_SCRIPT%
echo             print(f"   URL: {result['url']}") >> %TEMP_SCRIPT%
echo             print(f"   iframe源: {result['iframe_src']}") >> %TEMP_SCRIPT%
echo             print(f"   提取方法: {result.get('extracted_method', 'unknown')}") >> %TEMP_SCRIPT%
echo             print() >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo         # 保存结果到文件 >> %TEMP_SCRIPT%
echo         result_file = f"test_results_{datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S')}.json" >> %TEMP_SCRIPT%
echo         with open(result_file, 'w', encoding='utf-8') as f: >> %TEMP_SCRIPT%
echo             json.dump({"results": results, "stats": stats}, f, indent=2, ensure_ascii=False) >> %TEMP_SCRIPT%
echo         print(f"结果已保存到: {result_file}") >> %TEMP_SCRIPT%
echo     else: >> %TEMP_SCRIPT%
echo         print("未找到任何iframe") >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo except Exception as e: >> %TEMP_SCRIPT%
echo     import traceback >> %TEMP_SCRIPT%
echo     print(f"错误: {e}") >> %TEMP_SCRIPT%
echo     print(traceback.format_exc()) >> %TEMP_SCRIPT%
echo. >> %TEMP_SCRIPT%
echo input("按Enter键退出...") >> %TEMP_SCRIPT%

REM 运行测试脚本
echo 运行测试脚本...
echo 运行测试脚本... >> %LOG_FILE%
echo 执行命令: python %TEMP_SCRIPT% >> %LOG_FILE%

REM 使用重定向而非tee命令，同时保存和显示输出
echo 执行测试并保存结果到test_results.txt...
python %TEMP_SCRIPT% > test_results.txt
set TEST_RESULT=%errorlevel%
echo 测试结果代码: %TEST_RESULT% >> %LOG_FILE%

REM 显示测试结果
echo.
echo 测试结果:
echo -------------------
type test_results.txt
echo -------------------

REM 清理临时文件
del %TEMP_SCRIPT%

echo.
echo ===== 测试完成 =====
echo 查看"debug_html"目录中的HTML文件和"logs"目录中的日志文件可以了解更多细节。

:end
echo.
echo 详细日志已保存至: %LOG_FILE%
echo 按任意键继续...
pause > nul 