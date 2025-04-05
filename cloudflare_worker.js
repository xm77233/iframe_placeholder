/**
 * Cloudflare Worker用于爬取itch.io游戏iframe源地址
 * 与Vercel部署互为补充，提供另一种部署选择
 */

// 配置常量
const MAX_GAMES = 8;  // 每次最多爬取游戏数量
const BASE_URL = "https://itch.io/games/free/platform-web";
const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/96.0.1054.62",
  "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
];

// CORS头部，允许跨域请求
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};

// 随机获取一个用户代理
function getRandomUserAgent() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// 处理OPTIONS请求 (预检请求)
function handleOptions(request) {
  return new Response(null, {
    status: 204,
    headers: CORS_HEADERS
  });
}

// 构建完整URL，包括偏移量
function buildUrl(offset = 0) {
  return `${BASE_URL}?offset=${offset}`;
}

// 从游戏页面中提取iframe源地址
async function getIframeSrc(gameUrl) {
  try {
    const response = await fetch(gameUrl, {
      headers: { "User-Agent": getRandomUserAgent() }
    });
    
    if (!response.ok) {
      return null;
    }
    
    const html = await response.text();
    
    // 尝试从html_embed div中提取iframe标签
    let iframeMatch = html.match(/<div[^>]*id=["']html_embed["'][^>]*>.*?<iframe[^>]*src=["']([^"']+)["']/s);
    if (iframeMatch && iframeMatch[1]) {
      return decodeHTML(iframeMatch[1]);
    }
    
    // 尝试从data-iframe属性中提取
    let dataIframeMatch = html.match(/<div[^>]*id=["']html_embed["'][^>]*data-iframe=["']([^"']+)["']/);
    if (dataIframeMatch && dataIframeMatch[1]) {
      return decodeHTML(dataIframeMatch[1]);
    }
    
    // 尝试从iframe_placeholder中提取
    let placeholderMatch = html.match(/<div[^>]*class=["']iframe_placeholder["'][^>]*data-iframe=["']([^"']+)["']/);
    if (placeholderMatch && placeholderMatch[1]) {
      return decodeHTML(placeholderMatch[1]);
    }
    
    return null;
  } catch (error) {
    console.error("Error fetching game page:", error);
    return null;
  }
}

// 从itch.io游戏列表页面中提取游戏URL和标题
async function getGameUrls(offset = 0) {
  try {
    const url = buildUrl(offset);
    const response = await fetch(url, {
      headers: { "User-Agent": getRandomUserAgent() }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch games list: ${response.status}`);
    }
    
    const html = await response.text();
    const games = [];
    
    // 使用正则表达式提取游戏URL和标题
    const gamePattern = /<a\s+class="game_link"\s+href="([^"]+)"[\s\S]*?<div\s+class="game_title">([\s\S]*?)<\/div>/g;
    let match;
    
    while ((match = gamePattern.exec(html)) !== null && games.length < MAX_GAMES) {
      const gameUrl = match[1];
      let gameTitle = match[2].trim();
      
      // 清理标题中的HTML标签
      gameTitle = gameTitle.replace(/<[^>]*>/g, '');
      
      games.push({ url: gameUrl, title: gameTitle });
    }
    
    return games;
  } catch (error) {
    console.error("Error fetching games list:", error);
    return [];
  }
}

// 处理爬虫请求
async function handleScrape(request) {
  const url = new URL(request.url);
  const offset = parseInt(url.searchParams.get("offset") || "0", 10);
  const startTime = Date.now();
  
  try {
    // 获取游戏列表
    const games = await getGameUrls(offset);
    
    if (games.length === 0) {
      return new Response(
        JSON.stringify({ 
          error: "No games found or error fetching games list",
          success: false 
        }),
        {
          status: 404,
          headers: {
            "Content-Type": "application/json",
            ...CORS_HEADERS
          }
        }
      );
    }
    
    // 提取每个游戏的iframe源地址
    const results = [];
    for (const game of games) {
      const iframeSrc = await getIframeSrc(game.url);
      if (iframeSrc) {
        results.push({
          title: game.title,
          url: game.url,
          iframe_src: iframeSrc
        });
      }
    }
    
    const endTime = Date.now();
    const executionTime = (endTime - startTime) / 1000;
    
    return new Response(
      JSON.stringify({
        success: true,
        games_found: games.length,
        games_with_iframe: results.length,
        execution_time: executionTime,
        results: results
      }),
      {
        headers: {
          "Content-Type": "application/json",
          ...CORS_HEADERS
        }
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: error.message,
        success: false 
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          ...CORS_HEADERS
        }
      }
    );
  }
}

// 解码HTML实体
function decodeHTML(html) {
  return html
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

// 入口函数 - 处理所有请求
addEventListener("fetch", event => {
  const request = event.request;
  
  // 处理预检请求
  if (request.method === "OPTIONS") {
    event.respondWith(handleOptions(request));
    return;
  }
  
  // 处理爬虫API请求
  if (request.url.includes("/api/scrape")) {
    event.respondWith(handleScrape(request));
    return;
  }
  
  // 默认响应 - API信息
  event.respondWith(
    new Response(
      JSON.stringify({
        name: "itch.io游戏iframe源爬取API",
        version: "1.0.0",
        endpoints: {
          "/api/scrape": "爬取游戏iframe源地址 (可选参数: offset)"
        },
        github: "https://github.com/xm77233/iframe_placeholder"
      }),
      {
        headers: {
          "Content-Type": "application/json",
          ...CORS_HEADERS
        }
      }
    )
  );
}); 