# itch.io游戏iframe提取器

这是一个简单的工具，用于从 [itch.io](https://itch.io) 网站上的网页游戏中提取iframe地址，使您可以直接访问游戏内容。

## 功能特点

- 从itch.io提取游戏iframe地址
- 支持分页获取大量游戏
- 使用多种方法尝试提取iframe地址，提高成功率
- 简洁的图形用户界面
- 支持测试提取的iframe
- 结果保存为JSON格式，方便后续使用

## 使用方法

### 运行程序

有两种方式运行程序：

1. **直接运行Python脚本**

   ```
   python iframe_scraper_gui.py
   ```

   需要先安装Python和必要的依赖。

2. **使用打包好的可执行文件**

   如果您有打包好的可执行文件，可以直接双击运行。

### 打包为可执行文件

如果您希望将程序打包为可执行文件，可以使用包含的构建脚本：

```
python build_exe.py
```

这将使用PyInstaller将程序打包为独立的可执行文件。

## 使用界面说明

1. **设置区域**
   - 最大游戏数量：限制要爬取的游戏数量
   - 起始偏移量：设置开始爬取的位置，可用于续传
   - 请求延迟：设置请求间隔时间（秒）

2. **操作按钮**
   - 开始爬取：开始爬取过程
   - 停止爬取：中断当前爬取过程
   - 查看结果文件：打开结果保存目录
   - 测试选中的iframe：在浏览器中测试选中的游戏iframe

3. **结果与日志**
   - 日志标签页：显示程序运行日志
   - 结果标签页：显示已爬取的游戏及其iframe地址

## 注意事项

- 请勿频繁爬取，以免IP被限制
- 建议将请求延迟设置在1秒以上
- 爬取大量游戏时，可能需要较长时间
- 有些游戏可能无法提取到iframe地址

## 文件说明

- `iframe_scraper.py` - 核心爬虫功能实现
- `iframe_scraper_gui.py` - 图形界面程序
- `build_exe.py` - 打包构建脚本

## 更新日志

### 版本 1.0.0
- 初始版本发布
- 支持基本的iframe提取功能
- 简洁的图形用户界面 