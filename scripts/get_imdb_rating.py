#!/usr/bin/env python3
import logging
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup

#setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SeinfelderIMDB:
    def __init__(self):
        """init session"""
        self.session = requests.Session()
        #set a normal browser user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.episodes_cache: Dict[tuple, dict] = {}
    def _get_episode(self, season: int, episode: int) -> Optional[dict]:
        """get episode details by scraping IMDb"""
        try:
            #use advanced search url format
            search_url = (
                f"https://www.imdb.com/search/title/?"
                f"title_type=tv_episode&"
                f"series=tt0098904&"  #seinfeld's id
                f"season={season}&"
                f"episode={episode}"
            )
            logger.info(f"Searching: {search_url}")
            
            #get search results
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            #find episode in search results
            result_item = soup.find('div', class_='lister-item')
            if not result_item:
                logger.error("No episode found in search results")
                logger.debug(f"Response HTML: {soup.prettify()}")
                return None
                
            title = result_item.find('h3', class_='lister-item-header')
            if not title:
                logger.error("Could not find title element")
                return None
            episode_title = title.find('a').text.strip()
            rating_elem = result_item.find('div', class_='ratings-imdb-rating')
            rating = rating_elem.get('data-value', 'N/A') if rating_elem else 'N/A'
            #find additional info
            info_elements = result_item.find_all('p', class_='text-muted')
            air_date = "Unknown"
            votes = "0"
            for elem in info_elements:
                if 'Release Date:' in elem.text:
                    air_date = elem.text.split('Release Date:')[1].strip()
                if 'Votes:' in elem.text:
                    votes = elem.text.split('Votes:')[1].strip()
            
            episode_info = {
                'title': episode_title,
                'rating': rating,
                'votes': votes,
                'air_date': air_date,
            }
            logger.info(f"Found episode: {episode_title} with rating {rating}")
            return episode_info
        except Exception as e:
            logger.error(f"Failed to fetch episode data: {e}")
            return None
    def get_episode_rating(self, season: int, episode: int) -> Optional[dict]:
        """get rating for specific episode"""
        try:
            #check cache first
            cache_key = (season, episode)
            if cache_key in self.episodes_cache:
                return self.episodes_cache[cache_key]
            
            #get episode data
            episode_data = self._get_episode(season, episode)
            if not episode_data:
                return None
            
            #format response
            result = {
                'title': episode_data.get('title', 'Unknown'),
                'rating': episode_data.get('rating', 'N/A'),
                'votes': episode_data.get('votes', 0),
                'season': season,
                'episode': episode,
                'air_date': str(episode_data.get('original air date', 'Unknown'))
            }
            logger.info(f"Found episode: {result['title']} ({result['rating']}/10)")
            
            #cache it
            self.episodes_cache[cache_key] = result
            return result
            
        except KeyError:
            logger.error(f"episode S{season}E{episode} not found")
            return None
        except Exception as e:
            logger.error(f"error getting episode rating: {e}")
            return None

def get_rating(season: int, episode: int) -> Optional[dict]:
    """convenience function to get rating"""
    finder = SeinfelderIMDB()
    return finder.get_episode_rating(season, episode)

if __name__ == "__main__":
    #example usage
    import sys
    if len(sys.argv) != 3:
        print("Usage: python get_imdb_rating.py <season> <episode>")
        sys.exit(1)
        
    try:
        season = int(sys.argv[1])
        episode = int(sys.argv[2])
        
        result = get_rating(season, episode)
        if result:
            print(f"\nSeinfeld S{season}E{episode}:")
            print(f"Title: {result['title']}")
            print(f"Rating: {result['rating']}/10 ({result['votes']} votes)")
            print(f"Air Date: {result['air_date']}")
        else:
            print(f"\nFailed to get rating for S{season}E{episode}")
            
    except ValueError:
        print("Season and episode must be numbers")
        sys.exit(1)





















