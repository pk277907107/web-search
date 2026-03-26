# Web Search 🔍

多源聚合搜索引擎 — 无需 API 密钥，7 个搜索引擎并发，支持中英文深度搜索。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)

## ✨ 特性

- **7 个搜索引擎并发搜索**：百度、搜狗、Bing、DuckDuckGo (HTML/Lite)、Brave、Wikipedia
- **智能语言检测**：中文查询自动优先中文引擎，英文查询自动切换
- **深度搜索**：可提取网页正文，获取更详细的信息
- **自动去重 + 相关性排序**：同 URL 去重，关键词匹配优先
- **多种输出格式**：text / json / markdown / compact
- **零依赖**：纯 Python 标准库，无需安装任何第三方包
- **无需 API 密钥**：完全免费使用

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/pk277907107/web-search.git
cd web-search

# 基本搜索
python scripts/xiaoi_search.py "你的搜索关键词"

# 快速获取答案
python scripts/xiaoi_search.py "比特币价格" --quick

# 深度搜索（提取正文）
python scripts/xiaoi_search.py "AI 最新进展" --deep

# 指定搜索引擎
python scripts/xiaoi_search.py "Python教程" --engines baidu,bing,sogou

# JSON 输出
python scripts/xiaoi_search.py "今日新闻" --format json --count 5
```

## 📦 搜索引擎

| 引擎 | 标识 | 特点 |
|------|------|------|
| 百度 | `baidu` | 国内中文最全 |
| 搜狗 | `sogou` | 中文新闻权威源 |
| Bing | `bing` | 中英文通用 |
| DuckDuckGo HTML | `ddg-html` | 英文搜索首选 |
| DuckDuckGo Lite | `ddg-lite` | 轻量快速 |
| Brave | `brave` | 隐私友好 |
| Wikipedia | `wikipedia` | 百科知识 |

## 🔧 命令行参数

```
positional:
  query                 搜索关键词

options:
  --count, -n N         结果数量 (默认: 10)
  --format, -f FMT      输出格式: text|json|markdown|compact
  --quick, -q           快速获取答案摘要
  --deep, -d            深度搜索，提取正文内容
  --engines, -e ENGINES 指定搜索引擎，逗号分隔
```

## 📋 使用示例

```bash
# 中文新闻搜索
python scripts/xiaoi_search.py "今日科技新闻" --engines baidu,sogou,bing --count 8

# 英文技术搜索
python scripts/xiaoi_search.py "latest AI research" --engines ddg-html,brave --count 5

# 价格查询
python scripts/xiaoi_search.py "国际金价" --quick

# 获取 JSON 数据供程序处理
python scripts/xiaoi_search.py "机器学习入门" --format json --count 10
```

## 📁 项目结构

```
web-search/
├── README.md              # 项目说明
├── LICENSE                # MIT 开源协议
├── scripts/
│   └── xiaoi_search.py    # 搜索引擎核心脚本
├── references/            # 参考资料
└── docs/                  # 文档
```

## 🛠 技术实现

- 纯 Python 标准库（urllib, json, re, concurrent.futures）
- ThreadPoolExecutor 并发搜索
- 正则表达式解析 HTML（无第三方依赖）
- 智能语言检测（Unicode 范围判断）
- 基于关键词的相关性排序算法

## 📄 License

MIT License - 自由使用、修改和分发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本工具仅用于学习和研究目的。请遵守各搜索引擎的使用条款，合理使用搜索功能。
