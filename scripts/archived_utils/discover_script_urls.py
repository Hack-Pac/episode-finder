#!/usr/bin/env python3
"""
Scrape the seinfeldscripts.com website to find all available script URLs.
This helps identify the correct URLs for episodes that fail to download.
"""

import os
import re
import json
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
INDEX_URL = urljoin(BASE_URL, "seinfeld-scripts.html")
OUTPUT_DIR = Path("data/scripts")
DISCOVERED_URLS_FILE = OUTPUT_DIR / "discovered_urls.json"
REPORT_FILE = OUTPUT_DIR / "url_discovery_report.txt"

def get_page_content(url):
    """Get HTML content from a URL with error handling"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def find_all_script_links():
    """Find all script links on the website"""
    logger.info(f"Fetching index page from {INDEX_URL}")
    
    # Ensure output directory exists
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
    
    # Get the index page
    index_html = get_page_content(INDEX_URL)
    if not index_html:
        logger.error(f"Failed to fetch index page")
        return None
    
    # Save the index page for debugging
    with open(OUTPUT_DIR / "index_debug.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # Parse the index page
    soup = BeautifulSoup(index_html, 'html.parser')
    
    # Find all links and filter for potential script pages
    all_links = []
    script_links = []
    
    # Pattern for script URLs - typically like "TheContest.htm"
    script_pattern = re.compile(r'The[A-Za-z0-9-]+\.html?$')
    
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')
        text = a_tag.get_text().strip()
        if href and not href.startswith(('http://', 'https://', 'mailto:')):
            # Make URL absolute
            full_url = urljoin(BASE_URL, href)
            all_links.append((text, href, full_url))
            
            # Check if it's likely a script page
            if script_pattern.search(href) or "Episode" in href:
                script_links.append({
                    "title": text,
                    "url": href,
                    "full_url": full_url
                })
    
    # Save discovered links
    link_data = {
        "all_links": all_links,
        "script_links": script_links
    }
    
    with open(DISCOVERED_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(link_data, f, indent=2)
    
    # Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("Seinfeld Scripts URL Discovery Report\n")
        f.write("===================================\n\n")
        f.write(f"Total links found: {len(all_links)}\n")
        f.write(f"Potential script links found: {len(script_links)}\n\n")
        
        f.write("Script Links:\n")
        for link in sorted(script_links, key=lambda x: x['title']):
            f.write(f"- {link['title']}: {link['url']}\n")
    
    logger.info(f"Found {len(script_links)} potential script links")
    logger.info(f"Results saved to {DISCOVERED_URLS_FILE}")
    logger.info(f"Report saved to {REPORT_FILE}")
    
    return script_links

def find_episode_alternatives(episode_title, all_scripts):
    """Find alternative URLs for a specific episode title"""
    possibilities = []
    
    # Normalize the title for better matching
    norm_title = episode_title.lower().replace('the ', '')
    
    for script in all_scripts:
        # Check if the script title might match the episode
        script_title = script['title'].lower().replace('the ', '')
        
        # Check for similarity
        if (norm_title in script_title or script_title in norm_title or
            (len(norm_title) > 4 and any(w in script_title for w in norm_title.split() if len(w) > 3))):
            possibilities.append(script)
    
    return possibilities

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover available Seinfeld script URLs')
    parser.add_argument('--search', type=str, help='Search for a specific episode')
    
    args = parser.parse_args()
    
    logger.info("Starting Seinfeld scripts URL discovery")
    all_scripts = find_all_script_links()
    
    if args.search and all_scripts:
        print(f"\nSearching for alternatives for '{args.search}':")
        alternatives = find_episode_alternatives(args.search, all_scripts)
        
        if alternatives:
            print(f"Found {len(alternatives)} possible matches:")
            for alt in alternatives:
                print(f"- {alt['title']}: {alt['url']}")
        else:
            print("No alternatives found")
















