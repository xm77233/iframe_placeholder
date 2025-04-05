#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版的itch.io游戏iframe源爬取工具，专为Vercel无服务器环境设计
能够在Vercel函数执行时间限制内(10-60秒)完成部分数据爬取
"""

import urllib.request
import urllib.error
import re
import json
import time
import html
import random
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
            logger.error(f"获取URL {url} 失败: {e}")
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
        logger.info(f"获取游戏列表页面: {url}")
        
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
                    
            logger.info(f"找到 {len(games)} 个游戏")
            
        except Exception as e:
            logger.error(f"获取游戏列表失败: {e}")
        
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
                    logger.info(f"使用iframe标签提取成功: {game_url}")
            except Exception as e:
                logger.error(f"iframe标签提取失败: {e}")
        
        # 方法2: 检查html_embed区域中的data-iframe属性
        if not iframe_src:
            try:
                match = re.search(r'<div id="html_embed_content"[^>]*data-iframe="([^"]+)"', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "html_embed_data_iframe"
                    logger.info(f"使用data-iframe属性提取成功: {game_url}")
            except Exception as e:
                logger.error(f"data-iframe属性提取失败: {e}")
        
        # 方法3: 检查iframe_placeholder元素
        if not iframe_src:
            try:
                match = re.search(r'<div class="iframe_placeholder"[^>]*data-iframe="([^"]+)"', game_page_html)
                if match:
                    iframe_src = html.unescape(match.group(1))
                    extraction_method = "iframe_placeholder"
                    logger.info(f"使用iframe_placeholder提取成功: {game_url}")
            except Exception as e:
                logger.error(f"iframe_placeholder提取失败: {e}")
        
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
        logger.info(f"处理游戏: {game_title} ({game_url})")
        
        try:
            game_page_html = self.fetch_url(game_url)
            if not game_page_html:
                logger.error(f"无法获取游戏页面: {game_url}")
                return None
                
            iframe_src, extraction_method = self.get_iframe_src(game_page_html, game_url)
            
            if iframe_src:
                self.successful_count += 1
                logger.info(f"成功找到iframe源: {iframe_src}")
                
                return {
                    "title": game_title,
                    "url": game_url,
                    "iframe_src": iframe_src,
                    "extracted_method": extraction_method
                }
            else:
                logger.warning(f"未找到iframe源: {game_url}")
                return None
                
        except Exception as e:
            logger.error(f"处理游戏 {game_title} 失败: {e}")
            return None
    
    def scrape(self):
        """执行爬取过程"""
        logger.info(f"开始爬取，最大游戏数: {self.max_games}, 起始偏移: {self.start_offset}")
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
                logger.warning(f"接近时间限制，已处理 {i} 个游戏，提前结束")
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
        
        logger.info(f"爬取完成，处理了 {self.processed_count} 个游戏，成功提取 {self.successful_count} 个iframe源，耗时 {elapsed_time:.2f} 秒")
        
        return self.results, stats

# 用于直接测试
if __name__ == "__main__":
    scraper = FastItchIoScraper(max_games=5, delay=0.5)
    results, stats = scraper.scrape()
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}") 