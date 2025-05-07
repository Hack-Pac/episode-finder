#!/usr/bin/env python3
"""
Check which Seinfeld script URLs are still valid on seinfeldscripts.com
and generate an updated episode list.
"""

import os
import re
import time
import json
import logging
import requests
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urljoin

# Import the episode list from our download script
try:
    from download_scripts_improved import EPISODES, BASE_URL
except ImportError:
    try:
        from download_scripts_direct import EPISODES, BASE_URL
    except ImportError:
        # Fallback if both imports fail
        BASE_URL = "https://www.seinfeldscripts.com/"
        EPISODES = []  # Will need to define manually if import fails

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path("data/scripts")
VALID_EPISODES_FILE = OUTPUT_DIR / "valid_episodes.json"
REPORT_FILE = OUTPUT_DIR / "url_check_report.txt"

def get_page_status(url, timeout=5):
    """
    Check if a URL exists without downloading the full content
    Returns: (status_code, exists)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        # Some servers don't support HEAD, try GET if we get a 405 Method Not Allowed
        if response.status_code == 405:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            # Close the connection without downloading the full content
            response.close()
        return response.status_code, response.status_code == 200
    except requests.RequestException as e:
        logger.warning(f"Error checking {url}: {e}")
        return None, False

def check_all_episodes():
    """Check all episode URLs and build a new valid episode list"""
    valid_episodes = []
    invalid_urls = []
    
    # Ensure output directory exists
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
    
    # Check each URL and track valid/invalid ones
    total_episodes = sum(len(episodes) for _, episodes in EPISODES)
    with tqdm(total=total_episodes, desc="Checking URLs") as pbar:
        for season_name, episodes in EPISODES:
            valid_season_episodes = []
            
            for script_file, episode_title in episodes:
                url = urljoin(BASE_URL, script_file.strip())
                
                # Check if URL is valid (with a small delay to avoid rate limiting)
                status_code, exists = get_page_status(url)
                time.sleep(0.5)  # Delay between requests
                
                if exists:
                    valid_season_episodes.append((script_file, episode_title))
                    logger.debug(f"Valid URL: {url}")
                else:
                    invalid_urls.append((season_name, episode_title, script_file, status_code))
                    logger.debug(f"Invalid URL: {url} (Status: {status_code})")
                
                pbar.update(1)
            
            # Add season to valid episodes if it has any valid episodes
            if valid_season_episodes:
                valid_episodes.append((season_name, valid_season_episodes))
    
    # Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("Seinfeld Scripts URL Check Report\n")
        f.write("================================\n\n")
        f.write(f"Total URLs checked: {total_episodes}\n")
        f.write(f"Valid URLs: {total_episodes - len(invalid_urls)}\n")
        f.write(f"Invalid URLs: {len(invalid_urls)}\n\n")
        
        if invalid_urls:
            f.write("Invalid URLs:\n")
            for season, title, script_file, status in invalid_urls:
                f.write(f"- [{season}] {title} ({script_file}) - Status: {status}\n")
    
    # Save valid episodes as JSON for easy importing
    with open(VALID_EPISODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_episodes, f, indent=2)
    
    logger.info(f"URL check completed. Results saved to {REPORT_FILE}")
    logger.info(f"Valid episodes list saved to {VALID_EPISODES_FILE}")
    
    # Print summary
    print(f"\nURL Check Summary:")
    print(f"Total URLs checked: {total_episodes}")
    print(f"Valid URLs: {total_episodes - len(invalid_urls)}")
    print(f"Invalid URLs: {len(invalid_urls)}")
    print(f"\nDetailed report saved to {REPORT_FILE}")
    
    return valid_episodes, invalid_urls

def search_alternative_urls(episode_title, season):
    """Search for alternative URLs for a given episode title"""
    # This is a placeholder - in a real implementation, this would:
    # 1. Access the website's main index page
    # 2. Parse all links to find matches for this episode
    # 3. Return any alternative URLs found
    #
    # For now, we just return a formatted "possible" URL based on the title
    title_slug = episode_title.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return f"The{title_slug.title().replace(' ', '')}.htm"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check valid Seinfeld script URLs')
    parser.add_argument('--search-alternatives', action='store_true', 
                        help='Search for alternative URLs for invalid episodes')
    
    args = parser.parse_args()
    
    logger.info("Starting Seinfeld scripts URL verification")
    valid_episodes, invalid_urls = check_all_episodes()
    
    if args.search_alternatives and invalid_urls:
        # This would be implemented in a full solution
        logger.info("Searching for alternative URLs for invalid episodes")
        print("\nThis feature is not yet implemented.")
