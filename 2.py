import requests
from bs4 import BeautifulSoup
from lxml import etree
import os
from datetime import datetime
import json
import time
import urllib.parse
import sys
from pypinyin import lazy_pinyin
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
from tqdm import tqdm
import logging
import psutil
import pickle
from pathlib import Path
import re
import yaml
from nav_generator import generate_nav_page

# 添加日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_css_content():
    return '''
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}
.container {
    max-width: 800px;
    margin: 0 auto;
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.search-info {
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}
.search-keyword {
    color: #1a0dab;
    font-size: 20px;
    font-weight: bold;
}
.search-time {
    color: #70757a;
    font-size: 14px;
}
.results {
    list-style: none;
    padding: 0;
}
.result-item {
    margin-bottom: 20px;
    padding: 10px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.result-item:hover {
    background-color: #f8f9fa;
}
.result-link {
    color: #1a0dab;
    text-decoration: none;
    font-size: 16px;
    display: block;
    margin-bottom: 4px;
}
.result-snippet {
    color: #4d5156;
    font-size: 14px;
}
.footer {
    margin-top: 20px;
    text-align: center;
    color: #70757a;
    font-size: 12px;
}
.result-content {
    margin: 10px 0;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 4px;
}
.sub-title {
    font-size: 16px;
    color: #1a0dab;
    margin: 0 0 10px 0;
}
.source {
    color: #006621;
    margin-right: 10px;
}
.more-link {
    margin-top: 8px;
    font-size: 13px;
    color: #666;
}
.more-link a {
    color: #1a0dab;
    text-decoration: none;
}
.more-link a:hover {
    text-decoration: underline;
}
.result-meta {
    font-size: 12px;
    color: #70757a;
    margin-top: 5px;
}
'''

def get_meta_tags(keyword, related_searches):
    """生成增强的SEO相关meta标签"""
    # 生成更丰富的关键词组合
    primary_keywords = [keyword] + related_searches[:5]
    secondary_keywords = [f"{keyword}相关", f"{keyword}推荐", f"最新{keyword}", f"{keyword}排行"]
    long_tail_keywords = [f"{keyword}有哪些", f"怎么选择{keyword}", f"{keyword}哪个好", f"{keyword}排名"]
    
    all_keywords = list(set(primary_keywords + secondary_keywords + long_tail_keywords))
    keyword_str = ', '.join(all_keywords)
    
    # 生成更自然的描述
    description = (
        f"为您提供{keyword}的最新整理与分析。包含{len(related_searches)}个相关主题：" +
        f"{', '.join(related_searches[:3])}等。" +
        f"全方位解析{keyword}相关内容，助您快速了解{keyword}的核心信息。" +
        f"定期更新，确保信息时效性。"
    )
    
    # 添加更丰富的结构化数据
    structured_data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{keyword} - 最新整理与分析",
        "description": description,
        "datePublished": datetime.now().isoformat(),
        "dateModified": datetime.now().isoformat(),
        "about": {"@type": "Thing", "name": keyword},
        "keywords": keyword_str,
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "首页",
                    "item": "/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": keyword,
                    "item": f"/{keyword}.html"
                }
            ]
        },
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": term
                } for i, term in enumerate(related_searches[:10])
            ]
        },
        "publisher": {
            "@type": "Organization",
            "name": "Search Results Generator",
            "url": "/"
        }
    }

    return f'''
    <!-- 核心 SEO Meta 标签 -->
    <meta name="keywords" content="{keyword_str}">
    <meta name="description" content="{description}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    
    <!-- 增强的搜索引擎优化标签 -->
    <meta name="baidu-site-verification" content="">
    <meta name="google-site-verification" content="">
    <meta name="360-site-verification" content="">
    <meta name="sogou_site_verification" content="">
    <meta name="msvalidate.01" content="">
    
    <!-- 社交媒体优化标签 -->
    <meta property="og:title" content="{keyword} - 最新整理与分析">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:updated_time" content="{datetime.now().isoformat()}">
    <meta property="article:published_time" content="{datetime.now().isoformat()}">
    <meta property="article:modified_time" content="{datetime.now().isoformat()}">
    <meta property="article:section" content="搜索聚合">
    <meta property="article:tag" content="{keyword_str}">
    
    <!-- 移动设备优化 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="{keyword}">
    <meta name="format-detection" content="telephone=no,email=no,address=no">
    
    <!-- 内容属性标签 -->
    <meta name="author" content="Search Results Generator">
    <meta name="copyright" content="Search Results Generator">
    <meta name="generator" content="Search Results Generator 1.0">
    <meta name="revisit-after" content="1 days">
    <meta name="rating" content="general">
    
    <!-- 浏览器兼容性标签 -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta http-equiv="Cache-Control" content="no-transform">
    <meta http-equiv="Cache-Control" content="no-siteapp">
    
    <!-- 链接规范化标签 -->
    <link rel="canonical" href="{keyword}.html">
    <link rel="alternate" media="only screen and (max-width: 640px)" href="{keyword}.html">
    
    <!-- DNS预解析 -->
    <link rel="dns-prefetch" href="//www.baidu.com">
    <link rel="dns-prefetch" href="//www.google.com">
    
    <!-- 页面主题色 -->
    <meta name="theme-color" content="#ffffff">
    <meta name="msapplication-navbutton-color" content="#ffffff">
    <meta name="apple-mobile-web-app-status-bar-style" content="white">
    
    <!-- 增强的结构化数据 -->
    <script type="application/ld+json">
    {json.dumps(structured_data, ensure_ascii=False)}
    </script>
    
    <!-- 添加FAQ结构化数据 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {{
                "@type": "Question",
                "name": "什么是{keyword}？",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "{description}"
                }}
            }},
            {{
                "@type": "Question",
                "name": "{keyword}有哪些相关内容？",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "相关内容包括：{', '.join(related_searches[:5])}等。"
                }}
            }}
        ]
    }}
    </script>
    
    <!-- 性能优化标签 -->
    <link rel="preconnect" href="//www.baidu.com">
    <link rel="dns-prefetch" href="//www.baidu.com">
    <link rel="preload" href="css/style.css" as="style">
    <meta http-equiv="x-dns-prefetch-control" content="on">
    
    <!-- 安全相关标签 -->
    <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="SAMEORIGIN">
    <meta name="referrer" content="no-referrer-when-downgrade">
    '''

