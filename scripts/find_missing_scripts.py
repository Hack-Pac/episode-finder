#!/usr/bin/env python3
"""
Script to search for missing episode URLs on seinfeldscripts.com
"""

import os
import re
import logging
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
import urllib.parse
import time
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = "data/scripts"
DELAY = 1  # Delay between requests

# Missing episodes
MISSING_EPISODES = [
    ("The Pimple", "Season 3"),
    ("The Show", "Season 4"),
    ("The Handlebar", "Season 4"),
    ("The Junior Mint", "Season 4"),
    ("The Smelly Car", "Season 4"),
    ("Highlights of a Hundred", "Season 6"),
    ("The Dip", "Season 6"),
    ("The Cadillac", "Season 8")
]

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
                time.sleep(DELAY * 2)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

def extract_links_from_page(html_content):
    """Extract all links from an HTML page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '').strip()
        text = a_tag.get_text().strip()
        title = a_tag.get('title', '').strip() or text
        
        if href and (href.startswith('http') or not href.startswith('#')):
            # Normalize URL
            if not href.startswith('http'):
                href = urllib.parse.urljoin(BASE_URL, href)
                
            links.append((title, href))
    
    return links

def find_episode_links():
    """Find links for missing episodes"""
    logger.info("Searching for missing episode links...")
    results = {}
    
    # First get the main pages
    main_pages = [
        BASE_URL,  # Main page
        f"{BASE_URL}alpha.html",  # Alphabetical listing
        f"{BASE_URL}seinfeld-scripts.html",  # Scripts page
        f"{BASE_URL}episodes_oveview.html"   # Episodes overview
    ]
    
    all_links = []
    for page_url in tqdm(main_pages, desc="Checking pages"):
        logger.info(f"Checking {page_url} for links...")
        html_content = get_page_content(page_url)
        if html_content:
            page_links = extract_links_from_page(html_content)
            all_links.extend(page_links)
            logger.info(f"Found {len(page_links)} links on {page_url}")
        time.sleep(DELAY)
    
    # Look for variations of episode names
    for episode_name, season in MISSING_EPISODES:
        episode_results = []
        short_name = episode_name.replace("The ", "").strip()
        
        for title, url in all_links:
            # Check if the title contains the episode name (case insensitive)
            if (short_name.lower() in title.lower() or
                short_name.lower() in url.lower() or 
                episode_name.lower() in title.lower() or
                episode_name.lower() in url.lower()):
                
                episode_results.append({
                    'title': title,
                    'url': url,
                    'confidence': 'high' if episode_name.lower() in title.lower() else 'medium'
                })
        
        # Add to results
        if episode_results:
            results[f"{episode_name} ({season})"] = episode_results
            logger.info(f"Found {len(episode_results)} potential links for {episode_name}")
        else:
            logger.warning(f"No links found for {episode_name}")
            results[f"{episode_name} ({season})"] = []
    
    # Save results to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/missing_episodes_search.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate readable report
    with open(f"{OUTPUT_DIR}/missing_episodes_report.txt", 'w') as f:
        f.write("Missing Seinfeld Episodes Search Results\n")
        f.write("=======================================\n\n")
        
        for episode, links in results.items():
            f.write(f"{episode}:\n")
            if not links:
                f.write("  No links found\n\n")
                continue
                
            for i, link in enumerate(links, 1):
                f.write(f"  {i}. {link['title']} ({link['confidence']} confidence)\n")
                f.write(f"     URL: {link['url']}\n")
            f.write("\n")
    
    logger.info(f"Results saved to {OUTPUT_DIR}/missing_episodes_search.json and {OUTPUT_DIR}/missing_episodes_report.txt")
    return results

def search_scripts_index():
    """Search alphabetical scripts index page"""
    alpha_url = f"{BASE_URL}alpha.html"
    logger.info(f"Searching alphabetical index at {alpha_url}...")
    
    html_content = get_page_content(alpha_url)
    if not html_content:
        logger.error("Could not fetch alphabetical index page")
        return {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = {}
    
    # Find all links on the page
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '').strip()
        text = a_tag.get_text().strip()
        
        if href and not href.startswith('#'):
            # Normalize URL
            if not href.startswith('http'):
                href = urllib.parse.urljoin(BASE_URL, href)
            
            # Check if this matches any of our missing episodes
            for episode_name, season in MISSING_EPISODES:
                if (episode_name.lower() in text.lower() or
                    episode_name.replace("The ", "").strip().lower() in text.lower()):
                    
                    if f"{episode_name} ({season})" not in results:
                        results[f"{episode_name} ({season})"] = []
                    
                    results[f"{episode_name} ({season})"].append({
                        'title': text,
                        'url': href,
                        'confidence': 'high'
                    })
                    logger.info(f"Found match for {episode_name}: {text} at {href}")
    
    # Save results to file
    with open(f"{OUTPUT_DIR}/alpha_index_search.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate readable report
    with open(f"{OUTPUT_DIR}/alpha_index_report.txt", 'w') as f:
        f.write("Alphabetical Index Search Results\n")
        f.write("===============================\n\n")
        
        for episode, links in results.items():
            f.write(f"{episode}:\n")
            if not links:
                f.write("  No links found\n\n")
                continue
                
            for i, link in enumerate(links, 1):
                f.write(f"  {i}. {link['title']}\n")
                f.write(f"     URL: {link['url']}\n")
            f.write("\n")
    
    logger.info(f"Alpha index results saved to {OUTPUT_DIR}/alpha_index_search.json and {OUTPUT_DIR}/alpha_index_report.txt")
    return results

def try_common_variations():
    """Try common variations of episode names in URLs"""
    logger.info("Trying common URL variations for missing episodes...")
    results = {}
    
    for episode_name, season in MISSING_EPISODES:
        episode_results = []
        short_name = episode_name.replace("The ", "").strip()
        
        # Generate variations
        variations = []
        
        # Standard variations
        variations.append(f"The{short_name}.htm")
        variations.append(f"The{short_name}.html")
        
        # Remove spaces
        variations.append(f"The{short_name.replace(' ', '')}.htm")
        variations.append(f"The{short_name.replace(' ', '')}.html")
        
        # Replace spaces with underscore or dash
        variations.append(f"The{short_name.replace(' ', '_')}.htm")
        variations.append(f"The{short_name.replace(' ', '_')}.html")
        variations.append(f"The{short_name.replace(' ', '-')}.htm")
        variations.append(f"The{short_name.replace(' ', '-')}.html")
        
        # Try lowercase
        variations.append(f"the{short_name.lower().replace(' ', '')}.htm")
        variations.append(f"the{short_name.lower().replace(' ', '')}.html")
        
        # Try with episode prefix
        variations.append(f"episode-{short_name.lower().replace(' ', '-')}.htm")
        variations.append(f"episode-{short_name.lower().replace(' ', '-')}.html")
        # Special cases
        if episode_name == "The Junior Mint":
            variations.append("TheJuniorMint.htm")
            variations.append("TheJuniorMint.html")
            variations.append("TheJuniorMints.htm")  # Plural
            variations.append("TheJuniorMints.html") # Plural
        
        if episode_name == "The Smelly Car":
            variations.append("TheSmellyCar.htm")
            variations.append("TheSmellyCar.html")
            variations.append("TheSmellyCarEpisode.htm")
            variations.append("TheSmellyCarEpisode.html")
        
        if episode_name == "Highlights of a Hundred":
            variations.append("TheHighlights.htm")
            variations.append("TheHighlights.html")
            variations.append("Highlights100.htm")
            variations.append("Highlights100.html")
            variations.append("HighlightsOfAHundred.htm")
            variations.append("HighlightsOfAHundred.html")
        
        if episode_name == "The Cadillac":
            variations.append("TheCadillac.htm")
            variations.append("TheCadillac.html")
            variations.append("TheCadillac1.htm")
            variations.append("TheCadillac1.html")
            variations.append("TheCadillac2.htm")
            variations.append("TheCadillac2.html")
            variations.append("TheCadillacs.htm")
            variations.append("TheCadillacs.html")
        
        if episode_name == "The Handlebar":
            variations.append("TheOldMan.htm")  # It might be an alternate name
            variations.append("TheMoustache.htm")
            variations.append("TheMoustache.html")
            variations.append("TheHandlebarMoustache.htm")
            variations.append("TheHandlebarMoustache.html")
            
        if episode_name == "The Dip":
            variations.append("TheSeven.htm")  # Possible alternate name
            variations.append("TheSeven.html")
            variations.append("TheRanch.htm")  # Another possible alternate name
            variations.append("TheRanch.html")
        
        if episode_name == "The Show":
            variations.append("TheMoviePart1.htm")  # Could be related
            variations.append("TheMoviePart1.html")
            variations.append("TheMoviePart2.htm")
            variations.append("TheMoviePart2.html")
        
        # Check each variation
        logger.info(f"Trying {len(variations)} URL variations for {episode_name}")
        for var in tqdm(variations, desc=f"Checking {episode_name}"):
            url = urllib.parse.urljoin(BASE_URL, var)
            html_content = get_page_content(url)
            
            if html_content:
                logger.info(f"Success! Found valid URL for {episode_name}: {url}")
                episode_results.append({
                    'url': url,
                    'variation': var
                })
            
            time.sleep(DELAY)
        
        # Add to results
        results[f"{episode_name} ({season})"] = episode_results
    
    # Save results to file
    with open(f"{OUTPUT_DIR}/url_variations_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate readable report
    with open(f"{OUTPUT_DIR}/url_variations_report.txt", 'w') as f:
        f.write("URL Variations Search Results\n")
        f.write("===========================\n\n")
        
        for episode, urls in results.items():
            f.write(f"{episode}:\n")
            if not urls:
                f.write("  No working URLs found\n\n")
                continue
                
            for i, url_info in enumerate(urls, 1):
                f.write(f"  {i}. Variation: {url_info['variation']}\n")
                f.write(f"     URL: {url_info['url']}\n")
            f.write("\n")
    
    logger.info(f"URL variations results saved to {OUTPUT_DIR}/url_variations_results.json and {OUTPUT_DIR}/url_variations_report.txt")
    return results

def try_additional_names():
    """Try alternative names for the episodes from different sources"""
    logger.info("Searching for alternative episode names...")
    
    # Map of episodes to possible alternative names/URLs
    alternative_names = {
        "The Pimple": ["The Bubble Boy", "The Cheever Letters"],  # S3 episodes that might be mislabeled
        "The Show": ["The Pilot", "The Movie"],  # These might be alternative names
        "The Handlebar": ["The Beard", "The Statue"],  # Closest S4 episodes
        "The Junior Mint": ["The Junior Mints", "The Operation"],  # Common misspelling
        "The Smelly Car": ["The Car Smell", "The Odor"],  # Alternative phrasings
        "Highlights of a Hundred": ["The Highlights", "The Best Of", "The Clip Show"],  # Descriptive alternatives
        "The Dip": ["The Dip Area", "The Swimming Pool", "The Seven"],  # Possible related episodes
        "The Cadillac": ["The New Car", "The Luxury Car"]  # Alternative descriptions
    }
    
    results = {}
    
    for episode_name, season in MISSING_EPISODES:
        episode_results = []
        
        if episode_name in alternative_names:
            alt_names = alternative_names[episode_name]
            logger.info(f"Trying {len(alt_names)} alternative names for {episode_name}")
            
            for alt_name in alt_names:
                # Strip "The" if present and remove spaces
                alt_short = alt_name.replace("The ", "").replace(" ", "")
                
                # Try standard naming format
                url1 = urllib.parse.urljoin(BASE_URL, f"The{alt_short}.htm")
                url2 = urllib.parse.urljoin(BASE_URL, f"The{alt_short}.html")
                # Check first URL
                html_content = get_page_content(url1)
                if html_content:
                    logger.info(f"Success! Found possible match for {episode_name} using alt name {alt_name}: {url1}")
                    episode_results.append({
                        'url': url1,
                        'alternative_name': alt_name
                    })
                
                time.sleep(DELAY)
                
                # Check second URL
                html_content = get_page_content(url2)
                if html_content:
                    logger.info(f"Success! Found possible match for {episode_name} using alt name {alt_name}: {url2}")
                    episode_results.append({
                        'url': url2,
                        'alternative_name': alt_name
                    })
                
                time.sleep(DELAY)
        
        # Add to results
        results[f"{episode_name} ({season})"] = episode_results
    
    # Save results to file
    with open(f"{OUTPUT_DIR}/alternative_names_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate readable report
    with open(f"{OUTPUT_DIR}/alternative_names_report.txt", 'w') as f:
        f.write("Alternative Names Search Results\n")
        f.write("==============================\n\n")
        
        for episode, matches in results.items():
            f.write(f"{episode}:\n")
            if not matches:
                f.write("  No matches found using alternative names\n\n")
                continue
                
            for i, match in enumerate(matches, 1):
                f.write(f"  {i}. Alternative name: {match['alternative_name']}\n")
                f.write(f"     URL: {match['url']}\n")
            f.write("\n")
    
    logger.info(f"Alternative names results saved to {OUTPUT_DIR}/alternative_names_results.json")
    return results

def main():
    parser = argparse.ArgumentParser(description='Search for missing Seinfeld episode scripts')
    parser.add_argument('--all', action='store_true', help='Run all search methods')
    parser.add_argument('--find-links', action='store_true', help='Find links from main pages')
    parser.add_argument('--alpha-index', action='store_true', help='Search the alphabetical index')
    parser.add_argument('--variations', action='store_true', help='Try URL variations')
    parser.add_argument('--alt-names', action='store_true', help='Try alternative episode names')
    
    args = parser.parse_args()
    
    # If no specific methods selected, run all
    run_all = args.all or not (args.find_links or args.alpha_index or args.variations or args.alt_names)
    if run_all or args.find_links:
        find_episode_links()
    
    if run_all or args.alpha_index:
        search_scripts_index()
    
    if run_all or args.variations:
        try_common_variations()
    if run_all or args.alt_names:
        try_additional_names()
    
    logger.info("Search complete. Check the output files for results.")

if __name__ == "__main__":
    main()



















