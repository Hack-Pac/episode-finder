#!/usr/bin/env python3
"""
Script to find Seinfeld episodes based on keywords
"""

import os
import re
import logging
import json
from pathlib import Path
import sys
from collections import Counter
import string
from tqdm import tqdm

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# Import IMDb rating function
from scripts.get_imdb_rating import get_rating

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SCRIPTS_DIR = Path(__file__).parent.parent / "data" / "scripts"
TOP_RESULTS = 5  # Number of top results to return

def load_script_files():
    """
    Load all script files from the data/scripts directory
    Returns a dictionary with episode info as keys and file paths as values
    """
    script_files = {}
    
    # Check if scripts directory exists
    if not SCRIPTS_DIR.exists():
        logger.error(f"Scripts directory not found: {SCRIPTS_DIR}")
        return script_files
        
    # Walk through all season directories
    for season_dir in SCRIPTS_DIR.glob("Season *"):
        if not season_dir.is_dir():
            continue
            
        season_name = season_dir.name
        logger.info(f"Loading scripts from {season_name}")
        
        # Process each script file in this season
        for script_file in season_dir.glob("*.txt"):
            try:
                # Extract episode info from filename
                episode_name = script_file.stem
                episode_key = f"{season_name}: {episode_name}"
                script_files[episode_key] = script_file
            except Exception as e:
                logger.error(f"Error processing {script_file}: {e}")
    
    logger.info(f"Loaded {len(script_files)} script files")
    return script_files

def preprocess_text(text):
    """
    Preprocess text: lowercase, remove punctuation, extra whitespace
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parse_keywords(keywords_str):
    """
    Parse keywords string into a list of individual keywords
    """
    # Split by commas and spaces
    keywords = re.split(r'[,\s]+', keywords_str.lower())
    
    # Remove empty strings and strip whitespace
    keywords = [k.strip() for k in keywords if k.strip()]
    
    return keywords

def find_episodes_by_keywords(keywords_str, max_results=5):
    """
    Find episodes matching the given keywords
    
    Args:
        keywords_str (str): Comma or space separated keywords
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of dictionaries with episode info and scores
    """
    # Parse keywords
    keywords = parse_keywords(keywords_str)
    if not keywords:
        logger.warning("No valid keywords provided")
        return []
        
    logger.info(f"Searching for keywords: {', '.join(keywords)}")
    
    # Load script files
    script_files = load_script_files()
    if not script_files:
        logger.error("No script files found")
        return []
    
    # Results will store episode_key -> {score, keyword_counts}
    results = {}
    
    # Process each script file
    for episode_key, script_path in tqdm(script_files.items(), desc="Searching episodes"):
        try:
            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Preprocess content for better matching
            processed_content = preprocess_text(script_content)
            
            # Count keyword occurrences
            keyword_counts = {}
            for keyword in keywords:
                # Case-insensitive count (content is already lowercase)
                count = processed_content.count(keyword.lower())
                if count > 0:
                    keyword_counts[keyword] = count
              # Calculate score based on keyword matches
            # New scoring algorithm prioritizes matching multiple keywords:
            # - Base score from keyword occurrences
            # - Significant bonus for each unique keyword matched
            # - Bonus for matching higher percentage of all keywords
            
            # Base score from occurrences
            base_score = sum(count * len(keyword) for keyword, count in keyword_counts.items())
            
            # Calculate keyword diversity score - emphasize matching multiple different keywords
            unique_keywords_matched = len(keyword_counts)
            keyword_diversity_bonus = unique_keywords_matched * 100  # Significant bonus per unique keyword
            
            # Calculate coverage score - percentage of provided keywords that were matched
            coverage_ratio = unique_keywords_matched / len(keywords)
            coverage_bonus = int(coverage_ratio * 200)  # Up to 200 points for matching all keywords
            
            # Combine scores with proper weighting
            total_score = base_score + keyword_diversity_bonus + coverage_bonus
            
            # If any keywords matched, add to results
            if total_score > 0:
                results[episode_key] = {
                    "episode": episode_key,
                    "score": total_score,
                    "base_score": base_score,
                    "keyword_counts": keyword_counts,
                    "matched_keywords": unique_keywords_matched,
                    "total_keywords": len(keywords),
                    "keywords_coverage": f"{coverage_ratio:.1%}",
                    "script_path": str(script_path)
                }
                
        except Exception as e:
            logger.error(f"Error processing {script_path}: {e}")
      # Sort results with new priorities:
    # 1. First by number of matched keywords (most important)
    # 2. Then by total score (for episodes matching same number of keywords)
    sorted_results = sorted(
        results.values(),
        key=lambda x: (x["matched_keywords"], x["score"]),
        reverse=True
    )
    
    # Return top results
    top_results = sorted_results[:max_results]
    
    # Format the top results
    formatted_results = []
    for result in top_results:
        episode_key = result["episode"]
        
        # Extract season and episode name
        match = re.match(r"Season (\d+): (.*)", episode_key)
        if match:
            season_num = match.group(1)
            episode_name = match.group(2)
            
            # Get IMDb rating if available
            try:
                rating_info = get_rating(season_num, episode_name)
            except:
                rating_info = None
                  # Create result entry with more detailed match information
            entry = f"Season {season_num} Episode: {episode_name}"
            
            # Add keyword match statistics
            matched_count = result["matched_keywords"]
            total_count = result["total_keywords"]
            coverage = result["keywords_coverage"]
            
            entry += f"\nMatched {matched_count}/{total_count} keywords ({coverage} coverage)"
            
            # Add matched keywords info with their counts
            keyword_info = ", ".join([f"{k} ({v})" for k, v in result["keyword_counts"].items()])
            entry += f"\nKeywords found: {keyword_info}"
            
            # Add rating if available
            if rating_info and "rating" in rating_info and "votes" in rating_info:
                entry += f"\nIMDb Rating: {rating_info['rating']}/10 ({rating_info['votes']} votes)"
                
            formatted_results.append(entry)
    
    return formatted_results

def main():
    """Command line interface for keyword search"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Find Seinfeld episodes by keywords')
    parser.add_argument('keywords', type=str, help='Keywords to search for (comma or space separated)')
    parser.add_argument('--max', type=int, default=TOP_RESULTS, help='Maximum number of results to return')
    
    args = parser.parse_args()
    
    results = find_episodes_by_keywords(args.keywords, args.max)
    
    print(f"\nTop {len(results)} episodes matching keywords: {args.keywords}\n")
    for i, result in enumerate(results, 1):
        print(f"#{i}: {result}")
        print("-" * 50)

if __name__ == "__main__":
    main()
