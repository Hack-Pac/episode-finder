#!/usr/bin/env python3
"""
Script to download the remaining missing Seinfeld scripts.
This script uses the information found in previous searches to try
downloading the missing episodes using alternative URLs.
"""

import os
import re
import time
import random
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import json
import urllib.parse
from datetime import datetime
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = Path("data/scripts")
DELAY_MIN = 1.0  # Minimum delay between requests in seconds
DELAY_MAX = 3.0  # Maximum delay between requests in seconds
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
]

# Episodes that are still missing with their potential URLs
MISSING_EPISODES = [
    {
        "name": "The Fatigues",
        "season": "Season 8",
        "urls": [
            "TheFatigues.htm",
            "TheFatigues.html",
            "Fatigues.htm",
            "The-Fatigues.htm"
        ]
    },
    {
        "name": "The Susie",
        "season": "Season 8",
        "urls": [
            "TheSusie.htm",
            "TheSusie.html",
            "Susie.htm",
            "The-Susie.htm",
            "TheSuzy.htm",
            "TheSuzy.html",
            "Suzy.htm",
            "The-Suzy.htm"
        ]
    },
    {
        "name": "The Dealership",
        "season": "Season 9",
        "urls": [
            "TheDealership.htm",
            "TheDealership.html",
            "Dealership.htm",
            "The-Dealership.htm"
        ]
    },
    {
        "name": "The Strongbox",
        "season": "Season 9",
        "urls": [
            "TheStrongbox.htm",
            "TheStrongbox.html",
            "TheStrongBox.htm",
            "TheStrongBox.html",
            "Strongbox.htm",
            "StrongBox.htm",
            "The-Strongbox.htm",
            "The-Strong-Box.htm"
        ]
    },
    {
        "name": "The Little Jerry",
        "season": "Season 8",
        "urls": [
            "TheLittleJerry.htm",
            "TheLittleJerry.html",
            "LittleJerry.htm",
            "The-Little-Jerry.htm"
        ]
    },
    {
        "name": "The Money",
        "season": "Season 8",
        "urls": [
            "TheMoney.htm",
            "TheMoney.html",
            "Money.htm",
            "The-Money.htm"
        ]
    },
    {
        "name": "The Andrea Doria",
        "season": "Season 8",
        "urls": [
            "TheAndreaDoria.htm",
            "TheAndreaDoria.html",
            "Andrea-Doria.htm",
            "AndreaDoria.htm",
            "The-Andrea-Doria.htm"
        ]
    },
    {
        "name": "The Pimple",
        "season": "Season 3",
        "urls": [
            "ThePimple.htm",
            "ThePimplesEpisode.htm",  # Variation
            "TheBubbleBoy.htm",       # Alternative name
        ]
    },    {
        "name": "The Show",
        "season": "Season 4",
        "urls": [
            "TheShow.htm",
            "TheShowEpisode.htm",
            "ThePilot1.htm",          # Alternative name
            "TheDay.htm",             # Another alternative (The Pilot/The Day) - Season 4 finale
            "ThePilot.htm",           # Simple alternative name
            "TheMoviePart1.htm",      # Another potential alias
            "TheMoviePart2.htm",      # Another potential alias
            "TheMovie.htm",           # Another potential alias
        ]
    },
    {
        "name": "The Handlebar",
        "season": "Season 4",
        "urls": [
            "TheHandleBar.htm",
            "TheHandlebar.htm",
            "TheBeard.htm",           # Alternative name
            "TheOldMan.htm",          # Another alternative
        ]
    },    {
        "name": "The Dip",
        "season": "Season 6",
        "urls": [
            "TheDip.htm",
            "TheDipArea.htm",
            "TheSeven.htm",           # Alternative name
            "TheRanch.htm",           # Another alternative name
            "ThePool.htm",            # Another possible name
            "TheBigSalad.htm",        # Season 6 episode, might be mislabeled
            "TheSponge.htm",          # Season 6 episode, might be mislabeled
            "TheSecretCode.htm",      # Season 6 episode, might be mislabeled
            "TheSwitch.htm",          # Season 6 episode, might be mislabeled
        ]
    },    {
        "name": "The Cadillac",
        "season": "Season 8",
        "urls": [
            "TheCadillac1.html",      # Part 1
            "TheCadillac2.html",      # Part 2
        ]
    },
    {
        "name": "The Comeback",
        "season": "Season 8",
        "urls": [
            "TheComeback.htm",
            "TheComeback.html",
            "Comeback.htm",
            "The-Comeback.htm"
        ]
    },
    {
        "name": "The Van Buren Boys",
        "season": "Season 8",
        "urls": [
            "TheVanBurenBoys.htm",
            "TheVanBurenBoys.html",
            "VanBurenBoys.htm",
            "The-Van-Buren-Boys.htm"
        ]
    },
    {
        "name": "The Susie",
        "season": "Season 8",
        "urls": [
            "TheSusie.htm",
            "TheSusie.html",
            "Susie.htm",
            "The-Susie.htm"
        ]
    },
    {
        "name": "The Bookstore",
        "season": "Season 9",
        "urls": [
            "TheBookstore.htm",
            "TheBookstore.html",
            "Bookstore.htm",
            "The-Bookstore.htm"
        ]
    },    {
        "name": "The Frogger",
        "season": "Season 9",
        "urls": [
            "TheFrogger.htm",
            "TheFrogger.html",
            "Frogger.htm",
            "The-Frogger.htm"
        ]
    },
    {
        "name": "The Finale",
        "season": "Season 9",
        "urls": [
            "TheFinale.htm",
            "TheFinale.html",
            "TheFinale1.htm",
            "TheFinale1.html",
            "TheFinale2.htm", 
            "TheFinale2.html",
            "The-Finale.htm",
            "The-Finale-1.htm",
            "The-Finale-2.htm"
        ]
    },
]

