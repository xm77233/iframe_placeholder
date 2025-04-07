#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
itch.io游戏iframe提取器GUI
基于iframe_scraper.py的功能构建简单的图形界面
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import webbrowser
from datetime import datetime
import subprocess
import importlib.util

# 导入iframe_scraper.py中的函数
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# 从iframe_scraper.py导入所需功能
spec = importlib.util.spec_from_file_location("iframe_scraper", os.path.join(script_dir, "iframe_scraper.py"))
scraper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper_module)

# 导入所需函数
get_game_page_urls = scraper_module.get_game_page_urls
get_iframe_src = scraper_module.get_iframe_src
setup_logger = scraper_module.setup_logger
save_results = scraper_module.save_results

# 设置日志记录器
logger = setup_logger()

class IframeExtractorGUI:
    """itch.io游戏iframe提取器GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("itch.io游戏iframe提取器")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 初始化变量
        self.max_games = tk.IntVar(value=5)
        self.offset = tk.IntVar(value=0)
        self.delay = tk.DoubleVar(value=2.0)
        self.results = []
        self.scraping_thread = None
        self.stop_scraping = False
        
        # 创建界面
        self._create_widgets()
        
        # 确保结果目录存在
        if not os.path.exists('results'):
            os.makedirs('results')
    
    def _create_widgets(self):
        """创建GUI组件"""
        # 顶部设置区域
        settings_frame = ttk.LabelFrame(self.root, text="设置")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 最大游戏数量
        ttk.Label(settings_frame, text="最大游戏数量:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.max_games, width=5).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 起始偏移量
        ttk.Label(settings_frame, text="起始偏移量:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Spinbox(settings_frame, from_=0, to=100000, textvariable=self.offset, width=5).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 请求延迟
        ttk.Label(settings_frame, text="请求延迟(秒):").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Spinbox(settings_frame, from_=0.5, to=10.0, increment=0.5, textvariable=self.delay, width=5).grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # 按钮区域
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="开始爬取", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止爬取", command=self.stop_scraping_process, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.view_results_button = ttk.Button(buttons_frame, text="查看结果文件", command=self.open_results_file)
        self.view_results_button.pack(side=tk.LEFT, padx=5)
        
        self.test_iframe_button = ttk.Button(buttons_frame, text="测试选中的iframe", command=self.test_iframe, state=tk.DISABLED)
        self.test_iframe_button.pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # 创建标签页控制
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="日志")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 结果标签页
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="结果")
        
        # 创建结果表格
        columns = ('序号', '标题', '游戏链接', 'iframe源')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.results_tree.heading(col, text=col)
        
        # 设置列宽
        self.results_tree.column('序号', width=50, stretch=False)
        self.results_tree.column('标题', width=150)
        self.results_tree.column('游戏链接', width=200)
        self.results_tree.column('iframe源', width=400)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 打包组件
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定表格选择事件
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_selected)
    
    def log(self, message, level='info'):
        """向日志文本框添加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据日志级别设置标签
        level_tag = {
            'info': 'info',
            'warning': 'warning',
            'error': 'error',
            'success': 'success'
        }.get(level, 'info')
        
        # 在日志末尾添加消息
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{message}\n", level_tag)
        
        # 配置标签颜色
        self.log_text.tag_config('timestamp', foreground='blue')
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('success', foreground='green')
        
        # 滚动到底部
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 更新状态栏
        self.status_var.set(message)
    
    def start_scraping(self):
        """开始爬取过程"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            messagebox.showwarning("警告", "爬取过程已在进行中")
            return
        
        # 重置停止标志
        self.stop_scraping = False
        
        # 启用停止按钮，禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 清空结果
        self.results = []
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 重置进度条
        self.progress_var.set(0)
        
        # 创建并启动爬取线程
        self.scraping_thread = threading.Thread(target=self.scraping_process)
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
        
        self.log("开始爬取处理", 'info')
    
    def scraping_process(self):
        """爬取处理线程"""
        try:
            max_games = self.max_games.get()
            start_offset = self.offset.get()
            delay = self.delay.get()
            
            self.log(f"开始爬取: 最大游戏数量={max_games}, 起始偏移量={start_offset}, 延迟={delay}秒", 'info')
            
            # itch.io网页游戏列表页面，只爬取免费游戏
            url = 'https://itch.io/games/free/platform-web'
            
            # 处理的游戏总数
            total_processed = 0
            successful_processed = 0
            
            # 当前偏移量
            offset = start_offset
            
            # 继续抓取直到达到最大游戏数或没有更多游戏
            while total_processed < max_games and not self.stop_scraping:
                # 获取当前页的游戏
                self.log(f"获取游戏列表 (偏移量: {offset})...")
                games, has_more = get_game_page_urls(url, offset)
                
                if not games:
                    self.log("没有找到更多游戏，结束爬取", 'warning')
                    break
                
                # 计算本次要处理的游戏数量
                games_to_process = min(len(games), max_games - total_processed)
                games = games[:games_to_process]
                
                # 遍历游戏页面并获取iframe src
                for i, game in enumerate(games):
                    if self.stop_scraping:
                        self.log("用户已停止爬取过程", 'warning')
                        break
                    
                    self.log(f"处理游戏 {total_processed+1}/{max_games}: {game['title']}")
                    
                    # 获取iframe src
                    iframe_src = get_iframe_src(game['url'])
                    
                    if iframe_src:
                        self.log(f"成功找到iframe源: {iframe_src}", 'success')
                        self.update_results_table(
                            total_processed + 1, 
                            game['title'], 
                            game['url'], 
                            iframe_src
                        )
                        
                        self.results.append({
                            'title': game['title'],
                            'game_url': game['url'],
                            'iframe_src': iframe_src
                        })
                        successful_processed += 1
                    else:
                        self.log(f"未找到iframe源", 'warning')
                    
                    total_processed += 1
                    
                    # 更新进度条
                    progress_percent = (total_processed / max_games) * 100
                    self.progress_var.set(progress_percent)
                    
                    # 添加延迟，避免请求过于频繁
                    if i < len(games) - 1 and not self.stop_scraping:
                        self.log(f"等待{delay}秒...")
                        
                        # 使用小间隔来检查停止标志
                        for _ in range(int(delay * 2)):
                            if self.stop_scraping:
                                break
                            time.sleep(0.5)
                    
                    # 检查是否达到最大游戏数量
                    if total_processed >= max_games:
                        self.log(f"已达到最大游戏数量 {max_games}，停止爬取", 'info')
                        break
                
                # 如果没有更多游戏或已达到最大游戏数量，退出循环
                if not has_more or total_processed >= max_games:
                    break
                
                # 更新偏移量进入下一页
                offset += 36  # itch.io的默认每页大小
                self.log(f"进入下一页，偏移量: {offset}")
                
                # 页面之间添加额外延迟
                if not self.stop_scraping:
                    self.log(f"翻页等待 {delay * 2} 秒...")
                    
                    # 使用小间隔来检查停止标志
                    for _ in range(int(delay * 4)):
                        if self.stop_scraping:
                            break
                        time.sleep(0.5)
            
            # 保存最终结果
            if self.results:
                output_file = f"results/game_iframes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_results(self.results, output_file)
                self.log(f"结果已保存到: {output_file}", 'success')
            
            self.log("==== 爬取完成 ====", 'success')
            self.log(f"总共处理 {total_processed} 个游戏，成功获取 {successful_processed} 个游戏的iframe源", 'success')
            
            # 完成后恢复按钮状态
            self.root.after(0, self.update_buttons_after_scraping)
        
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.log(f"爬取过程中出错: {str(e)}", 'error')
            self.log(error_msg, 'error')
            
            # 出错后恢复按钮状态
            self.root.after(0, self.update_buttons_after_scraping)
    
    def update_buttons_after_scraping(self):
        """爬取完成后更新按钮状态"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def stop_scraping_process(self):
        """停止爬取过程"""
        self.stop_scraping = True
        self.log("正在停止爬取过程...", 'warning')
    
    def update_results_table(self, index, title, game_url, iframe_src):
        """更新结果表格"""
        def _update():
            """在主线程中更新UI"""
            self.results_tree.insert('', 'end', values=(index, title, game_url, iframe_src))
        
        # 在主线程中调用UI更新
        self.root.after(0, _update)
    
    def on_result_selected(self, event):
        """当结果表格中的项目被选中时调用"""
        selection = self.results_tree.selection()
        if selection:
            self.test_iframe_button.config(state=tk.NORMAL)
        else:
            self.test_iframe_button.config(state=tk.DISABLED)
    
    def test_iframe(self):
        """测试选中的iframe"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        selected_item = self.results_tree.item(selection[0])
        values = selected_item['values']
        
        if len(values) >= 4:
            iframe_src = values[3]
            if iframe_src:
                self.create_html_viewer(iframe_src, values[1])
    
    def create_html_viewer(self, iframe_src, title):
        """创建HTML页面来显示iframe"""
        html_dir = "iframe_viewer"
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        
        html_file = os.path.join(html_dir, "iframe_viewer.html")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - iframe查看器</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: white;
            padding: 20px;
            border-radius: 0 0 5px 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .iframe-container {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            margin-top: 20px;
            position: relative;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .controls {{
            margin-bottom: 20px;
        }}
        button {{
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            border-radius: 4px;
            margin-right: 10px;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        .iframe-url {{
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        <div class="content">
            <div class="controls">
                <button id="refresh-btn">刷新iframe</button>
                <button id="fullscreen-btn">全屏显示</button>
            </div>
            <div class="iframe-url">
                <strong>iframe URL:</strong> 
                <span id="iframe-url">{iframe_src}</span>
            </div>
            <div class="iframe-container" id="iframe-container">
                <iframe id="game-iframe" src="{iframe_src}" allowfullscreen></iframe>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('refresh-btn').addEventListener('click', function() {{
            document.getElementById('game-iframe').src = document.getElementById('iframe-url').textContent;
        }});

        document.getElementById('fullscreen-btn').addEventListener('click', function() {{
            const iframe = document.getElementById('game-iframe');
            if (iframe.requestFullscreen) {{
                iframe.requestFullscreen();
            }} else if (iframe.mozRequestFullScreen) {{
                iframe.mozRequestFullScreen();
            }} else if (iframe.webkitRequestFullscreen) {{
                iframe.webkitRequestFullscreen();
            }} else if (iframe.msRequestFullscreen) {{
                iframe.msRequestFullscreen();
            }}
        }});
    </script>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 在浏览器中打开HTML文件
        html_file_url = "file://" + os.path.abspath(html_file)
        webbrowser.open(html_file_url)
        
        self.log(f"在浏览器中打开iframe查看器: {html_file}", 'info')
    
    def open_results_file(self):
        """打开结果文件目录"""
        results_dir = os.path.abspath("results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # 在文件浏览器中打开结果目录
        if sys.platform == 'win32':
            os.startfile(results_dir)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', results_dir])
        else:  # Linux
            subprocess.call(['xdg-open', results_dir])

# 主程序入口
def main():
    """主函数"""
    root = tk.Tk()
    app = IframeExtractorGUI(root)
    
    # 添加退出确认
    def on_closing():
        if app.scraping_thread and app.scraping_thread.is_alive():
            if messagebox.askokcancel("退出", "爬取过程正在进行中，确定要退出吗？"):
                app.stop_scraping = True
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    import time  # 用于延迟
    main() 