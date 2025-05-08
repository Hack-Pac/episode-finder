#!/usr/bin/env python3
"""
Analyze the structure of the Seinfeld scripts website to help with scraping.
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEBUG_HTML_PATH = Path("data/scripts/index_debug.html")
OUTPUT_ANALYSIS = Path("data/scripts/site_analysis.txt")

def analyze_html_structure():
    """Analyze the HTML structure of the website"""
    if not DEBUG_HTML_PATH.exists():
        logger.error(f"Debug HTML file not found: {DEBUG_HTML_PATH}")
        return False
    
    # Read the HTML file
    with open(DEBUG_HTML_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create analysis file
    with open(OUTPUT_ANALYSIS, 'w', encoding='utf-8') as f:
        # 1. Page title
        f.write("=== PAGE TITLE ===\n")
        if soup.title:
            f.write(f"{soup.title.text.strip()}\n\n")
        else:
            f.write("No title found\n\n")
        
        # 2. All links (URLs and text) sorted by category
        f.write("=== ALL LINKS ===\n")
        all_links = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.strip()
            if href and text and not href.startswith('#'):
                all_links.append((href, text))
                f.write(f"{text} => {href}\n")
        f.write(f"\nTotal links found: {len(all_links)}\n\n")
        # 3. Table structure analysis - which seems to be where the content is
        f.write("=== TABLE STRUCTURE ===\n")
        tables = soup.find_all('table')
        f.write(f"Number of tables: {len(tables)}\n\n")
        
        for i, table in enumerate(tables):
            f.write(f"--- Table {i+1} ---\n")
            rows = table.find_all('tr')
            f.write(f"Number of rows: {len(rows)}\n")
            
            # Look at first 3 rows for example
            for j, row in enumerate(rows[:3]):
                f.write(f"Row {j+1} structure:\n")
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    cell_content = cell.get_text().strip().replace('\n', ' ')[:50]  # First 50 chars
                    f.write(f"  Cell content: {cell_content}...\n")
                    # Extract links in this cell
                    cell_links = cell.find_all('a')
                    for link in cell_links:
                        href = link.get('href', '')
                        text = link.text.strip()
                        if href and text:
                            f.write(f"    Link: {text} => {href}\n")
            
            f.write("\n")
    
    logger.info(f"Analysis completed and saved to {OUTPUT_ANALYSIS}")
    return True
if __name__ == "__main__":
    logger.info("Starting Seinfeld website HTML analysis")
    analyze_html_structure()













