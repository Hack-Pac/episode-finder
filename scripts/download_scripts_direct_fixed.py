#!/usr/bin/env python3
"""
Script to directly download Seinfeld scripts from seinfeldscripts.com
by accessing the individual episode URLs directly, rather than parsing the index page.
"""
import os
import re
import time
import logging
import random
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.parse
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.seinfeldscripts.com/"
OUTPUT_DIR = Path("data/scripts")
DELAY = 1  # Delay between requests to avoid overloading the server (in seconds)

# Define season and episode pattern
# Based on the website structure, scripts are named like "TheStakeout.htm"
EPISODES = [
    # Season 1
    ("Season 1", [
        ("TheSeinfeldChronicles.htm", "The Seinfeld Chronicles (Pilot)"),
        ("TheSeinfeld-Chronicles.htm", "The Seinfeld Chronicles (Pilot)"),  # Alternative URL
        ("ThePilotqt.htm", "The Pilot (Good News Bad News)"),
        ("TheStakeOut.htm", "The Stakeout"),
        ("TheRobbery.htm", "The Robbery"),
        ("MaleUnbonding.htm", "Male Unbonding"),
        ("TheStockTip.htm", "The Stock Tip"),
    ]),
    # Season 2
    ("Season 2", [
        ("TheExGirlfriend.htm", "The Ex-Girlfriend"),
        ("ThePonyRemark.htm", "The Pony Remark"),
        ("TheJacket.htm", "The Jacket"),
        ("ThePhoneMessage.htm", "The Phone Message"),
        ("TheApartment.htm", "The Apartment"),
        ("TheStatue.htm", "The Statue"),
        ("TheRevenge.htm", "The Revenge"),
        ("TheHeartAttack.htm", "The Heart Attack"),
        ("TheDeal.htm", "The Deal"),
        ("TheBabyShower.htm", "The Baby Shower"),
        ("TheChineseRestaurant.htm", "The Chinese Restaurant"),
        ("TheBusboy.htm", "The Busboy"),
    ]),
    # Season 3
    ("Season 3", [
        ("TheNote.htm", "The Note"),
        ("TheTruth.htm", "The Truth"),
        ("ThePen.htm", "The Pen"),
        ("TheDogEpisode.htm", "The Dog"),
        ("TheLibrary.htm", "The Library"),
        ("TheParkingGarage.htm", "The Parking Garage"),
        ("TheCafe.htm", "The Cafe"),
        ("TheTape.htm", "The Tape"),
        ("TheNose-Job.htm", "The Nose Job"),
        ("TheAlternateNoseJob.htm", "The Alternate Side"),
        ("TheStrangeEpisode.htm", "The Red Dot"),
        ("TheSubway.htm", "The Subway"),
        ("ThePimple.htm", "The Pimple"),
        ("TheFixUp.htm", "The Fix-Up"),
        ("TheSuicide.htm", "The Suicide"),
        ("TheLimo.htm", "The Limo"),
        ("TheGoodSamaritan.htm", "The Good Samaritan"),
        ("TheLetterEpisode.htm", "The Letter"),
        ("TheParkingSpace.htm", "The Parking Space"),
        ("TheKeys.htm", "The Keys")
    ]),
    # Season 4
    ("Season 4", [
        ("TheTrip1.htm", "The Trip (Part 1)"),
        ("TheTrip2.htm", "The Trip (Part 2)"),
        ("ThePickEpisode.htm", "The Pick"),
        ("TheMasseuseEpisode.htm", "The Masseuse"),
        ("TheShow.htm", "The Show"),
        ("TheVirginEpisode.htm", "The Virgin"),
        ("TheContest.htm", "The Contest"),
        ("TheAirport.htm", "The Airport"),
        ("TheOuting.htm", "The Outing"),
        ("TheBoyfriend-p1.htm", "The Boyfriend (Part 1)"),
        ("TheBoyfriend-p2.htm", "The Boyfriend (Part 2)"),
        ("TheShoes.htm", "The Shoes"),
        ("TheHandleBar.htm", "The Handlebar"),
        ("TheSightseer.htm", "The Junior Mint"),
        ("TheSmelly.htm", "The Smelly Car"),
        ("TheImplant.htm", "The Implant"),
        ("TheHamptonEpisode.htm", "The Hamptons"),
        ("TheDay.htm", "The Pilot (The Pilot)"),
    ]),
    # Season 5
    ("Season 5", [
        ("TheMango.htm", "The Mango"),
        ("ThePuffy.htm", "The Puffy Shirt"),
        ("TheGlasses.htm", "The Glasses"),
        ("TheSniffing.htm", "The Sniffing Accountant"),
        ("TheBris.htm", "The Bris"),
        ("TheLip.htm", "The Lip Reader"),
        ("TheNonFat.htm", "The Non-Fat Yogurt"),
        ("TheBarber.htm", "The Barber"),
        ("TheMasseuse.htm", "The Masseuse"),
        ("TheCigar.htm", "The Cigar Store Indian"),
        ("TheConversion.htm", "The Conversion"),
        ("TheStall.htm", "The Stall"),
        ("TheMarine.htm", "The Marine Biologist"),
        ("TheDinner.htm", "The Dinner Party"),
        ("ThePieEpisode.htm", "The Pie"),
        ("TheStand-In.htm", "The Stand-In"),
        ("TheWife.htm", "The Wife"),
        ("TheRaincoats.htm", "The Raincoats"),
        ("TheFireEpisode.htm", "The Fire"),
        ("TheHamptons.htm", "The Hamptons"),
        ("TheOpposite.htm", "The Opposite")
    ]),
    # Season 6
    ("Season 6", [
        ("TheChaperone.htm", "The Chaperone"),
        ("TheBigSalad.htm", "The Big Salad"),
        ("ThePledge.htm", "The Pledge Drive"),
        ("TheChineseWoman.htm", "The Chinese Woman"),
        ("TheCouch.htm", "The Couch"),
        ("TheGymnast.htm", "The Gymnast"),
        ("TheSoupEpisode.htm", "The Soup"),
        ("TheMomAndPop.htm", "The Mom & Pop Store"),
        ("TheSecretCode.htm", "The Secret Code"),
        ("TheRace.htm", "The Race"),
        ("TheLabelMaker.htm", "The Label Maker"),
        ("TheScofflaw.htm", "The Scofflaw"),
        ("TheHighlight.htm", "Highlights of a Hundred"),
        ("TheCaddy.htm", "The Caddy"),
        ("TheDoodle.htm", "The Doodle"),
        ("TheBeard.htm", "The Beard"),
        ("ThePRMan.htm", "The Kiss Hello"),
        ("TheDoorman.htm", "The Doorman"),
        ("TheJimmyEpisode.htm", "The Jimmy"),
        ("TheDipEpisode.htm", "The Dip"),
        ("TheFace.htm", "The Face Painter"),
        ("TheUnderstudy.htm", "The Understudy")
    ]),
    # Season 7
    ("Season 7", [
        ("TheEngagement.htm", "The Engagement"),
        ("ThePostponement.htm", "The Postponement"),
        ("TheMaestro.htm", "The Maestro"),
        ("TheWinking.htm", "The Winking"),
        ("TheHotTub.htm", "The Hot Tub"),
        ("TheSoup.htm", "The Soup Nazi"),
        ("TheSecretCode.htm", "The Secret Code"),
        ("ThePool.htm", "The Pool Guy"),
        ("TheSponge.htm", "The Sponge"),
        ("TheGum.htm", "The Gum"),
        ("TheRye.htm", "The Rye"),
        ("TheCadillac1.htm", "The Cadillac (Part 1)"),
        ("TheCadillac2.htm", "The Cadillac (Part 2)"),
        ("TheShowerHead.htm", "The Shower Head"),
        ("TheDoll.htm", "The Doll"),
        ("TheFriarsClub.htm", "The Friars Club"),
        ("TheWig.htm", "The Wig Master"),
        ("TheCalzone.htm", "The Calzone"),
        ("TheBottle.htm", "The Bottle Deposit"),
        ("TheWait.htm", "The Wait Out"),
        ("TheInvitations.htm", "The Invitations")
    ]),
    # Season 8
    ("Season 8", [
        ("TheFoundation.htm", "The Foundation"),
        ("TheSoulMate.htm", "The Soul Mate"),
        ("TheBizarro.htm", "The Bizarro Jerry"),
        ("TheLittleKicks.htm", "The Little Kicks"),
        ("ThePackage.htm", "The Package"),
        ("TheApology.htm", "The Apology"),
        ("TheCadillacs.htm", "The Cadillacs"),
        ("TheMaid.htm", "The Maid"),
        ("TheNewberry.htm", "The Yada Yada"),
        ("TheCheck.htm", "The Check"),
        ("ThePothole.htm", "The Pothole"),
        ("TheEnglish.htm", "The English Patient"),
        ("TheNap.htm", "The Nap"),
        ("TheYadaYada.htm", "The Yada Yada"),
        ("TheMillennium.htm", "The Millennium"),
        ("TheShowerHead2.htm", "The Muffin Tops"),
        ("ThePhony2.htm", "The Summer of George")
    ]),
    # Season 9
    ("Season 9", [
        ("TheButterShave.htm", "The Butter Shave"),
        ("TheVoice.htm", "The Voice"),
        ("TheSerenity.htm", "The Serenity Now"),
        ("TheMercedes.htm", "The Blood"),
        ("TheJunk.htm", "The Junk Mail"),
        ("TheMerv.htm", "The Merv Griffin Show"),
        ("TheSlicer.htm", "The Slicer"),
        ("TheBetrayal.htm", "The Betrayal"),
        ("TheApology2.htm", "The Apology"),
        ("TheStrike.htm", "The Strike"),
        ("TheSubwayEpisode.htm", "The Subway"),
        ("TheReverse.htm", "The Reverse Peephole"),
        ("TheCartoon.htm", "The Cartoon"),
        ("TheBurnout.htm", "The Strong Box"),
        ("TheWizard.htm", "The Wizard"),
        ("TheBurning.htm", "The Burning"),
        ("ThePuertoRican.htm", "The Puerto Rican Day"),
        ("TheChronicle1.htm", "The Chronicle (Part 1)"),
        ("TheChronicle2.htm", "The Chronicle (Part 2)"),
        ("TheFinale1.htm", "The Finale (Part 1)"),
        ("TheFinale2.htm", "The Finale (Part 2)")
    ])
]
def sanitize_filename(filename):
    """Convert a string to a valid filename"""
    # Replace invalid characters with underscores
    valid_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Remove leading/trailing spaces and dots
    valid_filename = valid_filename.strip(". ")
    return valid_filename

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not path.exists():
        path.mkdir(parents=True)
        logger.info(f"Created directory: {path}")

