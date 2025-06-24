#!/usr/bin/env python3
import logging
import re
import json
from typing import Optional, Dict, Union, Tuple
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import urllib.parse
from datetime import datetime
import sys

#setup logging for this script specifically
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#if running standalone and no handlers configured, add default one
if not logger.handlers and not logging.getLogger().handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
elif not logger.handlers and logging.getLogger().handlers:
    pass

#setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#seinfeld imdb id
SEINFELD_IMDB_ID = "tt0098904"

#parse air dates consistently
def parse_air_date(date_str: Optional[str]) -> str:
    logger.debug(f"parse_air_date received: '{date_str}'")
    if not date_str or date_str == "Unknown" or date_str.strip() == "":
        return "Unknown"

    #clean the date string
    cleaned_date_str = date_str.replace(" aired", "").strip()
    #remove ordinal indicators (st, nd, rd, th)
    cleaned_date_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", cleaned_date_str, flags=re.IGNORECASE)
    #remove "TV Episode • " prefix if present
    cleaned_date_str = re.sub(r"^TV Episode\s*•\s*", "", cleaned_date_str, flags=re.IGNORECASE)
    #remove potential year in parentheses
    cleaned_date_str = re.sub(r"\s*\(\d{4}\)$", "", cleaned_date_str).strip()


    formats_to_try = [
        "%d %b. %Y",      # e.g., "18 Nov. 1992"
        "%d %B %Y",       # e.g., "18 November 1992"
        "%b %d, %Y",      # e.g., "Nov 18, 1992"
        "%B %d, %Y",      # e.g., "November 18, 1992"
        "%Y-%m-%d",       # e.g., "1992-11-18"
        "%a, %b %d, %Y",  # e.g., "Wed, Nov 18, 1992"
        "%A, %B %d, %Y",  # e.g., "Wednesday, November 18, 1992"
        "%b. %d, %Y",     # e.g., "Nov. 18, 1992"
        "%B %d %Y",       # e.g., "November 18 1992"
        "%b %d %Y",       # e.g., "Nov 18 1992"
    ]

    for fmt in formats_to_try:
        try:
            # Use cleaned_date_str, which preserves original case for month/day names
            dt_obj = datetime.strptime(cleaned_date_str, fmt)
            formatted_date = dt_obj.strftime("%Y-%m-%d")
            logger.debug(f"Successfully parsed '{date_str}' (cleaned: '{cleaned_date_str}') using format '{fmt}' to '{formatted_date}'")
            return formatted_date
        except ValueError:
            logger.debug(f"Date string '{date_str}' (cleaned: '{cleaned_date_str}') did not match format '{fmt}'")
            continue
    
    logger.warning(f"Could not parse date string: '{date_str}' (cleaned: '{cleaned_date_str}') with known formats.")
    return "Unknown"

