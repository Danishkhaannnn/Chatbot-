import json
import csv
import re
import hashlib
from bs4 import BeautifulSoup

# Combined regex pattern for technical code and specified strings
TECHNICAL_PATTERNS = re.compile(
    r'(//<\!\[CDATA\[\s*)?'  # CDATA prefix
    r'(\(function\(\$\)\s*{.*?})(\)\s*\);?)'  # jQuery functions
    r'|(var\s+\w+\s*=.*?;)'  # Variable declarations
    r'|(/\*.*?\*/)'  # CSS comments
    r'|(particlesJS\(.*?}\);)'  # Particles.js initialization
    r'|(\.tparrows.*?})'  # Specific CSS classes
    r'|(#rev_slider_\d+_wrapper.*?})'  # Slider wrapper styles
    r'|(Portfolio Case Studies.*?Cross Platform Mobile Development)'  # Text duplicates
    r'|(\$\(document\)\.ready\(function\(\).*?}\);)'  # Document ready
    r'|(</script>.*?<script>)'  # Nested script tags
    r'|(</style>.*?<style>)'  # Nested style tags
    r'|(\+1 510 850 4645)'  # Phone number pattern
    r'|(Mon - Fri 9\.00 - 6\.00)'  # Working hours
    r'|(744 Brick Row Drive, Richardson, TX 75081)'  # Address
    r'|(AppsGenii Technologies Consultancy.*?Technology)',  # Repeated header
    re.DOTALL | re.IGNORECASE
)

REMOVE_PATTERN = re.compile(
    r'deCaptionAtLimit:0,\s*hideAllCaptionAtLilmit:0,\s*debugMode:false,\s*fallbacks:\s*{\s*simplifyAll:"off",\s*nextSlideOnWindowFocus:"off",\s*disableFocusListener:false,\s*}\s*}\);\s*}\s*}\);\s*/\*ready\*/\s*'
    r'var\s+htmlDivCss\s*=\s*unescape\("body%20\.tparrows\%3Ahover\%20%7B%0A%20%20%20%20background\%3A\%20%23f2a91e\%3B%0A%20%20%20%20border-color\%3A\%20%23f2a91e\%3B\%0A%7D\%0A'
    r'%23rev_slider_4_1_wrapper%7B%0A%20%20min-height\%3A\%20375px\%20%21important\%3B%0A%20%20background\%3A\%20rgb\%2847%2C\%2047%2C\%2047\%29\%20%21important\%3B%0A%7D"\);\s*'
    r'var\s+htmlDiv\s*=\s*document\.getElementById\(\'rs-plugin-settings-inline-css\'\);\s*'
    r'if\(htmlDiv\)\s*{\s*htmlDiv\.innerHTML\s*=\s*htmlDiv\.innerHTML\s*\+\s*htmlDivCss;\s*}\s*else{\s*'
    r'var\s+htmlDiv\s*=\s*document\.createElement\(\'div\'\);\s*htmlDiv\.innerHTML\s*=\s*\'\';\s*'
    r'document\.getElementsByTagName\(\'head\'\)\[0\]\.appendChild\(htmlDiv\.childNodes\[0\]\);\s*}\s*',
    re.DOTALL | re.IGNORECASE
)

def clean_content(text):
    """Multi-stage content cleaning pipeline"""
    try:
        # Stage 1: Remove HTML/CSS/JS tags and their content using BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')
        for tag in soup(['script', 'style', 'link', 'meta', 'nav', 'footer']):  # Remove script, style, and other tags
            tag.decompose()
        
        # Stage 2: Clean the text inside the tags and remove unwanted content
        cleaned = soup.get_text(separator=' ', strip=True)
        
        # Stage 3: Remove technical patterns, JavaScript, and CSS-related content
        cleaned = TECHNICAL_PATTERNS.sub('', cleaned)
        
        # Stage 4: Remove specific unwanted data (like the provided pattern for sliders and fallback info)
        cleaned = REMOVE_PATTERN.sub('', cleaned)
        
        # Stage 5: Extra cleaning to remove unwanted characters and collapse whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Collapse multiple spaces into one
        cleaned = re.sub(r'[^\w\s.,-]', '', cleaned)  # Remove special characters like punctuation
        
        # Remove any remaining unwanted specific words/phrases if any
        unwanted_phrases = [
            "Portfolio Case Studies", "ShareNGo Case Study", "Serviceman Case Study", 
            "Careers Blogs Contact Us", "AppsGenii Technologies Consultancy", 
            "Strategy", "Technology", "Home About Us", "Mobile App Marketing", "Cross Platform Mobile Development"
        ]
        for phrase in unwanted_phrases:
            cleaned = cleaned.replace(phrase, '')
        
        return cleaned.strip()
    
    except Exception as e:
        print(f"Cleaning error: {str(e)}")
        return text

def normalize_text(text):
    """Text normalization for deduplication"""
    return hashlib.sha256(text.lower().encode()).hexdigest()

def process_data(input_file, output_file):
    """Main processing workflow"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        seen_hashes = set()
        unique_entries = []
        added_string = False  # Flag to ensure the string is only added once
        
        for page in data.get('pages', []):
            raw_text = page.get('text', '')
            cleaned_text = clean_content(raw_text)
            
            # Add the specific string once if it has not been added yet
            if not added_string and "Portfolio Case Studies" in cleaned_text:
                cleaned_text = "Portfolio Case Studies Serviceman Case Study ShareNGo Case Study Careers Blogs Contact Us AppsGenii Technologies Consultancy | Strategy | Technology Home About Us Services Android App Development iOS App Development Mobile App Design Game Development Mobile App Marketing Web Development Search Engine Optimization Cross Platform Mobile Development " + cleaned_text
                added_string = True
            
            if not cleaned_text:
                continue
                
            text_hash = normalize_text(cleaned_text)
            
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_entries.append({
                    'url': page.get('url', ''),
                    'content': cleaned_text,
                    'timestamp': page.get('timestamp', ''),
                    'original_hash': page.get('content_hash', ' ')
                })
        
        # Save results
        if unique_entries:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=unique_entries[0].keys())
                writer.writeheader()
                writer.writerows(unique_entries)
            
            print(f"Successfully processed {len(unique_entries)} unique records")
            print("Sample output:")
            for idx, entry in enumerate(unique_entries[:3]):
                print(f"\nEntry {idx+1}:")
                print(f"URL: {entry['url']}")
                print(f"Content: {entry['content'][:200]}...")
        else:
            print("No valid data found after cleaning")
            
    except Exception as e:
        print(f"Processing failed: {str(e)}")

if __name__ == '__main__':
    process_data(
        input_file='full_coverage_data.json',
        output_file='final_cleaned_output.csv'
    )