def get_page_content(url):
    """Get HTML content from a URL with error handling and retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(DELAY * 2)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

def extract_script_content(html_content):
    """Extract the actual script content from a script page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find the content in several ways since the site structure might vary
    
    # 1. First try to find main content areas
    content = None
    content_candidates = [
        soup.find('div', class_='content'),  # Try class='content'
        soup.find('div', id='content'),      # Try id='content'
        soup.find('pre'),                    # Some scripts are just in a pre tag
        soup.find('body')                    # Fall back to body if needed
    ]
    
    for candidate in content_candidates:
        if candidate:
            content = candidate
            break
            
    if not content:
        return "Could not find script content"
    
    # 2. Now extract the text - considering multiple formats
    script_content = ""
    
    # Try to find the script in pre tags first (formatted scripts)
    pre_tags = content.find_all('pre')
    if pre_tags:
        for pre in pre_tags:
            script_content += pre.get_text() + "\n\n"
    else:
        # Otherwise try to get text from paragraphs
        paragraphs = content.find_all(['p', 'div', 'font'])
        if paragraphs:
            for p in paragraphs:
                # Skip navigation or header paragraphs
                if any(x in p.get_text().lower() for x in ['home', 'scripts', 'episodes', 'next', 'previous']):
                    if len(p.get_text()) < 100:  # Skip only if it's a short nav element
                        continue
                script_content += p.get_text().strip() + "\n\n"
        else:
            # Last resort: just get all text
            script_content = content.get_text()
    
    # Clean up the script content
    script_content = re.sub(r'\n{3,}', '\n\n', script_content)  # Remove excessive newlines
    
    # Remove common navigation or website elements
    lines = script_content.split('\n')
    cleaned_lines = []
    
    skip_patterns = [
        r'^home$', r'^episodes$', r'^scripts$', r'^previous$', r'^next$', 
        r'^back to scripts$', r'^back to seinfeld$', r'^copyright', r'^all rights reserved',
        r'^seinfeldscripts\.com', r'^www\.seinfeldscripts\.com'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append('')
            continue
            
        # Skip navigation links and copyright notices
        if any(re.search(pattern, line.lower()) for pattern in skip_patterns):
            continue
            
        # Keep the line if it's not filtered out
        cleaned_lines.append(line)
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Final cleanup for multi-line breaks
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
    
    return cleaned_content.strip()

def verify_links(check_all=False):
    """Verify that the episode links are valid
    
    Args:
        check_all: If True, check all links. If False, just do a quick sample check.
    
    Returns:
        bool: True if all checked links are valid, False otherwise
    """
    if not check_all:
        # Just check one episode from the first and last season
        sample_links = [
            (EPISODES[0][0], EPISODES[0][1][0][0]),  # First episode of first season
            (EPISODES[-1][0], EPISODES[-1][1][-1][0])  # Last episode of last season
        ]
        
        for season_name, script_file in sample_links:
            url = urllib.parse.urljoin(BASE_URL, script_file.strip())
            logger.info(f"Verifying link: {url}")
            
            if not get_page_content(url):
                logger.error(f"Could not verify link: {url}")
                return False
        
        logger.info("Sample links verified successfully")
        return True
    else:
        # Check all links (this could take a while)
        logger.info("Verifying all links (this may take a while)...")
        invalid_links = []
        
        with tqdm(total=sum(len(episodes) for _, episodes in EPISODES), 
                  desc="Checking links") as pbar:
            for season_name, episodes in EPISODES:
                for script_file, episode_title in episodes:
                    url = urllib.parse.urljoin(BASE_URL, script_file.strip())
                    
                    content = get_page_content(url)
                    if not content:
                        invalid_links.append((season_name, episode_title, url))
                    
                    # Use a small delay to avoid hammering the server
                    time.sleep(0.2)
                    pbar.update(1)
        
        if invalid_links:
            logger.error(f"Found {len(invalid_links)} invalid links:")
            for season, title, url in invalid_links:
                logger.error(f" - [{season}] {title}: {url}")
            return False
        
        logger.info("All links verified successfully")
        return True

def download_and_save_scripts(selected_seasons=None, force_download=False):
    """Main function to download and organize scripts
    
    Args:
        selected_seasons: List of seasons to download, None means all seasons
        force_download: If True, re-download even if script file exists
    """
    # Create the base output directory
    create_directory(OUTPUT_DIR)
    
    # Use selected seasons or default to all
    seasons_to_process = selected_seasons if selected_seasons is not None else EPISODES
    
    total_episodes = sum(len(episodes) for _, episodes in seasons_to_process)
    scripts_downloaded = 0
    scripts_failed = 0
    
    # Track which episodes we've already processed (to handle duplicates)
    processed_episodes = set()
    
    with tqdm(total=total_episodes, desc="Downloading scripts") as pbar:
        for season_name, episodes in seasons_to_process:
            # Create season directory
            season_dir = OUTPUT_DIR / sanitize_filename(season_name)
            create_directory(season_dir)
            
            for script_file, episode_title in episodes:
                # Use a random delay between 0.5 and 2 seconds to avoid detection
                sleep_time = DELAY * (0.5 + random.random() * 1.5)  # Random between 0.5*DELAY and 2*DELAY
                time.sleep(sleep_time)
                try:
                    url = urllib.parse.urljoin(BASE_URL, script_file.strip())
                    
                    # Create a unique filename using both title and script filename
                    # This helps when the same episode has multiple URLs
                    base_name = sanitize_filename(episode_title)
                    file_name = f"{base_name}.txt"
                    file_path = season_dir / file_name
                    
                    # Handle duplicate filenames by appending the script file name
                    if episode_title in processed_episodes and not file_path.exists():
                        script_name = script_file.replace('.htm', '').replace('.html', '')
                        file_name = f"{base_name}_{script_name}.txt"
                        file_path = season_dir / file_name
                    
                    # Mark as processed
                    processed_episodes.add(episode_title)
                    
                    # Skip if already downloaded and not forcing re-download
                    if file_path.exists() and not force_download:
                        logger.info(f"Script already exists: {file_path}")
                        scripts_downloaded += 1
                        pbar.update(1)
                        continue
                    elif file_path.exists() and force_download:
                        logger.info(f"Re-downloading: {file_path}")
                    
                    # Get script content
                    logger.info(f"Downloading: {episode_title} [{season_name}] from {url}")
                    html_content = get_page_content(url)
                    if not html_content:
                        logger.error(f"Failed to download {episode_title} - URL may be invalid")
                        scripts_failed += 1
                        pbar.update(1)
                        continue
                    
                    # Extract script text
                    script_content = extract_script_content(html_content)
                    if len(script_content) < 500:  # Basic check for empty scripts
                        logger.warning(f"Script content for {episode_title} seems too short ({len(script_content)} chars)")
                    
                    # Save script to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {episode_title}\n")
                        f.write(f"Season: {season_name}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(script_content)
                    
                    scripts_downloaded += 1
                    logger.info(f"Saved script: {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing script {episode_title}: {e}")
                    scripts_failed += 1
                
                pbar.update(1)
    
    # Generate summary report
    logger.info(f"Download complete. {scripts_downloaded} scripts downloaded, {scripts_failed} failed.")
    
    # Create a summary file
    summary_file = OUTPUT_DIR / "download_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Seinfeld Scripts Download Summary\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total episodes attempted: {total_episodes}\n")
        f.write(f"Successfully downloaded: {scripts_downloaded}\n")
        f.write(f"Failed: {scripts_failed}\n\n")
        
        f.write("Episodes by season:\n")
        for season_name, episodes in EPISODES:
            f.write(f"{season_name}: {len(episodes)} episodes\n")
    
    return scripts_failed == 0

def list_available_seasons():
    """Print available seasons for download"""
    print("\nAvailable seasons:")
    for i, (season_name, episodes) in enumerate(EPISODES):
        print(f"{i+1}. {season_name}: {len(episodes)} episodes")
    print(f"0. All seasons ({sum(len(episodes) for _, episodes in EPISODES)} episodes)")

if __name__ == "__main__":
    print("Starting Seinfeld Scripts Downloader...")
    import argparse
    
    parser = argparse.ArgumentParser(description='Download Seinfeld scripts from seinfeldscripts.com')
    parser.add_argument('-s', '--season', type=int, help='Season number to download (1-9), or 0 for all seasons')
    parser.add_argument('-l', '--list', action='store_true', help='List available seasons')
    parser.add_argument('-f', '--force', action='store_true', help='Force re-download of existing scripts')
    parser.add_argument('-v', '--verify', action='store_true', help='Verify links without downloading')
    parser.add_argument('--check-all', action='store_true', help='Check all links (use with --verify)')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_seasons()
        exit(0)
    
    if args.verify:
        logger.info("Verifying links before downloading")
        if verify_links(args.check_all):
            logger.info("All verified links are valid")
            if not args.season and not args.force:  # If only verifying, exit after verification
                exit(0)
        else:
            logger.error("Link verification failed")
            if not args.force:  # Exit unless forcing download
                exit(1)
    
    # Determine which seasons to download
    selected_seasons = EPISODES
    if args.season is not None:
        if args.season == 0:
            logger.info("Downloading all seasons")
        elif 1 <= args.season <= len(EPISODES):
            selected_seasons = [EPISODES[args.season-1]]
            logger.info(f"Downloading only {selected_seasons[0][0]}")
        else:
            logger.error(f"Invalid season number: {args.season}")
            list_available_seasons()
            exit(1)
    
    logger.info("Starting Seinfeld scripts download")
    success = download_and_save_scripts(
        selected_seasons=selected_seasons,
        force_download=args.force
    )
    
    if success:
        logger.info("Script download completed successfully")
    else:
        logger.error("Script download failed")