def get_html_template():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{keyword} - 搜索结果聚合 | 最新整理 {timestamp}</title>
    
    <!-- 增强的SEO Meta标签 -->
    <meta name="keywords" content="{keywords}, 搜索结果, 相关内容, 最新资讯">
    <meta name="description" content="{description} 更新时间: {timestamp}. 提供最新、最全面的相关内容整理与分析。">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    <meta name="author" content="Search Results Generator">
    <meta name="revisit-after" content="1 days">
    <meta name="generator" content="Search Results Generator 1.0">
    <meta name="copyright" content="Search Results Generator">
    <meta name="rating" content="general">
    <meta name="distribution" content="global">
    
    <!-- 新增百度特定Meta标签 -->
    <meta name="bytedance-verification-code" content="验证码">
    <meta name="baidu-site-verification" content="验证码">
    <meta name="360-site-verification" content="验证码">
    <meta name="sogou_site_verification" content="验证码">
    
    <!-- 强的Open Graph Meta标签 -->
    <meta property="og:title" content="{keyword} - 最新搜索结果聚合 | {timestamp}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="index.html">
    <meta property="og:site_name" content="搜索结果聚合">
    <meta property="og:locale" content="zh_CN">
    <meta property="og:updated_time" content="{timestamp}">
    <meta property="og:image" content="logo.png">
    <meta property="og:image:type" content="image/png">
    
    <!-- 增强的结构化数据 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "搜索结果聚合",
        "alternateName": ["搜索聚合", "内容聚合"],
        "url": "./",
        "potentialAction": {{
            "@type": "SearchAction",
            "target": {{
                "@type": "EntryPoint",
                "urlTemplate": "?keyword={{search_term_string}}"
            }},
            "query-input": "required name=search_term_string"
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "Search Results Generator",
            "logo": {{
                "@type": "ImageObject",
                "url": "logo.png"
            }}
        }},
        "mainEntity": {{
            "@type": "ItemList",
            "itemListElement": {json_results},
            "numberOfItems": {result_count}
        }},
        "datePublished": "{timestamp}",
        "dateModified": "{timestamp}",
        "inLanguage": "zh-CN"
    }}
    </script>

    <!-- 添加Breadcrumb结构化数 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{
                "@type": "ListItem",
                "position": 1,
                "name": "首页",
                "item": "./"
            }},
            {{
                "@type": "ListItem",
                "position": 2,
                "name": "{keyword}",
                "item": "?keyword={keyword}"
            }}
        ]
    }}
    </script>

    <!-- 添加FAQ结构化数据 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {{
                "@type": "Question",
                "name": "如何使用搜索功能",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "在搜索框中输入关键词，点击搜索按钮或按回车键即可开始搜索。"
                }}
            }},
            {{
                "@type": "Question",
                "name": "搜索结果如何排序？",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "搜索结果按照相关度排序，最相关的内容会显示在最前面。"
                }}
            }}
        ]
    }}
    </script>
    
    <link rel="stylesheet" href="css/style.css">
    <link rel="canonical" href="index.html">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
    
    <style>
        /* 全局样式优化 */
        body {{
            font-family: 'Noto Sans SC', sans-serif;
            background: #f8f9fa;
            color: #202124;
        }}
        
        /* 搜索框样式优化 */
        .search-box {{
            margin: 30px auto;
            max-width: 650px;
            padding: 25px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: box-shadow 0.3s;
        }}
        .search-box:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        .search-form {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .search-input {{
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e8eaed;
            border-radius: 30px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }}
        .search-input:focus {{
            border-color: #1a73e8;
            box-shadow: 0 0 0 4px rgba(26,115,232,0.1);
        }}
        .search-button {{
            padding: 12px 24px;
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .search-button:hover {{
            background: #1557b0;
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(26,115,232,0.3);
        }}
        
        /* ���果列表样式优化 */
        .result-item {{
            background: white;
            padding: 20px 25px;
            margin-bottom: 15px;
            border-radius: 12px;
            border: 1px solid #e8eaed;
        }}
        .result-link {{
            font-size: 18px;
            color: #1a73e8;
            text-decoration: none;
            display: block;
            margin-bottom: 10px;
            font-weight: 500;
            border-bottom: 2px solid transparent;
        }}
        .result-link:hover {{
            border-bottom-color: #1a73e8;
        }}
        .result-snippet {{
            color: #5f6368;
            line-height: 1.6;
            font-size: 15px;
        }}
        
        /* 页面布局优化 */
        .container {{
            max-width: 850px;
            margin: 0 auto;
            padding: 20px;
        }}
        .search-info {{
            text-align: center;
            margin: 30px 0;
            padding: 25px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .search-keyword {{
            color: #1a73e8;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .search-time {{
            color: #5f6368;
            font-size: 15px;
        }}
        .footer {{
            text-align: center;
            padding: 25px;
            color: #5f6368;
            background: white;
            border-radius: 12px;
            margin-top: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        
        /* 加载状态样式 */
        .search-status {{
            margin-top: 15px;
            text-align: center;
            color: #5f6368;
            font-size: 14px;
        }}
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #1a73e8;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    
    <script>
    async function performSearch() {{
        const keyword = document.getElementById('search-input').value.trim();
        const statusDiv = document.getElementById('search-status');
        
        if (keyword) {{
            try {{
                // 显示加载状态
                statusDiv.innerHTML = '<span class="loading"></span>搜索中...';
                
                // 构建新的URL
                const currentUrl = new URL(window.location.href);
                const baseUrl = currentUrl.origin + currentUrl.pathname;
                const newUrl = baseUrl + '?keyword=' + encodeURIComponent(keyword);
                
                // 发起搜索请求
                const response = await fetch(newUrl);
                
                if (response.ok) {{
                    // 更新URL刷新页面
                    window.location.href = newUrl;
                }} else {{
                    throw new Error('搜索请求失败');
                }}
            }} catch (error) {{
                console.error('搜索错误:', error);
                statusDiv.textContent = '搜索失败，请稍后重试';
                
                // 3秒后清除错误消息
                setTimeout(() => {{
                    statusDiv.textContent = '';
                }}, 3000);
            }}
        }}
        return false;
    }}
    
    // 添加键盘事件监听
    document.addEventListener('DOMContentLoaded', function() {{
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                performSearch();
            }}
        }});
    }});
    </script>
</head>
<body>
    <div class="container">
        <!-- 搜索框 -->
        <div class="search-box">
            <form onsubmit="return performSearch()" class="search-form">
                <input type="text" id="search-input" class="search-input" 
                       placeholder="输入关键词搜索..." value="{keyword}"
                       autocomplete="off" spellcheck="false">
                <button type="submit" class="search-button">搜索</button>
            </form>
            <div id="search-status" class="search-status"></div>
        </div>
        
        <!-- 搜索信息 -->
        <header class="search-info">
            <h1 class="search-keyword">{keyword}</h1>
            <div class="search-time">搜索时间: {timestamp}</div>
        </header>
        
        <!-- 搜索结果 -->
        <main class="results">
            {search_results}
        </main>
        
        <!-- 页脚 -->
        <footer class="footer">
            <p>共找到 {result_count} 个相关结果</p>
            <p>© 2024 搜索结果聚合. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
'''

def create_json_results(related_searches):
    """创建结构化数据的搜索结果列表"""
    json_items = []
    for i, term in enumerate(related_searches, 1):
        item = {
            "@type": "ListItem",
            "position": i,
            "name": term,
            "url": f"https://www.baidu.com/s?wd={term}"
        }
        json_items.append(json.dumps(item))
    return "[" + ",".join(json_items) + "]"

def is_chinese_text(text):
    """判断文本是否包含中文"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def get_article_content(term):
    """获取每个搜索词的详细内容"""
    url = f'http://www.baidu.com/s?wd={urllib.parse.quote(term)}'
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            html = etree.HTML(response.text)
            contents = []
            
            # 遍历前10个搜索结果
            for result_id in range(1, 12):
                try:
                    # 为每个结果ID构建特定的XPath
                    result_paths = {
                        'title': f'//*[@id="{result_id}"]/div/div[1]/h3/a//text()',
                        'abstract': f'//*[@id="{result_id}"]/div/div[1]/div[2]/div[1]/div[2]//text()',
                        'source': f'//*[@id="{result_id}"]/div/div[1]/div[2]/div[1]/div[2]/div/a/span/text()',
                        'url': f'//*[@id="{result_id}"]/@mu'
                    }
                    
                    # 获取当前结果的所有容
                    result_content = {}
                    
                    # 获取标题
                    title = html.xpath(result_paths['title'])
                    if title:
                        temp_title = ''.join(title).strip()
                        if is_chinese_text(temp_title):
                            result_content['title'] = temp_title
                        else:
                            continue
                    else:
                        continue
                    
                    # 获取摘要
                    abstract = html.xpath(result_paths['abstract'])
                    if abstract:
                        abstract_text = ''.join(abstract).strip()
                        if abstract_text:
                            result_content['abstract'] = abstract_text
                        else:
                            continue
                    else:
                        continue
                    
                    # 获取来源
                    source = html.xpath(result_paths['source'])
                    result_content['source'] = source[0].strip() if source else ""
                    
                    # 获取URL
                    url_element = html.xpath(result_paths['url'])
                    result_content['url'] = url_element[0] if url_element else ""
                    
                    # 只有当必要内容都获取到时才添加到结果中
                    if result_content.get('title') and result_content.get('abstract'):
                        contents.append(result_content)
                    
                except Exception as e:
                    print(f"处理第 {result_id} 条搜索结果时出错: {str(e)}")
                    continue
            
            return contents
            
    except Exception as e:
        print(f"获取 {term} 的详细内容时出错: {str(e)}")
        return None

def generate_seo_filename(text):
    """生成SEO友好的文件名，并保存到文件中"""
    try:
        # 读取1.txt中的原始关键词
        original_keywords = set()
        try:
            with open('1.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    keyword = line.strip()
                    if keyword:
                        original_keywords.add(keyword)
        except Exception as e:
            print(f"读取1.txt时出错: {str(e)}")
        
        # 中文转拼音
        pinyin_list = lazy_pinyin(text)
        pinyin_text = ''.join(pinyin_list)
        
        # 只保留字母和数字
        safe_text = ''.join(c.lower() for c in pinyin_text if c.isalnum())
        
        # 限制长度为15个字符
        safe_text = safe_text[:15]
        
        # 如果转换后为空，返回默认值
        if not safe_text:
            safe_text = 'page'
            
        # 生成目录名（添加s_前缀）
        dir_name = f's_{safe_text}'
        
        # 只有当text是1.txt中的关键词时才保存
        if text in original_keywords:
            with open('folder_keywords.txt', 'a', encoding='utf-8') as f:
                f.write(f'{text}\t{dir_name}\n')
            
        return safe_text
        
    except Exception as e:
        print(f"生成文件名出错: {str(e)}")
        return 'page'

def get_related_terms_html(term):
    """获取相关搜索词并生成HTML"""
    try:
        url = f'http://www.baidu.com/s?wd={urllib.parse.quote(term)}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            # 获取相关搜索词
            related_terms = html.xpath('//*[@id="rs_new"]/div/table//td/a/span/text()')
            
            # 生成HTML
            terms_html = ''
            for term in related_terms:
                if term.strip():
                    terms_html += f'<a href="?keyword={urllib.parse.quote(term.strip())}" class="related-term">{term.strip()}</a>'
            
            return terms_html
        return ''
    except Exception as e:
        print(f"获取相关搜索词时出错: {str(e)}")
        return ''

def create_detail_page(term, contents, output_dir):
    """创建详细内容页面"""
    if not contents:
        return None
    
    try:
        # 生成SEO友好的文件名
        filename = generate_seo_filename(term)
        safe_term = filename  # 添加这行，定义safe_term
        
        # 创建详细页面目录
        detail_dir = os.path.join(output_dir, 'p')  # 改用简短的目录名
        if not os.path.exists(detail_dir):
            os.makedirs(detail_dir)
        
        # 生成内容HTML和结构化数据
        content_html = ""
        article_schema = []
        
        # 集所有标题和摘要用于SEO
        all_titles = [content['title'] for content in contents if content.get('title')]
        all_abstracts = [content['abstract'] for content in contents if content.get('abstract')]
        
        # 生成更丰富的meta描述
        meta_description = f"{term}的详细内容。包含{len(contents)}个相关结果："
        meta_description += ''.join(all_titles[:3]) + "等。"
        if all_abstracts:
            meta_description += all_abstracts[0][:100] + "..."
            
        # 生成更丰富的关键词
        meta_keywords = set([term])
        meta_keywords.update(all_titles)
        meta_keywords.update([word for title in all_titles for word in title if len(word) > 1])
        meta_keywords_str = ', '.join(list(meta_keywords)[:20])  # 限制关键字量
        
        # 为每个内容块创建更丰富的Schema.org结构化数据
        for i, content in enumerate(contents, 1):
            article_schema.append({
                "@type": "Article",
                "headline": f"{content['source']}{content['title']}",
                "description": content['abstract'],
                "url": content['url'],
                "publisher": {
                    "@type": "Organization",
                    "name": content['source']
                },
                "position": i,
                "datePublished": datetime.now().isoformat(),
                "inLanguage": "zh-CN",
                "articleSection": term,
                "keywords": content['title'].split(),
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": content['url']
                }
            })
            
            # 生成更语义化的HTML内容
            content_html += f'''
            <article class="search-result" itemscope itemtype="http://schema.org/Article">
                <h2 itemprop="headline">{content['source']}{content['title']}</h2>
                <div class="content-body">
                    <p itemprop="description" class="abstract">{content['abstract']}</p>
                    <div class="meta-info">
                        <span class="source" itemprop="publisher" itemscope itemtype="http://schema.org/Organization">
                            来源：<span itemprop="name">{content['source']}</span>
                        </span>
                        <time itemprop="datePublished" datetime="{datetime.now().isoformat()}">
                            发布时间：{datetime.now().strftime('%Y-%m-%d')}
                        </time>
                    </div>
                    <p class="source-link">
                        原文链接：<a href="{content['url']}" target="_blank" rel="noopener noreferrer" itemprop="url">{content['url']}</a>
                    </p>
                </div>
            </article>
            '''
        
        # 获取相关搜索词的HTML
        related_terms_html = get_related_terms_html(term)
        
        # 在生成HTML内容时使用相关搜索词
        content_html += f'''
            <!-- 在footer前添加相关搜索部分 -->
            <div class="related-searches">
                <h3>相关搜索</h3>
                <div class="related-terms">
                    {related_terms_html}
                </div>
            </div>
        '''
        
        # 详细页面的HTML模板，添加更多SEO优化
        detail_template = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{term} - 相关内容详细信息 - 最新整理</title>
    
    <!-- 增强的SEO Meta标签 -->
    <meta name="keywords" content="{meta_keywords_str}">
    <meta name="description" content="{meta_description}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    <meta name="author" content="Search Results Generator">
    
    <!-- Open Graph Meta标签强 -->
    <meta property="og:title" content="{term} - 最新相关内容汇总">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{safe_term}.html">
    <meta property="og:site_name" content="搜索结果聚合">
    <meta property="article:published_time" content="{datetime.now().isoformat()}">
    <meta property="article:modified_time" content="{datetime.now().isoformat()}">
    <meta property="og:locale" content="zh_CN">
    
    <!-- Twitter Card Meta标签增强 -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{term} - 最新相关内容汇总">
    <meta name="twitter:description" content="{meta_description}">
    
    <!-- 其他重要Meta标签 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="format-detection" content="telephone=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    
    <!-- 百度特定Meta标签 -->
    <meta http-equiv="Cache-Control" content="no-transform">
    <meta http-equiv="Cache-Control" content="no-siteapp">
    <meta name="applicable-device" content="pc,mobile">
    <meta name="MobileOptimized" content="width">
    <meta name="HandheldFriendly" content="true">
    
    <link rel="stylesheet" href="../c/style.css">
    <link rel="canonical" href="{filename}.html">
    
    <!-- 增强的结构化数据 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": {json.dumps(article_schema)},
        "mainEntity": {{
            "@type": "WebPage",
            "name": "{term} - 相关内容详细信息",
            "description": "{meta_description}",
            "datePublished": "{datetime.now().isoformat()}",
            "dateModified": "{datetime.now().isoformat()}",
            "inLanguage": "zh-CN",
            "isPartOf": {{
                "@type": "WebSite",
                "name": "搜索结果聚合",
                "url": "../index.html"
            }}
        }}
    }}
    </script>
    
    <style>
        /* 文章页面特定样式 */
        .search-result {{
            margin-bottom: 30px;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .content-body {{
            margin-top: 15px;
            line-height: 1.8;
            font-size: 16px;
        }}
        .abstract {{
            color: #4d5156;
            margin-bottom: 15px;
            text-indent: 2em;
        }}
        .source-link {{
            color: #006621;
            font-size: 14px;
            margin-top: 10px;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }}
        h1 {{
            font-size: 24px;
            color: #1a0dab;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        h2 {{
            font-size: 18px;
            color: #1a0dab;
            margin: 0 0 15px 0;
        }}
        .article-meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .breadcrumb {{
            margin-bottom: 20px;
            color: #666;
            font-size: 14px;
        }}
        
        /* 相关搜索样式 */
        .related-searches {{
            margin-top: 40px;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .related-searches h3 {{
            color: #1a0dab;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .related-terms {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .related-term {{
            background: #f8f9fa;
            padding: 8px 15px;
            border-radius: 20px;
            color: #1a0dab;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        .related-term:hover {{
            background: #e8eaed;
            transform: translateY(-1px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <nav class="breadcrumb">
            <a href="../index.html">首页</a> > {term}
        </nav>
        <article>
            <h1>{term}</h1>
            <div class="article-meta">
                发布时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            <main>
                {content_html}
            </main>
            
            <footer>
                <p><a href="../index.html">返回搜索结果</a></p>
            </footer>
        </article>
    </div>
</body>
</html>
'''
        
        # 保存详细页面
        file_path = os.path.join(detail_dir, f"{filename}.html")
        with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(detail_template)
        
        return f'p/{filename}.html'
        
    except Exception as e:
        print(f"创建详细页面时出错: {str(e)}")
        return None

def create_result_item(index, term):
    """创建主页面的搜索结果项"""
    # 生成SEO友好的文件名
    filename = generate_seo_filename(term)
    
    return f'''
        <article class="result-item">
            <h2>
                <a href="p/{filename}.html" class="result-link">
                    {term}
                </a>
            </h2>
            <div class="result-snippet">
                <p>点击查看详细内容</p>
            </div>
        </article>
    '''

def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_to_html(keyword, related_searches):
    try:
        if not keyword or not related_searches:
            print("关键词或搜索结果为空")
            return None
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成目录名
        dir_name = generate_seo_filename(keyword)
        output_dir = f's_{dir_name}'  # 使用更短的前缀
        css_dir = os.path.join(output_dir, 'c')  # 简化css目录名
        details_dir = os.path.join(output_dir, 'p')  # 简详情页目录名
        
        try:
            # 创建必要的目录
            for directory in [output_dir, css_dir, details_dir]:
                if not os.path.exists(directory):
                    os.makedirs(directory)
        except Exception as e:
            print(f"创建目录失败: {str(e)}")
            return None
            
        try:
            # 保存CSS文件
            css_file = os.path.join(css_dir, 'style.css')
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(get_css_content())
        except Exception as e:
            print(f"保存CSS文件失败: {str(e)}")
            return None
            
        try:
            # 生成搜索结果HTML
            search_results = ""
            for i, term in enumerate(related_searches, 1):
                search_results += create_result_item(i, term)
            
            # 生成其他内容
            meta_tags = get_meta_tags(keyword, related_searches)
            json_results = create_json_results(related_searches)
            keywords = ', '.join(list(set([keyword] + related_searches)))
            description = f"关于{keyword}的相关搜索结果，含{len(related_searches)}个相关主题。"
            
            # 生成完整的HTML
            html_content = get_html_template().format(
                keyword=str(keyword),
                meta_tags=str(meta_tags),
                timestamp=str(timestamp),
                search_results=str(search_results),
                result_count=len(related_searches),
                json_results=str(json_results),
                keywords=str(keywords),
                description=str(description)
            )
            
            # 保存主页HTML
            html_file = os.path.join(output_dir, 'index.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # 为每个搜索词创建详细页面
            for term in related_searches:
                print(f"正在为 {term} 创建详细页面...")
                contents = get_article_content(term)
                if contents:
                    detail_page = create_detail_page(term, contents, output_dir)
                    if not detail_page:
                        print(f"创建 {term} 的详细页面失败")
                time.sleep(2)  # 加延迟避免请求过快
            
            # 生成主页
            generate_nav_page('.', [keyword] + related_searches)
            
            return output_dir
            
        except Exception as e:
            print(f"生成HTML容失败: {str(e)}")
            return None
            
    except Exception as e:
        print(f"保存HTML时出错: {str(e)}")
        return None

def get_related_searches(keyword):
    # 发送HTTP请求获取百度搜索页面的HTML内容
    url = f'http://www.baidu.com/s?wd={keyword}'
    response = requests.get(url, headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        # 使用lxml解析HTML内容
        html = etree.HTML(response.text)
        
        # 使用xpath获取相关搜索区域
        related_searches = html.xpath('//*[@id="rs_new"]/div/table//text()')
        
        # 过滤空白字符
        related_searches = [term.strip() for term in related_searches if term.strip()]
        
        return related_searches
    else:
        print('Failed to retrieve the webpage')
        return []

def read_keywords_from_file(filename):
    """从文件中读取关键词，确保正确读取所有行"""
    keywords = []
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                # 读取所有行
                lines = f.readlines()
                for line in lines:
                    # 清每行的空白字符和特殊字符
                    keyword = line.strip().replace('\ufeff', '').replace('\u200b', '')
                    if keyword:  # 只添加非空关键词
                        keywords.append(keyword)
                
                if keywords:  # 如果成功读取到关键词就跳出循环
                    break
                    
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码读取文件时出错: {str(e)}")
            continue
    
    if keywords:
        # 去重但保持原有顺序
        seen = set()
        keywords = [x for x in keywords if not (x in seen or seen.add(x))]
        print(f"成功读取到 {len(keywords)} 个关键词: {keywords}")
    else:
        print("警告: 未从文件中读取到任何关键词")
    
    return keywords

class ResourceMonitor:
    def __init__(self, max_memory_percent=75):
        self.max_memory_percent = max_memory_percent
        
    def check_resources(self):
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.max_memory_percent:
            logging.warning(f"内存使用率过高: {memory_percent}%")
            return False
        return True

class ThreadedSearchManager:
    """管理多线程搜索任务"""
    def __init__(self, max_workers=3):
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.result_queue = Queue()
        self.lock = threading.Lock()
        self.monitor = ResourceMonitor()
        self.progress_bar = None
        
    def process_keyword(self, keyword):
        """处理单个关键词的搜索任务"""
        try:
            related_searches = get_related_searches(keyword)
            if related_searches:
                output_dir = save_to_html(keyword, related_searches)
                with self.lock:
                    self.result_queue.put((keyword, output_dir))
                    if self.progress_bar:
                        self.progress_bar.update(1)
        except Exception as e:
            logging.error(f"处理关键词 '{keyword}' 时出错: {str(e)}")

class ResultCache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def get(self, key):
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            with cache_file.open('rb') as f:
                return pickle.load(f)
        return None
        
    def set(self, key, value):
        cache_file = self.cache_dir / f"{key}.pkl"
        with cache_file.open('wb') as f:
            pickle.dump(value, f)

class ProxyManager:
    def __init__(self, proxy_list=None):
        self.proxy_list = proxy_list or []
        self.current_index = 0
        
    def get_proxy(self):
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy

class AsyncSearchClient:
    """异步搜索客户端"""
    def __init__(self):
        self.headers = headers  # 使用原有的 headers
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_article_content_async(self, term):
        """异步获取文章内容"""
        url = f'http://www.baidu.com/s?wd={urllib.parse.quote(term)}'
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    tree = etree.HTML(html)
                    return self._parse_search_results(tree)
        except Exception as e:
            print(f"获取 {term} 内容时出错: {str(e)}")
            return None

    def _parse_search_results(self, html):
        """保持原有的解析逻辑"""
        # ... (使用原有的解析代码)
        pass

# 修改 main 函数支持多线程
def main():
    try:
        # 从1.txt读取关键词
        keywords = read_keywords_from_file('1.txt')
        
        if not keywords:
            print("未能从1.txt读取到关键词")
            return
        
        print(f"准备处理以下关键词: {keywords}")
        
        # 建线程池管理器
        thread_manager = ThreadedSearchManager(max_workers=3)
        
        # 提交所有任务到线程池
        futures = []
        for keyword in keywords:
            future = thread_manager.thread_pool.submit(thread_manager.process_keyword, keyword)
            futures.append(future)
            
        # 等待所有任务完成
        for future in futures:
            future.result()
            
        # 处理结果
        while not thread_manager.result_queue.empty():
            keyword, output_dir = thread_manager.result_queue.get()
            if output_dir:
                print(f"'{keyword}' 的搜索结果已保存到目录: {output_dir}")
                print(f"请在浏览器中打开 {os.path.join(output_dir, 'index.html')} 看搜索结果")
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 关闭线程池
        thread_manager.thread_pool.shutdown()

# 添加步搜索类
class AsyncSearchClient:
    """异步搜索客户端"""
    def __init__(self):
        self.headers = headers  # 使用原有的 headers
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_article_content_async(self, term):
        """异步获取文章内容"""
        url = f'http://www.baidu.com/s?wd={urllib.parse.quote(term)}'
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    tree = etree.HTML(html)
                    return self._parse_search_results(tree)
        except Exception as e:
            print(f"获取 {term} 内容时出错: {str(e)}")
            return None

    def _parse_search_results(self, html):
        """保持原有的解析逻辑"""
        # ... (使用原有的解析代码)
        pass

# 添加异步处理函数
async def process_keywords_async(keywords):
    """异步处理关键词列表"""
    async with AsyncSearchClient() as client:
        tasks = []
        for keyword in keywords:
            task = asyncio.create_task(process_keyword_async(client, keyword))
            tasks.append(task)
        await asyncio.gather(*tasks)

async def process_keyword_async(client, keyword):
    """异步处理单个关键词"""
    try:
        related_searches = await get_related_searches_async(client, keyword)
        if related_searches:
            output_dir = await save_to_html_async(keyword, related_searches, client)
            print(f"'{keyword}' 的搜索结果已异步保存到目录: {output_dir}")
    except Exception as e:
        print(f"异步处理关键词 '{keyword}' 时出错: {str(e)}")

# 添加异步主函数
async def main_async():
    """异步主函数"""
    try:
        keywords = read_keywords_from_file('1.txt')
        if keywords:
            await process_keywords_async(keywords)
    except Exception as e:
        print(f"异步处理错: {str(e)}")

# 修改原有的 main 函数，添加选择机制
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--async':
        # 使用异步式
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main_async())
    else:
        # 使用多线程模式
        main()
 
class RetryableRequest:
    def __init__(self, max_retries=3, delay=1):
        self.max_retries = max_retries
        self.delay = delay
        
    async def execute(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                logging.warning(f"请求失败，{self.delay}秒后重试: {str(e)}")
                await asyncio.sleep(self.delay)
                self.delay *= 2  # 指数退避
 
class ResultValidator:
    @staticmethod
    def validate_content(content):
        if not content.get('title') or not content.get('abstract'):
            return False
        if len(content['title']) < 2 or len(content['abstract']) < 10:
            return False
        return True
        
    @staticmethod
    def clean_text(text):
        """清理文本中的特殊字符"""
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
 
class Config:
    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.load_config()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f)
        else:
            self.settings = self.get_default_config()
            self.save_config()
            
    def get_default_config(self):
        return {
            'max_workers': 3,
            'max_retries': 3,
            'delay': 1,
            'max_memory_percent': 75,
            'cache_enabled': True,
            'proxy_list': []
        }
 
# 添加新函数用于获取相关搜索词
def get_related_terms_html(term):
    """获取相关搜索词并生成HTML"""
    try:
        url = f'http://www.baidu.com/s?wd={urllib.parse.quote(term)}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            # 获取相关搜索词
            related_terms = html.xpath('//*[@id="rs_new"]/div/table//td/a/span/text()')
            
            # 生成HTML
            terms_html = ''
            for term in related_terms:
                if term.strip():
                    terms_html += f'<a href="?keyword={urllib.parse.quote(term.strip())}" class="related-term">{term.strip()}</a>'
            
            return terms_html
        return ''
    except Exception as e:
        print(f"获取相关搜索词时出错: {str(e)}")
        return ''
 
async def get_related_searches_async(client, keyword):
    """异步获取相关搜索词"""
    url = f'http://www.baidu.com/s?wd={urllib.parse.quote(keyword)}'
    try:
        async with client.session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                tree = etree.HTML(html)
                related_searches = tree.xpath('//*[@id="rs_new"]/div/table//text()')
                return [term.strip() for term in related_searches if term.strip()]
    except Exception as e:
        print(f"获取相关搜索词时出错: {str(e)}")
        return []
 
async def save_to_html_async(keyword, related_searches, client):
    """异步版本的save_to_html函数"""
    try:
        if not keyword or not related_searches:
            return None
            
        # 复用原有的目录创建逻辑
        dir_name = generate_seo_filename(keyword)
        output_dir = f's_{dir_name}'
        css_dir = os.path.join(output_dir, 'c')
        details_dir = os.path.join(output_dir, 'p')
        
        # 创建目录
        for directory in [output_dir, css_dir, details_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # 保存CSS文件
        css_file = os.path.join(css_dir, 'style.css')
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(get_css_content())
        
        # 使用nav_generator生成导航页面
        generate_nav_page('.', [keyword] + related_searches)
        
        return output_dir
        
    except Exception as e:
        print(f"保存HTML时出错: {str(e)}")
        return None
 
def generate_sitemap(output_dir, urls):
    """生成sitemap.xml文件"""
    sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {urls}
</urlset>'''
    
    with open(os.path.join(output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

def create_sitemap_url(loc, lastmod=None, changefreq='daily', priority='0.8'):
    """创建单个URL的sitemap条目"""
    return f'''
    <url>
        <loc>{loc}</loc>
        <lastmod>{lastmod or datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
 
def generate_robots_txt(output_dir, domain):
    """生成robots.txt文件"""
    robots_content = f'''User-agent: *
Allow: /
Sitemap: {domain}/sitemap.xml
Crawl-delay: 1

# 允许主要搜索引擎快速抓取
User-agent: Googlebot
Crawl-delay: 0.5
Allow: /

User-agent: Baiduspider
Crawl-delay: 0.5
Allow: /

User-agent: bingbot
Crawl-delay: 0.5
Allow: /

User-agent: Sogou web spider
Crawl-delay: 0.5
Allow: /'''

    with open(os.path.join(output_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(robots_content)
 
def create_internal_links(related_searches, current_term):
    """创建内部链接HTML"""
    links = []
    for term in related_searches:
        if term != current_term:
            filename = generate_seo_filename(term)
            links.append(f'<a href="../p/{filename}.html" class="internal-link">{term}</a>')
    return '\n'.join(links)
 
def get_html_template():
    return '''
    <!-- ... 现有代码 ... -->
    <nav class="breadcrumb">
        <a href="../index.html">首页</a> > 
        <a href="index.html">搜索果</a> > 
        {keyword}
    </nav>
    
    <!-- 添加相关页面链接 -->
    <div class="related-pages">
        <h3>相关页面</h3>
        <div class="related-links">
            {internal_links}
        </div>
    </div>
    <!-- ... 现有代码 ... -->
    '''
 
def generate_rss_feed(output_dir, items, title="最新搜索结果"):
    """生成RSS feed"""
    rss_content = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>{title}</title>
    <link>./</link>
    <description>最新搜索结果更新</description>
    <language>zh-CN</language>
    <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')}</pubDate>
    {items}
</channel>
</rss>'''
    
    with open(os.path.join(output_dir, 'feed.xml'), 'w', encoding='utf-8') as f:
        f.write(rss_content)
 
def get_advanced_structured_data(keyword, related_searches, contents):
    """生成更丰富的结构化数据"""
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": f"{keyword}相关内容聚合",
                "url": "./",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": "?q={search_term_string}",
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "CollectionPage",
                "name": f"{keyword} - 内容聚合",
                "description": f"关于{keyword}的全面分析与整理",
                "isPartOf": {"@id": "./"},
                "about": {"@type": "Thing", "name": keyword}
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "item": {"@id": "./", "name": "首页"}
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "item": {"name": keyword}
                    }
                ]
            },
            {
                "@type": "HowTo",
                "name": f"如何了解{keyword}",
                "step": [
                    {
                        "@type": "HowToStep",
                        "text": f"浏览{keyword}的基本信息"
                    },
                    {
                        "@type": "HowToStep",
                        "text": "查看相关推荐内容"
                    }
                ]
            }
        ]
    }
 
def create_semantic_html(content):
    """生成语义化HTML"""
    return f'''
    <article itemscope itemtype="http://schema.org/Article">
        <header>
            <h1 itemprop="headline">{content['title']}</h1>
            <div class="meta">
                <time itemprop="datePublished" datetime="{datetime.now().isoformat()}">
                    {datetime.now().strftime('%Y-%m-%d')}
                </time>
                <span itemprop="author" itemscope itemtype="http://schema.org/Person">
                    <meta itemprop="name" content="Search Results Generator">
                </span>
            </div>
        </header>
        <div itemprop="articleBody">
            <p itemprop="description">{content['abstract']}</p>
        </div>
        <footer>
            <div class="source" itemprop="publisher" itemscope itemtype="http://schema.org/Organization">
                <span itemprop="name">{content['source']}</span>
            </div>
        </footer>
    </article>
    '''
 
def generate_internal_links(keyword, related_terms):
    """生成智能内链"""
    links = []
    for term in related_terms:
        # 计算相关度
        relevance = calculate_relevance(keyword, term)
        if relevance > 0.5:  # 相关度阈值
            filename = generate_seo_filename(term)
            links.append({
                'term': term,
                'url': f'p/{filename}.html',
                'relevance': relevance
            })
    return sorted(links, key=lambda x: x['relevance'], reverse=True)

def calculate_relevance(keyword, term):
    """计算两个词的相关度"""
    # 可以使用编辑距离、词向量等方法
    common_chars = set(keyword) & set(term)
    return len(common_chars) / max(len(keyword), len(term))
 
def add_update_info(output_dir):
    """添加更新时间信息"""
    update_file = os.path.join(output_dir, 'last_update.txt')
    with open(update_file, 'w', encoding='utf-8') as f:
        f.write(datetime.now().isoformat())
    
    # 同时更新sitemap
    update_sitemap_dates(output_dir)
 
def optimize_url_structure(term):
    """生成对搜索引擎友好的URL结构"""
    # 使用拼音转换
    pinyin = '-'.join(lazy_pinyin(term))
    # 添加日期
    date = datetime.now().strftime('%Y%m')
    # 生成最终URL
    return f"{date}/{pinyin}.html"
 
def update_sitemap_dates(output_dir):
    """更新sitemap中的时间戳"""
    sitemap_file = os.path.join(output_dir, 'sitemap.xml')
    if not os.path.exists(sitemap_file):
        return
        
    try:
        with open(sitemap_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 更新所有lastmod标签的日期为当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        updated_content = re.sub(
            r'<lastmod>.*?</lastmod>',
            f'<lastmod>{current_date}</lastmod>',
            content
        )
        
        with open(sitemap_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
    except Exception as e:
        logging.error(f"更新sitemap日期时出错: {str(e)}")
 