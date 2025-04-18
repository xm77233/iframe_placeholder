#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Flask server for the itch.io Game Iframe Extractor
Handles extraction requests and allows downloading results
"""

from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
import os
import sys
import json
import smtplib
import threading
import subprocess
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import uuid
import urllib.request
import urllib.error
import re
import html
import random

# Vercel requires us to create our app at the global scope
app = Flask(__name__, static_url_path='')

# File paths - for Vercel we need to use writable directories
if 'VERCEL' in os.environ:
    # On Vercel, use the tmp directory which is writable
    JOBS_DATA_DIR = '/tmp/jobs'
    RESULTS_DIR = '/tmp/results'
    LOGS_DIR = '/tmp/logs'
    DEBUG_HTML_DIR = '/tmp/debug_html'
else:
    # Local development
    JOBS_DATA_DIR = 'jobs'
    RESULTS_DIR = 'results'
    LOGS_DIR = 'logs'
    DEBUG_HTML_DIR = 'debug_html'

# Job storage
jobs = {}

# Load jobs from files
def load_jobs():
    global jobs
    if os.path.exists(JOBS_DATA_DIR):
        for filename in os.listdir(JOBS_DATA_DIR):
            if filename.endswith('.json'):
                job_id = filename.split('.')[0]
                try:
                    with open(os.path.join(JOBS_DATA_DIR, filename), 'r', encoding='utf-8') as f:
                        jobs[job_id] = json.load(f)
                except Exception as e:
                    print(f"Error loading job {job_id}: {e}")

# Save job to file
def save_job(job_id):
    try:
        if not os.path.exists(JOBS_DATA_DIR):
            os.makedirs(JOBS_DATA_DIR)
        
        job_file = os.path.join(JOBS_DATA_DIR, f"{job_id}.json")
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(jobs[job_id], f)
    except Exception as e:
        print(f"Error saving job {job_id}: {e}")

def setup_result_directories():
    """Create necessary directories if they don't exist"""
    for directory in [RESULTS_DIR, LOGS_DIR, DEBUG_HTML_DIR, JOBS_DATA_DIR]:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except Exception as e:
            print(f"Warning: Could not create directory {directory}: {e}")

# Add a job update function
def update_job(job_id, updates):
    if job_id in jobs:
        for key, value in updates.items():
            jobs[job_id][key] = value
        save_job(job_id)

# User-Agent列表，用于模拟不同浏览器
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

