#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import logging
from pathlib import Path

#setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
def scrape_seinfeld():
    """scrape episode descriptions from seinfeldscripts.com"""
    descriptions = []
    
    #ensure output dir exists
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    logger.info("starting seinfeld scraper")
    
    #grab all seasons
    for season in range(1, 10):
        url = f"https://www.seinfeldscripts.com/seinfeld-season-{season}.html"
        try:
            #dont hammer the server
            time.sleep(1)
            logger.info(f"scraping season {season}")
            #grab season page with browser-like headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            #parse html
            soup = BeautifulSoup(response.text, 'html.parser')
            #extract episode descriptions
            episodes = soup.find_all('p')
            season_count = 0
            for ep in episodes:
                text = ep.text.strip()
                if text:  #skip empty paragraphs
                    descriptions.append(f"Season {season}: {text}")
                    season_count += 1
            
            logger.info(f"found {season_count} episodes in season {season}")
        except requests.RequestException as e:
            logger.error(f"failed to fetch season {season}: {str(e)}")
        except Exception as e:
            logger.error(f"error processing season {season}: {str(e)}")
    #save all descriptions
    if descriptions:
        output_file = output_dir / "seinfeld_descriptions.txt"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(descriptions))
            logger.info(f"saved {len(descriptions)} descriptions to {output_file}")
        except IOError as e:
            logger.error(f"failed to save descriptions: {str(e)}")
    else:
        logger.warning("no descriptions found to save")
if __name__ == "__main__":
    try:
        scrape_seinfeld()
    except KeyboardInterrupt:
        logger.info("scraping interrupted by user")
    except Exception as e:
        logger.error(f"unexpected error: {str(e)}")












