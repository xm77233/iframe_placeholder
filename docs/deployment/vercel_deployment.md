# Vercel 部署指南

本文档提供了将 iframe_placeholder 项目部署到 Vercel 平台的详细步骤。Vercel 是一个流行的静态网站和无服务器函数托管平台，提供便捷的部署流程和免费计划。

## 部署前准备

1. 注册 [Vercel 账户](https://vercel.com/signup)
2. 确保您的项目已经推送到 GitHub 仓库
3. 项目中应包含 `vercel.json` 配置文件，用于定义部署设置

## 项目配置

1. 确保项目根目录包含 `vercel.json` 文件，内容如下：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "server.py",
      "use": "@vercel/python"
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/server.py"
    }
  ],
  "env": {
    "VERCEL": "true",
    "PYTHONUNBUFFERED": "1",
    "USE_REAL_SCRAPER": "true"
  },
  "functions": {
    "server.py": {
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

**重要提示**:
- 请注意 `USE_REAL_SCRAPER` 环境变量设置为 `"true"`，这将启用实时爬虫功能
- `maxDuration` 设置为 `60` 秒，这需要 Vercel 的 Hobby 计划才能生效
- 如果您使用免费计划，实际执行时间可能会被限制在 10 秒内

2. 检查 `server.py` 文件是否已适配 Vercel 环境
3. 确保 `requirements.txt` 文件包含所有必要的依赖项：

```
flask==2.0.1
```

## 部署步骤

### 方法一：通过 Vercel 网站部署

1. 登录 [Vercel 控制面板](https://vercel.com/dashboard)
2. 点击 "New Project"
3. 选择导入您的 GitHub 仓库
4. 设置部署配置：
   - 构建命令和输出目录将自动设置
   - 环境变量可以在此处添加，也可以在部署后在项目设置中添加
5. 点击 "Deploy" 开始部署

### 方法二：通过 Vercel CLI 部署

1. 安装 Vercel CLI
   ```bash
   npm install -g vercel
   ```

2. 登录 Vercel 账户
   ```bash
   vercel login
   ```

3. 在项目根目录运行部署命令
   ```bash
   vercel
   ```

4. 按照提示配置部署选项

## 部署后配置

1. 访问项目设置页面，选择 "Environment Variables"，确认所有必要的环境变量已设置：
   - `USE_REAL_SCRAPER`: 必须设置为 `true` 以启用实时爬虫功能 (这是最重要的设置)
   - 其他项目特定变量

2. 如需自定义域名，请在 "Domains" 设置中添加并验证您的域名

3. 确认 "Functions" 设置中，函数超时时间已设置为最大值 (60秒)

## 实时爬虫与预设数据

- **实时爬虫模式**: 当 `USE_REAL_SCRAPER` 设置为 `true` 时，系统将尝试从 itch.io 实时爬取游戏 iframe 源
  - 优点：总是获取最新的游戏数据
  - 缺点：可能受到 Vercel 执行时间限制，导致仅能爬取少量游戏
  
- **预设数据模式**: 当 `USE_REAL_SCRAPER` 设置为 `false` 时，系统将使用预设数据
  - 优点：稳定可靠，不受执行时间限制
  - 缺点：数据可能过时

- **自动回退**: 如果实时爬虫失败或无法获取数据，系统会自动回退到使用预设数据

**您的部署设置为: 实时爬虫模式**

## 使用限制

Vercel 免费计划有以下重要限制，需要考虑：

1. **无服务器函数执行时间限制**：
   - 最长执行时间为 10 秒（免费计划）
   - 我们已配置为最大值 60 秒（Hobby 计划），但实际执行仍受限

2. **内存限制**：
   - 函数可用内存为 1024 MB（1 GB）

3. **部署规模限制**：
   - 免费计划下每个函数部署包大小限制为 50 MB

4. **带宽和请求限制**：
   - 每月 100 GB 带宽
   - 每月 100万请求（免费计划）

因此，此部署方式适合：
- 快速爬虫任务，每次爬取少量游戏（5-8个）
- 轻到中度使用场景
- 不需要长时间运行的任务

## 故障排除

1. **部署失败**
   - 检查 `vercel.json` 配置
   - 确认所有依赖项都已在 `requirements.txt` 中列出
   - 查看部署日志获取详细错误信息

2. **函数执行超时**
   - 减少单次爬取的游戏数量 (在UI界面上设置小于10的值)
   - 验证 `maxDuration` 是否已设置为 60 (需要 Hobby 计划)
   - 检查 `USE_REAL_SCRAPER` 环境变量是否正确设置为 `true`

3. **爬取返回空结果**
   - 检查服务器日志，查看爬虫执行情况
   - 可能是由于网络问题导致无法访问itch.io网站
   - 请稍后再试，或尝试使用不同的偏移量

4. **内存不足错误**
   - 优化代码减少内存使用
   - 确认 `memory` 设置为 1024 MB

5. **API 响应慢**
   - 考虑实施缓存策略
   - 优化爬虫代码，减少请求数量

## 监控与日志

1. 可在 Vercel 控制面板的 "Analytics" 和 "Logs" 部分查看详细使用情况和日志
2. 设置 Monitoring 以获取性能和错误警报

## 升级注意事项

如需升级到 Vercel Pro 计划，主要获得以下好处：
- 更长的函数执行时间（最多 60 秒）
- 更多的并发执行
- 更高的带宽和请求限制

## 相关资源

- [Vercel 文档](https://vercel.com/docs)
- [Vercel Python 运行时](https://vercel.com/docs/runtimes#official-runtimes/python)
- [Vercel CLI 文档](https://vercel.com/docs/cli) 