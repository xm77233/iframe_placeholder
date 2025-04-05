# Cloudflare Worker 部署指南

本文档提供了将 iframe_placeholder 项目部署到 Cloudflare Worker 的详细步骤。Cloudflare Worker 提供轻量级的无服务器计算环境，适合运行此类爬虫API。

## 部署前准备

1. 注册 [Cloudflare 账户](https://dash.cloudflare.com/sign-up)
2. 确保已安装 [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)，这是 Cloudflare Worker 的命令行工具
   ```bash
   npm install -g wrangler
   ```
3. 登录 Wrangler
   ```bash
   wrangler login
   ```

## 配置部署文件

1. 在项目根目录创建 `wrangler.toml` 配置文件：

```toml
name = "iframe-scraper"
main = "cloudflare_worker.js"
compatibility_date = "2023-11-09"

[triggers]
crons = []

[vars]
MAX_GAMES = "8"
```

2. 确保项目中包含 `cloudflare_worker.js` 文件（已在项目中提供）

## 部署步骤

1. 检查配置并验证
   ```bash
   wrangler config
   ```

2. 发布 Worker
   ```bash
   wrangler publish
   ```

3. 部署成功后，Wrangler 会提供一个类似 `https://iframe-scraper.你的用户名.workers.dev` 的URL

## 使用方法

部署完成后，您可以通过以下API端点使用爬虫服务：

- 根端点: `https://iframe-scraper.你的用户名.workers.dev/`
  - 返回API信息和可用端点

- 爬虫端点: `https://iframe-scraper.你的用户名.workers.dev/api/scrape`
  - 爬取默认数量的游戏iframe源

- 爬虫端点（带偏移）: `https://iframe-scraper.你的用户名.workers.dev/api/scrape?offset=100`
  - 从第100个游戏开始爬取

## Worker限制与注意事项

Cloudflare Worker 免费计划有以下限制：

- 每天10万次请求
- 每个请求最多执行时间为10ms CPU时间（实际可执行约50ms的代码）
- 每天总计最多100,000ms CPU时间

因此，此部署方式适合：

- 偶尔使用的小型爬虫任务
- 每次爬取少量游戏（建议不超过10个）
- 不需要长时间运行的任务

如果需要更高的限制，可以升级到 Cloudflare Workers Paid 计划。

## 前端集成

要将前端页面与Cloudflare Worker集成，需要在前端代码中更新API端点URL：

1. 修改前端JavaScript中的API调用URL为您的Worker URL
2. 确保前端处理CORS和响应格式

示例：
```javascript
const API_URL = "https://iframe-scraper.你的用户名.workers.dev/api/scrape";

async function fetchGames() {
  const response = await fetch(API_URL);
  const data = await response.json();
  // 处理响应数据
}
```

## 故障排除

1. **部署失败**
   - 检查 `wrangler.toml` 配置是否正确
   - 确保已登录 Wrangler CLI

2. **Worker执行超时**
   - 减少每次爬取的游戏数量
   - 优化Worker代码，减少CPU使用

3. **请求超出限额**
   - 考虑升级到付费计划
   - 实施请求限流策略

4. **跨域资源共享(CORS)问题**
   - 确认Worker正确设置了CORS头部
   - 检查前端请求格式

## 相关资源

- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
- [Wrangler CLI 文档](https://developers.cloudflare.com/workers/wrangler/commands/)
- [Cloudflare Workers 限制](https://developers.cloudflare.com/workers/platform/limits/) 