from playwright.sync_api import sync_playwright
import json
from urllib.parse import urlparse, urljoin
from collections import deque
import hashlib
import time
import random

def normalize_url(url, base=None):
    """Improved URL normalization with base URL resolution"""
    if base:
        url = urljoin(base, url)
    parsed = urlparse(url)
    scheme = parsed.scheme or 'https'
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/') or '/'
    return f"{scheme}://{netloc}{path}".lower()

def scrape_website(base_url):
    visited_urls = set()
    content_hashes = set()
    queue = deque([base_url])
    scraped_data = []
    
    # Expanded list of HTML elements and attributes containing text
    text_selectors = [
        # Standard content tags
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'li', 'span', 'div', 'a', 'strong', 'em',
        'blockquote', 'cite', 'caption', 'th', 'td',
        'article', 'section', 'header', 'footer', 'nav',
        'aside', 'main', 'figcaption', 'dt', 'dd',
        'code', 'pre', 'q', 'mark', 'time', 'label',
        'abbr', 'b', 'i', 'small', 'sub', 'sup', 'var',
        'samp', 'kbd', 'output', 'progress', 'meter',
        'button', 'legend', 'textarea', 'option',
        
        # Semantic HTML5 tags
        'address', 'details', 'summary', 'del', 'ins',
        'dfn', 'ruby', 'rt', 'rp', 'bdi', 'data', 'wbr',
        
        # Form elements
        'input[type="text"]', 'input[type="email"]',
        'input[type="search"]', 'input[type="tel"]',
        'input[type="url"]', 'datalist', 'fieldset',
        'optgroup',
        
        # Tables
        'colgroup', 'col', 'tbody', 'thead', 'tfoot', 'tr',
        
        # Legacy/deprecated tags
        'marquee', 'nobr', 'acronym', 'big', 'center',
        'font', 'tt', 'dir', 'menu', 'isindex', 'strike',
        
        # Metadata and special content
        'title', 'meta[property="og:title"]', 
        'meta[name="description"]', 'meta[property="og:description"]',
        'img', 'iframe', 'noscript', 'canvas'
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            bypass_csp=True
        )

        try:
            while queue:
                current_url = queue.popleft()
                normalized_url = normalize_url(current_url, base_url)

                if normalized_url in visited_urls:
                    continue
                
                visited_urls.add(normalized_url)
                print(f"Processing: {normalized_url}")

                page = context.new_page()
                try:
                    # Load page with multiple wait strategies
                    response = page.goto(current_url, wait_until="networkidle", timeout=60000)
                    
                    # Wait for critical content
                    page.wait_for_selector(':root', state='attached', timeout=30000)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Extract content with expanded attribute coverage
                    content_blocks = page.evaluate('''(selectors) => {
                        const results = [];
                        const elements = document.querySelectorAll(selectors.join(','));
                        
                        elements.forEach(el => {
                            // Get all possible text sources
                            const textContent = el.textContent.trim();
                            const altText = el.getAttribute('alt')?.trim() || '';
                            const metaContent = el.getAttribute('content')?.trim() || '';
                            const placeholder = el.getAttribute('placeholder')?.trim() || '';
                            const value = el.getAttribute('value')?.trim() || '';
                            const title = el.getAttribute('title')?.trim() || '';
                            
                            // Special handling for different element types
                            let combined = [
                                textContent,
                                altText,
                                metaContent,
                                placeholder,
                                value,
                                title
                            ].join(' ').replace(/\s+/g, ' ').trim();
                            
                            // Handle special elements
                            if (el.tagName === 'NOSCRIPT') {
                                combined = el.innerHTML.trim();
                            }
                            
                            if (combined) results.push(combined);
                        });
                        
                        return results;
                    }''', text_selectors)

                    # Process and validate content
                    full_text = ' '.join(content_blocks)
                    if len(full_text) < 100:
                        print(f"Skipping low-content page: {normalized_url}")
                        continue

                    # Deduplication with SHA-256
                    text_hash = hashlib.sha256(full_text.encode()).hexdigest()
                    if text_hash not in content_hashes:
                        scraped_data.append({
                            "url": normalized_url,
                            "text": full_text,
                            "content_hash": text_hash,
                            "timestamp": time.time()
                        })
                        content_hashes.add(text_hash)

                    # Link discovery with improved filtering
                    links = page.eval_on_selector_all(
                        'a[href]',
                        '''elements => elements.map(el => el.href)'''
                    )
                    for link in links:
                        normalized = normalize_url(link, normalized_url)
                        if (normalized not in visited_urls and 
                            normalized.startswith(base_url)):
                            queue.append(normalized)

                    # Randomized delay with human pattern
                    delay = random.uniform(1.0, 4.0)
                    time.sleep(delay)

                except Exception as e:
                    print(f"Error processing {normalized_url}: {str(e)}")
                finally:
                    try:
                        page.close()
                    except:
                        pass

        finally:
            browser.close()

    # Save structured data
    with open("full_coverage_data.json", "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "base_url": base_url,
                "scrape_date": time.ctime(),
                "page_count": len(scraped_data),
                "content_hash": hashlib.sha256(json.dumps(scraped_data).encode()).hexdigest()
            },
            "pages": scraped_data
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_website("https://www.appsgenii.com/")