class FastItchIoScraper:
    """快速itch.io游戏iframe源爬取器"""
    
    def __init__(self, max_games=5, start_offset=0, delay=0.5, concurrent=True):
        """
        初始化爬取器
        
        Args:
            max_games: 最多爬取的游戏数量
            start_offset: 起始偏移量
            delay: 请求间隔时间(秒)
            concurrent: 是否并发爬取
        """
        self.max_games = max_games
        self.start_offset = start_offset
        self.delay = delay
        self.concurrent = concurrent
        self.results = []
        self.processed_count = 0
        self.successful_count = 0
        self.start_time = datetime.now()
        self.debug_save_html = True  # 保存HTML用于调试
    
    def get_random_user_agent(self):
        """随机获取一个User-Agent"""
        return random.choice(USER_AGENTS)
    
    def fetch_url(self, url):
        """
        获取URL内容，增加重试机制
        
        Args:
            url: 要获取的URL
            
        Returns:
            str: 页面HTML内容
        """
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
                    'Cache-Control': 'max-age=0',
                    'TE': 'Trailers'
                }
                
                print(f"正在获取URL: {url} (尝试 {retry_count+1}/{max_retries})")
                print(f"使用User-Agent: {headers['User-Agent']}")
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:  # 增加超时时间
                    html_content = response.read().decode('utf-8')
                    
                    # 保存HTML用于调试
                    if self.debug_save_html:
                        try:
                            if not os.path.exists(DEBUG_HTML_DIR):
                                os.makedirs(DEBUG_HTML_DIR)
                            
                            # 从URL中提取游戏名称用作文件名
                            game_name = url.split('/')[-1]
                            debug_file = os.path.join(DEBUG_HTML_DIR, f"{game_name}.html")
                            
                            with open(debug_file, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                                
                            print(f"已保存HTML到 {debug_file}")
                        except Exception as e:
                            print(f"保存HTML失败: {e}")
                    
                    return html_content
            except urllib.error.HTTPError as e:
                print(f"HTTP错误: {e.code} - {e.reason}, URL: {url}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 2  # 逐渐增加等待时间
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"达到最大重试次数，放弃获取URL: {url}")
                    return ""
            except urllib.error.URLError as e:
                print(f"URL错误: {e.reason}, URL: {url}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 2
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"达到最大重试次数，放弃获取URL: {url}")
                    return ""
            except Exception as e:
                print(f"获取URL {url} 失败: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 2
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"达到最大重试次数，放弃获取URL: {url}")
                    return ""
        
        return ""
    
    def get_game_page_urls(self, limit=None):
        """
        获取游戏页面URL列表
        
        Args:
            limit: 限制获取的游戏数量
            
        Returns:
            list: 游戏URL和标题的列表
        """
        offset = self.start_offset
        max_to_fetch = self.max_games if limit is None else min(self.max_games, limit)
        games = []
        page_size = 36  # itch.io每页显示36个游戏
        
        print(f"------------------------------")
        print(f"开始获取游戏列表 - 最大数量: {max_to_fetch}, 偏移量: {offset}")
        
        # 尝试不同的页面类型
        page_types = [
            # 格式: (URL模板, 描述)
            (f"https://itch.io/games/free/platform-web?offset={offset}", "普通自由网页游戏"),
            (f"https://itch.io/games/top-rated/free/platform-web?offset={offset}", "排名最高网页游戏"),
            (f"https://itch.io/games/genre-action/free/platform-web?offset={offset}", "动作类游戏"),
            (f"https://itch.io/games/genre-puzzle/free/platform-web?offset={offset}", "解谜类游戏")
        ]
        
        # 从列表中尝试不同的页面类型，直到获取足够的游戏
        for url_template, description in page_types:
            if len(games) >= max_to_fetch:
                break
                
            print(f"尝试从 {description} 列表获取游戏 (URL: {url_template})")
            
            try:
                html_content = self.fetch_url(url_template)
                if not html_content:
                    print(f"无法获取 {description} 列表HTML内容")
                    continue
                
                print(f"成功获取 {description} 列表HTML内容，长度: {len(html_content)} 字符")
                
                # 保存列表页HTML用于调试
                if self.debug_save_html:
                    try:
                        debug_file = os.path.join(DEBUG_HTML_DIR, f"game_list_{description.replace(' ', '_')}_offset_{offset}.html")
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        print(f"已保存游戏列表HTML到 {debug_file}")
                    except Exception as e:
                        print(f"保存游戏列表HTML失败: {e}")
                
                # 使用三种不同的正则表达式模式尝试提取游戏链接
                extraction_patterns = [
                    # 标准游戏链接格式
                    (r'<a\s+class="game_link"\s+href="(https://[^"]+\.itch\.io/[^"]+)"[^>]*>[\s\S]*?<div\s+class="game_title">([\s\S]*?)</div>', "标准模式"),
                    # 备用格式 - 链接后跟标题
                    (r'<a\s+href="(https://[^"]+\.itch\.io/[^"]+)"[^>]*class="[^"]*game[^"]*"[^>]*>[\s\S]*?<div\s+class="[^"]*title[^"]*">([\s\S]*?)</div>', "备用模式"),
                    # 最宽松模式 - 任何itch.io链接
                    (r'<a\s+href="(https://[^"]+\.itch\.io/[^"]+)"[^>]*>([\s\S]*?)</a>', "宽松模式")
                ]
                
                for pattern, pattern_name in extraction_patterns:
                    if len(games) >= max_to_fetch:
                        break
                        
                    matches = re.findall(pattern, html_content, re.DOTALL)
                    print(f"使用{pattern_name}找到 {len(matches)} 个游戏匹配项")
                    
                    if matches:
                        # 处理找到的匹配项
                        for game_url, game_title in matches:
                            if len(games) >= max_to_fetch:
                                break
                                
                            # 检查URL格式
                            if not game_url.startswith("https://") or not ".itch.io/" in game_url:
                                continue
                                
                            # 清理标题
                            clean_title = html.unescape(game_title.strip())
                            clean_title = re.sub(r'<[^>]+>', '', clean_title)
                            clean_title = clean_title.strip()
                            
                            # 跳过没有标题的游戏
                            if not clean_title:
                                continue
                                
                            # 跳过重复的游戏URL
                            if any(existing_url == game_url for existing_url, _ in games):
                                continue
                            
                            games.append((game_url, clean_title))
                            self.processed_count += 1
                            
                            print(f"添加游戏: {clean_title} ({game_url})")
                
                if games:
                    # 如果这个来源找到了游戏，就不再尝试其他来源
                    print(f"从 {description} 来源找到 {len(games)} 个游戏，停止搜索其他来源")
                    break
            except Exception as e:
                print(f"获取 {description} 列表失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
        
        print(f"总共提取 {len(games)} 个游戏信息")
        print(f"------------------------------")
        return games
    
    def get_iframe_src(self, game_page_html, game_url):
        """
        从游戏页面中提取iframe源
        
        Args:
            game_page_html: 游戏页面HTML内容
            game_url: 游戏URL，用于日志
            
        Returns:
            str: iframe源URL
        """
        iframe_src = None
        extraction_method = ""
        
        print(f"------------------------------")
        print(f"开始提取iframe源 - {game_url}")
        
        # 方法1: 检查html_embed区域中的iframe标签
        if not iframe_src:
            try:
                print("尝试方法1: html_embed > iframe")
                match = re.search(r'<div[^>]*id=["\'](html_embed_content|html_embed)["\']\s*[^>]*>[\s\S]*?<iframe[^>]*src=["\'](.*?)["\']', game_page_html, re.DOTALL)
                if match:
                    iframe_src = html.unescape(match.group(2))
                    extraction_method = "html_embed_iframe"
                    print(f"方法1成功: {iframe_src}")
                else:
                    print("方法1未找到匹配")
            except Exception as e:
                print(f"方法1出错: {e}")
        
        # 方法2: 检查html_embed区域中的data-iframe属性
        if not iframe_src:
            try:
                print("尝试方法2: html_embed > data-iframe")
                match = re.search(r'<div[^>]*id=["\'](html_embed_content|html_embed)["\']\s*[^>]*data-iframe=["\']([^"\']+)["\']', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(2))
                    extraction_method = "html_embed_data_iframe"
                    print(f"方法2成功: {iframe_src}")
                else:
                    print("方法2未找到匹配")
            except Exception as e:
                print(f"方法2出错: {e}")
        
        # 方法3: 检查iframe_placeholder元素
        if not iframe_src:
            try:
                print("尝试方法3: iframe_placeholder")
                match = re.search(r'<div[^>]*class=["\'](iframe_placeholder)["\']\s*[^>]*data-iframe=["\']([^"\']+)["\']', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(2))
                    extraction_method = "iframe_placeholder"
                    print(f"方法3成功: {iframe_src}")
                else:
                    print("方法3未找到匹配")
            except Exception as e:
                print(f"方法3出错: {e}")
        
        # 方法4: 查找包含id="game_drop"的区域
        if not iframe_src:
            try:
                print("尝试方法4: game_drop区域")
                match = re.search(r'<div[^>]*id=["\'](game_drop)["\']\s*[^>]*>[\s\S]*?data-iframe=["\'](.*?)["\']', game_page_html, re.DOTALL)
                if match:
                    iframe_src = html.unescape(match.group(2))
                    extraction_method = "game_drop"
                    print(f"方法4成功: {iframe_src}")
                else:
                    print("方法4未找到匹配")
            except Exception as e:
                print(f"方法4出错: {e}")
        
        # 方法5: 直接搜索data-iframe属性，不限制元素类型
        if not iframe_src:
            try:
                print("尝试方法5: 全局data-iframe搜索")
                match = re.search(r'data-iframe=["\']([^"\']+)["\']', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "global_data_iframe"
                    print(f"方法5成功: {iframe_src}")
                else:
                    print("方法5未找到匹配")
            except Exception as e:
                print(f"方法5出错: {e}")
        
        # 方法6: 搜索嵌入式iframe
        if not iframe_src:
            try:
                print("尝试方法6: 嵌入式iframe")
                match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*class=["\'](game_frame)["\']', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "embedded_iframe"
                    print(f"方法6成功: {iframe_src}")
                else:
                    print("方法6未找到匹配")
            except Exception as e:
                print(f"方法6出错: {e}")
        
        # 尝试清理和验证提取的URL
        if iframe_src:
            # 移除可能的换行符和多余空格
            iframe_src = iframe_src.strip().replace('\n', '').replace('\r', '')
            
            # 如果iframe源不是URL格式，但包含完整的iframe标签，则尝试从中提取src
            if '<iframe' in iframe_src and 'src=' in iframe_src:
                try:
                    print("从完整iframe标签中提取src")
                    tag_match = re.search(r'src=["\']([^"\']+)["\']', iframe_src)
                    if tag_match:
                        iframe_src = html.unescape(tag_match.group(1))
                        print(f"从标签中提取成功: {iframe_src}")
                except Exception as e:
                    print(f"从标签提取失败: {e}")

            # 检查提取的URL是否有效
            is_valid = iframe_src.startswith(('http://', 'https://', '//', '/')) and len(iframe_src) > 10
            print(f"URL验证: {'有效' if is_valid else '无效'} - {iframe_src}")
            
            if not is_valid:
                iframe_src = None
                extraction_method = ""
                print("提取的URL无效，设置为None")
        
        if iframe_src:
            print(f"成功提取iframe源: {iframe_src}")
            print(f"提取方法: {extraction_method}")
        else:
            print(f"所有方法均未找到iframe源")
            
        print(f"------------------------------")
        
        return iframe_src, extraction_method
    
    def process_game(self, game_url, game_title):
        """
        处理单个游戏页面
        
        Args:
            game_url: 游戏URL
            game_title: 游戏标题
            
        Returns:
            dict: 游戏信息字典
        """
        print(f"开始处理游戏: {game_title} ({game_url})")
        
        try:
            # 尝试两次获取页面内容，第二次使用不同的UA
            game_page_html = self.fetch_url(game_url)
            
            if not game_page_html or len(game_page_html) < 1000:  # HTML太短可能是错误
                print(f"首次获取页面失败或内容过短 ({len(game_page_html) if game_page_html else 0} 字符)，尝试第二次获取...")
                time.sleep(1)  # 延迟1秒再试
                game_page_html = self.fetch_url(game_url)
            
            if not game_page_html:
                print(f"无法获取游戏页面: {game_url}")
                return None
                
            print(f"成功获取游戏页面，HTML长度: {len(game_page_html)} 字符")
            
            iframe_src, extraction_method = self.get_iframe_src(game_page_html, game_url)
            
            if iframe_src:
                self.successful_count += 1
                print(f"成功找到iframe源: {iframe_src}")
                
                # 获取额外的游戏信息
                game_info = {
                    "title": game_title,
                    "url": game_url,
                    "iframe_src": iframe_src,
                    "extracted_method": extraction_method,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 尝试提取游戏简介
                try:
                    description_match = re.search(r'<div[^>]*class=["\']game_description["\'][^>]*>([\s\S]*?)</div>', game_page_html)
                    if description_match:
                        description = description_match.group(1).strip()
                        # 清理HTML标签
                        description = re.sub(r'<[^>]+>', '', description)
                        # 实体解码
                        description = html.unescape(description)
                        game_info["description"] = description
                except Exception as e:
                    print(f"提取游戏简介失败: {e}")
                
                # 尝试提取缩略图URL
                try:
                    thumbnail_match = re.search(r'<img[^>]*class=["\']game_thumb["\'][^>]*src=["\']([^"\']+)["\']', game_page_html)
                    if thumbnail_match:
                        thumbnail_url = thumbnail_match.group(1)
                        game_info["thumbnail_url"] = thumbnail_url
                except Exception as e:
                    print(f"提取缩略图URL失败: {e}")
                
                return game_info
            else:
                print(f"未找到iframe源: {game_url}")
                return None
                
        except Exception as e:
            print(f"处理游戏 {game_title} 失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return None
    
    def scrape(self):
        """执行爬取过程"""
        print(f"==========================================")
        print(f"开始爬取 - 最大游戏数: {self.max_games}, 起始偏移: {self.start_offset}")
        print(f"开始时间: {self.start_time.isoformat()}")
        print(f"==========================================")
        
        # 检查是否是单游戏模式（爬取单个游戏可以优化性能）
        single_game_mode = self.max_games == 1
        print(f"单游戏模式: {single_game_mode}")
        
        # 获取游戏页面URL
        game_urls = self.get_game_page_urls()
        
        if not game_urls:
            print("未找到任何游戏，爬取结束")
            return [], {
                "total_processed": 0,
                "successful_extractions": 0,
                "elapsed_seconds": 0,
                "timestamp": datetime.now().isoformat(),
                "error": "No games found in the list page"
            }
        
        # 如果是单游戏模式，设置更激进的超时保护
        if single_game_mode:
            max_time_allowed = 8  # 单游戏模式下只给8秒时间
        else:
            max_time_allowed = 50  # 多游戏模式下给50秒时间
        
        # 处理每个游戏
        for i, (game_url, game_title) in enumerate(game_urls):
            print(f"\n处理游戏 {i+1}/{len(game_urls)}: {game_title}")
            
            # 添加延迟（但单游戏模式下减少延迟）
            if i > 0:
                if single_game_mode:
                    delay_time = min(self.delay, 0.5)  # 单游戏模式下最多延迟0.5秒
                else:
                    delay_time = self.delay
                    
                print(f"等待 {delay_time} 秒...")
                time.sleep(delay_time)
                
            # 检查是否超时
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > max_time_allowed:
                print(f"接近时间限制 ({elapsed:.2f}秒)，已处理 {i} 个游戏，提前结束")
                break
                
            # 处理游戏
            result = self.process_game(game_url, game_title)
            if result:
                self.results.append(result)
                print(f"成功添加结果 - {game_title}")
                
                # 如果是单游戏模式并且已获取一个结果，直接结束
                if single_game_mode and len(self.results) > 0:
                    print("单游戏模式：已获取结果，提前结束爬取")
                    break
            else:
                print(f"未能获取结果 - {game_title}")
            
            # 再次检查是否超时（处理游戏可能耗时很长）
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > max_time_allowed:
                print(f"处理游戏后超过时间限制 ({elapsed:.2f}秒)，提前结束")
                break
        
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
            "single_game_mode": single_game_mode
        }
        
        print(f"==========================================")
        print(f"爬取完成")
        print(f"处理了 {self.processed_count} 个游戏")
        print(f"成功提取 {self.successful_count} 个iframe源")
        print(f"耗时 {elapsed_time:.2f} 秒")
        print(f"成功率: {(self.successful_count / max(1, self.processed_count) * 100):.2f}%")
        print(f"==========================================")
        
        return self.results, stats

def run_extraction_job(job_id, params):
    """
    Run the iframe extraction job in the background
    
    Args:
        job_id: Unique job identifier
        params: Job parameters
    """
    # Update job status
    update_job(job_id, {'status': 'processing'})
    
    try:
        # Prepare command line arguments
        cmd = [sys.executable, "iframe_scraper.py"]
        
        if params.get('max_games'):
            cmd.extend(["--max_games", str(params['max_games'])])
        
        if params.get('offset'):
            cmd.extend(["--start_offset", str(params['offset'])])
        
        if params.get('delay'):
            cmd.extend(["--delay", str(params['delay'])])
        
        # Set output file specific to this job
        output_file = f"results/job_{job_id}.json"
        cmd.extend(["--output", output_file])
        
        # Run the extraction process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Capture log output
        log_file = f"logs/job_{job_id}.log"
        with open(log_file, 'w', encoding='utf-8') as log:
            for line in iter(process.stdout.readline, ''):
                log.write(line)
                log.flush()
                
                # Update job info with progress data
                if "找到 " in line and " 个游戏" in line:
                    try:
                        games_found = int(line.split("找到 ")[1].split(" 个游戏")[0])
                        update_job(job_id, {'found': games_found})
                    except:
                        pass
                
                if "成功找到iframe源" in line:
                    update_job(job_id, {'successful': jobs[job_id].get('successful', 0) + 1})
                
                if "已处理 " in line and " 个游戏" in line:
                    try:
                        processed = int(line.split("已处理 ")[1].split(" 个游戏")[0])
                        update_job(job_id, {'processed': processed})
                    except:
                        pass
        
        # Wait for process to complete
        process.wait()
        
        # Check if results were generated
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Read results file
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                
            # Update job info
            update_job(job_id, {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'result_count': len(results),
                'result_file': output_file
            })
        else:
            # Something went wrong
            update_job(job_id, {
                'status': 'failed',
                'error': 'No results were generated'
            })
    
    except Exception as e:
        # Handle exceptions
        update_job(job_id, {
            'status': 'failed',
            'error': str(e)
        })

# 修改模拟数据处理函数，优化真实爬取功能
def mock_process_job(job_id, params):
    """
    A mock job processing function for demonstration purposes
    This is useful for Vercel deployment where background processing isn't available
    
    Args:
        job_id: Job ID
        params: Processing parameters
    """
    # Update job status
    update_job(job_id, {'status': 'processing'})
    
    # Create a results directory if it doesn't exist
    try:
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        
        # Create a sample result
        result_file = os.path.join(RESULTS_DIR, f"job_{job_id}.json")
        
        # 限制最大游戏数量，避免超时
        max_games = min(params.get('max_games', 1), 5)  # 默认只爬取1个游戏，最多5个
        offset = params.get('offset', 0)
        delay = min(max(params.get('delay', 1.0), 1.0), 2.0)  # 确保延迟在1-2秒之间
        
        # 强制使用真实爬虫，禁用回退机制
        use_real_scraper = True
        print(f"强制使用真实爬虫模式 (禁用回退)")
        
        # 创建独立的日志文件
        log_file_path = os.path.join(LOGS_DIR, f"job_{job_id}.log")
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"===== 任务开始: {job_id} =====\n")
            log_file.write(f"时间: {datetime.now().isoformat()}\n")
            log_file.write(f"参数: max_games={max_games}, offset={offset}, delay={delay}\n")
            log_file.write(f"环境变量: USE_REAL_SCRAPER=true (强制启用)\n")
            log_file.write(f"运行环境: {'Vercel' if 'VERCEL' in os.environ else '本地'}\n")
            log_file.write(f"Vercel环境变量检查:\n")
            for key, value in os.environ.items():
                if key.startswith('VERCEL') or key == 'USE_REAL_SCRAPER' or key == 'PYTHONUNBUFFERED':
                    log_file.write(f"  {key}={value}\n")
            log_file.flush()
            
            # 始终使用真实爬虫进行爬取
            log_file.write(f"=== 强制使用真实爬虫进行爬取 ===\n")
            log_file.flush()
            print("=== 强制使用真实爬虫进行爬取 ===")
            print(f"最大游戏数: {max_games}, 偏移量: {offset}, 延迟: {delay}秒")
            
            try:
                # 创建自定义爬虫实例
                scraper = FastItchIoScraper(max_games=max_games, start_offset=offset, delay=delay)
                
                # 执行爬取
                results, stats = scraper.scrape()
                
                # 更新状态并输出统计信息
                log_file.write(f"爬取完成: 处理了 {stats['total_processed']} 个游戏，成功提取 {stats['successful_extractions']} 个iframe源\n")
                log_file.write(f"耗时: {stats['elapsed_seconds']:.2f}秒\n")
                log_file.flush()
                
                update_job(job_id, {
                    'processed': stats['total_processed'],
                    'successful': stats['successful_extractions']
                })
                
                # 详细记录请求和响应
                log_file.write("------ 网络请求详情 ------\n")
                try:
                    # 测试网络连接
                    test_url = "https://itch.io/games/free/platform-web"
                    headers = {
                        'User-Agent': scraper.get_random_user_agent(),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    }
                    req = urllib.request.Request(test_url, headers=headers)
                    
                    # 记录请求信息
                    log_file.write(f"测试请求URL: {test_url}\n")
                    log_file.write(f"请求头: {headers}\n")
                    
                    try:
                        with urllib.request.urlopen(req, timeout=10) as response:
                            log_file.write(f"响应状态码: {response.status}\n")
                            log_file.write(f"响应头: {response.headers}\n")
                            response_text = response.read().decode('utf-8')[:500]  # 只记录前500个字符
                            log_file.write(f"响应内容摘要: {response_text}...(已截断)\n")
                    except Exception as e:
                        log_file.write(f"测试请求失败: {e}\n")
                except Exception as e:
                    log_file.write(f"网络测试发生错误: {e}\n")
                
                log_file.write("-------------------------\n")
                log_file.flush()
                
                # 无论结果如何，都使用真实爬取的数据
                if results:
                    log_file.write(f"成功获取 {len(results)} 个结果\n")
                    for i, result in enumerate(results):
                        log_file.write(f"结果 {i+1}: {result.get('title')} - {result.get('iframe_src')}\n")
                        
                    # 确保每个结果都有iframe_src
                    valid_results = []
                    for result in results:
                        if result.get('iframe_src'):
                            valid_results.append(result)
                            result['extracted_method'] = "real_scraper"  # 明确标记为实时爬取
                        else:
                            log_file.write(f"警告: 跳过没有iframe_src的结果: {result.get('title')}\n")
                    
                    if valid_results:
                        log_file.write(f"有效结果数: {len(valid_results)}\n")
                        sample_results = valid_results
                    else:
                        log_file.write("警告: 没有有效的iframe源结果\n")
                        # 创建一个明确标记失败的结果
                        sample_results = [{
                            "title": "爬取失败 - 无有效结果",
                            "url": "https://itch.io/games/free/platform-web",
                            "iframe_src": "",
                            "extracted_method": "real_scraper_failed",
                            "error": "No valid iframe sources found"
                        }]
                else:
                    log_file.write("警告: 爬取完成但没有结果\n")
                    # 创建一个明确标记失败的结果
                    sample_results = [{
                        "title": "爬取失败 - 无结果",
                        "url": "https://itch.io/games/free/platform-web",
                        "iframe_src": "",
                        "extracted_method": "real_scraper_failed",
                        "error": "No results returned from scraper"
                    }]
            except Exception as e:
                log_file.write(f"错误: 真实爬取失败: {e}\n")
                import traceback
                error_trace = traceback.format_exc()
                log_file.write(f"错误详情:\n{error_trace}\n")
                
                print(f"真实爬取失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
                
                # 创建一个明确标记错误的结果
                sample_results = [{
                    "title": f"爬取失败 - {str(e)[:50]}",
                    "url": "https://itch.io/games/free/platform-web",
                    "iframe_src": "",
                    "extracted_method": "real_scraper_error",
                    "error": str(e)
                }]
            
            # 添加元数据到结果中
            result_with_metadata = {
                "metadata": {
                    "job_id": job_id,
                    "timestamp": datetime.now().isoformat(),
                    "params": params,
                    "source": "real_scraper",  # 即使失败也标记为真实爬取
                    "count": len(sample_results),
                    "vercel_env": 'VERCEL' in os.environ,
                    "env_vars": {k: os.environ.get(k, 'not_set') for k in ['USE_REAL_SCRAPER', 'VERCEL', 'PYTHONUNBUFFERED']},
                    "execution_time": stats['elapsed_seconds'] if 'stats' in locals() else 0
                },
                "results": sample_results
            }
            
            # 保存结果
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_with_metadata, f, indent=2, ensure_ascii=False)
            
            log_file.write(f"结果已保存到: {result_file}\n")
            log_file.write(f"===== 任务结束: {job_id} =====\n")
            log_file.flush()
            
            print(f"结果已保存到: {result_file}")
            
            # 更新任务状态
            update_job(job_id, {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'result_count': len(sample_results),
                'result_file': result_file,
                'processed': stats['total_processed'] if 'stats' in locals() else 0,
                'successful': stats['successful_extractions'] if 'stats' in locals() else 0,
                'found': stats['total_processed'] if 'stats' in locals() else 0,
                'source': "real_scraper"  # 即使失败也标记为真实爬取
            })
    except Exception as e:
        print(f"Error in mock processing: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"详细错误: {error_trace}")
        
        # 记录错误到日志文件
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"致命错误: {e}\n")
                log_file.write(f"错误详情:\n{error_trace}\n")
                log_file.write(f"===== 任务失败: {job_id} =====\n")
        except:
            pass
            
        update_job(job_id, {
            'status': 'failed',
            'error': str(e)
        })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        return send_from_directory('.', 'index.html')
    else:
        return send_from_directory('.', path)

@app.route('/api/extract', methods=['POST'])
def extract():
    """Handle extraction requests"""
    try:
        # Get request data
        data = request.json
        print(f"Received request data: {data}")
        
        if data is None:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON data'
            }), 400
        
        # Email is now optional
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        print(f"Generated job ID: {job_id}")
        
        # Process numeric parameters safely
        try:
            max_games = int(data.get('max_games', 10))
        except (ValueError, TypeError):
            max_games = 10
            
        try:
            offset = int(data.get('offset', 0))
        except (ValueError, TypeError):
            offset = 0
            
        try:
            delay = float(data.get('delay', 2))
        except (ValueError, TypeError):
            delay = 2
        
        # Create job record
        jobs[job_id] = {
            'id': job_id,
            'email': data.get('email', ''),  # Email is now optional
            'params': {
                'max_games': max_games,
                'offset': offset,
                'delay': delay,
                'categories': data.get('categories', []),
                'include_info': data.get('include_info', [])
            },
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'processed': 0,
            'successful': 0,
            'found': 0
        }
        
        # Save job to file
        save_job(job_id)
        print(f"Saved job {job_id} to file")
        
        # Check if we're running on Vercel or locally
        in_vercel = 'VERCEL' in os.environ
        print(f"Running in Vercel environment: {in_vercel}")
        
        if in_vercel:
            # On Vercel, use mock processing since we can't run background threads
            print(f"Using mock processing for job {job_id}")
            mock_process_job(job_id, jobs[job_id]['params'])
        else:
            # Start extraction process in a new thread for local development
            print(f"Starting background thread for job {job_id}")
            thread = threading.Thread(
                target=run_extraction_job,
                args=(job_id, jobs[job_id]['params'])
            )
            thread.daemon = True
            thread.start()
        
        # Return job ID to client
        return jsonify({
            'status': 'success',
            'message': 'Extraction job submitted successfully',
            'job_id': job_id
        })
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        print(f"Error in extract endpoint: {str(e)}")
        print(f"Traceback: {err_trace}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/status/<job_id>')
def job_status(job_id):
    """Get job status"""
    try:
        print(f"Status request for job: {job_id}")
        print(f"Available jobs: {list(jobs.keys())}")
        
        if job_id not in jobs:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
        
        # Return job info
        job_info = {
            'id': jobs[job_id]['id'],
            'status': jobs[job_id]['status'],
            'created_at': jobs[job_id]['created_at'],
            'processed': jobs[job_id].get('processed', 0),
            'successful': jobs[job_id].get('successful', 0),
            'found': jobs[job_id].get('found', 0),
            'completed_at': jobs[job_id].get('completed_at'),
            'result_count': jobs[job_id].get('result_count')
        }
        print(f"Returning job info: {job_info}")
        
        return jsonify({
            'status': 'success',
            'job': job_info
        })
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        print(f"Error in status endpoint: {str(e)}")
        print(f"Traceback: {err_trace}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

# 修改下载API端点，支持更灵活的结果格式
@app.route('/api/download/<job_id>')
def download_results(job_id):
    """Download job results"""
    try:
        if job_id not in jobs:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
        
        if jobs[job_id]['status'] != 'completed':
            return jsonify({
                'status': 'error',
                'message': 'Job is not completed yet'
            }), 400
        
        result_file = jobs[job_id].get('result_file')
        if not result_file or not os.path.exists(result_file):
            return jsonify({
                'status': 'error',
                'message': 'Result file not found'
            }), 404
        
        # 读取结果文件，检查格式
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否已经包含元数据结构
        if isinstance(data, dict) and 'results' in data and 'metadata' in data:
            # 已经是新格式，直接使用
            formatted_results = data
        else:
            # 旧格式，添加元数据结构
            formatted_results = {
                "metadata": {
                    "job_id": job_id,
                    "timestamp": jobs[job_id].get('completed_at', datetime.now().isoformat()),
                    "params": jobs[job_id].get('params', {}),
                    "source": jobs[job_id].get('source', 'unknown'),
                    "count": len(data)
                },
                "results": data
            }
        
        # 保存回文件
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_results, f, indent=2, ensure_ascii=False)
        
        # 输出简单的结果摘要
        result_summary = {
            "job_id": job_id,
            "count": len(formatted_results["results"]),
            "completed_at": jobs[job_id].get('completed_at'),
            "source": formatted_results["metadata"]["source"]
        }
        print(f"下载结果: {result_summary}")
        
        return send_file(
            result_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'iframe_results_{job_id}.json'
        )
    except Exception as e:
        print(f"Error in download endpoint: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

# Add a healthcheck endpoint for Vercel
@app.route('/api/healthcheck')
def healthcheck():
    """Health check endpoint for Vercel"""
    return jsonify({
        'status': 'success',
        'message': 'Service is running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# For local development, we keep the old handlers
if __name__ == '__main__':
    # Load existing jobs
    load_jobs()
    
    # Create necessary directories
    setup_result_directories()
    
    # Start Flask server
    print("Starting itch.io Game Iframe Extractor server on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000) 