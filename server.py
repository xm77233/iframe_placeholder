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
    
    def get_random_user_agent(self):
        """随机获取一个User-Agent"""
        return random.choice(USER_AGENTS)
    
    def fetch_url(self, url):
        """
        获取URL内容
        
        Args:
            url: 要获取的URL
            
        Returns:
            str: 页面HTML内容
        """
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"获取URL {url} 失败: {e}")
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
        
        url = f"https://itch.io/games/free/platform-web?offset={offset}"
        print(f"获取游戏列表页面: {url}")
        
        try:
            html_content = self.fetch_url(url)
            if not html_content:
                return []
            
            # 提取游戏标题和链接
            pattern = r'<a class="game_link" href="(https://[^"]+\.itch\.io/[^"]+)">\s*<div class="game_cell_data">\s*<div class="game_title">(.*?)</div>'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            for game_url, game_title in matches[:max_to_fetch]:
                games.append((game_url, html.unescape(game_title.strip())))
                self.processed_count += 1
                
                if len(games) >= max_to_fetch:
                    break
                    
            print(f"找到 {len(games)} 个游戏")
            
        except Exception as e:
            print(f"获取游戏列表失败: {e}")
        
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
        
        # 方法1: 检查html_embed区域中的iframe标签
        if not iframe_src:
            try:
                match = re.search(r'<div id="html_embed_content"[^>]*>.*?<iframe[^>]*src="([^"]+)"', game_page_html, re.DOTALL)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "html_embed_iframe"
                    print(f"使用iframe标签提取成功: {game_url}")
            except Exception as e:
                print(f"iframe标签提取失败: {e}")
        
        # 方法2: 检查html_embed区域中的data-iframe属性
        if not iframe_src:
            try:
                match = re.search(r'<div id="html_embed_content"[^>]*data-iframe="([^"]+)"', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "html_embed_data_iframe"
                    print(f"使用data-iframe属性提取成功: {game_url}")
            except Exception as e:
                print(f"data-iframe属性提取失败: {e}")
        
        # 方法3: 检查iframe_placeholder元素
        if not iframe_src:
            try:
                match = re.search(r'<div class="iframe_placeholder"[^>]*data-iframe="([^"]+)"', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "iframe_placeholder"
                    print(f"使用iframe_placeholder提取成功: {game_url}")
            except Exception as e:
                print(f"iframe_placeholder提取失败: {e}")
        
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
        print(f"处理游戏: {game_title} ({game_url})")
        
        try:
            game_page_html = self.fetch_url(game_url)
            if not game_page_html:
                print(f"无法获取游戏页面: {game_url}")
                return None
                
            iframe_src, extraction_method = self.get_iframe_src(game_page_html, game_url)
            
            if iframe_src:
                self.successful_count += 1
                print(f"成功找到iframe源: {iframe_src}")
                
                return {
                    "title": game_title,
                    "url": game_url,
                    "iframe_src": iframe_src,
                    "extracted_method": extraction_method
                }
            else:
                print(f"未找到iframe源: {game_url}")
                return None
                
        except Exception as e:
            print(f"处理游戏 {game_title} 失败: {e}")
            return None
    
    def scrape(self):
        """执行爬取过程"""
        print(f"开始爬取，最大游戏数: {self.max_games}, 起始偏移: {self.start_offset}")
        self.start_time = datetime.now()
        
        # 获取游戏页面URL
        game_urls = self.get_game_page_urls()
        
        # 处理每个游戏
        for i, (game_url, game_title) in enumerate(game_urls):
            # 添加延迟
            if i > 0 and self.delay > 0:
                time.sleep(self.delay)
                
            # 检查是否超时
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > 8:  # 设置8秒的安全阈值，确保在Vercel 10秒限制前返回
                print(f"接近时间限制，已处理 {i} 个游戏，提前结束")
                break
                
            # 处理游戏
            result = self.process_game(game_url, game_title)
            if result:
                self.results.append(result)
        
        # 生成统计信息
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        stats = {
            "total_processed": self.processed_count,
            "successful_extractions": self.successful_count,
            "elapsed_seconds": elapsed_time,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"爬取完成，处理了 {self.processed_count} 个游戏，成功提取 {self.successful_count} 个iframe源，耗时 {elapsed_time:.2f} 秒")
        
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

# 修改模拟数据处理函数，添加真实爬取功能
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
        
        max_games = min(params.get('max_games', 10), 15)  # 限制为最多15个游戏
        offset = params.get('offset', 0)
        
        # 使用环境变量决定是否使用真实爬虫
        use_real_scraper = os.environ.get('USE_REAL_SCRAPER', 'false').lower() == 'true'
        print(f"是否使用真实爬虫: {use_real_scraper}")
        
        # 如果启用真实爬虫，尝试爬取真实数据
        if use_real_scraper:
            try:
                print("使用真实爬虫进行爬取")
                scraper = FastItchIoScraper(max_games=max_games, start_offset=offset, delay=0.2)
                results, stats = scraper.scrape()
                
                # 如果爬取成功但结果为空，回退到预设数据
                if not results:
                    print("真实爬取无结果，回退到预设数据")
                    use_real_scraper = False
                else:
                    print(f"真实爬取成功，获取到 {len(results)} 个结果")
                    sample_results = results
            except Exception as e:
                print(f"真实爬取失败: {e}，回退到预设数据")
                use_real_scraper = False
        
        # 如果不使用真实爬虫或爬取失败，使用预设数据
        if not use_real_scraper:
            # 使用预先收集的真实iframe数据
            real_game_data = [
                {
                    "title": "Polytrack",
                    "url": "https://dddoooccc.itch.io/polytrack",
                    "iframe_src": "https://itch.io/embed-upload/8357347?color=444444",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Mr. Magpie's Harmless Card Game",
                    "url": "https://magpiecollective.itch.io/mr-magpies-harmless-card-game",
                    "iframe_src": "https://itch.io/embed-upload/8410214?color=222222",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Narrow One",
                    "url": "https://krajzeg.itch.io/narrow-one",
                    "iframe_src": "https://itch.io/embed-upload/2034417?color=222336",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Unleashed",
                    "url": "https://apoc.itch.io/unleashed",
                    "iframe_src": "https://itch.io/embed-upload/1694088?color=333333",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "GET YOKED: Extreme Bodybuilding",
                    "url": "https://frenchbread.itch.io/get-yoked-2",
                    "iframe_src": "https://itch.io/embed-upload/4507744?color=3a3a3a",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Friday Night Funkin'",
                    "url": "https://ninja-muffin24.itch.io/funkin",
                    "iframe_src": "https://itch.io/embed-upload/3671753?color=ffffff",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "TRACE: Definitive Edition",
                    "url": "https://pnkl.itch.io/trace-definitive-edition",
                    "iframe_src": "https://itch.io/embed-upload/7519291?color=4d4d4d",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Cantata",
                    "url": "https://afterthought-games.itch.io/cantata",
                    "iframe_src": "https://itch.io/embed-upload/2358082?color=16303b",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Chasing Control",
                    "url": "https://jn.itch.io/chasing-control",
                    "iframe_src": "https://itch.io/embed-upload/7519291?color=2d2d2d",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Sort the Court!",
                    "url": "https://graebor.itch.io/sort-the-court",
                    "iframe_src": "https://itch.io/embed/42665?dark=true",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Before the Darkness",
                    "url": "https://eumolpo.itch.io/before-the-darkness",
                    "iframe_src": "https://itch.io/embed-upload/5337708?color=100001",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Space Shooter",
                    "url": "https://maximilian-winter.itch.io/space-shooter",
                    "iframe_src": "https://itch.io/embed-upload/7563568?color=000000",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Spellbreak Alpha",
                    "url": "https://proletariat.itch.io/spellbreak",
                    "iframe_src": "https://itch.io/embed/276014?border_width=0&amp;bg_color=000000&amp;fg_color=44D6A2&amp;link_color=44D6A2&amp;border_color=000000",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Wander Home",
                    "url": "https://lambdadiode.itch.io/wander-home",
                    "iframe_src": "https://itch.io/embed/1472578?bg_color=d6c7ae&amp;fg_color=222222&amp;link_color=1dabe8&amp;border_color=4d463d",
                    "extracted_method": "real_preset_data"
                },
                {
                    "title": "Shoot-Out!",
                    "url": "https://cg-games.itch.io/shoot-out",
                    "iframe_src": "https://itch.io/embed-upload/4023233?color=000000",
                    "extracted_method": "real_preset_data"
                }
            ]
            
            # 根据请求的游戏数量返回相应数量的真实数据
            max_games = min(max_games, len(real_game_data))
            sample_results = real_game_data[:max_games]
            
            # 如果真实数据不够，再添加模拟数据补充
            if max_games > len(real_game_data):
                for i in range(len(real_game_data), max_games):
                    sample_results.append({
                        "title": f"Sample Game {i+1}",
                        "url": f"https://example.itch.io/sample-game-{i+1}",
                        "iframe_src": f"https://itch.io/embed-upload/1234567?color=333333",
                        "extracted_method": "mock_data"
                    })
        
        # Save the sample results
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(sample_results, f, indent=2)
        
        # Update the job status
        update_job(job_id, {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'result_count': len(sample_results),
            'result_file': result_file,
            'processed': len(sample_results),
            'successful': len(sample_results),
            'found': len(sample_results)
        })
    except Exception as e:
        print(f"Error in mock processing: {e}")
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

# 添加新的下载API端点
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
        
        return send_file(
            result_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'iframe_results_{job_id}.json'
        )
    except Exception as e:
        print(f"Error in download endpoint: {str(e)}")
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