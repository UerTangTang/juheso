from datetime import datetime
import os
import json
from urllib.parse import quote
import random
import logging

def get_random_keywords(max_count=20):
    """从folder_keywords.txt中随机获取指定数量的关键词"""
    try:
        keywords = []
        with open('folder_keywords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    keyword, _ = line.strip().split('\t')
                    keywords.append(keyword)
        
        # 如果关键词数量超过max_count，随机选择max_count个
        if len(keywords) > max_count:
            return random.sample(keywords, max_count)
        return keywords
    except Exception as e:
        logging.error(f"获取随机关键词时出错: {str(e)}")
        return []

def generate_nav_page(output_dir, all_keywords):
    """生成导航页面"""
    # 获取随机关键词
    display_keywords = get_random_keywords(19)  # 获取19个随机关键词
    if all_keywords and all_keywords[0] not in display_keywords:  # 确保当前关键词在列表中
        display_keywords.insert(0, all_keywords[0])  # 将当前关键词放在最前面
    
    # 生成HTML内容
    nav_html = create_nav_html(group_keywords_by_topic(display_keywords), len(display_keywords))
    
    # 保存导航页
    save_nav_page(output_dir, nav_html)
    
    # 生成sitemap
    generate_sitemap(output_dir, display_keywords)

def get_keywords_from_file():
    """从folder_keywords.txt获取关键词"""
    keywords = set()
    try:
        with open('folder_keywords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    keyword, _ = line.strip().split('\t')
                    keywords.add(keyword)
    except Exception as e:
        print(f"读取folder_keywords.txt时出错: {str(e)}")
    return list(keywords)

def get_nav_css():
    """获取导航页面的CSS样式"""
    return '''
        :root {
            --primary: #1a73e8;
            --text: #202124;
            --bg: #ffffff;
            --border: #e0e0e0;
            --hover: #f8f9fa;
            --shadow: rgba(0,0,0,0.05);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        .nav-header {
            text-align: center;
            margin-bottom: 40px;
        }

        .nav-title {
            font-size: 2em;
            color: var(--text);
            margin-bottom: 10px;
        }

        .nav-description {
            color: #666;
            max-width: 600px;
            margin: 0 auto;
        }

        .keyword-section {
            background: #fff;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 12px var(--shadow);
        }

        .section-title {
            font-size: 1.2em;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }

        .keyword-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 15px;
            padding: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .keyword-link {
            color: var(--text);
            text-decoration: none;
            font-size: 15px;
            padding: 10px 20px;
            border-radius: 20px;
            background: var(--bg);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border);
            box-shadow: 0 2px 4px var(--shadow);
            position: relative;
            overflow: hidden;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            grid-column: span var(--cols, 1);
        }

        .keyword-link:hover {
            color: var(--primary);
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow);
            z-index: 1;
        }

        .keyword-link::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                120deg,
                transparent,
                rgba(255,255,255,0.6),
                transparent
            );
            transition: 0.5s;
        }

        .keyword-link:hover::before {
            left: 100%;
        }

        .page-footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }

        @media (max-width: 768px) {
            .nav-container {
                padding: 20px;
            }
            .keyword-section {
                padding: 20px;
            }
            .keyword-list {
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                gap: 10px;
                padding: 15px;
            }
            .keyword-link {
                font-size: 14px;
                padding: 8px 12px;
            }
        }
    '''

def create_nav_html(keyword_groups, total_keywords):
    """创建导航页HTML内容"""
    # 生成关键词和描述
    all_keywords = []
    for keywords in keyword_groups.values():
        all_keywords.extend(keywords)
    
    # 生成更丰富的meta描述
    meta_description = f"提供{total_keywords}个精选热门关键词的搜索结果聚合。包含{', '.join(all_keywords[:5])}等热门内容，每日更新。"
    
    # 生成结构化数据
    mapping = get_keyword_folder_mapping()
    structured_data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "内容导航中心",
        "description": meta_description,
        "url": "./",
        "dateModified": datetime.now().isoformat(),
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": keyword,
                    "url": f"{folder}/index.html"
                } for i, (keyword, folder) in enumerate(mapping.items())
            ]
        }
    }

    return f'''<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>聚合搜 - 最新更新 | {datetime.now().strftime('%Y-%m-%d')}</title>
        
        <!-- 增强搜索引擎抓取设置 -->
        <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1, max-video-preview:-1">
        <meta name="googlebot" content="index, follow, max-snippet:-1, max-image-preview:large">
        <meta name="bingbot" content="index, follow, max-snippet:-1, max-image-preview:large">
        <meta name="baidu-site-verification" content="codeva-5Tx3gC2Tal" content="code-{datetime.now().strftime('%Y%m%d')}"/>
        <meta name="msvalidate.01" content="71A98B01C97FA508E1DF9917FB8E0C00" content="code-{datetime.now().strftime('%Y%m%d')}"/>
        <meta name="google-site-verification" content="dYg1tNb5pqr-ZRMcNAbVqPEk0kt6_Us3lTUpzuUri2U" content="code-{datetime.now().strftime('%Y%m%d')}"/>
        
        <!-- 增强SEO Meta标签 -->
        <meta name="description" content="{meta_description}">
        <meta name="keywords" content="{','.join(all_keywords)}">
        <meta name="author" content="Content Navigation Center">
        <meta name="copyright" content="Content Navigation Center">
        <meta name="revisit-after" content="1 days">
        <meta name="generator" content="Content Navigation System 2.0">
        
        <!-- 搜索引擎链接优化 -->
        <link rel="canonical" href="./index.html">
        <link rel="alternate" href="./index.html" hreflang="zh-CN">
        <link rel="alternate" href="./index.html" hreflang="x-default">
        
        <!-- DNS预解析和资源提示 -->
        <link rel="preconnect" href="//www.baidu.com">
        <link rel="preconnect" href="//www.google.com">
        <link rel="dns-prefetch" href="//www.baidu.com">
        <link rel="dns-prefetch" href="//www.google.com">
        
        <!-- 添加RSS Feed -->
        <link rel="alternate" type="application/rss+xml" title="RSS 2.0" href="./feed.xml">
        
        <!-- 其他现有meta标签... -->
        
        <!-- 结构化数据增强 -->
        <script type="application/ld+json">
        {json.dumps(structured_data, ensure_ascii=False)}
        </script>
        
        <!-- 添加Breadcrumb结构化数据 -->
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
                }}
            ]
        }}
        </script>
        
        <style>{get_nav_css()}</style>
    </head>
    <body>
        <div class="nav-container" itemscope itemtype="http://schema.org/WebPage">
            <header class="nav-header">
                <h1 class="nav-title" itemprop="headline">热门内容导航</h1>
                <p class="nav-description" itemprop="description">
                    精选{total_keywords}个优质内容，每日实时更新。
                </p>
            </header>
            <main itemprop="mainContentOfPage">
                <div class="keyword-list">
                    {generate_keyword_links(get_keywords_from_file())}
                </div>
            </main>
            <footer class="page-footer">
                <p>更新时间：<time itemprop="dateModified" datetime="{datetime.now().isoformat()}">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</time></p>
                <p>本站内容由AI智能算法推荐，每小时更新一次</p>
            </footer>
        </div>
    </body>
    </html>
    '''

