# 🗞️ Automated Kindle News Pipeline

A serverless Python pipeline that fetches, cleans, and formats daily bilingual news (English and Bengali) into EPUBs, delivering them directly to a Kindle via GitHub Actions.

### The Problem
I wanted a distraction-free way to read daily news on my e-reader, including regional Bengali publishers that don't always play nicely with standard RSS aggregators. 

### The Solution
This project automates the entire extraction and delivery process without requiring a dedicated server or paid cloud hosting. 

### Core Features
* **Full-Text Extraction:** Bypasses RSS summaries to scrape and clean the full article text using `trafilatura`.
* **Multilingual Parsing:** Configured with UTF-8 encoding to perfectly render Bengali (Indic) scripts alongside standard Latin characters.
* **E-Reader Optimized:** Generates lightweight, dark-mode compatible EPUBs with a hierarchical Table of Contents (grouped by Global, USA, and West Bengal news).
* **Zero-Touch Automation:** Scheduled via GitHub Actions (CI/CD) to build and email the daily edition to my Kindle every morning at 6:00 AM IST.

### Tech Stack
* **Python 3.11** 
* **Libraries:** `feedparser`, `trafilatura`, `EbookLib`
* **Infrastructure:** GitHub Actions, Google SMTP
