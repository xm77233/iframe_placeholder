# itch.io游戏iframe源爬取工具

一个用于从itch.io网站爬取免费网页游戏iframe源地址的综合工具，提供友好的Web界面和强大的爬取功能。

## 最新功能：在线工具网站

我们推出了全新设计的在线工具网站，通过浏览器界面轻松提交爬虫任务并直接下载结果！

![在线工具网站截图](https://via.placeholder.com/800x450.png?text=itch.io+Game+Iframe+Extractor)

### Vercel在线部署

您可以直接访问我们在Vercel上部署的版本：
[https://iframe-placeholder.vercel.app](https://iframe-placeholder.vercel.app)

无需自行部署，直接在浏览器中使用。

### 本地启动在线工具网站

如需本地部署，请按照以下步骤操作：

1. 克隆仓库或下载源代码
```bash
git clone https://github.com/xm77233/iframe_placeholder.git
cd iframe_placeholder
```

2. 安装Python依赖
```bash
pip install flask
```

3. 启动在线工具网站服务器
```bash
python server.py
```

4. 在浏览器中访问
```
http://127.0.0.1:5000
```

## 项目介绍

这是一个用于从itch.io网站爬取免费网页游戏iframe源地址的工具。通过分析网页结构，提取内嵌游戏的iframe源地址，可以方便地获取游戏的嵌入链接，用于展示或测试。

## 主要功能

- **在线工具网站**：用户友好的界面，简单配置参数，直接下载结果
- **Vercel部署**：提供随时可用的在线版本，无需本地部署
- 自动爬取itch.io上的免费网页游戏列表
- 支持分页爬取，可获取全部50万+免费网页游戏
- 分析游戏页面结构，提取iframe源地址
- 支持多种iframe嵌入模式的识别
- 提供HTML查看器，方便直接加载和查看游戏
- 支持延迟加载策略，解决音频自动播放限制问题

## 技术实现

- 爬虫使用Python标准库实现，无需安装第三方依赖
- 在线工具网站使用Flask和Tailwind CSS构建
- HTML查看器使用纯JavaScript实现
- 采用多种正则表达式匹配策略，提高提取成功率
- 分页机制基于offset参数实现，自动处理翻页
- 完善的日志系统，便于追踪和调试
- 异步任务处理，通过电子邮件发送结果

## 使用方法

### 通过在线工具网站

1. 启动服务器：`python server.py`
2. 在浏览器访问：`http://127.0.0.1:5000`
3. 输入您的电子邮件地址和所需参数
4. 提交任务
5. 结果将发送到您的电子邮件

### 通过命令行

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

## 目录结构

- `iframe_scraper.py` - 主爬虫脚本
- `server.py` - 在线工具网站的Flask服务器
- `index.html` - 在线工具网站页面
- `iframe_viewer.html` - 查看爬取结果的HTML页面
- `README_en.md` - 英文详细文档
- `README_zh.md` - 中文详细文档
- `使用说明.md` - 使用说明文档
- `results/` - 保存爬取结果的目录
- `logs/` - 保存日志文件的目录
- `debug_html/` - 保存调试用HTML源码的目录
- `jobs/` - 保存任务信息的目录

## 注意事项

- 完整爬取所有游戏需要相当长的时间，建议使用`--max_games`参数限制爬取数量
- 长时间爬取可能会被itch.io网站限制访问，建议适当增加`--delay`参数值
- 请尊重itch.io的使用条款，不要过度爬取或用于商业用途
- 某些游戏可能存在加载问题，特别是带有音频自动播放的游戏
- 建议使用最新版的Chrome或Firefox浏览器访问在线工具网站和HTML查看器

## GitHub仓库

### 创建GitHub仓库

1. 登录GitHub账户
2. 点击右上角"+"图标，选择"New repository"
3. 填写仓库名称（例如："iframe_placeholder"或"xm77233"）
4. 添加描述："itch.io游戏iframe源爬取工具"
5. 选择公开或私有仓库
6. 点击"Create repository"

### 上传项目到GitHub

```bash
# 初始化Git仓库（如果尚未初始化）
git init

# 添加所有文件到暂存区
git add .

# 提交更改
git commit -m "初始提交：iframe_placeholder项目"

# 添加远程仓库
git remote add origin https://github.com/用户名/仓库名.git

# 推送到GitHub
git push -u origin main
```

### 克隆仓库

```bash
# 克隆仓库到本地
git clone https://github.com/用户名/仓库名.git

# 进入项目目录
cd 仓库名
```

## 在线工具网站

您可以直接访问我们部署在Vercel上的在线工具：[iframe采集工具](https://iframe-placeholder.vercel.app/)

通过在线工具，您可以：
1. 一键采集最新的itch.io免费网页游戏iframe源地址
2. 即时预览并体验游戏
3. 导出JSON结果文件 