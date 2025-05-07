#!/usr/bin/env python3
"""
Script to download Seinfeld episode scripts from seinfeldscripts.com
and organize them by season/category in the data/scripts directory.
"""
import os
import re
import time
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.parse
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
SCRIPTS_INDEX_URL = "https://www.seinfeldscripts.com/seinfeld-scripts.html"
OUTPUT_DIR = Path("data/scripts")
DELAY = 1  # Delay between requests to avoid overloading the server (in seconds)

def sanitize_filename(filename):
    """Convert a string to a valid filename"""
    # Replace invalid characters with underscores
    valid_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Remove leading/trailing spaces and dots
    valid_filename = valid_filename.strip(". ")
    return valid_filename

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not path.exists():
        path.mkdir(parents=True)
        logger.info(f"Created directory: {path}")

def get_page_content(url):
    """Get HTML content from a URL with error handling and retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(DELAY * 2)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

def extract_script_links(html_content):
    """Extract script links and organize them into categories/seasons"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Dictionary to store categories/seasons and their links
    categories = {}
    current_category = "Uncategorized"
    
    # The site appears to be using tables for layout
    # Find tables that might contain our content
    tables = soup.find_all('table')
    
    if not tables:
        logger.error("Could not find any tables on the scripts page")
        return categories
    
    # Process each table to find script links
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            # Look for links in this row
            links = row.find_all('a')
            for link in links:
                href = link.get('href')
                title = link.text.strip()
                
                # Skip empty links or non-script links
                if not href or not title or href.startswith('#'):
                    continue
                
                # Try to determine the category from nearby text or table structure
                # For simplicity, we'll use the first part of the text if it contains season indicators
                if 'season' in title.lower():
                    parts = title.split(':')
                    if len(parts) > 1:
                        current_category = parts[0].strip()
                else:
                    # Look for a header nearby
                    prev_element = row.find_previous(['h1', 'h2', 'h3', 'h4', 'b', 'strong'])
                    if prev_element and prev_element.text.strip():
                        current_category = prev_element.text.strip()
                  # Construct absolute URL if it's relative
                if not href.startswith('http'):
                    # Fix spaces in URLs
                    href = href.strip()
                    href = urllib.parse.urljoin(BASE_URL, href)
                
                # Clean up any spaces in the URL and properly encode
                href = href.replace(' ', '')
                
                # Only include links that are likely to be script pages
                if 'seinfeldscripts.com' in href and href != SCRIPTS_INDEX_URL and '.htm' in href:
                    logger.debug(f"Found script: {title} in category: {current_category}")
                    categories.setdefault(current_category, []).append({
                        'url': href,
                        'title': title
                    })
    
    return categories

def extract_script_content(html_content):
    """Extract the actual script content from a script page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find the content in several ways since the site structure might vary
    
    # 1. First try to find main content areas
    content = None
    content_candidates = [
        soup.find('div', class_='content'),  # Try class='content'
        soup.find('div', id='content'),      # Try id='content'
        soup.find('body')                    # Fall back to body if needed
    ]
    
    for candidate in content_candidates:
        if candidate:
            content = candidate
            break
            
    if not content:
        return "Could not find script content"
    
    # 2. Now extract the text - considering multiple formats
    script_content = ""
    
    # Try to find the script in pre tags first (formatted scripts)
    pre_tags = content.find_all('pre')
    if pre_tags:
        for pre in pre_tags:
            script_content += pre.get_text() + "\n\n"
    else:
        # Otherwise try to get text from paragraphs
        paragraphs = content.find_all(['p', 'div', 'font'])
        if paragraphs:
            for p in paragraphs:
                # Skip navigation or header paragraphs
                if any(x in p.get_text().lower() for x in ['home', 'scripts', 'episodes', 'next', 'previous']):
                    if len(p.get_text()) < 100:  # Skip only if it's a short nav element
                        continue
                script_content += p.get_text().strip() + "\n\n"
        else:
            # Last resort: just get all text
            script_content = content.get_text()
    
    # Clean up the script content
    script_content = re.sub(r'\n{3,}', '\n\n', script_content)  # Remove excessive newlines
    
    return script_content.strip()

def download_and_save_scripts():
    """Main function to download and organize scripts"""
    # Create the base output directory
    create_directory(OUTPUT_DIR)
    
    # Get the index page with all script links
    logger.info(f"Fetching script index from {SCRIPTS_INDEX_URL}")
    index_html = get_page_content(SCRIPTS_INDEX_URL)
    if not index_html:
        logger.error("Failed to retrieve the script index page")
        return False
    
    # For debugging, save the raw HTML
    debug_html_path = OUTPUT_DIR / "index_debug.html"
    with open(debug_html_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    logger.info(f"Saved debug HTML to {debug_html_path}")
    
    # Extract links organized by category/season
    categories = extract_script_links(index_html)
    if not categories:
        logger.error("No script links found")
        return False
    
    # Display found categories
    logger.info(f"Found {len(categories)} categories of scripts")
    for category, links in categories.items():
        logger.info(f"Category: {category} - {len(links)} scripts")
    
    # Download each script
    total_scripts = sum(len(links) for links in categories.values())
    scripts_downloaded = 0
    scripts_failed = 0
    
    with tqdm(total=total_scripts, desc="Downloading scripts") as pbar:
        for category, links in categories.items():
            # Create category directory
            category_dir = OUTPUT_DIR / sanitize_filename(category)
            create_directory(category_dir)
            
            for link in links:
                # Sleep to avoid hammering the server
                time.sleep(DELAY)
                
                try:
                    url = link['url']
                    title = link['title']
                    file_name = f"{sanitize_filename(title)}.txt"
                    file_path = category_dir / file_name
                    
                    # Skip if already downloaded
                    if file_path.exists():
                        logger.debug(f"Script already exists: {file_path}")
                        scripts_downloaded += 1
                        pbar.update(1)
                        continue
                    
                    # Get script content
                    logger.debug(f"Downloading script: {title} from {url}")
                    html_content = get_page_content(url)
                    if not html_content:
                        logger.error(f"Failed to download {title}")
                        scripts_failed += 1
                        pbar.update(1)
                        continue
                    
                    # Extract script text
                    script_content = extract_script_content(html_content)
                    
                    # Save script to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    
                    scripts_downloaded += 1
                    logger.debug(f"Saved script: {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing script {link.get('title', 'Unknown')}: {e}")
                    scripts_failed += 1
                
                pbar.update(1)
    
    logger.info(f"Download complete. {scripts_downloaded} scripts downloaded, {scripts_failed} failed.")
    return True

if __name__ == "__main__":
    logger.info("Starting Seinfeld scripts download")
    success = download_and_save_scripts()
    if success:
        logger.info("Script download completed successfully")
    else:
        logger.error("Script download failed")
