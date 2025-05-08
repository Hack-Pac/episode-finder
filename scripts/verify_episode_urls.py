#!/usr/bin/env python3
"""
A comprehensive script to verify and list all available Seinfeld episodes on seinfeldscripts.com
"""
import os
import requests
from pathlib import Path
import time
import json
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = Path("data/scripts")
def check_if_url_exists(url):
    """Check if a URL exists without downloading the whole page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=5)
        # Some servers don't support HEAD requests correctly
        if response.status_code == 405:  # Method not allowed
            response = requests.get(url, headers=headers, timeout=5, stream=True)
            # Abort after getting headers
            response.close()
        
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_final_episode_list():
    """Check all the official episodes and their file availability"""
    
    # Comprehensive list of all Seinfeld episodes by season
    all_episodes = {
        "Season 1": [
            {"title": "The Seinfeld Chronicles", "filenames": ["TheSeinfeldChronicles.htm", "TheSeinfeldChronicles.html"]},
            {"title": "The Stakeout", "filenames": ["TheStakeout.htm", "TheStakeout.html"]},
            {"title": "The Robbery", "filenames": ["TheRobbery.htm", "TheRobbery.html"]},
            {"title": "Male Unbonding", "filenames": ["MaleUnbonding.htm", "MaleUnbonding.html"]},
            {"title": "The Stock Tip", "filenames": ["TheStockTip.htm", "TheStockTip.html"]}
        ],
        "Season 3": [
            {"title": "The Pez Dispenser", "filenames": ["ThePezDispenser.htm", "ThePezDispenser.html"]}
        ],
        "Season 4": [
            {"title": "The Movie", "filenames": ["TheMovie.htm", "TheMovie.html"]},
            {"title": "The Old Man", "filenames": ["TheOldMan.htm", "TheOldMan.html"]},
            {"title": "The Junior Mint", "filenames": ["TheJuniorMint.htm", "TheJuniorMints.htm", "TheJuniorMint.html"]},
            {"title": "The Smelly Car", "filenames": ["TheSmellyCar.htm", "TheSmellyCarEpisode.htm", "TheSmellyCar.html"]}
        ],
        "Season 6": [
            {"title": "The Secret Code", "filenames": ["TheSecretCode.htm", "TheSecretCode2.htm", "TheSecretCode.html"]},
            {"title": "Highlights of a Hundred", "filenames": ["TheHighlightsofaHundred.htm", "The-Clip-Show-1.html", "Highlights100.htm"]},
            {"title": "The Diplomat's Club", "filenames": ["TheDiplomatClub.htm", "TheDiplomatClub.html", "TheDiplomatsClub.htm"]},
            {"title": "The Switch", "filenames": ["TheSwitch.htm", "TheSwitch.html"]},
            {"title": "The Fusilli Jerry", "filenames": ["TheFusilliJerry.htm", "TheFusilliJerry.html"]}
        ],
        "Season 7": [
            {"title": "The Cadillac (Part 1)", "filenames": ["TheCadillac1.htm", "TheCadillac1.html"]},
            {"title": "The Cadillac (Part 2)", "filenames": ["TheCadillac2.htm", "TheCadillac2.html"]}
        ],
        "Season 8": [
            # Add any problematic Season 8 episodes here
        ],
        "Season 9": [
            {"title": "The Chronicle (Part 1)", "filenames": ["The-Clip-Show-1.html", "TheChronicle1.htm"]},
            {"title": "The Chronicle (Part 2)", "filenames": ["The-Clip-Show-2.html", "TheChronicle2.htm"]}
        ]
    }
    
    # Results of URL checking
    results = {}
    
    print("Checking URLs for all episodes...")
    
    # Check each URL
    for season, episodes in all_episodes.items():
        results[season] = []
        
        for episode in episodes:
            episode_results = {"title": episode["title"], "urls_checked": []}
            
            for filename in episode["filenames"]:
                url = f"{BASE_URL}{filename}"
                exists = check_if_url_exists(url)
                
                episode_results["urls_checked"].append({
                    "url": url,
                    "exists": exists
                })
                
                if exists:
                    print(f"✓ {season} - {episode['title']} - {url}")
                else:
                    print(f"× {season} - {episode['title']} - {url}")
                # Be nice to the server
                time.sleep(0.5)
            results[season].append(episode_results)
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/url_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate report
    with open(f"{OUTPUT_DIR}/url_verification_report.txt", "w") as f:
        f.write("Seinfeld URLs Verification Report\n")
        f.write("===============================\n\n")
        
        for season, episodes in results.items():
            f.write(f"{season}:\n")
            for episode in episodes:
                working_urls = [url["url"] for url in episode["urls_checked"] if url["exists"]]
                if working_urls:
                    first_working = working_urls[0]
                    f.write(f"  ✓ {episode['title']}: {first_working}\n")
                    
                    if len(working_urls) > 1:
                        f.write(f"      Also available at: {', '.join(working_urls[1:])}\n")
                else:
                    f.write(f"  × {episode['title']}: No working URLs found\n")
                    f.write(f"      Tried: {', '.join(url['url'] for url in episode['urls_checked'])}\n")
            f.write("\n")
    
    print(f"Results saved to {OUTPUT_DIR}/url_verification_report.txt")
    return results

if __name__ == "__main__":
    print("Starting URL verification process...")
    check_final_episode_list()
    print("Done!")




























