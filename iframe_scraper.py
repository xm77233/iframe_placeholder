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
import argparse
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

def get_game_page_urls(url, offset=0):
    """
    获取游戏页面的URL列表和标题
    
    参数:
        url: itch.io游戏列表页面的URL
        offset: 分页偏移量
    
    返回:
        包含游戏URL和标题的字典列表, 以及是否有更多游戏的布尔值
    """
    # 添加offset参数到URL
    if '?' in url:
        page_url = f"{url}&offset={offset}"
    else:
        page_url = f"{url}?offset={offset}"
    
    logger.info(f"正在获取游戏列表: {page_url} (偏移量: {offset})")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 创建请求
    req = urllib.request.Request(page_url, headers=headers)
    
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
        
        # 检查是否有"下一页"按钮，判断是否还有更多游戏
        has_more = "Next page" in html_content or "下一页" in html_content
        
        logger.info(f"找到 {len(games)} 个游戏")
        return games, has_more
    
    except Exception as e:
        logger.error(f"获取页面时出错: {e}")
        return [], False

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
        
        # 寻找iframe源的综合方法
        iframe_src = None
        
        # 情况1: 查找html_embed元素中的iframe标签的src属性
        html_embed_match = re.search(r'<div[^>]*id="html_embed_\d+"[^>]*>(.*?)</div>', html_content, re.DOTALL)
        if html_embed_match:
            html_embed_content = html_embed_match.group(1)
            
            # 情况1.1: 直接从iframe标签中提取src属性
            iframe_tag = re.search(r'<iframe[^>]*src="([^"]*)"[^>]*>', html_embed_content)
            if iframe_tag:
                iframe_src = iframe_tag.group(1)
                logger.info(f"从html_embed的iframe标签中找到iframe源: {iframe_src}")
            
            # 情况1.2: 从data-iframe属性中提取src
            if not iframe_src:
                data_iframe = re.search(r'data-iframe="([^"]*)"', html_embed_content)
                if data_iframe:
                    # 获取data-iframe属性值并解码HTML实体
                    iframe_data_str = data_iframe.group(1)
                    iframe_data_str = html.unescape(iframe_data_str)
                    
                    # 从iframe标签中提取src属性
                    iframe_src_match = re.search(r'src="([^"]*)"', iframe_data_str)
                    if iframe_src_match:
                        iframe_src = iframe_src_match.group(1)
                        logger.info(f"从html_embed的data-iframe属性中找到iframe源: {iframe_src}")
        
        # 情况2: 如果在html_embed中找不到，则查找iframe_placeholder中的data-iframe属性
        if not iframe_src:
            iframe_placeholder = re.search(r'<div[^>]*class="iframe_placeholder"[^>]*data-iframe="([^"]*)"', html_content, re.DOTALL)
            if iframe_placeholder:
                # 获取data-iframe属性值并解码HTML实体
                iframe_data_str = iframe_placeholder.group(1)
                iframe_data_str = html.unescape(iframe_data_str)
                
                # 从iframe标签中提取src属性
                iframe_src_match = re.search(r'src="([^"]*)"', iframe_data_str)
                if iframe_src_match:
                    iframe_src = iframe_src_match.group(1)
                    logger.info(f"从iframe_placeholder的data-iframe属性中找到iframe源: {iframe_src}")
        
        # 情况3: 查找load_iframe_btn的父元素中的data-iframe属性
        if not iframe_src:
            load_iframe_btn = re.search(r'<div[^>]*data-iframe="([^"]*)"[^>]*>\s*<button[^>]*class="[^"]*load_iframe_btn[^"]*"', html_content, re.DOTALL)
            if load_iframe_btn:
                # 获取data-iframe属性值并解码HTML实体
                iframe_data_str = load_iframe_btn.group(1)
                iframe_data_str = html.unescape(iframe_data_str)
                
                # 从iframe标签中提取src属性
                iframe_src_match = re.search(r'src="([^"]*)"', iframe_data_str)
                if iframe_src_match:
                    iframe_src = iframe_src_match.group(1)
                    logger.info(f"从load_iframe_btn父元素的data-iframe属性中找到iframe源: {iframe_src}")
        
        # 情况4: 查找game_frame元素内的data-iframe属性
        if not iframe_src:
            game_frame = re.search(r'<div[^>]*class="game_frame[^"]*"[^>]*>\s*<div[^>]*data-iframe="([^"]*)"', html_content, re.DOTALL)
            if game_frame:
                # 获取data-iframe属性值并解码HTML实体
                iframe_data_str = game_frame.group(1)
                iframe_data_str = html.unescape(iframe_data_str)
                
                # 从iframe标签中提取src属性
                iframe_src_match = re.search(r'src="([^"]*)"', iframe_data_str)
                if iframe_src_match:
                    iframe_src = iframe_src_match.group(1)
                    logger.info(f"从game_frame内元素的data-iframe属性中找到iframe源: {iframe_src}")
        
        if iframe_src:
            return iframe_src
        else:
            logger.warning(f"未能找到iframe源")
            return None
    
    except Exception as e:
        logger.error(f"获取游戏页面时出错: {e}")
        return None

