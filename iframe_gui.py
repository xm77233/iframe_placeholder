import os
import sys
import json
import time
import threading
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import urllib.request
import urllib.error
import re
import html
import random
import traceback

# 导入iframe_scraper模块的核心功能
# 尝试多种方式导入FastItchIoScraper
success = False

# 方式1：直接从server模块导入
try:
    from server import FastItchIoScraper
    success = True
    print("成功从server模块导入FastItchIoScraper")
except ImportError:
    print("无法直接从server模块导入FastItchIoScraper，尝试其他方法...")

# 方式2：相对路径导入
if not success:
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 将当前目录添加到sys.path
        sys.path.append(current_dir)
        # 再次尝试导入
        from server import FastItchIoScraper
        success = True
        print(f"成功从 {current_dir} 导入FastItchIoScraper")
    except ImportError:
        print(f"无法从 {current_dir} 导入FastItchIoScraper")

# 方式3：创建一个简化版的爬虫实现
if not success:
    try:
        print("使用自定义爬虫类作为后备...")
        
        # 创建文件夹
        RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        DEBUG_HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_html")
        
        for directory in [RESULTS_DIR, LOGS_DIR, DEBUG_HTML_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                
        # 用户代理列表
        USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
        class FastItchIoScraper:
            """自定义itch.io游戏iframe源爬取器"""
            
            def __init__(self, max_games=5, start_offset=0, delay=0.5):
                """
                初始化爬取器
                
                Args:
                    max_games: 最多爬取的游戏数量
                    start_offset: 起始偏移量
                    delay: 请求间隔时间(秒)
                """
                self.max_games = max_games
                self.start_offset = start_offset
                self.delay = delay
                self.results = []
                self.processed_count = 0
                self.successful_count = 0
                self.start_time = datetime.now()
                self.debug_save_html = True  # 保存HTML用于调试
                
                # 创建日志文件
                self.log_file = os.path.join(LOGS_DIR, f"scraper_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write(f"爬虫日志 - 开始时间: {self.start_time}\n")
                    f.write(f"参数: max_games={max_games}, start_offset={start_offset}, delay={delay}\n")
                    f.write("="*50 + "\n")
            
            def log(self, message):
                """写入日志"""
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_message = f"[{timestamp}] {message}"
                print(log_message)
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_message + "\n")
                except Exception as e:
                    print(f"写入日志失败: {e}")
            
            def get_random_user_agent(self):
                """随机获取一个User-Agent"""
                return random.choice(USER_AGENTS)
            
            def fetch_url(self, url):
                """获取URL内容，增加重试机制"""
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        headers = {
                            'User-Agent': self.get_random_user_agent(),
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Cache-Control': 'max-age=0'
                        }
                        
                        self.log(f"获取URL: {url} (尝试 {retry_count+1}/{max_retries})")
                        
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=15) as response:
                            html_content = response.read().decode('utf-8')
                            
                            # 保存HTML用于调试
                            if self.debug_save_html:
                                try:
                                    # 从URL中提取游戏名称或页面类型
                                    filename = url.split('/')[-1] if '/' in url else 'page'
                                    if '?' in filename:
                                        filename = filename.split('?')[0]
                                    if not filename:
                                        filename = 'index'
                                    
                                    # 添加时间戳避免覆盖
                                    timestamp = datetime.now().strftime("%H%M%S")
                                    debug_file = os.path.join(DEBUG_HTML_DIR, f"{filename}_{timestamp}.html")
                                    
                                    with open(debug_file, 'w', encoding='utf-8') as f:
                                        f.write(html_content)
                                        
                                    self.log(f"保存HTML到 {debug_file}")
                                except Exception as e:
                                    self.log(f"保存HTML失败: {e}")
                            
                            return html_content
                    except Exception as e:
                        self.log(f"获取URL {url} 失败: {str(e)}")
                        error_details = traceback.format_exc()
                        self.log(f"详细错误: {error_details}")
                        
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = retry_count * 2
                            self.log(f"等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                        else:
                            self.log(f"达到最大重试次数，放弃获取URL: {url}")
                
                return ""
            
            def get_game_page_urls(self):
                """获取游戏页面URL列表"""
                offset = self.start_offset
                games = []
                
                self.log(f"开始获取游戏列表 - 最大数量: {self.max_games}, 偏移量: {offset}")
                
                # 尝试不同的页面类型
                page_types = [
                    (f"https://itch.io/games/free/platform-web?offset={offset}", "普通自由网页游戏"),
                    (f"https://itch.io/games/top-rated/free/platform-web?offset={offset}", "排名最高网页游戏"),
                    (f"https://itch.io/games/genre-action/free/platform-web?offset={offset}", "动作类游戏"),
                    (f"https://itch.io/games/genre-puzzle/free/platform-web?offset={offset}", "解谜类游戏")
                ]
                
                # 从列表中尝试不同的页面类型，直到获取足够的游戏
                for url_template, description in page_types:
                    if len(games) >= self.max_games:
                        break
                        
                    self.log(f"尝试从 {description} 列表获取游戏 (URL: {url_template})")
                    
                    try:
                        html_content = self.fetch_url(url_template)
                        if not html_content:
                            self.log(f"无法获取 {description} 列表HTML内容")
                            continue
                        
                        self.log(f"成功获取 {description} 列表HTML内容，长度: {len(html_content)} 字符")
                        
                        # 使用正则表达式查找游戏信息
                        # 查找游戏卡片
                        game_cells = re.finditer(r'<div class="game_cell"[^>]*>.*?<a\s+class="game_link"\s+href="([^"]+)"[^>]*>.*?<div class="game_title"[^>]*>(.*?)</div>', html_content, re.DOTALL)
                        
                        for match in game_cells:
                            if len(games) >= self.max_games:
                                break
                                
                            game_url = match.group(1)
                            game_title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                            
                            # 确保URL是绝对路径
                            if not game_url.startswith('http'):
                                game_url = 'https://itch.io' + game_url
                            
                            games.append({
                                'url': game_url,
                                'title': game_title
                            })
                            
                            self.log(f"找到游戏: {game_title} - {game_url}")
                        
                        # 作为备选方案，寻找任何游戏链接
                        if len(games) == 0:
                            self.log("未找到游戏卡片，尝试查找任何游戏链接...")
                            game_links = re.finditer(r'<a[^>]*href="(https://[^"]+\.itch\.io/[^"]+)"[^>]*>(.*?)</a>', html_content, re.DOTALL)
                            
                            for match in game_links:
                                if len(games) >= self.max_games:
                                    break
                                    
                                game_url = match.group(1)
                                game_title_html = match.group(2)
                                
                                # 清理HTML标签
                                game_title = re.sub(r'<[^>]+>', '', game_title_html).strip()
                                if not game_title:
                                    game_title = f"游戏 {len(games) + 1}"
                                
                                # 避免重复
                                if not any(g['url'] == game_url for g in games):
                                    games.append({
                                        'url': game_url,
                                        'title': game_title
                                    })
                                    self.log(f"找到游戏链接: {game_title} - {game_url}")
                        
                        if games:
                            # 如果这个来源找到了游戏，就不再尝试其他来源
                            self.log(f"从 {description} 来源找到 {len(games)} 个游戏，停止搜索其他来源")
                            break
                    except Exception as e:
                        self.log(f"获取 {description} 列表失败: {e}")
                        error_details = traceback.format_exc()
                        self.log(f"详细错误: {error_details}")
                
                self.log(f"总共提取 {len(games)} 个游戏信息")
                return games
            
            def get_iframe_src(self, game_page_html, game_url):
                """从游戏页面中提取iframe源"""
                iframe_src = None
                extraction_method = "unknown"
                
                self.log(f"开始提取iframe源 - {game_url}")
                
                # 方法1: 检查html_embed区域中的iframe标签
                if not iframe_src:
                    try:
                        self.log("尝试方法1: html_embed > iframe")
                        match = re.search(r'<div[^>]*id=["\'](html_embed_content|html_embed)["\']\s*[^>]*>[\s\S]*?<iframe[^>]*src=["\'](.*?)["\']', game_page_html, re.DOTALL)
                        if match:
                            iframe_src = html.unescape(match.group(2))
                            extraction_method = "html_embed_iframe"
                            self.log(f"方法1成功: {iframe_src}")
                        else:
                            self.log("方法1未找到匹配")
                    except Exception as e:
                        self.log(f"方法1出错: {e}")
                
                # 方法2: 检查data-iframe属性
                if not iframe_src:
                    try:
                        self.log("尝试方法2: data-iframe属性")
                        match = re.search(r'<div[^>]*data-iframe=["\'](.*?)["\']', game_page_html, re.DOTALL)
                        if match:
                            iframe_data = html.unescape(match.group(1))
                            # 从iframe HTML中提取src
                            src_match = re.search(r'<iframe[^>]*src=["\'](.*?)["\']', iframe_data, re.DOTALL)
                            if src_match:
                                iframe_src = html.unescape(src_match.group(1))
                                extraction_method = "data_iframe"
                                self.log(f"方法2成功: {iframe_src}")
                            else:
                                self.log("方法2找到data-iframe但无法提取src")
                        else:
                            self.log("方法2未找到匹配")
                    except Exception as e:
                        self.log(f"方法2出错: {e}")
                
                # 方法3: 直接搜索所有iframe标签
                if not iframe_src:
                    try:
                        self.log("尝试方法3: 搜索所有iframe标签")
                        matches = re.finditer(r'<iframe[^>]*src=["\'](.*?)["\'][^>]*>', game_page_html, re.DOTALL)
                        for match in matches:
                            potential_src = html.unescape(match.group(1))
                            # 过滤掉不相关的iframe
                            if 'itch.io/embed' in potential_src or 'itch.io/embed-upload' in potential_src:
                                iframe_src = potential_src
                                extraction_method = "any_iframe"
                                self.log(f"方法3成功: {iframe_src}")
                                break
                        
                        if not iframe_src:
                            self.log("方法3未找到匹配")
                    except Exception as e:
                        self.log(f"方法3出错: {e}")
                
                # 方法4: 检查游戏下载或播放按钮链接
                if not iframe_src:
                    try:
                        self.log("尝试方法4: 游戏下载或播放按钮")
                        match = re.search(r'<a[^>]*class=["\'](button play_game|iframe_placeholder)["\'][^>]*href=["\'](.*?)["\']', game_page_html, re.DOTALL)
                        if match:
                            play_url = html.unescape(match.group(2))
                            # 判断是否为内嵌iframe的URL
                            if 'itch.io/embed' in play_url or 'itch.io/embed-upload' in play_url:
                                iframe_src = play_url
                                extraction_method = "play_button"
                                self.log(f"方法4成功: {iframe_src}")
                            else:
                                self.log(f"方法4找到按钮但链接不是iframe: {play_url}")
                        else:
                            self.log("方法4未找到匹配")
                    except Exception as e:
                        self.log(f"方法4出错: {e}")
                
                # 方法5: 检查JavaScript中的iframe URL
                if not iframe_src:
                    try:
                        self.log("尝试方法5: JavaScript中的iframe URL")
                        match = re.search(r'iframe_url\s*=\s*["\']([^"\']*)["\']', game_page_html, re.DOTALL)
                        if match:
                            iframe_src = html.unescape(match.group(1))
                            extraction_method = "js_iframe_url"
                            self.log(f"方法5成功: {iframe_src}")
                        else:
                            self.log("方法5未找到匹配")
                    except Exception as e:
                        self.log(f"方法5出错: {e}")
                
                # 方法6: 检查嵌入代码中的iframe
                if not iframe_src:
                    try:
                        self.log("尝试方法6: 嵌入代码中的iframe")
                        match = re.search(r'<textarea[^>]*class=["\']embed_code["\'][^>]*>(.*?)</textarea>', game_page_html, re.DOTALL)
                        if match:
                            embed_code = html.unescape(match.group(1))
                            src_match = re.search(r'src=["\'](.*?)["\']', embed_code, re.DOTALL)
                            if src_match:
                                iframe_src = html.unescape(src_match.group(1))
                                extraction_method = "embed_code"
                                self.log(f"方法6成功: {iframe_src}")
                            else:
                                self.log("方法6找到嵌入代码但无法提取src")
                        else:
                            self.log("方法6未找到匹配")
                    except Exception as e:
                        self.log(f"方法6出错: {e}")
                
                if iframe_src:
                    # 确保URL是绝对路径
                    if not iframe_src.startswith('http'):
                        iframe_src = 'https:' + iframe_src if iframe_src.startswith('//') else 'https://itch.io' + iframe_src
                    
                    self.log(f"成功提取iframe源: {iframe_src} (方法: {extraction_method})")
                    return iframe_src, extraction_method
                else:
                    self.log("所有方法都失败，未找到iframe源")
                    return None, "failed"
            
            def process_game(self, game):
                """处理单个游戏，提取iframe源"""
                self.processed_count += 1
                
                game_url = game['url']
                game_title = game['title']
                
                self.log(f"处理游戏 {self.processed_count}/{self.max_games}: {game_title}")
                
                # 获取游戏页面内容
                game_page_html = self.fetch_url(game_url)
                if not game_page_html:
                    self.log(f"无法获取游戏页面: {game_url}")
                    return None
                
                # 提取iframe源
                iframe_src, extraction_method = self.get_iframe_src(game_page_html, game_url)
                
                if iframe_src:
                    self.successful_count += 1
                    result = {
                        'title': game_title,
                        'url': game_url,
                        'iframe_src': iframe_src,
                        'extracted_method': extraction_method
                    }
                    self.log(f"成功提取: {game_title} - {iframe_src}")
                    return result
                else:
                    self.log(f"无法提取iframe源: {game_title}")
                    return None
            
            def scrape(self):
                """执行爬取过程"""
                self.log(f"开始爬取 - 最大游戏数: {self.max_games}, 起始偏移: {self.start_offset}")
                
                # 获取游戏页面URL列表
                games = self.get_game_page_urls()
                
                if not games:
                    self.log("未找到任何游戏")
                    end_time = datetime.now()
                    elapsed_time = (end_time - self.start_time).total_seconds()
                    stats = {
                        "total_processed": 0,
                        "successful_extractions": 0,
                        "elapsed_seconds": elapsed_time,
                        "timestamp": end_time.isoformat(),
                        "start_time": self.start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    }
                    return [], stats
                
                self.log(f"开始处理 {len(games)} 个游戏")
                
                # 处理每个游戏
                for i, game in enumerate(games):
                    if i > 0:
                        time.sleep(self.delay)  # 请求间隔
                    
                    result = self.process_game(game)
                    if result:
                        self.results.append(result)
                
                # 生成统计信息
                end_time = datetime.now()
                elapsed_time = (end_time - self.start_time).total_seconds()
                stats = {
                    "total_processed": self.processed_count,
                    "successful_extractions": self.successful_count,
                    "elapsed_seconds": elapsed_time,
                    "timestamp": end_time.isoformat(),
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
                
                self.log(f"爬取完成 - 处理游戏: {self.processed_count}, 成功: {self.successful_count}, 耗时: {elapsed_time:.2f}秒")
                return self.results, stats
        
        success = True
        print("成功创建自定义FastItchIoScraper类")
    except Exception as e:
        print(f"创建自定义爬虫类失败: {e}")
        print(traceback.format_exc())

# 如果所有导入方法都失败，则终止程序
if not success:
    print("严重错误: 无法导入或创建FastItchIoScraper类，程序无法继续运行。")
    print("请确保server.py文件存在且包含FastItchIoScraper类。")
    
    # 如果在GUI中，显示错误对话框
    try:
        import tkinter.messagebox as msgbox
        msgbox.showerror("严重错误", 
                         "无法导入爬虫模块(FastItchIoScraper)。\n\n"
                         "请确保server.py文件与本程序在同一目录下。\n\n"
                         "程序将退出。")
    except:
        pass
    
    # 延迟5秒再退出，让用户有时间看到错误信息
    try:
        time.sleep(5)
    except:
        pass
    
    sys.exit(1)

# 创建结果和日志目录
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
DEBUG_HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_html")

for directory in [RESULTS_DIR, LOGS_DIR, DEBUG_HTML_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class IframeExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("itch.io游戏iframe提取器")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 配置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TFrame", background="#f0f0f0")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(self.main_frame, text="itch.io游戏iframe提取器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(self.main_frame, text="爬取设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建输入控件
        # 游戏数量
        games_frame = ttk.Frame(input_frame)
        games_frame.pack(fill=tk.X, pady=5)
        ttk.Label(games_frame, text="最大游戏数量:").pack(side=tk.LEFT)
        self.games_var = tk.IntVar(value=5)
        games_spinbox = ttk.Spinbox(games_frame, from_=1, to=50, textvariable=self.games_var, width=5)
        games_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # 偏移量
        offset_frame = ttk.Frame(input_frame)
        offset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(offset_frame, text="起始偏移量:").pack(side=tk.LEFT)
        self.offset_var = tk.IntVar(value=0)
        offset_spinbox = ttk.Spinbox(offset_frame, from_=0, to=1000, increment=12, textvariable=self.offset_var, width=5)
        offset_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(offset_frame, text="(每页12个游戏)").pack(side=tk.LEFT, padx=(5, 0))
        
        # 延迟时间
        delay_frame = ttk.Frame(input_frame)
        delay_frame.pack(fill=tk.X, pady=5)
        ttk.Label(delay_frame, text="请求延迟(秒):").pack(side=tk.LEFT)
        self.delay_var = tk.DoubleVar(value=1.0)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.delay_var, width=5)
        delay_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # 游戏类型（多选框）
        categories_frame = ttk.LabelFrame(input_frame, text="游戏类型", padding="5")
        categories_frame.pack(fill=tk.X, pady=5)
        
        self.categories = {
            "action": tk.BooleanVar(value=True),
            "adventure": tk.BooleanVar(value=True),
            "puzzle": tk.BooleanVar(value=True),
            "platformer": tk.BooleanVar(value=True),
            "rpg": tk.BooleanVar(value=False),
            "strategy": tk.BooleanVar(value=False),
            "shooter": tk.BooleanVar(value=False),
            "racing": tk.BooleanVar(value=False)
        }
        
        # 每行显示4个选项
        row = 0
        col = 0
        for cat, var in self.categories.items():
            ttk.Checkbutton(categories_frame, text=cat.capitalize(), variable=var).grid(row=row, column=col, sticky=tk.W, padx=5)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # 按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 开始按钮
        self.start_button = ttk.Button(button_frame, text="开始提取", command=self.start_extraction)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 保存结果按钮（初始禁用）
        self.save_button = ttk.Button(button_frame, text="保存结果", command=self.save_results, state="disabled")
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # 查看HTML按钮
        self.view_button = ttk.Button(button_frame, text="用浏览器查看", command=self.view_in_browser, state="disabled")
        self.view_button.pack(side=tk.LEFT, padx=5)
        
        # 清除日志按钮
        clear_button = ttk.Button(button_frame, text="清除日志", command=self.clear_log)
        clear_button.pack(side=tk.RIGHT, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var, font=("Arial", 10, "italic"))
        status_label.pack(pady=(5, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志文本框
        log_frame = ttk.LabelFrame(self.main_frame, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 结果变量
        self.result_data = None
        self.extraction_completed = False
        
        # 初始化日志
        self.log("应用程序已启动")
        self.log(f"结果将保存在: {os.path.abspath(RESULTS_DIR)}")
    
    def log(self, message):
        """添加消息到日志文本框"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)  # 滚动到底部
    
    def clear_log(self):
        """清除日志文本"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清除")
    
    def start_extraction(self):
        """开始提取过程"""
        # 禁用开始按钮
        self.start_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.view_button.config(state="disabled")
        
        # 重置状态
        self.result_data = None
        self.extraction_completed = False
        
        # 获取设置
        max_games = self.games_var.get()
        offset = self.offset_var.get()
        delay = self.delay_var.get()
        
        # 获取选中的类别
        selected_categories = [cat for cat, var in self.categories.items() if var.get()]
        
        # 更新状态
        self.status_var.set("正在提取中...")
        
        # 开始进度条
        self.progress.start()
        
        # 创建并启动提取线程
        self.extraction_thread = threading.Thread(
            target=self.run_extraction, 
            args=(max_games, offset, delay, selected_categories)
        )
        self.extraction_thread.daemon = True
        self.extraction_thread.start()
    
    def run_extraction(self, max_games, offset, delay, categories):
        """在后台线程中运行提取过程"""
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            self.log(f"开始爬取 - 最大游戏数: {max_games}, 偏移量: {offset}, 延迟: {delay}秒")
            self.log(f"选中类别: {', '.join(categories)}")
            
            # 创建爬虫对象
            scraper = FastItchIoScraper(max_games=max_games, start_offset=offset, delay=delay)
            
            # 执行爬取
            results, stats = scraper.scrape()
            
            # 记录结果
            if results:
                self.log(f"成功爬取 {len(results)} 个游戏iframe源")
                for i, result in enumerate(results, 1):
                    self.log(f"{i}. {result.get('title')} - {result.get('iframe_src')}")
            else:
                self.log("未能获取任何游戏iframe源")
            
            # 记录统计信息
            self.log(f"总共处理: {stats['total_processed']} 个游戏")
            self.log(f"成功提取: {stats['successful_extractions']} 个游戏")
            self.log(f"耗时: {stats['elapsed_seconds']:.2f} 秒")
            
            # 保存结果
            if results:
                result_with_metadata = {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "params": {
                            "max_games": max_games,
                            "offset": offset,
                            "delay": delay,
                            "categories": categories
                        },
                        "source": "desktop_app",
                        "count": len(results),
                        "stats": stats
                    },
                    "results": results
                }
                
                self.result_data = result_with_metadata
                
                # 生成唯一的文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = os.path.join(RESULTS_DIR, f"iframe_results_{timestamp}.json")
                
                # 自动保存到默认位置
                with open(default_filename, 'w', encoding='utf-8') as f:
                    json.dump(result_with_metadata, f, indent=2, ensure_ascii=False)
                
                self.log(f"结果已自动保存至: {default_filename}")
                
                # 创建简单的HTML查看器
                viewer_path = self.create_html_viewer(results)
                self.log(f"HTML查看器已创建: {viewer_path}")
                
                # 设置提取完成标志
                self.extraction_completed = True
                
                # 启用保存按钮和查看按钮
                self.root.after(0, lambda: self.save_button.config(state="normal"))
                self.root.after(0, lambda: self.view_button.config(state="normal"))
            
            # 更新状态
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self.root.after(0, lambda: self.status_var.set(f"完成 (耗时: {elapsed_time:.2f}秒)"))
            
        except Exception as e:
            error_trace = traceback.format_exc()
            self.log(f"错误: {str(e)}")
            self.log(f"详细错误: {error_trace}")
            self.root.after(0, lambda: self.status_var.set(f"失败: {str(e)[:50]}..."))
        finally:
            # 停止进度条
            self.root.after(0, self.progress.stop)
            # 重新启用开始按钮
            self.root.after(0, lambda: self.start_button.config(state="normal"))
    
    def save_results(self):
        """保存结果到用户选择的位置"""
        if not self.result_data:
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        
        # 让用户选择保存位置
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialdir=RESULTS_DIR,
            initialfile=f"iframe_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.result_data, f, indent=2, ensure_ascii=False)
                self.log(f"结果已保存至: {filename}")
                messagebox.showinfo("成功", f"结果已保存至:\n{filename}")
            except Exception as e:
                self.log(f"保存失败: {e}")
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def create_html_viewer(self, results):
        """创建简单的HTML查看器来显示iframe内容"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        viewer_filename = os.path.join(RESULTS_DIR, f"iframe_viewer_{timestamp}.html")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>itch.io游戏iframe查看器</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #333; text-align: center; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .game-container {{ margin-bottom: 30px; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .game-header {{ padding: 15px; background-color: #4a4a4a; color: white; }}
        .game-title {{ margin: 0; font-size: 1.2em; }}
        .game-iframe {{ width: 100%; min-height: 600px; border: none; display: block; }}
        .iframe-controls {{ padding: 10px; background-color: #eee; }}
        .button {{ padding: 8px 15px; background-color: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        .button:hover {{ background-color: #2980b9; }}
        .note {{ font-size: 0.8em; color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>itch.io游戏iframe查看器</h1>
        <p style="text-align: center;">共 {len(results)} 个游戏 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div id="games">
"""
        
        for i, game in enumerate(results, 1):
            title = game.get('title', f'游戏 {i}')
            src = game.get('iframe_src', '')
            url = game.get('url', '#')
            
            if src:
                iframe_html = f"""
            <div class="game-container">
                <div class="game-header">
                    <h2 class="game-title">{i}. {title}</h2>
                    <div><a href="{url}" target="_blank">在itch.io上查看</a></div>
                </div>
                <div class="iframe-controls">
                    <button class="button" onclick="loadIframe(this, '{src}')">加载游戏</button>
                    <span class="note">说明: 点击按钮后加载游戏，避免自动播放音频问题</span>
                </div>
                <div class="iframe-placeholder" data-src="{src}" style="background-color: #eee; height: 600px; display: flex; align-items: center; justify-content: center;">
                    <p>点击上方按钮加载游戏</p>
                </div>
            </div>
"""
            else:
                iframe_html = f"""
            <div class="game-container">
                <div class="game-header">
                    <h2 class="game-title">{i}. {title}</h2>
                    <div><a href="{url}" target="_blank">在itch.io上查看</a></div>
                </div>
                <div class="iframe-controls">
                    <span class="note">无法加载游戏 - 未找到iframe源</span>
                </div>
            </div>
"""
            
            html_content += iframe_html
        
        html_content += """
        </div>
    </div>
    
    <script>
        function loadIframe(button, src) {
            const container = button.parentElement.nextElementSibling;
            container.innerHTML = `<iframe class="game-iframe" src="${src}" allowfullscreen></iframe>`;
            button.disabled = true;
            button.innerText = '游戏已加载';
        }
    </script>
</body>
</html>
"""
        
        with open(viewer_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.viewer_path = viewer_filename
        return viewer_filename
    
    def view_in_browser(self):
        """在浏览器中查看结果"""
        if hasattr(self, 'viewer_path') and os.path.exists(self.viewer_path):
            webbrowser.open('file://' + os.path.abspath(self.viewer_path))
            self.log(f"在浏览器中打开: {self.viewer_path}")
        else:
            messagebox.showwarning("警告", "没有可查看的HTML文件")

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    app = IframeExtractorGUI(root)
    
    # 启动主循环
    root.mainloop() 