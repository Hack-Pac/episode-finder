#!/usr/bin/env python3
"""
Script to try multiple variations of URLs to download 'The Susie' episode
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
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = Path("data/scripts/Season 8")
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
]

# List of all possible URL variations to try for "The Susie"
url_variations = [
    "TheSusie.htm",
    "TheSusie.html",
    "Susie.htm",
    "Susie.html",
    "The-Susie.htm",
    "The-Susie.html",
    "TheSuzy.htm",
    "TheSuzy.html",
    "Suzy.htm",
    "Suzy.html",
    "The-Suzy.htm",
    "The-Suzy.html",
    "Suzie.htm",
    "Suzie.html",
    "TheSuzie.htm",
    "TheSuzie.html",
    "The-Suzie.htm",
    "The-Suzie.html",
    "ep149.htm",
    "ep149.html",
    "Episode149.htm",
    "Episode149.html",
    "Season8Ep14.htm",
    "Season8Ep14.html",
    "S08E14.htm",
    "S08E14.html",
    "Season8-Episode14.htm",
    "Season8-Episode14.html",
    "TheSusy.htm",
    "TheSusy.html"
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
            delay = random.uniform(1.0, 3.0)
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
    title = "The Susie"
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
        f"Season: Season 8",
        f"URL: {url}",
        f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    return '\n'.join(metadata) + '\n' + cleaned_text

def check_if_valid_script(text):
    """Check if the content is likely a valid script"""
    if not text:
        return False
    
    # Check for key indicators of a script
    script_indicators = ["JERRY", "ELAINE", "GEORGE", "KRAMER", "INT.", "EXT."]
    
    for indicator in script_indicators:
        if indicator in text:
            return True
    
    return False

def main():
    """Main function to try all variations"""
    logger.info("Starting search for 'The Susie' episode script")
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Try each URL variation
    for url_suffix in url_variations:
        full_url = BASE_URL + url_suffix
        logger.info(f"Trying URL: {full_url}")
        
        # Get content
        content = get_script_content(full_url)
        if not content:
            logger.warning(f"Failed to get content from {full_url}")
            time.sleep(1)  # Add delay to avoid hammering the server
            continue
        
        # Clean the content
        cleaned_content = clean_script_content(content, full_url)
        if not cleaned_content:
            logger.warning(f"Failed to clean content from {full_url}")
            continue
        
        # Check if it's a valid script
        if check_if_valid_script(cleaned_content):
            output_file = OUTPUT_DIR / "The Susie.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            logger.info(f"Successfully downloaded 'The Susie' from {full_url}")
            logger.info(f"Saved to {output_file}")
            return True
        else:
            logger.warning(f"Content from {full_url} doesn't appear to be a valid script")
    
    logger.error("Failed to find a valid script for 'The Susie' after trying all variations")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
