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

def tokenize(text):
    """Tokenize preprocessed text into a list of words"""
    return text.split()

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
    # Parse and preprocess keywords
    keywords = parse_keywords(keywords_str)
    if not keywords:
        logger.warning("No valid keywords provided")
        return []
    logger.info(f"Searching for keywords: {', '.join(keywords)}")

    # Tokenize keywords for set operations
    keyword_set = set(keywords)

    # Load script files
    script_files = load_script_files()
    if not script_files:
        logger.error("No script files found")
        return []

    results = {}

    for episode_key, script_path in tqdm(script_files.items(), desc="Searching episodes"):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            processed_content = preprocess_text(script_content)
            tokens = tokenize(processed_content)
            token_counts = Counter(tokens)
            script_token_set = set(tokens)

            # Find which keywords are present (set intersection)
            matched_keywords = keyword_set & script_token_set
            unique_keywords_matched = len(matched_keywords)
            keyword_counts = {k: token_counts[k] for k in matched_keywords}

            # Score: prioritize number of unique keywords matched, then frequency
            base_score = sum(keyword_counts.values())
            keyword_diversity_bonus = unique_keywords_matched * 100
            coverage_ratio = unique_keywords_matched / len(keyword_set)
            coverage_bonus = int(coverage_ratio * 200)
            total_score = base_score + keyword_diversity_bonus + coverage_bonus

            if total_score > 0:
                results[episode_key] = {
                    "episode": episode_key,
                    "score": total_score,
                    "base_score": base_score,
                    "keyword_counts": keyword_counts,
                    "matched_keywords": unique_keywords_matched,
                    "total_keywords": len(keyword_set),
                    "keywords_coverage": f"{coverage_ratio:.1%}",
                    "script_path": str(script_path)
                }
        except Exception as e:
            logger.error(f"Error processing {script_path}: {e}")

    sorted_results = sorted(
        results.values(),
        key=lambda x: (x["matched_keywords"], x["score"]),
        reverse=True
    )
    top_results = sorted_results[:max_results]
    formatted_results = []
    for result in top_results:
        episode_key = result["episode"]
        match = re.match(r"Season (\d+): (.*)", episode_key)
        if match:
            season_num = match.group(1)
            episode_name = match.group(2)
            try:
                rating_info = get_rating(season_num, episode_name)
                if not rating_info:
                    base_name = episode_name.split('(')[0].strip()
                    if base_name != episode_name:
                        rating_info = get_rating(season_num, base_name)
            except Exception as e:
                logger.debug(f"Error fetching rating: {e}")
                rating_info = None
            entry = f"Season {season_num} Episode: {episode_name}"
            matched_count = result["matched_keywords"]
            total_count = result["total_keywords"]
            coverage = result["keywords_coverage"]
            entry += f"\nMatched {matched_count}/{total_count} keywords ({coverage} coverage)"
            keyword_info = ", ".join([f"{k} ({v})" for k, v in result["keyword_counts"].items()])
            entry += f"\nKeywords found: {keyword_info}"
            if rating_info:
                if "rating" in rating_info and "votes" in rating_info:
                    entry += f"\nIMDb Rating: {rating_info['rating']}/10 ({rating_info['votes']} votes)"
                if "air_date" in rating_info and rating_info["air_date"] and rating_info["air_date"] != "Unknown":
                    entry += f"\nAir Date: {rating_info['air_date']}"
                if "description" in rating_info and rating_info["description"] and rating_info["description"] != "N/A":
                    entry += f"\nDescription: {rating_info['description']}"
                if "image_url" in rating_info and rating_info["image_url"]:
                    entry += f"\nIMDb Image: {rating_info['image_url']}"
                if "imdb_url" in rating_info and rating_info["imdb_url"]:
                    entry += f"\nIMDb URL: {rating_info['imdb_url']}"
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

















