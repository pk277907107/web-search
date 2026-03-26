#!/usr/bin/env python3
"""
Web Search v2 - OpenClaw多源聚合搜索引擎
多源聚合搜索，无需API密钥，支持中英文深度搜索
"""

import sys
import json
import re
import urllib.parse
import urllib.request
import gzip
import html as html_module
import time
import random
import concurrent.futures
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Callable
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str = ""
    timestamp: str = ""
    engine: str = ""  # 来自哪个搜索引擎
    content: str = ""  # 页面全文提取（可选）

    def to_dict(self):
        d = {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "timestamp": self.timestamp,
            "engine": self.engine,
        }
        if self.content:
            d["content"] = self.content[:2000]
        return d


class WebSearch:
    """Web Search - 多源聚合搜索引擎"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
        ]

    def _get_headers(self, extra: dict = None) -> dict:
        """获取随机请求头"""
        h = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        if extra:
            h.update(extra)
        return h

    def _fetch(self, url: str, timeout: int = 12, headers: dict = None) -> str:
        """获取网页内容"""
        if headers is None:
            headers = self._get_headers()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            encoding = "utf-8"
            ct = resp.headers.get("Content-Type", "")
            m = re.search(r'charset=([^\s;]+)', ct)
            if m:
                encoding = m.group(1)
            return data.decode(encoding, errors="ignore")

    def _clean(self, text: str) -> str:
        """清理HTML文本"""
        text = re.sub(r'<[^>]+>', '', text)
        text = html_module.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_url(self, ddg_link: str) -> str:
        """从DuckDuckGo链接提取真实URL"""
        match = re.search(r'uddg=([^&]+)', ddg_link)
        if match:
            return urllib.parse.unquote(match.group(1))
        return ddg_link

    def _extract_source(self, url: str) -> str:
        """从URL提取网站来源"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return ""

    def _is_chinese_query(self, query: str) -> bool:
        """判断是否为中文搜索"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', query))
        return chinese_chars > len(query) * 0.3

    # ═══════════════════════════════════════════════════
    # 搜索引擎 1: DuckDuckGo Lite (原有)
    # ═══════════════════════════════════════════════════
    def search_ddg_lite(self, query: str, count: int = 10) -> List[SearchResult]:
        """DuckDuckGo Lite搜索"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://lite.duckduckgo.com/lite/?q={q}&kl=cn-zh"
            html_content = self._fetch(url)

            link_pattern = r'<a[^>]*href="([^"]*)"[^>]*class=[\'"]result-link[\'"][^>]*>(.*?)</a>'
            links = re.findall(link_pattern, html_content, re.DOTALL)

            snippet_pattern = r'<td[^>]*class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>'
            snippets = re.findall(snippet_pattern, html_content, re.DOTALL)

            timestamp_pattern = r'<span class=[\'"]timestamp[\'"]>(.*?)</span>'
            timestamps = re.findall(timestamp_pattern, html_content, re.DOTALL)

            for i, (ddg_url, title) in enumerate(links[:count]):
                title = self._clean(title)
                real_url = self._extract_url(ddg_url)
                snippet = self._clean(snippets[i]) if i < len(snippets) else ""
                timestamp = self._clean(timestamps[i]) if i < len(timestamps) else ""
                source = self._extract_source(real_url)
                if title and real_url.startswith("http"):
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, timestamp=timestamp, engine="ddg-lite"
                    ))
        except Exception as e:
            print(f"[ddg-lite] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 2: DuckDuckGo HTML (更丰富的结果)
    # ═══════════════════════════════════════════════════
    def search_ddg_html(self, query: str, count: int = 10) -> List[SearchResult]:
        """DuckDuckGo HTML版搜索 - 结果更丰富"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={q}&kl=cn-zh"
            html_content = self._fetch(url)

            # 结果块匹配
            blocks = re.findall(
                r'<div class="result[^"]*"[^>]*>.*?</div>\s*</div>',
                html_content, re.DOTALL
            )

            for block in blocks[:count]:
                # 标题和链接
                link_m = re.search(
                    r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    block, re.DOTALL
                )
                if not link_m:
                    continue
                url_raw = self._clean(link_m.group(1))
                real_url = self._extract_url(url_raw)
                title = self._clean(link_m.group(2))

                # 摘要
                snippet_m = re.search(
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    block, re.DOTALL
                )
                snippet = self._clean(snippet_m.group(1)) if snippet_m else ""

                # 来源显示
                source_m = re.search(r'<span class="result__url__domain">(.*?)</span>', block)
                source = self._clean(source_m.group(1)) if source_m else self._extract_source(real_url)

                if title and real_url.startswith("http"):
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, engine="ddg-html"
                    ))
        except Exception as e:
            print(f"[ddg-html] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 3: Bing 中文搜索
    # ═══════════════════════════════════════════════════
    def search_bing(self, query: str, count: int = 10) -> List[SearchResult]:
        """Bing搜索 - 中文结果优秀"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://cn.bing.com/search?q={q}&setlang=zh-CN&cc=CN"
            html_content = self._fetch(url, headers=self._get_headers({
                "Referer": "https://cn.bing.com/"
            }))

            # Bing 结果块
            blocks = re.findall(
                r'<li class="b_algo"[^>]*>(.*?)</li>',
                html_content, re.DOTALL
            )

            for block in blocks[:count]:
                link_m = re.search(r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
                if not link_m:
                    continue
                real_url = link_m.group(1)
                title = self._clean(link_m.group(2))

                # Bing摘要
                snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
                snippet = self._clean(snippet_m.group(1)) if snippet_m else ""

                source = self._extract_source(real_url)
                if title:
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, engine="bing"
                    ))
        except Exception as e:
            print(f"[bing] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 4: 搜狗搜索 (中文内容更丰富)
    # ═══════════════════════════════════════════════════
    def search_sogou(self, query: str, count: int = 10) -> List[SearchResult]:
        """搜狗搜索 - 中文内容权威源"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://www.sogou.com/web?query={q}"
            html_content = self._fetch(url, headers=self._get_headers({
                "Referer": "https://www.sogou.com/"
            }))

            # 搜狗结果块
            blocks = re.findall(
                r'<div class="vrwrap"[^>]*>(.*?)</div>\s*</div>',
                html_content, re.DOTALL
            )
            if not blocks:
                blocks = re.findall(
                    r'<div class="results"[^>]*>(.*?)</div>\s*</div>',
                    html_content, re.DOTALL
                )

            for block in blocks[:count]:
                link_m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
                if not link_m:
                    continue
                real_url = link_m.group(1)
                if real_url.startswith("/"):
                    real_url = "https://www.sogou.com" + real_url
                title = self._clean(link_m.group(2))

                snippet_m = re.search(r'<p[^>]*class="[^"]*space-txt[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
                if not snippet_m:
                    snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
                snippet = self._clean(snippet_m.group(1)) if snippet_m else ""

                source = self._extract_source(real_url)
                if title and real_url.startswith("http"):
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, engine="sogou"
                    ))
        except Exception as e:
            print(f"[sogou] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 5: Brave Search
    # ═══════════════════════════════════════════════════
    def search_brave(self, query: str, count: int = 10) -> List[SearchResult]:
        """Brave搜索 - 隐私友好，结果独立"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://search.brave.com/search?q={q}"
            html_content = self._fetch(url)

            # Brave 结果
            blocks = re.findall(
                r'<div[^>]*class="snippet[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
                html_content, re.DOTALL
            )

            for block in blocks[:count]:
                link_m = re.search(r'<a[^>]*href="(https?://[^"]*)"[^>]*>.*?<span[^>]*>(.*?)</span>', block, re.DOTALL)
                if not link_m:
                    link_m = re.search(r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
                if not link_m:
                    continue
                real_url = link_m.group(1)
                title = self._clean(link_m.group(2))

                snippet_m = re.search(r'<p[^>]*class="snippet-description[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
                if not snippet_m:
                    snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
                snippet = self._clean(snippet_m.group(1)) if snippet_m else ""

                source = self._extract_source(real_url)
                if title:
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, engine="brave"
                    ))
        except Exception as e:
            print(f"[brave] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 6: Wikipedia 中文
    # ═══════════════════════════════════════════════════
    def search_wikipedia(self, query: str, count: int = 3) -> List[SearchResult]:
        """Wikipedia搜索 - 知识类查询"""
        results = []
        try:
            q = urllib.parse.quote(query)
            lang = "zh" if self._is_chinese_query(query) else "en"
            # 搜索API
            url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&format=json&srlimit={count}"
            data = json.loads(self._fetch(url))
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = self._clean(item.get("snippet", ""))
                page_url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                results.append(SearchResult(
                    title=f"Wikipedia: {title}",
                    url=page_url,
                    snippet=snippet,
                    source=f"{lang}.wikipedia.org",
                    engine="wikipedia"
                ))
        except Exception as e:
            print(f"[wikipedia] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 搜索引擎 7: 百度 (通过移动端)
    # ═══════════════════════════════════════════════════
    def search_baidu(self, query: str, count: int = 10) -> List[SearchResult]:
        """百度搜索 - 国内最全的中文源"""
        results = []
        try:
            q = urllib.parse.quote(query)
            url = f"https://www.baidu.com/s?wd={q}&tn=json&ie=utf-8"
            headers = self._get_headers({
                "Referer": "https://www.baidu.com/",
                "Accept": "text/html",
            })
            html_content = self._fetch(url, headers=headers)

            # 百度结果块
            blocks = re.findall(
                r'<div[^>]*class="result[^"]*"[^>]*id="(\d+)"[^>]*>(.*?)</div>\s*</div>',
                html_content, re.DOTALL
            )

            for _, block in blocks[:count]:
                link_m = re.search(r'<a[^>]*href="([^"]*)"[^>]*target="_blank"[^>]*>(.*?)</a>', block, re.DOTALL)
                if not link_m:
                    link_m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
                if not link_m:
                    continue
                real_url = link_m.group(1)
                title = self._clean(link_m.group(2))

                snippet_m = re.search(r'<span[^>]*class="content-right_[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
                if not snippet_m:
                    snippet_m = re.search(r'<div[^>]*class="c-abstract"[^>]*>(.*?)</div>', block, re.DOTALL)
                if not snippet_m:
                    snippet_m = re.search(r'<span[^>]*>(.*?)</span>', block, re.DOTALL)
                snippet = self._clean(snippet_m.group(1)) if snippet_m else ""

                source = self._extract_source(real_url)
                if title:
                    results.append(SearchResult(
                        title=title, url=real_url, snippet=snippet,
                        source=source, engine="baidu"
                    ))
        except Exception as e:
            print(f"[baidu] 错误: {e}", file=sys.stderr)
        return results

    # ═══════════════════════════════════════════════════
    # 内容提取
    # ═══════════════════════════════════════════════════
    def extract_content(self, url: str, max_chars: int = 3000) -> str:
        """提取网页正文内容"""
        try:
            html_content = self._fetch(url, timeout=8)

            # 移除脚本和样式
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

            # 尝试找正文区域
            for pattern in [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class="[^"]*article[_-]?(?:body|content|main)[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                r'<main[^>]*>(.*?)</main>',
            ]:
                m = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if m:
                    content = self._clean(m.group(1))
                    if len(content) > 100:
                        return content[:max_chars]

            # 兜底：清理整个页面
            content = self._clean(html_content)
            return content[:max_chars] if len(content) > 50 else ""
        except Exception as e:
            print(f"[extract] 提取失败 {url}: {e}", file=sys.stderr)
            return ""

    # ═══════════════════════════════════════════════════
    # 核心搜索逻辑
    # ═══════════════════════════════════════════════════
    def _dedup(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重：同URL只保留一个，优先保留有摘要的"""
        seen = {}
        for r in results:
            key = r.url.rstrip('/')
            if key in seen:
                existing = seen[key]
                # 优先保留摘要更长的
                if len(r.snippet) > len(existing.snippet):
                    seen[key] = r
            else:
                seen[key] = r
        return list(seen.values())

    def search(self, query: str, count: int = 10, engines: List[str] = None) -> List[SearchResult]:
        """多源聚合搜索"""
        all_engines = {
            "ddg-lite": self.search_ddg_lite,
            "ddg-html": self.search_ddg_html,
            "bing": self.search_bing,
            "baidu": self.search_baidu,
            "sogou": self.search_sogou,
            "brave": self.search_brave,
            "wikipedia": self.search_wikipedia,
        }

        is_cn = self._is_chinese_query(query)

        # 根据语言选择引擎优先级
        if engines is None:
            if is_cn:
                # 中文搜索：优先中文源
                engines = ["baidu", "sogou", "bing", "ddg-html", "ddg-lite", "brave", "wikipedia"]
            else:
                # 英文搜索：优先英文源
                engines = ["ddg-html", "brave", "bing", "ddg-lite", "wikipedia"]

        # 并发搜索
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for eng_name in engines:
                if eng_name in all_engines:
                    req_count = max(count // 2, 5)
                    futures[executor.submit(all_engines[eng_name], query, req_count)] = eng_name

            for future in concurrent.futures.as_completed(futures, timeout=20):
                eng_name = futures[future]
                try:
                    eng_results = future.result()
                    results.extend(eng_results)
                except Exception as e:
                    print(f"[{eng_name}] 异常: {e}", file=sys.stderr)

        # 去重
        results = self._dedup(results)

        # 简单相关性排序（标题包含关键词优先）
        keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        def relevance(r: SearchResult) -> float:
            score = 0.0
            title_lower = r.title.lower()
            snippet_lower = r.snippet.lower()
            for kw in keywords:
                if kw in title_lower:
                    score += 3.0
                if kw in snippet_lower:
                    score += 1.0
            # 有摘要加分
            if r.snippet:
                score += 0.5
            return score

        results.sort(key=relevance, reverse=True)
        return results[:count]

    def search_deep(self, query: str, count: int = 5) -> List[SearchResult]:
        """深度搜索 - 搜索+提取正文"""
        results = self.search(query, count=count)
        # 并发提取前几个结果的正文
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.extract_content, r.url): i
                for i, r in enumerate(results[:min(3, len(results))])
            }
            for future in concurrent.futures.as_completed(futures, timeout=15):
                idx = futures[future]
                try:
                    content = future.result()
                    if content:
                        results[idx].content = content
                except:
                    pass
        return results

    def format_results(self, results: List[SearchResult], fmt: str = "text") -> str:
        """格式化结果"""
        if not results:
            return "未找到搜索结果"

        if fmt == "json":
            return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)

        lines = []
        for i, r in enumerate(results, 1):
            if fmt == "markdown":
                lines.append(f"**{i}. {r.title}**")
                lines.append(f"- 链接: {r.url}")
                lines.append(f"- 来源: {r.source} (via {r.engine})")
                if r.timestamp:
                    lines.append(f"- 时间: {r.timestamp}")
                lines.append(f"- 摘要: {r.snippet}")
                if r.content:
                    lines.append(f"- 正文摘要: {r.content[:300]}...")
            elif fmt == "compact":
                lines.append(f"{i}. {r.title} [{r.engine}]")
                lines.append(f"   {r.snippet[:100]}..." if len(r.snippet) > 100 else f"   {r.snippet}")
                lines.append(f"   {r.url}")
            else:  # text
                lines.append(f"{i}. {r.title}")
                lines.append(f"   URL: {r.url}")
                lines.append(f"   来源: {r.source} | 引擎: {r.engine}")
                if r.timestamp:
                    lines.append(f"   时间: {r.timestamp}")
                lines.append(f"   摘要: {r.snippet}")
                if r.content:
                    lines.append(f"   正文: {r.content[:200]}...")
            lines.append("")

        return "\n".join(lines)

    def quick_answer(self, query: str) -> str:
        """快速获取答案摘要"""
        results = self.search(query, count=5)
        if not results:
            return "未找到相关信息"

        answer_parts = []
        for r in results[:4]:
            if r.snippet:
                answer_parts.append(f"[{r.source}] {r.snippet}")

        if answer_parts:
            return "\n\n".join(answer_parts)
        return "搜索结果中没有找到明确的答案"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Web Search - OpenClaw多源聚合搜索引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "国际油价最新"
  %(prog)s "今日天气" --count 5
  %(prog)s "Python教程" --format json
  %(prog)s "油价" --format markdown
  %(prog)s "天气" --quick
  %(prog)s "某话题" --deep        # 深度搜索，提取正文
  %(prog)s "某话题" --engines baidu,bing  # 指定搜索引擎

可用引擎: ddg-lite, ddg-html, bing, baidu, sogou, brave, wikipedia

格式选项:
  text      - 默认文本格式
  json      - JSON格式
  markdown  - Markdown格式
  compact   - 紧凑格式
        """
    )

    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--count", "-n", type=int, default=10, help="结果数量 (默认: 10)")
    parser.add_argument("--format", "-f", choices=["text", "json", "markdown", "compact"],
                       default="text", help="输出格式")
    parser.add_argument("--quick", "-q", action="store_true", help="快速获取答案摘要")
    parser.add_argument("--deep", "-d", action="store_true", help="深度搜索，提取正文内容")
    parser.add_argument("--engines", "-e", type=str, default=None,
                       help="指定搜索引擎，逗号分隔 (如: baidu,bing,sogou)")

    args = parser.parse_args()

    engine = WebSearch()
    engines = args.engines.split(",") if args.engines else None

    if args.quick:
        print(engine.quick_answer(args.query))
    elif args.deep:
        print(f"正在深度搜索: {args.query}", file=sys.stderr)
        results = engine.search_deep(args.query, args.count)
        print(engine.format_results(results, args.format))
    else:
        print(f"正在搜索: {args.query}", file=sys.stderr)
        results = engine.search(args.query, args.count, engines=engines)
        print(engine.format_results(results, args.format))


if __name__ == "__main__":
    main()
