# iframe_placeholder

这是一个用于从itch.io网站爬取免费网页游戏iframe源地址的工具，可以轻松获取并展示游戏嵌入地址。

## 功能特点

- 自动爬取itch.io上免费网页游戏的iframe源地址
- 仅从`div class="iframe_placeholder"`的`data-iframe`属性中提取`src`值
- 提供HTML查看器，允许直接加载并体验游戏
- 采用延迟加载策略，解决浏览器音频自动播放限制问题
- 完全使用Python标准库实现，无需额外依赖

## 使用说明

### 运行爬虫

```bash
python iframe_scraper.py
```

默认爬取前10个免费网页游戏，结果保存在`results/game_iframes.json`文件中。

### 查看爬取结果

打开`iframe_viewer.html`文件，点击"选择JSON文件"按钮，选择生成的`results/game_iframes.json`文件。然后点击每个游戏的"点击开始游戏"按钮来加载并体验游戏。

## 目录结构

- `iframe_scraper.py`: 爬虫脚本
- `iframe_viewer.html`: HTML查看器
- `使用说明.md`: 详细的中文使用说明
- `results/`: 保存爬取结果的目录
- `logs/`: 保存爬取日志的目录
- `debug_html/`: 保存爬取的游戏HTML页面的目录

## 技术实现

- 爬虫使用Python标准库实现
- HTML查看器使用纯JavaScript实现
- 采用正则表达式提取源代码中的相关信息
- 使用HTML实体解码处理特殊字符

## 注意事项

- 该工具仅用于学习和研究目的
- 请尊重itch.io的使用条款和游戏开发者的权益
- 某些游戏可能无法正常加载，这可能是由于游戏本身的限制或浏览器的安全策略 