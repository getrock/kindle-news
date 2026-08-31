import sys
import feedparser
import trafilatura
from ebooklib import epub
import datetime

# Fix for Windows console Unicode error (Bengali characters)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 1. Define your RSS feeds grouped by Category
FEEDS = {
    'West Bengal': {
        'ABP Ananda': 'https://bengali.abplive.com/news/india/feed',
        'News24 Kolkata': 'https://news24-bengali.com/kolkata/feed'
    },
    'Global': {
        'BBC Top Stories': 'http://feeds.bbci.co.uk/news/rss.xml'
    },
    'USA': {
        'NYT US News': 'https://rss.nytimes.com/services/xml/rss/nyt/US.xml',
        'NPR National': 'https://feeds.npr.org/1003/rss.xml'
    }
}

def create_news_epub():
    book = epub.EpubBook()
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    book.set_identifier(f'daily_news_{date_str}')
    book.set_title(f'Daily News - {date_str}')
    book.set_language('en') 
    book.add_author('Automated Python Script')

    # Styling for both the index page and news chapters
    style = '''
        body { font-family: sans-serif; margin: 5%; }
        h1 { text-align: center; } 
        h2.category-title { border-bottom: 2px solid #888; padding-bottom: 4px; margin-top: 24px; }
        .meta { color: #888; font-size: 0.9em; margin-bottom: 1em; }
        p { line-height: 1.5; margin-bottom: 1em; }
        ul.toc-list { list-style-type: disc; margin-left: 20px; }
        li.toc-item { margin-bottom: 8px; }
        a { text-decoration: none; color: #4fa3e3; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    chapter_count = 1
    all_chapters = []
    toc_structure = []
    
    # Track articles by category to build an explicit on-page visual Index
    category_data = {}

    for category_name, category_feeds in FEEDS.items():
        print(f"\n=== Fetching Category: {category_name} ===")
        category_chapters = []

        for source_name, feed_url in category_feeds.items():
            print(f"Fetching from {source_name}...")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:7]:
                title = entry.title
                link = entry.link
                print(f" -> Downloading: {title}")
                
                downloaded = trafilatura.fetch_url(link)
                if not downloaded:
                    continue
                    
                content_text = trafilatura.extract(downloaded)
                if not content_text:
                    continue
                    
                clean_html = "".join([f"<p>{line.strip()}</p>" for line in content_text.split('\n') if line.strip()])
                
                file_name = f'chap_{chapter_count}.xhtml'
                chapter = epub.EpubHtml(title=title, file_name=file_name, lang='en')
                chapter.add_item(nav_css)
                chapter.content = f'<h1>{title}</h1><div class="meta"><strong>Category:</strong> {category_name} | <strong>Source:</strong> {source_name}</div><div>{clean_html}</div>'
                
                book.add_item(chapter)
                category_chapters.append(chapter)
                all_chapters.append(chapter)
                chapter_count += 1
        
        if category_chapters:
            category_data[category_name] = category_chapters
            # Creates expandable folders in Kindle TOC sidebar
            toc_structure.append((epub.Section(category_name), tuple(category_chapters)))

    # Create a custom categorized front Table of Contents page
    toc_html_content = [f'<h1>Daily News - {date_str}</h1><hr/>']
    for cat_name, chaps in category_data.items():
        toc_html_content.append(f'<h2 class="category-title">{cat_name}</h2><ul class="toc-list">')
        for chap in chaps:
            toc_html_content.append(f'<li class="toc-item"><a href="{chap.file_name}">{chap.title}</a></li>')
        toc_html_content.append('</ul>')

    main_index_page = epub.EpubHtml(title="Table of Contents", file_name="main_index.xhtml", lang='en')
    main_index_page.add_item(nav_css)
    main_index_page.content = "".join(toc_html_content)
    book.add_item(main_index_page)

    # Set Kindle metadata TOC
    book.toc = tuple(toc_structure)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Put the custom Category Index as the very first reading page
    book.spine = [main_index_page] + all_chapters

    output_filename = f'Daily_News_{date_str}.epub'
    epub.write_epub(output_filename, book, {})
    
    print(f"\nSuccess! Saved categorized newspaper to {output_filename}")

if __name__ == '__main__':
    create_news_epub()