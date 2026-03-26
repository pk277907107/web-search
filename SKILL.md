---
name: web-search
version: 2.0.0
author: xiaolongxia
updated: 2026-03-26
description: Web Search - 多源聚合搜索引擎，无需API，7个搜索引擎并发，支持中英文深度搜索。当用户需要联网搜索、查资料、确认最新信息、搜索新闻、查价格、查天气、查实时数据时使用。
homepage: https://github.com/openclaw/openclaw
---

# Web Search v2 - 多源聚合搜索引擎

多源聚合搜索引擎，无需API密钥，7个搜索引擎并发，支持中英文深度搜索。

## 何时使用

当用户有以下需求时，使用本技能：

- 需要联网搜索获取最新信息
- 需要确认"今天/最近/最新/当前"发生的事情
- 需要搜索新闻、公告、政策、价格、天气、股票、汇率等
- 需要查找特定主题的资料
- 用户说"搜一下"、"查一下"、"帮我看看"、"有没有最新消息"

## 搜索源（7个引擎）

| 引擎 | 特点 | 适用场景 |
|------|------|----------|
| `baidu` | 百度 - 国内中文最全 | 中文搜索首选 |
| `sogou` | 搜狗 - 中文权威源 | 中文新闻、百科 |
| `bing` | Bing - 微软搜索 | 中英文通用 |
| `ddg-html` | DuckDuckGo HTML - 丰富结果 | 英文搜索首选 |
| `ddg-lite` | DuckDuckGo Lite - 轻量快速 | 备用/补充 |
| `brave` | Brave - 隐私友好 | 独立视角 |
| `wikipedia` | Wikipedia - 百科知识 | 知识类查询 |

**自动策略**: 检测查询语言，中文搜索优先 baidu/sogou/bing，英文搜索优先 ddg-html/brave/bing。

## 使用方法

### 基本搜索

```bash
python scripts/xiaoi_search.py "搜索关键词"
```

### 快速获取答案

```bash
python scripts/xiaoi_search.py "搜索关键词" --quick
```

### 深度搜索（提取正文）

```bash
python scripts/xiaoi_search.py "某个复杂话题" --deep
```

### 指定搜索引擎

```bash
python scripts/xiaoi_search.py "关键词" --engines baidu,bing,sogou
```

### 其他参数

```bash
# 指定结果数量
python scripts/xiaoi_search.py "关键词" --count 10

# JSON格式输出
python scripts/xiaoi_search.py "关键词" --format json

# Markdown格式
python scripts/xiaoi_search.py "关键词" --format markdown

# 紧凑格式
python scripts/xiaoi_search.py "关键词" --format compact
```

## 输出格式说明

- **text** (默认): 完整文本格式，包含标题、URL、来源、摘要、引擎来源
- **json**: JSON格式，便于程序处理
- **markdown**: Markdown格式，适合文档展示
- **compact**: 紧凑格式，适合快速浏览
- **quick**: 快速答案模式，直接返回摘要

## 搜索策略建议

### 普通查询
```bash
python scripts/xiaoi_search.py "关键词" --count 5
```

### 中文事实核查 / 新闻
```bash
python scripts/xiaoi_search.py "最新政策" --engines baidu,sogou,bing --count 8
```

### 深度研究 / 需要详细内容
```bash
python scripts/xiaoi_search.py "某技术方案" --deep --count 5
```

### 英文搜索
```bash
python scripts/xiaoi_search.py "latest AI news" --engines ddg-html,brave,bing --count 8
```

## 回答规则

1. **多源交叉验证**：关键事实至少有2个独立来源确认
2. 基于搜索结果作答，不编造信息
3. 保留来源链接，便于用户查证
4. 涉及时效性问题时，说明搜索时间
5. 如果搜索结果不足，直接说明证据不足
6. 对于争议性话题，提供多方观点

## 技术说明

- 7个搜索引擎并发搜索（ThreadPoolExecutor）
- 自动去重和相关性排序
- 智能语言检测（中/英文自动选源）
- 深度搜索支持正文提取
- 无需任何API密钥

## 文件结构

```
xiaoi-search/
├── SKILL.md              # 本说明文件
├── scripts/
│   └── xiaoi_search.py   # 搜索脚本 (v2)
└── references/           # 参考资料目录
```
