import csv
import re
import hashlib
from bs4 import BeautifulSoup

# Configure CSV field size limit
csv.field_size_limit(2147483647)  # Windows-compatible maximum

# Combined regex pattern for technical code removal
TECHNICAL_PATTERNS = re.compile(
    r'(<\/?script.*?>|<\/?style.*?>|'
    r'var\s+\w+\s*=.*?;|'
    r'jQuery\(document\)\.ready\(.*?\);|'
    r'counter_[0-9a-f]+\.\w+|'
    r'particlesJS\(.*?\);|'
    r'revapi\d+\.show\.revolution\(.*?\);|'
    r'if\(htmlDiv\).*?childNodes\[0\]\)|'
    r'setREVStartSize\(.*?\);|'
    r'\.vc_cta3_content-container.*?\{.*?\}|'
    r'\/\*.*?\*\/|'
    r'\/\/.*?$|'
    r'\{.*?\})',
    re.DOTALL | re.IGNORECASE
)

# Exact text to remove (provided by you)
UNWANTED_TEXT = (
    "contact us ihtmlDiv.htmlDiv.innerHTML htmlDiv.innerHTML htmlDiv.css else htmlDiv.innerHTML document.getElementByIdElementsByTagNamehead().appendChildhtmlDiv.chidNotUsed ihtmlDiv.htmlDiv.innerHTML htmlDiv.innerHTML htmlDiv.css else htmlDiv.innerHTML document.getElementByIdElementsByTagNamehead().appendChildhtmlDiv.chidNotUsed setREVStartSince jQueryrev_slider_4_1, gridwidth 1170, gridheight 574, sliderLayout fullscreen, fullScreenAutoWidthoff, fullScreenAlignFroceroff, fullScreenOffsetContainer, fullScreenOffset var revap14, tpjjQuery tpjdocument.readyfunction iftpjrev_slider_4_1.revolution undefined revslider_showDolobledqueryErrorrev_slider_4_1 else revap14 tpjrev_slider_4_1.show.revolution sliderTypesstandard, jsFileLocationwww.appsgenii.comwp-content/uploads/revsliderpublicassetsjs, sliderLayoutfullscreen, dottedOverlaynone, delay9000, navigation keyboardNavigationoff, keyboard_direction horizontal, mouseScrollNavigationoff, mouseScrollReversedefault, onMoveStopOff, arrows style, enabletrue, hide_onmobilefalse, hide_onleavefalse, tmp_left h_alignleft, v_aligncenter, h_offset210, v_offset0, right h_alignright, v_aligncenter, h_offset210, v_offset0, visibility:level:1240,1024,778,480, gridwidth1170, gridheight574, lazyTypenone, shadow0, spinnerspinner0, stopLoopOff, stopAfterLoops-1, stopAtSide-1, shiftfleeff, autoHeightoff, fullScreenAutoWidthoff, fullScreenAlignFroceroff, fullScreenOffsetContainer, fullScreenOffset, disableProgressBaron, hideThumbOnMobileoff, hideSliderAttim10, hideCaptionAttim10, hideAllCaptionAttim10, debugModeFalse, fallbacks simplifyMidOff, nextSlideOnWindowFocusoff, disableFocusListenerFalse, ihtmlDiv.htmlDiv.innerHTML htmlDiv.innerHTML htmlDiv.css else htmlDiv.innerHTML document.getElementByIdElementsByTagNamehead().appendChildhtmlDiv.chidNotUsed particles_67dab947d6237 position absolute top 0 left 0 right 0 bottom 0.vc_c13_content-container position relative jQuerydocument.readyfunction ifscreenWidth 1140 else particles_67dab947d6237 css width screenWidth px, margin-left - marginleft px"
)

# Regex pattern to remove the exact unwanted text
REMOVE_PATTERN = re.compile(re.escape(UNWANTED_TEXT), re.DOTALL | re.IGNORECASE)

def clean_content(text):
    """Multi-layer content cleaning with error handling"""
    try:
        if not isinstance(text, str) or not text.strip():
            return text

        # Remove unwanted specific text using regex
        text = REMOVE_PATTERN.sub('', text)
        
        # Remove HTML tags and attributes
        soup = BeautifulSoup(text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'link', 'meta', 'noscript']):
            tag.decompose()
        
        # Remove inline attributes
        for tag in soup.find_all(True):
            for attr in ['style', 'class', 'id', 'onclick', 'hidden']:
                if attr in tag.attrs:
                    del tag[attr]
        
        # Convert to text
        cleaned = soup.get_text(separator=' ', strip=True)
        
        # Remove technical patterns
        cleaned = TECHNICAL_PATTERNS.sub('', cleaned)
        
        # Final cleanup - normalize spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
        
    except Exception as e:
        print(f"Cleaning error: {str(e)}")
        return text

def process_csv(input_path, output_path):
    """Process CSV with complete cleaning and deduplication"""
    seen_hashes = set()
    cleaned_rows = []  # Store cleaned rows temporarily
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        for row in reader:
            # Clean all fields
            cleaned_row = {
                k: clean_content(v) if isinstance(v, str) else v
                for k, v in row.items()
            }
            
            # Create content-based hash
            content_hash = hashlib.sha256(
                str(sorted(cleaned_row.items())).encode()
            ).hexdigest().lower()  # Make the hash comparison case-insensitive
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                cleaned_rows.append(cleaned_row)
                print(f"Processed: {cleaned_row.get('url', 'N/A')}")
    
    # Write all cleaned rows to the output CSV file
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

if __name__ == '__main__':
    INPUT_CSV = 'crashed.csv'
    OUTPUT_CSV = 'cleaned_data.csv'
    
    try:
        process_csv(INPUT_CSV, OUTPUT_CSV)
        print("\nCleaning completed successfully!")
        print(f"Output saved to: {OUTPUT_CSV}")
    except Exception as e:
        print(f"\nProcessing failed: {str(e)}")