HTML_PARSING_STRATEGIES = [
    {
        "name": "JSON-LD",        "type": "json-ld",
    },
    {
        "name": "H4AnchorSiblingStrategy",
        "type": "html",
        "use_sibling_navigation": True,
        "episode_blocks_selector": "h4:has(a[href*='/title/tt'])",
        "title_selector": "a",
        "link_selector": "a",
        "extract_image_src": lambda img_tag: img_tag.get('src') if img_tag else None,
        "extract_rating": lambda rating_text_node: re.search(r'(\d+\.\d+|\d+)/10', rating_text_node.get_text(strip=True)).group(1) if rating_text_node and re.search(r'(\d+\.\d+|\d+)/10', rating_text_node.get_text(strip=True)) else 'N/A',
        "extract_votes": lambda votes_text_node: re.search(r'\((\d[\d,.]*K?)\)', votes_text_node.get_text(strip=True)).group(1).replace('K', '000').replace(',', '') if votes_text_node and re.search(r'\((\d[\d,.]*K?)\)', votes_text_node.get_text(strip=True)) else '0',
    },
    {
        "name": "ModernEpisodeCard",
        "type": "html",
        "episode_blocks_selector": "article[data-testid*='episode-card-list-item'], div[class*=EpisodeCard__container]",
        "title_selector": "a[data-testid*='episode-title'], a.ipc-title-link-wrapper .ipc-title__text, h3.ipc-title__text",
        "link_selector": "a[data-testid*='episode-title'], a.ipc-title-link-wrapper",
        "image_selector": "figure[class*='EpisodeCard__imageContainer'] img, img.ipc-image",
        "extract_image_src": lambda img_tag: img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0] if img_tag else None,
        "rating_selector": "div[class*='EpisodeCard__ratings'] span[aria-label*='IMDb rating'], span.ipc-rating-star[class*='ipc-rating-star--base']",
        "extract_rating": lambda el: re.search(r'(\d\.\d|\d+)', el.text.strip()).group(1) if el and re.search(r'(\d\.\d|\d+)', el.text.strip()) else 'N/A',
        "votes_selector": "div[class*='EpisodeCard__ratings'] span[class*='EpisodeCard__voteCount'], span[class*='ipc-rating-star--voteCount']",
        "extract_votes": lambda el: re.sub(r'[^\d]', '', el.text.strip('()')) if el else '0',        "air_date_selector": "div[class*='EpisodeCard__releaseDateText'], div[class*='EpisodeCard__metadata'] span.ipc-metadata-list-summary-item__li",
        "extract_air_date": lambda el: el.text.strip() if el else 'Unknown',
        "description_selector": "div[class*='EpisodeCard__plot'] div[class*='ipc-html-content-inner-div'], div.ipc-metadata-list-summary-item__plot-description",
        "extract_description": lambda el: el.text.strip() if el else 'N/A',
        "episode_number_selector": "div[class*='EpisodeCard__episodeNumber'], div.ipc-title__text",
        "extract_episode_number": lambda el: re.search(r'[Ee](\d+)', el.text.strip()).group(1) if el and re.search(r'[Ee](\d+)', el.text.strip()) else None,
    },
    {
        "name": "ClassicEpisodeList",
        "type": "html",
        "episode_blocks_selector": "div.eplist-item, div.lister-item-content",
        "title_selector": "a[itemprop='name']",
        "link_selector": "a[itemprop='name']",
        "image_selector": "img[itemprop='image']",
        "extract_image_src": lambda img_tag: img_tag.get('src') if img_tag else None,
        "rating_selector": "span[itemprop='ratingValue']",
        "extract_rating": lambda el: el.text.strip() if el else 'N/A',
        "votes_selector": "span[itemprop='ratingCount']",
        "extract_votes": lambda el: el.text.strip() if el else '0',
        "air_date_selector": "div.airdate",
        "extract_air_date": lambda el: el.text.strip() if el else 'Unknown',
        "description_selector": "div[itemprop='description']",
        "extract_description": lambda el: el.text.strip() if el else 'N/A',
        "episode_number_selector": "meta[itemprop='episodeNumber']",
        "extract_episode_number": lambda el: el.get('content') if el else None,
    },
    {
        "name": "GeneralContentItem", # Fallback for less structured data
        "type": "html",
        "episode_blocks_selector": "div.ipc-metadata-list-summary-item", # A general item that might contain episode info
        "title_selector": ".ipc-title__text", # Often used for titles
        "link_selector": "a.ipc-title-link-wrapper", # Common link wrapper
        "image_selector": "img.ipc-image", # General image selector
        "extract_image_src": lambda img_tag: img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0] if img_tag else None,
        "rating_selector": "span.ipc-rating-star--base", # General rating star
        "extract_rating": lambda el: re.search(r'(\d\.\d|\d+)', el.text.strip()).group(1) if el and re.search(r'(\d\.\d|\d+)', el.text.strip()) else 'N/A',
        "votes_selector": "span.ipc-rating-star--voteCount", # General vote count
        "extract_votes": lambda el: re.sub(r'[^\d]', '', el.text.strip('()')) if el else '0',
        "air_date_selector": "span.ipc-metadata-list-summary-item__li", # List items often contain metadata like air dates
        "extract_air_date": lambda el: el.text.strip() if el and (re.match(r'^\d{4}$', el.text.strip()) or re.match(r'^[A-Za-z]{3,}\s\d{1,2},?\s\d{4}$', el.text.strip()) or re.match(r'^\d{1,2}\s[A-Za-z]{3,}\s\d{4}$', el.text.strip())) else 'Unknown',
        "description_selector": "div.ipc-html-content-inner-div", # Common for plot summaries
        "extract_description": lambda el: el.text.strip() if el else 'N/A',
        "episode_number_selector": None, # Hard to reliably get episode number from this general structure
        "extract_episode_number": lambda el: None,
    }
]

