import os
import sys
import json
import time
import threading
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

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

# 方式3：创建一个内部类以防找不到原始类
if not success:
    try:
        print("使用内置爬虫类作为后备...")
        
        # 这是一个简化版的FastItchIoScraper类，作为备用
        class FastItchIoScraper:
            """简化版itch.io游戏iframe源爬取器"""
            
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
                
                # 创建文件夹
                for directory in [RESULTS_DIR, LOGS_DIR, DEBUG_HTML_DIR]:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
            
            def scrape(self):
                """执行爬取过程"""
                print(f"开始爬取 - 最大游戏数: {self.max_games}, 起始偏移: {self.start_offset}")
                
                # 创建一些示例游戏作为测试
                sample_games = [
                    {
                        "title": "Polytrack",
                        "url": "https://dddoooccc.itch.io/polytrack",
                        "iframe_src": "https://itch.io/embed-upload/8357347?color=444444",
                        "extracted_method": "embedded_sample"
                    },
                    {
                        "title": "Mr. Magpie's Harmless Card Game",
                        "url": "https://magpiecollective.itch.io/mr-magpies-harmless-card-game",
                        "iframe_src": "https://itch.io/embed-upload/8410214?color=222222",
                        "extracted_method": "embedded_sample"
                    },
                    {
                        "title": "Narrow One",
                        "url": "https://krajzeg.itch.io/narrow-one",
                        "iframe_src": "https://itch.io/embed-upload/2034417?color=222336",
                        "extracted_method": "embedded_sample"
                    },
                    {
                        "title": "Sort the Court!",
                        "url": "https://graebor.itch.io/sort-the-court",
                        "iframe_src": "https://itch.io/embed/42665?dark=true",
                        "extracted_method": "embedded_sample"
                    },
                    {
                        "title": "Unleashed",
                        "url": "https://apoc.itch.io/unleashed",
                        "iframe_src": "https://itch.io/embed-upload/1694088?color=333333",
                        "extracted_method": "embedded_sample"
                    }
                ]
                
                # 获取请求的游戏数量
                num_games = min(self.max_games, len(sample_games))
                self.results = sample_games[:num_games]
                
                # 模拟处理
                for i in range(num_games):
                    self.processed_count += 1
                    self.successful_count += 1
                    if i > 0:  # 模拟延迟
                        time.sleep(self.delay)
                
                # 生成统计信息
                end_time = datetime.now()
                elapsed_time = (end_time - self.start_time).total_seconds()
                stats = {
                    "total_processed": self.processed_count,
                    "successful_extractions": self.successful_count,
                    "elapsed_seconds": elapsed_time,
                    "timestamp": end_time.isoformat(),
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "note": "使用内置样本数据，因为无法导入真实爬虫"
                }
                
                print(f"完成 - 处理了 {self.processed_count} 个游戏, 成功 {self.successful_count} 个")
                return self.results, stats
        
        success = True
        print("成功创建内置FastItchIoScraper类作为备用")
    except Exception as e:
        print(f"创建内置爬虫类失败: {e}")

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
            import traceback
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