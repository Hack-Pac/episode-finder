import requests
from bs4 import BeautifulSoup
import re

def test_imdb_fetch():
    # Try direct search API
    url = 'https://www.imdb.com/search/title/?series=tt0098904&season=3&episode=3'
    print(f'Fetching: {url}')
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first result
        result = soup.select_one('.lister-item')
        if result:
            # Get title
            title_elem = result.select_one('.lister-item-header a')
            title = title_elem.text.strip() if title_elem else 'Unknown'
            print(f'Title: {title}')
            
            # Get image
            image_elem = result.select_one('.lister-item-image img')
            image_url = None
            if image_elem:
                for attr in ['loadlate', 'src']:
                    if image_elem.has_attr(attr):
                        image_url = image_elem[attr]
                        break
            
            print(f'Image URL: {image_url}')
            
            # Get rating
            rating_elem = result.select_one('.ratings-imdb-rating strong')
            rating = rating_elem.text.strip() if rating_elem else 'N/A'
            print(f'Rating: {rating}')
        else:
            print('No search results found using .lister-item')
    else:
        print(f'Error fetching search page: {response.status_code}')
        
    # Try direct episodes page
    print('\nTrying episodes page method:')
    episodes_url = 'https://www.imdb.com/title/tt0098904/episodes?season=3'
    print(f'Fetching: {episodes_url}')
    response = requests.get(episodes_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors for episode blocks
        # Common modern IMDb selectors often involve 'ipc-' prefixes or data-testid attributes
        episode_block_selectors = [
            '.ipc-metadata-list-summary-item', # Modern layout for lists
            'div[data-testid="episodes-browse-episodes-results"] article', # Specific to episode browsing results
            '.eplist > .list_item', # Older layout
            'div.episode-item', # Another older layout
            '.episodes-container > div', 
            '[data-testid="episode-list-item"]', # Generic test id
            'section.ipc-page-section article' # More general content article
        ]

        found_episodes_block = False
        for selector in episode_block_selectors:
            episodes = soup.select(selector)
            if episodes:
                print(f'Found {len(episodes)} episodes with block selector: \"{selector}\"')
                found_episodes_block = True
                if len(episodes) >= 3:  # Try to get the 3rd episode
                    episode = episodes[2]  # 0-based index
                    
                    # Try to get title
                    title_selectors = [
                        'a.ipc-title-link-wrapper', # Modern title link
                        '.ipc-title__text', # Modern title text
                        'h4.ipc-title__text', # Title in a heading
                        'a[itemprop="name"]', 
                        '.title a', 
                        '[data-testid="title"] a',
                        '[data-testid="episodes-browse-episodes-results-item-title"]' # Very specific test id
                    ]
                    for title_selector in title_selectors:
                        title_elem = episode.select_one(title_selector)
                        if title_elem:
                            print(f'Title (using {title_selector}): {title_elem.text.strip()}')
                            break
                    
                    # Try to get image
                    image_selectors = [
                        'img.ipc-image', # Modern image
                        '.ipc-media img',
                        'img.zero-z-index', 
                        'img' # Generic image tag
                    ]
                    for img_selector in image_selectors:
                        img_elem = episode.select_one(img_selector)
                        if img_elem:
                            for attr in ['src', 'srcset', 'data-src']: # Check srcset for modern responsive images
                                if img_elem.has_attr(attr) and img_elem[attr]:
                                    img_src_val = img_elem[attr]
                                    # If srcset, take the first URL
                                    if ' ' in img_src_val and (attr == 'srcset'):
                                        img_src_val = img_src_val.split(' ')[0]
                                    print(f'Image URL (using {img_selector}/{attr}): {img_src_val}')
                                    break
                            if any(img_elem.has_attr(a) and img_elem[a] for a in ['src', 'srcset', 'data-src']):
                                break
                break 
        if not found_episodes_block:
            print('No episode block selectors matched.')
    else:
        print(f'Error fetching episodes page: {response.status_code}')

if __name__ == '__main__':
    test_imdb_fetch()
