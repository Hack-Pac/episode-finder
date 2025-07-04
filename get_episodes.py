import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
from pathlib import Path

# Setup logging
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(data_dir / "episode_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_episode_data(row, season_num):
    episode_data = {
        'season': season_num,
        'episode_in_season': None,
        'overall_episode': None,
        'title': None,
        'air_date': None,
        'description': None,
        'production_code': None
    }
    
    try:
        cells = row.find_all(['td', 'th'])
        
        if len(cells) >= 2:
            if cells[0].text.strip():
                episode_nums = cells[0].text.strip()
                logger.debug(f"Raw episode numbers: '{episode_nums}'")
                import re
                numbers = re.findall(r'\d+', episode_nums)
                if len(numbers) >= 1:
                    episode_data['episode_in_season'] = int(numbers[0])
                if len(numbers) >= 2:
                    episode_data['overall_episode'] = int(numbers[1])
            
            title_cell = row.find('th')
            if title_cell:
                title_link = title_cell.find('a')
                if title_link:
                    episode_data['title'] = title_link.text.strip()
                    logger.debug(f"Found title: '{episode_data['title']}'")
            
            for i, cell in enumerate(cells[2:], 2):
                cell_text = cell.text.strip()
                # Look for date patterns
                if any(month in cell_text for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                    episode_data['air_date'] = cell_text
                    logger.debug(f"Found air date: '{cell_text}'")
                    break
            
            for cell in cells[3:]:
                cell_text = cell.text.strip()
                if len(cell_text) > 20 and not any(month in cell_text for month in ['January', 'February', 'March', 'April', 'May', 'June']):
                    episode_data['description'] = cell_text
                    logger.debug(f"Found description: '{cell_text[:50]}...'")
                    break
                    
    except Exception as e:
        logger.error(f"Error extracting episode data: {e}")
    
    return episode_data

def scrape_seinfeld_episodes():
    """Main function to scrape Seinfeld episodes with comprehensive logging"""
    
    print("🎬 Starting Seinfeld Episode Scraper")
    logger.info("="*50)
    logger.info("SEINFELD EPISODE SCRAPER STARTED")
    logger.info("="*50)
    
    print("📡 Task 1: Fetching Wikipedia page...")
    logger.info("Task 1: Fetching Seinfeld episodes from Wikipedia")
    
    url = "https://en.wikipedia.org/wiki/List_of_Seinfeld_episodes"
    logger.info(f"URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info("Successfully fetched page (Status: {response.status_code})")
        print("Page fetched successfully (Status: {response.status_code})")
    except requests.RequestException as e:
        logger.error("Failed to fetch Wikipedia page: {e}")
        print("Failed to fetch page: {e}")
        return None
    
    print("Task 2: Parsing HTML content...")
    logger.info("Task 2: Parsing HTML with BeautifulSoup")
    
    soup = BeautifulSoup(response.text, "html.parser")
    logger.info("HTML parsed successfully")
    
    print("📋 Task 3: Finding episode tables...")
    logger.info("Task 3: Searching for episode tables")
    
    tables = soup.find_all("table", class_="wikitable plainrowheaders")
    logger.info(f"Found {len(tables)} tables with class 'wikitable plainrowheaders'")
    print("Found {len(tables)} episode tables")
    
    if len(tables) < 9:
        logger.warning(f"Expected at least 9 tables (seasons), but found {len(tables)}")
        print("Warning: Expected 9 seasons, found {len(tables)} tables")
    
    print("Task 4: Extracting episode data...")
    logger.info("Task 4: Extracting episode data from tables")
    
    all_episodes = []
    season_stats = {}
    
    # Processing 9 seasons
    for season_num, table in enumerate(tables[:9], 1):
        print("\n Processing Season {season_num}...")
        logger.info("Processing Season {season_num}")
        
        rows = table.find_all("tr")[1:]
        logger.info("Found {len(rows)} episode rows in Season {season_num}")
        
        season_episodes = []
        
        for row_idx, row in enumerate(rows, 1):
            logger.debug("Processing Season {season_num}, Row {row_idx}")
            
            episode_data = extract_episode_data(row, season_num)
            
            if episode_data['title']:
                season_episodes.append(episode_data)
                all_episodes.append(episode_data)
                print("Episode {episode_data.get('episode_in_season', '?')}: {episode_data['title']}")
                logger.info("Extracted: S{season_num}E{episode_data.get('episode_in_season', '?')} - {episode_data['title']}")
            else:
                logger.warning("Failed to extract title from Season {season_num}, Row {row_idx}")
        
        season_stats[season_num] = {
            'episodes_found': len(season_episodes),
            'episodes_with_air_dates': sum(1 for ep in season_episodes if ep['air_date']),
            'episodes_with_descriptions': sum(1 for ep in season_episodes if ep['description'])
        }
        
        logger.info(f"Season {season_num} completed: {len(season_episodes)} episodes extracted")
    
    print("\n Task 5: Saving data and generating reports...")
    logger.info("Task 5: Saving extracted data")
    
    # Detailed episode data
    episodes_file = data_dir / "seinfeld_episodes_metadata.json"
    with open(episodes_file, 'w', encoding='utf-8') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total_episodes': len(all_episodes),
            'seasons': 9,
            'source_url': url,
            'season_stats': season_stats,
            'episodes': all_episodes
        }, f, indent=2, ensure_ascii=False)
    
    logger.info("Saved {len(all_episodes)} episodes to {episodes_file}")
    print("Saved {len(all_episodes)} episodes to {episodes_file}")
    
    print("\n📊 EXTRACTION SUMMARY:")
    print("="*40)
    logger.info("EXTRACTION SUMMARY:")
    
    total_episodes = len(all_episodes)
    episodes_with_dates = sum(1 for ep in all_episodes if ep['air_date'])
    episodes_with_descriptions = sum(1 for ep in all_episodes if ep['description'])
    
    print("Total Episodes: {total_episodes}")
    print("Episodes with Air Dates: {episodes_with_dates}")
    print("Episodes with Descriptions: {episodes_with_descriptions}")
    
    logger.info("Total Episodes: {total_episodes}")
    logger.info("Episodes with Air Dates: {episodes_with_dates}")
    logger.info("Episodes with Descriptions: {episodes_with_descriptions}")
    
    print("\n🏷️  Season Breakdown:")
    for season, stats in season_stats.items():
        print("Season {season}: {stats['episodes_found']} episodes")
        logger.info("Season {season}: {stats['episodes_found']} episodes, {stats['episodes_with_air_dates']} with dates, {stats['episodes_with_descriptions']} with descriptions")
    
    logger.info("="*50)
    logger.info("SEINFELD EPISODE SCRAPER COMPLETED SUCCESSFULLY")
    logger.info("="*50)
    
    return all_episodes

if __name__ == "__main__":
    episodes = scrape_seinfeld_episodes()
    if episodes:
        print("\nScraping completed! Found {len(episodes)} episodes total.")
    else:
        print("\nScraping failed. Check logs for details.")