def save_results(results, output_file):
    """保存结果到JSON文件"""
    # 确保目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 如果没有找到任何游戏，创建一个空数组的JSON文件
    if not results:
        results = []
    
    # 确保结果是UTF-8格式，不使用ensure_ascii
    with open(output_file, 'w', encoding='utf-8') as f:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        f.write(json_str)
    
    logger.info(f"结果已保存到 {output_file}")
    logger.info(f"成功获取 {len(results)} 个游戏的iframe源")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='爬取itch.io网站上的游戏iframe源地址')
    parser.add_argument('--max_games', type=int, default=None, help='最多爬取的游戏数量，默认为无限制')
    parser.add_argument('--start_offset', type=int, default=0, help='开始的偏移量，用于继续上次的爬取')
    parser.add_argument('--page_size', type=int, default=36, help='每页游戏数量，默认为36')
    parser.add_argument('--delay', type=float, default=2.0, help='请求间隔时间（秒），默认为2秒')
    parser.add_argument('--output', type=str, default='results/game_iframes.json', help='输出文件路径')
    parser.add_argument('--save_interval', type=int, default=50, help='每爬取多少个游戏保存一次结果，默认为50')
    args = parser.parse_args()
    
    # 开始记录
    logger.info("==== 开始爬取itch.io游戏iframe源 ====")
    logger.info(f"参数设置: 最大游戏数量={args.max_games}, 起始偏移量={args.start_offset}, 每页大小={args.page_size}, 延迟={args.delay}秒")
    
    # itch.io网页游戏列表页面，只爬取免费游戏
    url = 'https://itch.io/games/free/platform-web'
    
    # 创建保存结果的目录
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # 结果列表
    results = []
    
    # 如果输出文件已存在并且开始偏移量大于0，尝试加载现有结果
    if os.path.exists(args.output) and args.start_offset > 0:
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                results = json.load(f)
                logger.info(f"从现有文件加载了 {len(results)} 个结果")
        except Exception as e:
            logger.error(f"加载现有结果文件时出错: {e}")
            results = []
    
    # 处理的游戏总数
    total_processed = 0
    successful_processed = 0
    
    # 当前偏移量
    offset = args.start_offset
    
    # 继续抓取直到达到最大游戏数或没有更多游戏
    while args.max_games is None or total_processed < args.max_games:
        # 获取当前页的游戏
        games, has_more = get_game_page_urls(url, offset)
        
        if not games:
            logger.info("没有找到更多游戏，结束爬取")
            break
        
        # 计算本次要处理的游戏数量
        if args.max_games is not None:
            games_to_process = min(len(games), args.max_games - total_processed)
            games = games[:games_to_process]
        
        # 遍历游戏页面并获取iframe src
        for i, game in enumerate(games):
            logger.info(f"处理游戏 {total_processed+1}: {game['title']}")
            
            # 获取iframe src
            iframe_src = get_iframe_src(game['url'])
            
            if iframe_src:
                logger.info(f"成功找到iframe源: {iframe_src}")
                results.append({
                    'title': game['title'],
                    'game_url': game['url'],
                    'iframe_src': iframe_src
                })
                successful_processed += 1
            else:
                logger.warning(f"未找到iframe源")
            
            total_processed += 1
            
            # 定期保存结果
            if total_processed % args.save_interval == 0:
                save_results(results, args.output)
                logger.info(f"已处理 {total_processed} 个游戏，其中 {successful_processed} 个成功")
            
            # 添加延迟，避免请求过于频繁
            if i < len(games) - 1:
                logger.info(f"等待{args.delay}秒...")
                time.sleep(args.delay)
            
            # 检查是否达到最大游戏数量
            if args.max_games is not None and total_processed >= args.max_games:
                logger.info(f"已达到最大游戏数量 {args.max_games}，停止爬取")
                break
        
        # 如果没有更多游戏或已达到最大游戏数量，退出循环
        if not has_more or (args.max_games is not None and total_processed >= args.max_games):
            break
        
        # 更新偏移量进入下一页
        offset += args.page_size
        logger.info(f"进入下一页，偏移量: {offset}")
        
        # 页面之间添加额外延迟
        logger.info(f"翻页等待 {args.delay * 2} 秒...")
        time.sleep(args.delay * 2)
    
    # 保存最终结果
    save_results(results, args.output)
    
    logger.info("==== 爬取完成 ====")
    logger.info(f"总共处理 {total_processed} 个游戏，成功获取 {successful_processed} 个游戏的iframe源")

if __name__ == "__main__":
    main() 