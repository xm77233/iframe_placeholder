# 本地部署指南

本文档提供了在本地环境部署和运行 iframe_placeholder 项目的详细步骤。本地部署适合开发测试、大规模爬取或需要完全控制爬虫行为的场景。

## 系统要求

- Python 3.7 或更高版本
- pip（Python 包管理器）
- 稳定的网络连接
- Git（可选，用于克隆仓库）

## 部署步骤

### 1. 获取项目代码

**方法一：使用 Git 克隆**

```bash
git clone https://github.com/xm77233/iframe_placeholder.git
cd iframe_placeholder
```

**方法二：下载 ZIP 压缩包**

1. 访问 [GitHub 仓库页面](https://github.com/xm77233/iframe_placeholder)
2. 点击 "Code" 按钮，然后点击 "Download ZIP"
3. 解压下载的文件，并通过终端进入解压后的目录

### 2. 安装依赖

本项目核心功能仅使用 Python 标准库，无需安装额外依赖。但如果您想运行在线工具网站，需要安装 Flask：

```bash
pip install flask
```

### 3. 创建目录结构

确保项目中存在以下目录，如果不存在，请创建它们：

```bash
mkdir -p results logs debug_html
```

### 4. 运行方式

本项目有两种主要的运行方式：

#### A. 命令行爬虫

命令行爬虫提供完整的爬取功能，支持各种参数配置：

```bash
# 基本用法（爬取前10个游戏）
python iframe_scraper.py

# 爬取指定数量的游戏
python iframe_scraper.py --max_games 50

# 从指定偏移量开始爬取
python iframe_scraper.py --start_offset 100

# 调整爬取延迟（秒）
python iframe_scraper.py --delay 2

# 调整保存间隔（每爬取多少个游戏保存一次）
python iframe_scraper.py --save_interval 20

# 组合使用多个参数
python iframe_scraper.py --max_games 200 --start_offset 300 --delay 3 --save_interval 50
```

爬取结果将保存在 `results/game_iframes.json` 文件中。

#### B. 在线工具网站服务器

在线工具网站提供了用户友好的Web界面，适合那些不熟悉命令行的用户：

```bash
# 启动服务器
python server.py
```

启动后，在浏览器中访问：http://127.0.0.1:5000

### 5. 查看结果

#### 查看 JSON 结果

爬取结果保存为 JSON 格式，您可以使用任何文本编辑器查看：

```bash
# Linux/Mac
cat results/game_iframes.json

# Windows
type results\game_iframes.json
```

#### 使用 HTML 查看器

项目提供了 HTML 查看器，用于预览和测试游戏：

1. 在浏览器中打开 `iframe_viewer.html` 文件
2. 点击 "选择文件" 按钮，选择 `results/game_iframes.json`
3. 点击游戏列表中的项目，在右侧预览游戏

## 常见问题

### 1. 爬取速度慢

爬取速度受以下因素影响：
- 网络连接质量
- 设置的延迟时间 (`--delay` 参数)
- 目标网站响应速度

建议增加延迟时间，以避免被目标网站临时封禁。

### 2. 部分游戏无法提取 iframe 源

不同游戏页面的结构可能略有不同，导致某些游戏的 iframe 源无法提取。项目已实现多种提取方法，但仍无法保证100%的成功率。

### 3. 游戏加载问题

某些游戏可能存在加载问题，特别是带有音频自动播放的游戏，这是由于浏览器策略限制引起的，非项目本身问题。

### 4. 如何持续运行大规模爬取

对于需要长时间运行的大规模爬取任务，可以考虑：

```bash
# Linux/Mac 使用 nohup 后台运行
nohup python iframe_scraper.py --max_games 10000 --delay 3 &

# 或使用 screen/tmux 会话管理
screen -S scraper
python iframe_scraper.py --max_games 10000 --delay 3
# Ctrl+A, D 分离会话
```

## 性能优化建议

1. **调整延迟时间**：
   - 过低的延迟可能导致被封禁
   - 过高的延迟会降低爬取效率
   - 建议从 2-3 秒开始，根据情况调整

2. **分段爬取**：
   - 使用 `--start_offset` 和 `--max_games` 参数分批爬取
   - 例如：先爬取 1-1000，再爬取 1001-2000，依此类推

3. **定期备份**：
   - 使用 `--save_interval` 参数控制保存频率
   - 手动备份 `results/game_iframes.json` 文件

## 相关资源

- [项目 GitHub 仓库](https://github.com/xm77233/iframe_placeholder)
- [itch.io 网站](https://itch.io)
- [Python 文档](https://docs.python.org) 