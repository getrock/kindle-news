import sys
import os
import datetime
import feedparser
import trafilatura
from ebooklib import epub
import weasyprint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
# Add your extra PDF email addresses here
PDF_EMAILS = ['sarasij2800.basu@gmail.com', 'poulomi.ankita@gmail.com']

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

def send_emails(epub_filepath, pdf_filepath):
    sender_email = os.environ.get('GMAIL_USER')
    sender_password = os.environ.get('GMAIL_PASS')
    kindle_email = os.environ.get('KINDLE_EMAIL')

    if not sender_email or not sender_password:
        print("Email credentials not found. Skipping delivery.")
        return

    # Build a list of recipients and which file they should get
    deliveries = []
    if kindle_email:
        deliveries.append((kindle_email, epub_filepath, 'epub+zip'))
    for pdf_email in PDF_EMAILS:
        deliveries.append((pdf_email, pdf_filepath, 'pdf'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)

        for recipient_email, filepath, mime_subtype in deliveries:
            print(f"Sending {filepath} to {recipient_email}...")
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Your Daily News Edition"

            try:
                with open(filepath, "rb") as attachment:
                    part = MIMEBase('application', mime_subtype)
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {filepath}')
                msg.attach(part)
                
                server.send_message(msg)
                print(f" -> Success sending to {recipient_email}")
            except Exception as e:
                print(f" -> Error attaching or sending to {recipient_email}: {e}")

        server.quit()
    except Exception as e:
        print(f"Error connecting to email server: {e}")

def create_news_files():
    book = epub.EpubBook()
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    book.set_identifier(f'daily_news_{date_str}')
    book.set_title(f'Daily News - {date_str}')
    book.set_language('en') 
    book.add_author('Automated Python Script')

    style = '''
        body { font-family: sans-serif; margin: 5%; }
        h1 { text-align: center; } 
        h2.category-title { border-bottom: 2px solid #888; padding-bottom: 4px; margin-top: 24px; }
        .meta { color: #888; font-size: 0.9em; margin-bottom: 1em; }
        p { line-height: 1.5; margin-bottom: 1em; }
        ul.toc-list { list-style-type: disc; margin-left: 20px; }
        li.toc-item { margin-bottom: 8px; }
        a { text-decoration: none; color: #4fa3e3; }
        .article-divider { border-top: 1px dashed #ccc; margin: 40px 0; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    chapter_count = 1
    all_chapters = []
    toc_structure = []
    category_data = {}

    # Initialize PDF HTML structure
    pdf_html = [f"<html><head><meta charset='utf-8'><style>{style}</style></head><body>"]
    pdf_html.append(f"<h1>Daily News - {date_str}</h1><hr/>")

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
                
                # 1. Build EPUB Chapter
                file_name = f'chap_{chapter_count}.xhtml'
                chapter = epub.EpubHtml(title=title, file_name=file_name, lang='en')
                chapter.add_item(nav_css)
                chapter.content = f'<h1>{title}</h1><div class="meta"><strong>Category:</strong> {category_name} | <strong>Source:</strong> {source_name}</div><div>{clean_html}</div>'
                book.add_item(chapter)
                category_chapters.append(chapter)
                all_chapters.append(chapter)
                
                # 2. Add to PDF HTML
                pdf_html.append(f'<h2>{title}</h2><div class="meta"><strong>Category:</strong> {category_name} | <strong>Source:</strong> {source_name}</div><div>{clean_html}</div><div class="article-divider"></div>')

                chapter_count += 1
        
        if category_chapters:
            category_data[category_name] = category_chapters
            toc_structure.append((epub.Section(category_name), tuple(category_chapters)))

    pdf_html.append("</body></html>")

    # Finalize EPUB
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
    book.toc = tuple(toc_structure)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [main_index_page] + all_chapters
    epub_filename = f'Daily_News_{date_str}.epub'
    epub.write_epub(epub_filename, book, {})
    
    # Finalize PDF
    pdf_filename = f'Daily_News_{date_str}.pdf'
    full_html_string = "".join(pdf_html)
    weasyprint.HTML(string=full_html_string).write_pdf(pdf_filename)

    print(f"\nFiles Generated: {epub_filename} and {pdf_filename}")
    
    # Trigger dual-format delivery
    send_emails(epub_filename, pdf_filename)

if __name__ == '__main__':
    create_news_files()