def get_random_headers():
    """Generate random headers for requests to avoid being blocked"""
    user_agent = random.choice(USER_AGENTS)
    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def get_script_content(url):
    """
    Fetch script content from URL with error handling and retries
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Get random delay and headers
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            if attempt > 0:
                time.sleep(delay * 2)  # Additional delay for retries
                
            # Make request with random headers
            headers = get_random_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Return content if successful
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None
    
    return None

def clean_script_content(html_content, url):
    """Clean up HTML content to extract script text"""
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts, styles, and other unwanted elements
    for element in soup(['script', 'style', 'meta', 'link', 'iframe']):
        element.decompose()
    
    # Extract title if present
    title = "Unknown Episode"
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
        title = re.sub(r'Seinfeld Scripts\s*[-|:]\s*', '', title)
        title = title.strip()
    
    # Get the text content
    text_content = soup.get_text(separator='\n', strip=True)
    
    # Remove duplicate lines and clean up spacing
    lines = text_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and (not cleaned_lines or line not in cleaned_lines[-3:]):  # Avoid very recent duplicates
            cleaned_lines.append(line)
    
    # Join and clean final output
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # Replace 3+ consecutive newlines with 2
    
    # Prepend metadata
    metadata = [
        f"Title: {title}",
        f"Season: {title.split('(')[0].strip() if '(' in title else 'Unknown Season'}",
        f"URL: {url}",
        f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    return '\n'.join(metadata) + '\n' + cleaned_text

def download_missing_episodes():
    """
    Try to download all missing episodes using the list of alternative URLs
    """
    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each missing episode
    for episode in tqdm(MISSING_EPISODES, desc="Processing episodes"):
        episode_name = episode["name"]
        season_dir = OUTPUT_DIR / episode["season"]
        episode_file = season_dir / f"{episode_name}.txt"
        
        # Check if episode file already exists
        if episode_file.exists():
            logger.info(f"Episode '{episode_name}' already exists at {episode_file}")
            results["skipped"].append({
                "name": episode_name,
                "season": episode["season"],
                "reason": "File already exists"
            })
            continue
            
        # Create season directory if needed
        season_dir.mkdir(exist_ok=True)
        
        # Try each URL for this episode
        episode_found = False
        
        for url_path in episode["urls"]:
            if episode_found:
                break
                
            url = urllib.parse.urljoin(BASE_URL, url_path)
            logger.info(f"Trying URL: {url} for '{episode_name}'")
            
            html_content = get_script_content(url)
            if not html_content:
                continue
                  # Process the script content
            script_content = clean_script_content(html_content, url)
            if not script_content:
                continue
                
            # Check if it looks like a valid script (at least 100 words)
            if len(script_content.split()) < 100:
                logger.warning(f"Content from {url} seems too short to be a script")
                continue
                
            # If we reach here, we have a valid script
            try:
                # Special handling for multi-part episodes
                if "Cadillac" in episode_name and "1" in url_path:
                    output_file = season_dir / f"{episode_name} (Part 1).txt"
                elif "Cadillac" in episode_name and "2" in url_path:
                    output_file = season_dir / f"{episode_name} (Part 2).txt"
                else:
                    output_file = episode_file
                
                # Save the script content
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                    
                logger.info(f"Successfully downloaded '{episode_name}' from {url}")
                
                # For multi-part episodes, continue checking other URLs
                if "Cadillac" in episode_name:
                    continue  # Keep checking for other parts
                
                # Mark episode as found for single episodes
                episode_found = True
                results["success"].append({
                    "name": episode_name,
                    "season": episode["season"],
                    "url": url,
                    "file": str(output_file)
                })
                
            except Exception as e:
                logger.error(f"Error saving script for '{episode_name}': {e}")
        
        # After trying all URLs, check if episode was found
        if not episode_found:
            logger.warning(f"Failed to download '{episode_name}' - all URLs failed")
            results["failed"].append({
                "name": episode_name,
                "season": episode["season"],
                "tried_urls": episode["urls"]
            })
    
    # Generate summary report
    summary_file = OUTPUT_DIR / "download_remaining_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Remaining Episodes Download Summary\n")
        f.write("==================================\n\n")
        
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Successfully downloaded: {len(results['success'])}\n")
        for episode in results["success"]:
            f.write(f"- {episode['name']} ({episode['season']})\n")
            f.write(f"  Source: {episode['url']}\n")
            f.write(f"  Saved to: {episode['file']}\n\n")
        
        f.write(f"Failed to download: {len(results['failed'])}\n")
        for episode in results["failed"]:
            f.write(f"- {episode['name']} ({episode['season']})\n")
            f.write(f"  Tried URLs: {', '.join(episode['tried_urls'])}\n\n")
            
        f.write(f"Skipped (already exist): {len(results['skipped'])}\n")
        for episode in results["skipped"]:
            f.write(f"- {episode['name']} ({episode['season']})\n")
    
    logger.info(f"Download summary saved to {summary_file}")
    return results

def check_episode_status():
    """
    Check which episodes were successfully downloaded and which are still missing
    """
    status = {
        "found": [],
        "missing": []
    }
    
    for episode in MISSING_EPISODES:
        name = episode["name"]
        season = episode["season"]
        episode_file = OUTPUT_DIR / season / f"{name}.txt"
        
        # For The Cadillac, check both parts
        if name == "The Cadillac":
            part1 = OUTPUT_DIR / season / f"{name} (Part 1).txt"
            part2 = OUTPUT_DIR / season / f"{name} (Part 2).txt"
            
            if part1.exists() and part2.exists():
                status["found"].append({
                    "name": name,
                    "season": season,
                    "files": [str(part1), str(part2)]
                })
            elif part1.exists():
                status["found"].append({
                    "name": f"{name} (Part 1)",
                    "season": season, 
                    "files": [str(part1)]
                })
                status["missing"].append({
                    "name": f"{name} (Part 2)",
                    "season": season
                })
            elif part2.exists():
                status["found"].append({
                    "name": f"{name} (Part 2)",
                    "season": season,
                    "files": [str(part2)]
                })
                status["missing"].append({
                    "name": f"{name} (Part 1)",
                    "season": season
                })
            else:
                status["missing"].append({
                    "name": name,
                    "season": season
                })
        else:
            if episode_file.exists():
                status["found"].append({
                    "name": name,
                    "season": season,
                    "files": [str(episode_file)]
                })
            else:
                status["missing"].append({
                    "name": name,
                    "season": season
                })
    
    # Print status report
    print("\n--- Episode Status Report ---")
    print(f"Found episodes: {len(status['found'])}")
    for ep in status["found"]:
        print(f"- {ep['name']} ({ep['season']})")
        
    print(f"\nStill missing: {len(status['missing'])}")
    for ep in status["missing"]:
        print(f"- {ep['name']} ({ep['season']})")
    
    return status

def main():
    """Main entry point"""
    logger.info("Starting download of remaining missing Seinfeld scripts")
    download_results = download_missing_episodes()
    
    logger.info("Checking episode status")
    status = check_episode_status()
    
    if status["missing"]:
        logger.warning(f"There are still {len(status['missing'])} episodes missing.")
    else:
        logger.info("All missing episodes have been successfully downloaded!")
    
if __name__ == "__main__":
    main()