class SeinfelderIMDB:
    def __init__(self):
        """init session"""
        self.session = requests.Session()
        # set a normal browser user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.episodes_cache: Dict[Tuple[str, str], dict] = {}
    
    def _try_api_method(self, season: Union[int, str], episode_name: Union[int, str]) -> Optional[dict]:
        """Try to get episode data from IMDb API if available"""
        try:
            # Use a more direct approach with potential API endpoints
            if isinstance(season, str) and season.isdigit():
                season = int(season)
                
            # Use IMDb's graphql API if available
            url = "https://www.imdb.com/graphql"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-Type': 'application/json',
                'Referer': f'https://www.imdb.com/title/{SEINFELD_IMDB_ID}/episodes/',
            }
            
            # Prepare the query - specific to the episode if name is numeric
            variables = {
                "titleId": SEINFELD_IMDB_ID,
                "seasonNumber": season,
                "first": 50  # Get up to 50 episodes
            }
            
            # Simple GraphQL query to get episode data
            query = """
            query Episodes($titleId: ID!, $seasonNumber: Int!, $first: Int!) {
                title(id: $titleId) {
                    episodes(season: $seasonNumber, first: $first) {
                        edges {
                            node {
                                titleText {
                                    text
                                }
                                plot {
                                    plotText {
                                        plainText
                                    }
                                }
                                releaseDate {
                                    day
                                    month
                                    year
                                }
                                runtime {
                                    seconds
                                }
                                ratingsSummary {
                                    aggregateRating
                                    voteCount
                                }
                                primaryImage {
                                    url
                                }
                                id
                            }
                        }
                    }
                }
            }
            """
            
            payload = {
                "operationName": "Episodes",
                "variables": variables,
                "query": query
            }
            
            logger.info(f"Attempting GraphQL API call for season {season}")
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "title" in data["data"] and "episodes" in data["data"]["title"]:
                    episodes = data["data"]["title"]["episodes"]["edges"]
                    if episodes:
                        # Find the right episode
                        target_episode_node = None
                        edge_index = -1
                        if isinstance(episode_name, int) or (isinstance(episode_name, str) and episode_name.isdigit()):
                            # Handle numeric episode number
                            ep_num = int(episode_name)
                            if 0 < ep_num <= len(episodes):
                                target_episode_node = episodes[ep_num - 1]["node"]
                                edge_index = ep_num -1
                        else:
                            # Try to find by title
                            for idx, edge in enumerate(episodes):
                                node = edge["node"]
                                if "titleText" in node and "text" in node["titleText"]:
                                    if episode_name.lower() in node["titleText"]["text"].lower():
                                        target_episode_node = node
                                        edge_index = idx
                                        break
                        
                        if target_episode_node:
                            # Format the output
                            episode_info = {
                                "title": target_episode_node.get("titleText", {}).get("text", "Unknown"),
                                "rating": str(target_episode_node.get("ratingsSummary", {}).get("aggregateRating", "N/A")),
                                "votes": str(target_episode_node.get("ratingsSummary", {}).get("voteCount", 0)),
                                "image_url": target_episode_node.get("primaryImage", {}).get("url"),
                                "imdb_url": f"https://www.imdb.com/title/{target_episode_node.get('id')}/",
                                "episode_num": edge_index + 1 if edge_index != -1 else "Unknown",
                                "season_num": season,
                                "description": target_episode_node.get("plot", {}).get("plotText", {}).get("plainText", "N/A")
                            }
                            
                            # Build the air date
                            if "releaseDate" in target_episode_node and target_episode_node["releaseDate"]:
                                rd = target_episode_node["releaseDate"]
                                # API gives month as 1-12, day as 1-31, year as YYYY
                                # Construct a date string that parse_air_date can handle, e.g., YYYY-MM-DD
                                if rd.get("year") is not None and rd.get("month") is not None and rd.get("day") is not None:
                                    try:
                                        # Ensure month and day are two digits for consistent parsing
                                        date_str = f"{rd['year']}-{str(rd['month']).zfill(2)}-{str(rd['day']).zfill(2)}"
                                        episode_info["air_date"] = date_str # Will be parsed by parse_air_date later
                                    except Exception as e_date:
                                        logger.warning(f"Could not construct date from API parts: {rd}, error: {e_date}")
                                        episode_info["air_date"] = "Unknown"
                                else:
                                    episode_info["air_date"] = "Unknown"
                            else:
                                episode_info["air_date"] = "Unknown"
                            
                            logger.info(f"Found episode via GraphQL API: {episode_info['title']}")
                            return episode_info
            
            logger.info(f"GraphQL API method failed or episode not found (status: {response.status_code}), falling back to HTML parsing")
            return None
        except Exception as e:
            logger.warning(f"GraphQL API method failed: {str(e)}")
            return None
    
    def _get_episode(self, season: Union[int, str], episode_identifier_to_find: Union[int, str]) -> Optional[dict]:
        """Get episode details using a structured approach with multiple strategies."""
        BASE_URL = "https://www.imdb.com"
        try:
            # Attempt API/JSON-LD methods first as they are more reliable if available
            api_result = self._try_api_method(season, episode_identifier_to_find)
            if api_result:
                api_result['air_date'] = parse_air_date(api_result.get('air_date'))
                return api_result
            
            json_ld_result = self._try_json_ld_method(season, episode_identifier_to_find)
            if json_ld_result:
                json_ld_result['air_date'] = parse_air_date(json_ld_result.get('air_date'))
                return json_ld_result

            logger.info("GraphQL and JSON-LD methods failed or episode not found, proceeding to HTML parsing strategies.")

            season_url = f"https://www.imdb.com/title/{SEINFELD_IMDB_ID}/episodes?season={season}"
            logger.info(f"Fetching HTML from: {season_url}")
            response = self.session.get(season_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for strategy in HTML_PARSING_STRATEGIES:
                if strategy["type"] != "html": continue # Skip non-HTML strategies here
                
                logger.info(f"Trying HTML parsing strategy: {strategy['name']}")
                episode_blocks = soup.select(strategy["episode_blocks_selector"])
                
                if not episode_blocks:
                    logger.debug(f"No episode blocks found with selector: {strategy['episode_blocks_selector']}")
                    continue
                
                logger.info(f"Found {len(episode_blocks)} potential episode blocks using strategy: {strategy['name']} (selector: {strategy['episode_blocks_selector']})")
                if episode_blocks and strategy['name'] == "H4AnchorSiblingStrategy": # Debug for H4 strategy
                    logger.debug(f"First H4 block HTML: {episode_blocks[0].prettify()[:1000]}")

                for idx, block in enumerate(episode_blocks):
                    episode_data = self.process_episode_block(block, strategy, season, episode_identifier_to_find, BASE_URL, idx)
                    if episode_data:
                        logger.info(f"Successfully extracted episode data using strategy: {strategy['name']}")
                        # Ensure air_date is parsed
                        episode_data['air_date'] = parse_air_date(episode_data.get('air_date'))
                        return episode_data
                
                logger.debug(f"Strategy {strategy['name']} did not yield a match for S{season}E{episode_identifier_to_find}")

            logger.error(f"All HTML parsing strategies failed for S{season}E{episode_identifier_to_find}. No episode blocks found or no matching episode identified.")
            logger.debug(f"Final HTML snippet for season page (first 3000 chars): {soup.prettify()[:3000]}")
            return None

        except requests.RequestException as e:
            logger.error(f"Request failed for season {season} page: {e}")
            return None
        except Exception as e:
            logger.error(f"General error in _get_episode for S{season} E{episode_identifier_to_find}: {e}", exc_info=True)
            return None

    def process_episode_block(self, episode_block: Tag, strategy: dict, season_num_str: str, episode_identifier: Union[int, str], base_url: str, block_index: int):
        logger.debug(f"Processing episode block with strategy: {strategy.get('name')}, looking for S{season_num_str}E{episode_identifier}, block index {block_index}")
        try:
            title_tag = episode_block.select_one(strategy.get("title_selector", "a")) # Default for H4 is h4 > a
            title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

            # For H4 strategy, episode_block is the H4 tag itself. Link is usually its child 'a'.
            # For other strategies, link_selector might be different relative to episode_block.
            link_source_tag = episode_block if strategy.get("name") == "H4AnchorSiblingStrategy" else episode_block
            link_tag = link_source_tag.select_one(strategy.get("link_selector", "a"))
            episode_imdb_path = link_tag.get(strategy.get("link_attr", "href")) if link_tag else None
            
            if not episode_imdb_path:
                logger.warning(f"Could not extract episode IMDb path for '{title}' using strategy {strategy.get('name')}")
                return None
            
            imdb_url = urllib.parse.urljoin(base_url, episode_imdb_path) # Use base_url passed in
            
            episode_num_match = re.search(r"ep(\d+)", episode_imdb_path)
            episode_num_from_link = episode_num_match.group(1) if episode_num_match else "Unknown"

            # Initialize details
            air_date = "Unknown"
            rating = "N/A"
            votes = "0"
            description = "N/A"
            image_url = None

            # Sibling navigation for AirDate, Rating, Votes, Description (primarily for H4AnchorSiblingStrategy)
            if strategy.get("use_sibling_navigation"):
                logger.debug(f"Strategy {strategy.get('name')}: Using sibling navigation for details (air_date, rating, votes, description) starting from after: {episode_block.name}")
                current_sibling = episode_block.next_sibling
                temp_description_parts = []
                description_collection_completed_for_this_episode = False # Flag to stop collecting description

                while current_sibling:
                    if isinstance(current_sibling, Tag):
                        # Determine if current_sibling indicates the start of the *next* episode block
                        should_stop_main_sibling_walk = False
                        if current_sibling.name == 'h4': # Primary indicator for H4 strategy
                            should_stop_main_sibling_walk = True
                        else:
                            # Check if current_sibling matches the general episode_blocks_selector for the strategy
                            episode_block_sel = strategy.get("episode_blocks_selector")
                            if episode_block_sel:
                                match_method = getattr(current_sibling, 'match', None)
                                if callable(match_method):
                                    try:
                                        if match_method(episode_block_sel):
                                            should_stop_main_sibling_walk = True
                                    except Exception as e_match_exception:
                                        logger.warning(f"H4 Sibling Nav: Exception during .match('{episode_block_sel}') call: {e_match_exception}. Sibling: <{current_sibling.name}>")
                                else:
                                    logger.error(f"H4 Sibling Nav: CRITICAL - current_sibling.match is None or not callable for tag <{current_sibling.name} class='{current_sibling.get('class','')}'>. Selector: '{episode_block_sel}'. This is unexpected for a BS4 Tag.")
                        
                        if should_stop_main_sibling_walk:
                            logger.debug(f"H4 Sibling Nav: Encountered next episode's main block indicator (<{current_sibling.name}>). Stopping sibling walk for current episode's details.")
                            break # Exit the `while current_sibling:` loop

                        # Air Date Parsing (remains largely the same)
                        if air_date == 'Unknown':
                            air_date_text_source = current_sibling.get_text(strip=True)
                            air_date_sibling_selector = strategy.get("air_date_sibling_selector")
                            if air_date_sibling_selector:
                                air_date_el_in_sibling = current_sibling.select_one(air_date_sibling_selector)
                                if air_date_el_in_sibling:
                                    air_date_text_source = air_date_el_in_sibling.get_text(strip=True)
                            
                            parsed_date_val = parse_air_date(air_date_text_source)
                            if parsed_date_val != 'Unknown':
                                air_date = parsed_date_val
                                logger.debug(f"H4 Sibling Nav: Parsed air_date: '{air_date}' from text: '{air_date_text_source}'")
                        
                        # Rating & Votes Parsing (remains largely the same)
                        if rating == "N/A":
                            rating_el = current_sibling.select_one(strategy.get("rating_sibling_selector", "span[aria-label*='IMDb rating'], span[class*='ratingGroup__imdb-rating']"))
                            if rating_el:
                                rating_text = rating_el.get_text(strip=True)
                                rating_match = re.search(r"(\d(?:\.\d)?)", rating_text)
                                if rating_match:
                                    rating = rating_match.group(1)
                                    logger.debug(f"H4 Sibling Nav: Parsed rating: '{rating}' from element: <{rating_el.name}> text: '{rating_text}'")
                                    votes_container_to_search = rating_el.parent if rating_el.parent else current_sibling
                                    votes_el = votes_container_to_search.select_one(
                                        strategy.get("votes_sibling_selector", 
                                                     "span[class*='voteCount'], span[class*='TotalRatingAmount'], a[href*='ratings'], button[data-testid*='ratings-bar__vote-count'] span")
                                    )
                                    if votes_el:
                                        votes_text = votes_el.get_text(strip=True)
                                        normalized_votes_text = re.sub(r"[(),]|\s*votes", "", votes_text, flags=re.IGNORECASE)
                                        votes_match = re.search(r"([\d.,KkMmBbTt]+(?:\.\d[KkMmBbTt])?)", normalized_votes_text)
                                        if votes_match:
                                            votes = votes_match.group(1)
                                            logger.debug(f"H4 Sibling Nav: Parsed votes: '{votes}' from element: <{votes_el.name}> text: '{votes_text}' (normalized: '{normalized_votes_text}')")
                                else:
                                     logger.debug(f"H4 Sibling Nav: Rating found in element <{rating_el.name}> but couldn't parse numeric value from '{rating_text}'")
                        
                        # Description Parsing (modified break logic)
                        if not description_collection_completed_for_this_episode:
                            desc_container_selector = strategy.get("description_sibling_selector", "div.ipc-html-content-inner-div, div[data-testid='plot'], p.ipc-overflowText--children, div.ipc-overflowText")
                            current_tag_is_description = False
                            desc_text_from_tag = ""

                            # Check if current sibling matches the description selector
                            # Using select_one for CSS selectors is generally safer/clearer than .match for this purpose.
                            # However, to minimize changes if .match was intended for non-CSS filters, we'll guard it.
                            if current_sibling.select_one(f":scope > {desc_container_selector}", soupsieve_adapter=None) if isinstance(desc_container_selector, str) and ('>' in desc_container_selector or '[' in desc_container_selector or '#' in desc_container_selector or ':' in desc_container_selector) else (getattr(current_sibling, 'match', None) and callable(getattr(current_sibling, 'match', None)) and current_sibling.match(desc_container_selector)):
                                current_tag_is_description = True
                                desc_text_from_tag = current_sibling.get_text(separator=' ', strip=True)
                            elif current_sibling.name in ['p', 'div'] and not current_sibling.find(strategy.get("rating_sibling_selector", "span[aria-label*='IMDb rating']")) and not (air_date == 'Unknown' and parse_air_date(current_sibling.get_text(strip=True)) != 'Unknown'):
                                text_content = current_sibling.get_text(separator=' ', strip=True)
                                if len(text_content) > 20: # Heuristic for generic p/div tags
                                    current_tag_is_description = True
                                    desc_text_from_tag = text_content
                            
                            if current_tag_is_description and desc_text_from_tag:
                                if not temp_description_parts: # First part of description for this episode
                                    logger.debug(f"H4 Sibling Nav: Starting description collection with: '{desc_text_from_tag[:100]}...'")
                                temp_description_parts.append(desc_text_from_tag)
                            elif temp_description_parts and not current_tag_is_description: # Was collecting, but this tag is not part of desc
                                logger.debug("H4 Sibling Nav: Description collection ended for this episode due to encountering a non-description tag.")
                                description_collection_completed_for_this_episode = True # Stop collecting for this episode

                    current_sibling = current_sibling.next_sibling
                # End of `while current_sibling:` loop

                if temp_description_parts:
                    description = " ".join(temp_description_parts).strip()
                if not description or description.lower() == "n/a": # Check if still N/A or empty
                    # Last attempt for description if H4 sibling didn't find it: check parent of H4 for a plot summary
                    if strategy.get("name") == "H4AnchorSiblingStrategy" and episode_block.parent:
                        parent_plot_el = episode_block.parent.select_one(strategy.get("description_fallback_selector_in_parent", "div[data-testid='plot'], .ipc-html-content-inner-div"))
                        if parent_plot_el:
                            description = parent_plot_el.get_text(separator=' ', strip=True)
                            logger.debug(f"H4 Strategy: Found description from parent fallback: {description[:100]}")
                description = description if description and description.lower() != "n/a" else "N/A"
                logger.debug(f"H4 Sibling Nav: Final description: '{description[:200]}...'")
            else: # For strategies NOT using sibling navigation (i.e., direct selectors from episode_block)
                # This part is for other strategies that define direct selectors for each field from the main episode_block
                air_date_el = episode_block.select_one(strategy.get("air_date_selector"))
                if air_date_el: air_date = parse_air_date(air_date_el.get_text(strip=True))
                
                rating_el = episode_block.select_one(strategy.get("rating_selector"))
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    rating_match = re.search(r"(\d(?:\.\d)?)", rating_text)
                    if rating_match: rating = rating_match.group(1)
                
                votes_el = episode_block.select_one(strategy.get("votes_selector"))
                if votes_el:
                    votes_text = votes_el.get_text(strip=True)
                    normalized_votes_text = re.sub(r"[(),]|\s*votes", "", votes_text, flags=re.IGNORECASE)
                    votes_match = re.search(r"([\d.,KkMmBbTt]+(?:\.\d[KkMmBbTt])?)", normalized_votes_text)
                    if votes_match: votes = votes_match.group(1)
                
                desc_el = episode_block.select_one(strategy.get("description_selector"))
                if desc_el: description = desc_el.get_text(separator=' ', strip=True)

            # General image extraction if not found by H4 specific logic or for other strategies
            if not image_url and strategy.get("image_selector"):
                # For non-H4 strategies, episode_block is the container. For H4, this won't typically find it.
                # This also serves as a fallback if H4 specific logic failed.
                image_source_container = episode_block
                if strategy.get("name") == "H4AnchorSiblingStrategy":
                    # For H4, the image is not IN the H4 tag. Try its parent or grandparent again if strategy allows.
                    # This might be redundant with earlier H4 image logic but can act as a broader fallback.
                    if episode_block.parent and episode_block.parent.parent:
                        image_source_container = episode_block.parent.parent
                    elif episode_block.parent:
                        image_source_container = episode_block.parent
                
                image_tag_el = image_source_container.select_one(strategy.get("image_selector"))
                if image_tag_el:
                    raw_img_src = image_tag_el.get(strategy.get("image_attr", "src"))
                    if raw_img_src:
                        image_url = self._get_high_res_image_url(raw_img_src)
                        logger.debug(f"General/Fallback Strategy ({strategy.get('name')}): Found image_url via select_one on container: {image_url}")

            # Final episode number determination: use link first, then index if link didn't yield number
            final_episode_num = episode_num_from_link if episode_num_from_link != "Unknown" else str(block_index + 1)

            episode_info = {
                "title": title,
                "imdb_url": imdb_url,
                "episode_num": final_episode_num,
                "season_num": str(season_num_str),
                "air_date": air_date, # Will be parsed again by caller if it's a raw string
                "rating": rating,
                "votes": votes,
                "description": description if description else "N/A",
                "image_url": image_url if image_url else "N/A"
            }

            # Matching logic
            matched = False
            if isinstance(episode_identifier, int): # Matching by episode number
                # Try matching against episode_num_from_link if available
                if episode_num_from_link != "Unknown" and episode_num_from_link == str(episode_identifier):
                    logger.info(f"Matched by episode number from link ({episode_num_from_link}) for S{season_num_str}E{episode_identifier}")
                    episode_info["episode_num"] = episode_num_from_link # Ensure it's the matched one
                    matched = True
                # Fallback to block_index + 1 if link didn't provide number or didn't match
                elif str(block_index + 1) == str(episode_identifier):
                    logger.info(f"Matched by block index ({block_index + 1}) for S{season_num_str}E{episode_identifier} (link ep num: {episode_num_from_link}).")
                    episode_info["episode_num"] = str(episode_identifier) # Update to the identifier
                    matched = True
            elif isinstance(episode_identifier, str): # Matching by title
                if episode_identifier.lower() in title.lower():
                    logger.info(f"Matched by title ('{episode_identifier}') for S{season_num_str} -> '{title}' (Ep num in info: {final_episode_num})")
                    matched = True
            
            if matched:
                return episode_info
            
            logger.debug(f"No match for S{season_num_str}E{episode_identifier} in this block. Title: '{title}', Link Ep#: {episode_num_from_link}, Index Ep#: {block_index+1}")
            return None

        except Exception as e:
            logger.error(f"Error processing episode block with strategy {strategy['name']} for S{season_num_str}E{episode_identifier} (idx {block_index}): {e}", exc_info=True)
            # logger.debug(f"Problematic block HTML (strategy {strategy['name']}): {episode_block.prettify()[:1000]}")
            return None

    def _try_json_ld_method(self, season: Union[int, str], episode_identifier_to_find: Union[int, str]) -> Optional[dict]:
        """Attempts to extract episode data using JSON-LD from the season page."""
        try:
            season_url = f"https://www.imdb.com/title/{SEINFELD_IMDB_ID}/episodes?season={season}"
            logger.info(f"Fetching HTML for JSON-LD extraction from: {season_url}")
            response = self.session.get(season_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            scripts = soup.find_all('script', type='application/ld+json')
            for script_tag in scripts:
                if script_tag.string:
                    try:
                        data = json.loads(script_tag.string)
                        # JSON-LD can be a list or a dict
                        if isinstance(data, list):
                            # Find the TVSeries object in the list
                            series_data = next((item for item in data if item.get("@type") == "TVSeries"), None)
                            if not series_data: data = data[0] # Fallback if no TVSeries type explicitly found
                            else: data = series_data
                        
                        if data.get("@type") == "TVSeries" and 'episode' in data:
                            episodes_list_json = data['episode']
                            for idx, ep_json in enumerate(episodes_list_json):
                                ep_title_json = ep_json.get('name', '').lower()
                                ep_num_json = ep_json.get('episodeNumber') # This is usually an int
                                
                                match_by_title = False
                                # Corrected: Added colon here
                                if isinstance(episode_identifier_to_find, str) and not episode_identifier_to_find.isdigit():
                                    match_by_title = episode_identifier_to_find.lower() in ep_title_json
                                
                                match_by_ep_num = False
                                if ep_num_json is not None:
                                    if isinstance(episode_identifier_to_find, int) and int(ep_num_json) == episode_identifier_to_find:
                                        match_by_ep_num = True
                                    elif isinstance(episode_identifier_to_find, str) and episode_identifier_to_find.isdigit() and int(ep_num_json) == int(episode_identifier_to_find):
                                        match_by_ep_num = True

                                if match_by_title or match_by_ep_num:
                                    imdb_url_json = ep_json.get('url')
                                    if imdb_url_json and not imdb_url_json.startswith('http'):
                                        imdb_url_json = urllib.parse.urljoin("https://www.imdb.com", imdb_url_json)

                                    episode_data = {
                                        'title': ep_json.get('name', 'Unknown'),
                                        'rating': str(ep_json.get('aggregateRating', {}).get('ratingValue', 'N/A')),
                                        'votes': str(ep_json.get('aggregateRating', {}).get('ratingCount', 0)),
                                        'image_url': ep_json.get('image'),
                                        'imdb_url': imdb_url_json,
                                        'episode_num': str(ep_num_json) if ep_num_json is not None else "Unknown",
                                        'season_num': season,
                                        'air_date': ep_json.get('datePublished', 'Unknown'), # Will be parsed by parse_air_date
                                        'description': ep_json.get('description', 'N/A')
                                    }
                                    logger.info(f"Found episode via JSON-LD: {episode_data['title']}")
                                    return episode_data
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON-LD parsing error: {e} for script content: {script_tag.string[:200]}...")
                        continue # Try next script tag
            logger.info("JSON-LD method did not find the episode or no suitable JSON-LD script found.")
            return None
        except requests.RequestException as e:
            logger.error(f"Request failed for JSON-LD data for season {season}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in _try_json_ld_method for S{season}E{episode_identifier_to_find}: {e}", exc_info=True)
            return None

    def get_episode_rating(self, season: Union[int, str], episode: Union[int, str]) -> Optional[dict]:
        """get rating for specific episode"""
        try:
            cache_key = (str(season), str(episode))
            if cache_key in self.episodes_cache:
                logger.info(f"Returning cached data for S{season}E{episode}")
                return self.episodes_cache[cache_key]
            
            episode_data = self._get_episode(season, episode)
            if not episode_data:
                logger.warning(f"No data found for S{season}E{episode} after all attempts.")
                # Cache the failure to avoid re-fetching repeatedly for known misses
                self.episodes_cache[cache_key] = None 
                return None
            
            # Ensure air_date is parsed if not already (it should be by the sub-methods)
            if 'air_date' in episode_data and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(episode_data['air_date'])):
                episode_data['air_date'] = parse_air_date(episode_data.get('air_date'))

            # Ensure all expected keys are present, providing defaults
            result = {
                'title': episode_data.get('title', 'Unknown'),
                'rating': episode_data.get('rating', 'N/A'),
                'votes': episode_data.get('votes', '0'),
                'season': episode_data.get('season_num', season),
                'episode': episode_data.get('episode_num', episode), # Ensure this is the actual episode number
                'air_date': str(episode_data.get('air_date', 'Unknown')),
                'image_url': episode_data.get('image_url'),
                'imdb_url': episode_data.get('imdb_url'),
                'description': episode_data.get('description', 'N/A')
            }
            
            logger.info(f"Successfully retrieved: {result['title']} (S{result['season']}E{result['episode']}) - Rating: {result['rating']}/10")
            self.episodes_cache[cache_key] = result # Cache successful result
            return result
        except Exception as e:
            logger.error(f"Error in get_episode_rating for S{season}E{episode}: {e}", exc_info=True)
            return None

def get_rating(season: Union[int, str], episode: Union[int, str]) -> Optional[dict]:
    """convenience function to get rating"""
    finder = SeinfelderIMDB()
    return finder.get_episode_rating(season, episode)

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Get IMDb rating for a Seinfeld episode.")
    parser.add_argument("season", help="Season number (e.g., 3 or '3')")
    parser.add_argument("episode", help="Episode number (e.g., 5 or '5') or episode title (e.g., 'The Pen')")
    parser.add_argument("--use_title", action="store_true", help="Indicates that the 'episode' argument is a title, not a number.")

    if len(sys.argv) == 1: # If no arguments are provided, print help and exit.
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    season_input = args.season
    episode_input = args.episode

    # If episode_input is a title, it will be passed as a string.
    # If it's an episode number, it can be passed as int or string.
    # The script logic should handle this (e.g. _try_api_method, _get_episode)

    result = get_rating(season_input, episode_input)
    if result:
        print(json.dumps(result, indent=4))
    else:
        print(f"Failed to get rating for S{season_input}E{episode_input}")
        sys.exit(1)








































