def group_keywords_by_topic(keywords):
    """将关键词按主题智能分组"""
    # 读取folder_keywords.txt中的射关系
    keyword_folder_map = {}
    try:
        with open('folder_keywords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    keyword, folder = line.strip().split('\t')
                    keyword_folder_map[keyword] = folder
    except Exception as e:
        print(f"读取folder_keywords.txt时出错: {str(e)}")
        return {}

    # 对关键词进行分组
    groups = {
        "热门推荐": [],
        "影视娱乐": [],
        "游戏动漫": [],
        "科技数码": [],
        "其他": []
    }
    
    # 使用folder_keywords.txt中的关键词进行分类
    for keyword in keyword_folder_map.keys():
        if "电影" in keyword or "视频" in keyword or "观看" in keyword:
            groups["影视娱乐"].append(keyword)
        elif "游戏" in keyword or "动漫" in keyword:
            groups["游戏动漫"].append(keyword)
        elif "app" in keyword.lower() or "下载" in keyword:
            groups["科技数码"].append(keyword)
        else:
            groups["其他"].append(keyword)
    
    # 移除空分类
    return {k: v for k, v in groups.items() if v}

def generate_topic_cards(keyword_groups):
    """生成主题卡片HTML - 优化版本"""
    cards = []
    for topic, keywords in keyword_groups.items():
        cards.append(f'''
        <section class="keyword-section">
            <h2 class="section-title">{topic}</h2>
            <div class="keyword-list">
                {generate_keyword_links(keywords)}
            </div>
        </section>
        ''')
    return '\n'.join(cards)

def generate_keyword_links(keywords):
    """生成关键词链接HTML - 根据文字长度排序"""
    links = []
    
    # 读取folder_keywords.txt中的映射关系
    keyword_folder_map = {}
    try:
        with open('folder_keywords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    keyword, folder = line.strip().split('\t')
                    keyword_folder_map[keyword] = folder
    except Exception as e:
        print(f"读取folder_keywords.txt时出错: {str(e)}")
        return ''
    
    # 获取所有关键词并按长度排序
    all_keywords = list(keyword_folder_map.keys())
    all_keywords.sort(key=len)  # 按文字长度排序
    
    # 生成链接，根据文字长度设置跨列数
    for keyword in all_keywords:
        folder = keyword_folder_map[keyword]
        # 根据文字长度决定跨列数
        cols = min(len(keyword) // 5 + 1, 4)  # 最多跨4列
        
        # 生成指向html目录下的链接
        links.append(f'''
        <a href="html/{folder}/index.html" 
           class="keyword-link" 
           title="{keyword}的详细信息"
           style="--cols: {cols}">
            {keyword}
        </a>
        ''')
    
    return '\n'.join(links)

def generate_seo_filename(term):
    """生成SEO友好的文件名 - 与1.py保持一致"""
    return ''.join(c for c in term if c.isalnum() or '\u4e00' <= c <= '\u9fff')

def generate_sitemap(output_dir, keywords):
    """生成增强版sitemap.xml"""
    # 生成sitemap
    sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>',
                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
                      'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                      'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"',
                      'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    
    # 添加导航页（更高更新频率）
    sitemap_content.append(f'''
    <url>
        <loc>./index.html</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}</lastmod>
        <changefreq>always</changefreq>
        <priority>1.0</priority>
    </url>
    ''')
    
    # 添加所有关键词页面（高更新���率）
    for keyword in keywords:
        dir_name = f's_{generate_seo_filename(keyword)}'
        sitemap_content.append(f'''
        <url>
            <loc>./html/{dir_name}/index.html</loc>
            <lastmod>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}</lastmod>
            <changefreq>hourly</changefreq>
            <priority>0.9</priority>
            <news:news>
                <news:publication>
                    <news:name>Content Navigation Center</news:name>
                    <news:language>zh</news:language>
                </news:publication>
                <news:publication_date>{datetime.now().strftime('%Y-%m-%d')}</news:publication_date>
                <news:title>{keyword}</news:title>
            </news:news>
        </url>
        ''')
    
    sitemap_content.append('</urlset>')
    
    # 保存sitemap
    with open(os.path.join(output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sitemap_content))
    
    # 生成robots.txt
    robots_content = f'''User-agent: *
Allow: /
Sitemap: ./sitemap.xml

# 优化主要搜索引擎抓取
User-agent: Googlebot
Crawl-delay: 1
Allow: /

User-agent: Baiduspider
Crawl-delay: 1
Allow: /

User-agent: bingbot
Crawl-delay: 1
Allow: /

User-agent: Sogou web spider
Crawl-delay: 1
Allow: /

User-agent: Bytespider
Crawl-delay: 1
Allow: /

# 禁止图片抓取器
User-agent: Googlebot-Image
Disallow: /

User-agent: Baiduspider-image
Disallow: /
'''
    
    # 保存robots.txt
    with open(os.path.join(output_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(robots_content)

def save_nav_page(output_dir, html_content):
    """保存导航页HTML文件到根目录"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def get_keyword_folder_mapping():
    """获取关键词和文件夹的映射关系"""
    mapping = {}
    try:
        with open('folder_keywords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    keyword, folder = line.strip().split('\t')
                    # 修改映射路径，添加html目录前缀
                    mapping[keyword] = f'html/{folder}'
    except Exception as e:
        print(f"读取folder_keywords.txt时出错: {str(e)}")
    return mapping 