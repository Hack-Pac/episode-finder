#!/usr/bin/env python3
"""
Script to download only the previously missing Seinfeld scripts
"""

import os
import requests
from pathlib import Path
import urllib.parse
import time
from bs4 import BeautifulSoup
import logging
import sys
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = Path("data/scripts")
DELAY = 1  # Delay between requests

# Previously missing episodes with corrected URLs
MISSING_EPISODES = [
    # Season 3 - "The Pimple" was incorrect, should be "The Pez Dispenser"
    ("Season 3", "The Pez Dispenser", "ThePezDispenser.htm"),
    ("Season 3", "The Pez Dispenser", "ThePezDispenser.html"),
    
    # Season 4 - "The Show" was incorrect, should be "The Movie"
    ("Season 4", "The Movie", "TheMovie.htm"),
    ("Season 4", "The Movie", "TheMovie.html"),
    
    # Season 4 - "The Handlebar" was incorrect, should be "The Old Man"
    ("Season 4", "The Old Man", "TheOldMan.htm"),
    ("Season 4", "The Old Man", "TheOldMan.html"),
    
    # Season 6 - Special episode "Highlights of 100"
    ("Season 6", "Highlights of a Hundred", "TheHighlightsofaHundred.htm"),
    ("Season 6", "Highlights of a Hundred", "The-Clip-Show-1.html"),
    
    # Season 6 - "The Dip" was incorrect, should be "The Diplomat's Club"
    ("Season 6", "The Diplomat's Club", "TheDiplomatClub.htm"),
    ("Season 6", "The Diplomat's Club", "TheDiplomatClub.html"),
    
    # Season 7 - Additional variations for The Cadillac
    ("Season 7", "The Cadillac (Part 1)", "TheCadillac1.html"),
    ("Season 7", "The Cadillac (Part 1)", "TheCadillac1.htm"),
    ("Season 7", "The Cadillac (Part 2)", "TheCadillac2.html"),
    ("Season 7", "The Cadillac (Part 2)", "TheCadillac2.htm"),
    
    # Season 6 - The Switch
    ("Season 6", "The Switch", "TheSwitch.htm"),
    ("Season 6", "The Switch", "TheSwitch.html"),
    
    # Season 6 - The Fusilli Jerry
    ("Season 6", "The Fusilli Jerry", "TheFusilliJerry.htm"),
    ("Season 6", "The Fusilli Jerry", "TheFusilliJerry.html")
]

def sanitize_filename(filename):
    """Convert a string to a valid filename"""
    # Replace invalid characters with underscores
    valid_filename = filename.replace('/', '_').replace('\\', '_').replace('*', '_') \
        .replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_') \
        .replace('|', '_').replace(':', '_')
    # Remove leading/trailing spaces and dots
    valid_filename = valid_filename.strip(". ")
    return valid_filename

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not path.exists():
        path.mkdir(parents=True)
        logger.info(f"Created directory: {path}")

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

def extract_script_content(html_content):
    """Extract the actual script content from a script page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main content
    content = None
    content_candidates = [
        soup.find('div', class_='content'),  # Try class='content'
        soup.find('div', id='content'),      # Try id='content'
        soup.find('pre'),                    # Some scripts are just in a pre tag
        soup.find('body')                    # Fall back to body if needed
    ]
    
    for candidate in content_candidates:
        if candidate:
            content = candidate
            break
            
    if not content:
        return "Could not find script content"
    
    # Extract the text
    script_content = ""
    
    # Try to find pre tags first (formatted scripts)
    pre_tags = content.find_all('pre')
    if pre_tags:
        for pre in pre_tags:
            script_content += pre.get_text() + "\n\n"
    else:
        # Try paragraphs
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
    
    # Clean up excessive newlines
    script_content = script_content.replace('\n\n\n\n', '\n\n')
    
    return script_content.strip()

def download_missing_scripts():
    """Download the previously missing episodes"""
    # Create the base output directory
    create_directory(OUTPUT_DIR)
    
    successful = []
    failed = []
    
    for season_name, episode_title, script_file in MISSING_EPISODES:
        # Create season directory
        season_dir = OUTPUT_DIR / sanitize_filename(season_name)
        create_directory(season_dir)
        
        # Build URL and filename
        url = urllib.parse.urljoin(BASE_URL, script_file)
        file_name = f"{sanitize_filename(episode_title)}.txt"
        file_path = season_dir / file_name
        
        # Get the content
        logger.info(f"Downloading: {episode_title} from {url}")
        html_content = get_page_content(url)
        
        if not html_content:
            logger.error(f"Failed to download {episode_title}")
            failed.append((season_name, episode_title, url))
            continue
            
        # Extract script content
        script_content = extract_script_content(html_content)
        
        # Check if content seems valid
        if len(script_content) < 500:
            logger.warning(f"Script content for {episode_title} seems too short ({len(script_content)} chars)")
            
        # Save script to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {episode_title}\n")
            f.write(f"Season: {season_name}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(script_content)
        
        logger.info(f"Saved script: {file_path}")
        successful.append((season_name, episode_title, url))
        
        # Delay to avoid overloading the server
        time.sleep(DELAY)
    
    # Generate summary report
    summary_file = OUTPUT_DIR / "missing_episodes_results.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Missing Seinfeld Scripts Download Summary\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total episodes attempted: {len(MISSING_EPISODES)}\n")
        f.write(f"Successfully downloaded: {len(successful)}\n")
        f.write(f"Failed: {len(failed)}\n\n")
        
        if successful:
            f.write("Successfully downloaded:\n")
            for season, title, url in successful:
                f.write(f"- [{season}] {title}: {url}\n")
            f.write("\n")
        
        if failed:
            f.write("Failed downloads:\n")
            for season, title, url in failed:
                f.write(f"- [{season}] {title}: {url}\n")
    
    logger.info(f"Download complete. {len(successful)} scripts downloaded, {len(failed)} failed.")
    return len(failed) == 0

if __name__ == "__main__":
    logger.info("Starting download of missing Seinfeld episodes...")
    try:
        download_missing_scripts()
        logger.info("Script completed successfully!")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        traceback.print_exc()
        sys.exit(1)
