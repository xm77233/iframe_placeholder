#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这是一个简单的爬虫脚本，用于爬取itch.io网站上的游戏，
并找到游戏链接和标题信息
"""

import urllib.request
import json
import os
import time
import re
import logging
import html
from datetime import datetime

# 设置日志
def setup_logger():
    """设置日志记录器"""
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 获取当前时间作为日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/scraper_log_{timestamp}.txt"
    
    # 配置日志记录器
    logger = logging.getLogger('iframe_scraper')
    logger.setLevel(logging.DEBUG)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 全局日志记录器
logger = setup_logger()

def get_game_page_urls(url):
    """
    获取游戏页面的URL列表和标题
    
    参数:
        url: itch.io游戏列表页面的URL
    
    返回:
        包含游戏URL和标题的字典列表
    """
    logger.info(f"正在获取游戏列表: {url}")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 创建请求
    req = urllib.request.Request(url, headers=headers)
    
    try:
        # 发送请求获取网页内容
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            
        # 找到所有游戏单元格
        game_cells = re.findall(r'<div class="game_cell[^>]*>(.*?)</div>\s*</div>\s*</div>', html_content, re.DOTALL)
        
        games = []
        for cell in game_cells:
            # 从game_cell_data中提取游戏标题和链接
            cell_data = re.search(r'<div class="game_cell_data">(.*?)</div>', cell, re.DOTALL)
            if cell_data:
                cell_data_content = cell_data.group(1)
                
                # 提取游戏标题和链接
                title_match = re.search(r'<div class="game_title">\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', cell_data_content, re.DOTALL)
                
                if title_match:
                    game_url = title_match.group(1)
                    game_title = re.sub(r'<[^>]*>', '', title_match.group(2)).strip()
                    
                    games.append({
                        'title': game_title,
                        'url': game_url
                    })
        
        logger.info(f"找到 {len(games)} 个游戏")
        return games
    
    except Exception as e:
        logger.error(f"获取页面时出错: {e}")
        return []

def get_iframe_src(game_url):
    """
    从游戏页面获取iframe的src属性
    
    参数:
        game_url: 游戏页面的URL
    
    返回:
        iframe的src属性值，如果没有找到则返回None
    """
    logger.info(f"正在分析游戏页面: {game_url}")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 创建请求
    req = urllib.request.Request(game_url, headers=headers)
    
    try:
        # 发送请求获取网页内容
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
        
        # 保存HTML到文件进行调试
        debug_dir = 'debug_html'
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        game_id = game_url.split('/')[-1] if '/' in game_url else 'game'
        with open(f"{debug_dir}/{game_id}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 查找iframe_placeholder中的data-iframe属性
        iframe_placeholder = re.search(r'<div class="iframe_placeholder"\s+data-iframe="([^"]*)"', html_content)
        if iframe_placeholder:
            # 获取data-iframe属性值并解码HTML实体
            iframe_data_str = iframe_placeholder.group(1)
            iframe_data_str = html.unescape(iframe_data_str)
            
            # 从iframe标签中提取src属性
            iframe_src_match = re.search(r'src="([^"]*)"', iframe_data_str)
            if iframe_src_match:
                iframe_src = iframe_src_match.group(1)
                logger.info(f"从data-iframe属性中找到iframe源: {iframe_src}")
                return iframe_src
            else:
                logger.warning(f"在data-iframe中未找到src属性")
        
        logger.warning(f"未能找到iframe源")
        return None
    
    except Exception as e:
        logger.error(f"获取游戏页面时出错: {e}")
        return None

def main():
    """主函数"""
    # 开始记录
    logger.info("==== 开始爬取itch.io游戏iframe源 ====")
    
    # itch.io网页游戏列表页面，只爬取免费游戏
    url = 'https://itch.io/games/free/platform-web'
    
    # 创建保存结果的目录
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # 获取游戏页面URL和标题
    games = get_game_page_urls(url)
    
    # 限制爬取的游戏数量，防止请求过多
    max_games = 10  # 增加到10个游戏
    logger.info(f"限制处理前{max_games}个游戏（总共有{len(games)}个）")
    games = games[:max_games]
    
    # 结果列表
    results = []
    
    # 遍历游戏页面并获取iframe src
    for i, game in enumerate(games):
        logger.info(f"处理游戏 {i+1}/{len(games)}: {game['title']}")
        
        # 获取iframe src
        iframe_src = get_iframe_src(game['url'])
        
        if iframe_src:
            logger.info(f"成功找到iframe源: {iframe_src}")
            results.append({
                'title': game['title'],
                'game_url': game['url'],
                'iframe_src': iframe_src
            })
        else:
            logger.warning(f"未找到iframe源")
        
        # 添加延迟，避免请求过于频繁
        if i < len(games) - 1:
            logger.info("等待2秒...")
            time.sleep(2)
    
    # 保存结果到JSON文件
    output_file = 'results/game_iframes.json'
    
    # 如果没有找到任何游戏，创建一个空数组的JSON文件
    if not results:
        results = []
    
    # 确保结果是UTF-8格式，不使用ensure_ascii
    with open(output_file, 'w', encoding='utf-8') as f:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        f.write(json_str)
    
    logger.info(f"完成! 结果已保存到 {output_file}")
    logger.info(f"成功获取 {len(results)}/{len(games)} 个游戏的iframe源")
    logger.info("==== 爬取完成 ====")

if __name__ == "__main__":
    main() 