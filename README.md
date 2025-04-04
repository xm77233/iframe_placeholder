# itch.io游戏iframe源爬取工具

## 项目介绍

这是一个用于从itch.io网站爬取免费网页游戏iframe源地址的工具。通过分析网页结构，提取内嵌游戏的iframe源地址，可以方便地获取游戏的嵌入链接，用于展示或测试。

## 主要功能

- 自动爬取itch.io上的免费网页游戏列表
- 支持分页爬取，可获取全部50万+免费网页游戏
- 分析游戏页面结构，提取iframe源地址
- 支持多种iframe嵌入模式的识别
- 提供HTML查看器，方便直接加载和查看游戏
- 支持延迟加载策略，解决音频自动播放限制问题

## 技术实现

- 爬虫使用Python标准库实现，无需安装第三方依赖
- HTML查看器使用纯JavaScript实现
- 采用多种正则表达式匹配策略，提高提取成功率
- 分页机制基于offset参数实现，自动处理翻页
- 完善的日志系统，便于追踪和调试

## 最近更新

- 添加了分页爬取功能，现在可以爬取itch.io上所有的免费网页游戏（超过50万款）
- 新增命令行参数支持，实现更灵活的配置：
  - `--max_games`: 限制爬取游戏数量
  - `--start_offset`: 设置起始偏移量，支持断点续传
  - `--delay`: 控制请求间隔时间
  - `--save_interval`: 定义自动保存频率
- 增强了正则表达式匹配模式，支持更灵活的HTML结构分析
- 新增了多种iframe源提取方法，包括：
  - 从`html_embed`元素中提取iframe标签的src属性
  - 从`html_embed`元素中提取data-iframe属性
  - 从`iframe_placeholder`元素中提取data-iframe属性
  - 从`load_iframe_btn`按钮的父元素中提取data-iframe属性
  - 从`game_frame`元素中提取data-iframe属性
- 解决了特殊游戏页面（如Cantata）的iframe源提取问题
- 提高了整体提取成功率

## 使用方法

1. 运行爬虫脚本：
```bash
# 爬取全部游戏
python iframe_scraper.py

# 只爬取前100个游戏
python iframe_scraper.py --max_games 100

# 从第200个游戏开始爬取
python iframe_scraper.py --start_offset 200

# 自定义延迟和保存间隔
python iframe_scraper.py --delay 3 --save_interval 20
```

2. 查看结果文件：`results/game_iframes.json`
3. 使用HTML查看器：打开`iframe_viewer.html`并加载结果文件

## 目录结构

- `iframe_scraper.py` - 主爬虫脚本
- `iframe_viewer.html` - 查看爬取结果的HTML页面
- `使用说明.md` - 中文使用说明文档
- `results/` - 保存爬取结果的目录
- `logs/` - 保存日志文件的目录
- `debug_html/` - 保存调试用HTML源码的目录

## 注意事项

- 完整爬取所有游戏需要相当长的时间，建议使用`--max_games`参数限制爬取数量
- 长时间爬取可能会被itch.io网站限制访问，建议适当增加`--delay`参数值
- 请尊重itch.io的使用条款，不要过度爬取或用于商业用途
- 某些游戏可能存在加载问题，特别是带有音频自动播放的游戏
- 建议使用最新版的Chrome或Firefox浏览器访问HTML查看器 