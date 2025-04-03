# feat：itch.io游戏iframe爬虫实现

## 描述
开发一个简单的Python爬虫，用于从itch.io网站获取网页游戏的iframe源地址，以便将这些游戏嵌入到自己的网站中。这个功能将允许我们在自己的网站上展示和播放itch.io上的HTML5游戏。爬虫必须只使用Python标准库（不使用第三方依赖），并且正确提取"game_title"信息。

## 任务
- [x] 创建Python爬虫脚本(iframe_scraper.py)，仅使用标准库
- [x] 从"div class='game_cell_data'"中"div class='game_title'"中提取游戏标题和链接
- [x] 编写HTML查看器(iframe_viewer.html)，支持加载本地JSON文件
- [x] 编写README.md，提供无依赖使用说明
- [ ] 添加更多游戏信息获取(如游戏描述、缩略图等)
- [ ] 实现分页爬取，获取更多游戏
- [ ] 添加错误处理和重试机制

## 相关问题
- 克服了无法安装第三方依赖的问题，改用Python标准库
- 解决了本地HTML文件无法通过fetch加载JSON的跨域问题，改用FileReader API
- 修复了游戏数据获取错误，正确提取"game_title"信息
- 可能需要考虑跨域(CORS)问题
- 需要遵守itch.io的服务条款和使用政策
- 一些游戏可能不允许通过iframe嵌入

## 状态历史
- [2023-10-30] - [x] 创建
- [2023-10-30] - [-] 实现基本功能
- [2023-10-31] - [x] 修复依赖和数据提取问题 