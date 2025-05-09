#!/usr/bin/env python3
"""
Improved script to download Seinfeld scripts from seinfeldscripts.com
with updated URLs and better error handling
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

# Updated URLs based on the current website structure and discovery results
EPISODES = [    # Season 1
    ("Season 1", [
        ("TheSeinfeldChronicles.htm", "The Seinfeld Chronicles (Pilot)"),  # From url_discovery_report
        ("TheSeinfeld-Chronicles.htm", "The Seinfeld Chronicles (Pilot)"),  # Alternative URL
        ("TheSeinfeldChronicles.html", "The Seinfeld Chronicles (Pilot)"),  # Try .html extension
        ("TheStakeout.htm", "The Stakeout"),  # Fixed based on successful downloads
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
        ("TheNote.htm", "The Note"),  # Fixed based on discovered URLs
        ("TheTruth.htm", "The Truth"),
        ("ThePen.htm", "The Pen"),
        ("TheDog.htm", "The Dog"),  # Fixed based on successful downloads
        ("TheLibrary.htm", "The Library"),
        ("TheParkingGarage.htm", "The Parking Garage"),
        ("TheCafe.htm", "The Cafe"),
        ("TheTape.htm", "The Tape"),
        ("TheNoseJob.htm", "The Nose Job"),  # Fixed based on successful downloads
        ("TheAlternateSide.htm", "The Alternate Side"),  # Fixed based on successful downloads
        ("TheRedDot.htm", "The Red Dot"),  # Fixed based on successful downloads
        ("TheSubway.htm", "The Subway"),
        # Remove non-existent "The Pimple" and replace with the correct episode
        ("ThePezDispenser.htm", "The Pez Dispenser"),  # Correct episode name
        ("ThePezDispenser.html", "The Pez Dispenser"),  # Try alternate extension
        ("TheFixUp.htm", "The Fix-Up"),  # Fixed based on successful downloads
        ("TheSuicide.htm", "The Suicide"),
        ("TheLimo.htm", "The Limo"),
        ("TheGoodSamaritan.htm", "The Good Samaritan"),
        ("TheLetter.htm", "The Letter"),  # Fixed based on successful downloads
        ("TheParkingSpace.htm", "The Parking Space"),
        ("TheKeys.htm", "The Keys")
    ]),
    # Season 4
    ("Season 4", [
        ("TheTrip1.htm", "The Trip (Part 1)"),
        ("TheTrip2.htm", "The Trip (Part 2)"),
        ("ThePitch.htm", "The Pitch"),
        ("TheTicket.htm", "The Ticket"),
        ("TheWallet.htm", "The Wallet"),
        ("TheWatch.htm", "The Watch"),
        ("TheBubbleBoy.htm", "The Bubble Boy"),
        ("TheCheeverLetters.htm", "The Cheever Letters"),
        ("TheOpera.htm", "The Opera"),
        ("ThePick.htm", "The Pick"), 
        ("TheMasseuse.htm", "The Masseuse"),
        # Remove non-existent "The Show" and replace with the correct episode
        ("TheMovie.htm", "The Movie"),  # Correct episode name
        ("TheMovie.html", "The Movie"),  # Try alternate extension
        ("TheVirgin.htm", "The Virgin"),
        ("TheContest.htm", "The Contest"),
        ("TheAirport.htm", "The Airport"),
        ("TheOuting.htm", "The Outing"),
        ("TheBoyfriend1.htm", "The Boyfriend (Part 1)"),
        ("TheBoyfriend2.htm", "The Boyfriend (Part 2)"),
        ("TheShoes.htm", "The Shoes"),
        # Remove non-existent "The Handlebar" and replace with the correct episode
        ("TheOldMan.htm", "The Old Man"),  # Correct episode name
        ("TheOldMan.html", "The Old Man"),  # Try alternate extension
        ("TheJuniorMint.htm", "The Junior Mint"),
        ("TheJuniorMints.htm", "The Junior Mint"),# From url_discovery_report - CONFIRMED
        ("TheJuniorMint.html", "The Junior Mint"),  # Try alternate extension        
        ("TheSmellyCar.htm", "The Smelly Car"),  # From url_discovery_report - CONFIRMED
        ("TheSmellyCarEpisode.htm", "The Smelly Car"),
        ("TheImplant.htm", "The Implant"),
        ("TheHandicapSpot.htm", "The Handicap Spot"),  # Fixed based on discovered URLs
        ("ThePilot.htm", "The Pilot (Part 1)"),  # Fixed URL based on discovery
        ("ThePilot2.htm", "The Pilot (Part 2)")  # Added part 2 based on discovery
    ]),
    # Season 5
    ("Season 5", [
        ("TheMango.htm", "The Mango"),
        ("ThePuffyShirt.htm", "The Puffy Shirt"),
        ("TheGlasses.htm", "The Glasses"),
        ("TheSniffingAccountant.htm", "The Sniffing Accountant"),
        ("TheBris.htm", "The Bris"),
        ("TheLipReader.htm", "The Lip Reader"),
        ("TheNonFatYogurt.htm", "The Non-Fat Yogurt"),
        ("TheBarber.htm", "The Barber"),
        ("TheMasseuse.htm", "The Masseuse"), # Note: duplicate with Season 4
        ("TheCigarStoreIndian.htm", "The Cigar Store Indian"),
        ("TheConversion.htm", "The Conversion"),
        ("TheStall.htm", "The Stall"),
        ("TheMarineBiologist.htm", "The Marine Biologist"),
        ("TheDinnerParty.htm", "The Dinner Party"),
        ("ThePie.htm", "The Pie"),
        ("TheStand-In.htm", "The Stand-In"),
        ("TheWife.htm", "The Wife"),
        ("TheRaincoats.htm", "The Raincoats"),
        ("TheFire.htm", "The Fire"),
        ("TheHamptons.htm", "The Hamptons"), # Note: duplicate with Season 4
        ("TheOpposite.htm", "The Opposite")
    ]),
    # Season 6
    ("Season 6", [
        ("TheChaperone.htm", "The Chaperone"),
        ("TheBigSalad.htm", "The Big Salad"),
        ("ThePledgeDrive.htm", "The Pledge Drive"),
        ("TheChineseWoman.htm", "The Chinese Woman"),
        ("TheCouch.htm", "The Couch"),
        ("TheGymnast.htm", "The Gymnast"),
        ("TheSoup.htm", "The Soup"),
        ("TheMomAndPopStore.htm", "The Mom & Pop Store"),
        ("TheSecretary.htm", "The Secretary"),
        ("TheSecretCode.htm", "The Secret Code"),
        ("TheSecretCode2.htm", "The Secret Code"),  # From url_discovery_report
        ("TheRace.htm", "The Race"),
        ("TheLabelMaker.htm", "The Label Maker"),
        ("TheScofflaw.htm", "The Scofflaw"),
        ("TheSwitch.htm", "The Switch"),
        ("TheHighlightsofaHundred.htm", "Highlights of a Hundred"),
        ("The-Clip-Show-1.html", "Highlights of a Hundred"),  # Alternative name
        ("TheCaddy.htm", "The Caddy"),
        ("TheDoodle.htm", "The Doodle"),
        ("TheBeard.htm", "The Beard"),
        ("TheKissHello.htm", "The Kiss Hello"),
        ("TheDoorman.htm", "The Doorman"),
        ("TheJimmy.htm", "The Jimmy"),
        # Remove non-existent "The Dip" and replace with the correct episode
        ("TheDiplomatClub.htm", "The Diplomat's Club"),  # Correct episode name
        ("TheDiplomatClub.html", "The Diplomat's Club"),  # Try alternate extension
        ("TheFusilliJerry.htm", "The Fusilli Jerry"),
        ("TheFacePainter.htm", "The Face Painter"),
        ("TheUnderstudy.htm", "The Understudy")
    ]),
    # Season 7
    ("Season 7", [
        ("TheEngagement.html", "The Engagement"),     # Fixed URL based on discovery
        ("ThePostponement.htm", "The Postponement"),
        ("TheMaestro.htm", "The Maestro"),
        ("TheWink.htm", "The Wink"),
        ("TheHotTub.htm", "The Hot Tub"),
        ("TheSoupNazi.htm", "The Soup Nazi"),
        ("TheSecretCode2.htm", "The Secret Code"),    # Fixed URL based on discovery
        ("ThePoolGuy.htm", "The Pool Guy"),
        ("TheSponge.html", "The Sponge"),             # Fixed URL based on discovery
        ("TheGum.html", "The Gum"),                   # Fixed URL based on discovery
        ("TheRye.htm", "The Rye"),
        ("TheCadillac1.html", "The Cadillac (Part 1)"), # CONFIRMED from url_discovery
        ("TheCadillac1.htm", "The Cadillac (Part 1)"),  # Alternative extension
        ("TheCadillac2.html", "The Cadillac (Part 2)"), # CONFIRMED from url_discovery
        ("TheCadillac2.htm", "The Cadillac (Part 2)"),  # Alternative extension
        ("TheShowerhead.htm", "The Shower Head"),      # Fixed URL based on discovery
        ("TheDoll.htm", "The Doll"),
        ("TheFriarsClub.html", "The Friars Club"),     # Fixed URL based on discovery
        ("TheWigMaster.htm", "The Wig Master"),
        ("TheCalzone.htm", "The Calzone"),
        ("TheBottleDeposit1.html", "The Bottle Deposit (Part 1)"), # Fixed URL based on discovery
        ("TheBottleDeposit2.html", "The Bottle Deposit (Part 2)"), # Added part 2 based on discovery
        ("TheWaitOut.htm", "The Wait Out"),
        ("TheInvitations.htm", "The Invitations")
    ]),
    # Season 8
    ("Season 8", [
        ("TheFoundation.html", "The Foundation"),
        ("TheSoulMate.html", "The Soul Mate"),
        ("TheBizarroJerry.htm", "The Bizarro Jerry"),
        ("TheLittleKicks.htm", "The Little Kicks"),
        ("ThePackage.htm", "The Package"),
        ("TheFatigues.htm", "The Fatigues"),
        # Remove duplicate "The Cadillac" as it's in Season 7, not 8
        ("TheMaid.htm", "The Maid"),
        ("TheYadaYada.html", "The Yada Yada"),  # Fixed URL based on discovery
        ("TheChecks.html", "The Checks"),
        ("ThePothole.htm", "The Pothole"),
        ("TheEnglishPatient.html", "The English Patient"),
        ("TheNap.html", "The Nap"),
        ("TheYadaYada.htm", "The Yada Yada (2)"),
        ("TheMillennium.html", "The Millennium"),
        ("TheMuffinTops.htm", "The Muffin Tops"),
        ("TheSummerofGeorge.htm", "The Summer of George")  # Fixed URL based on discovery
    ]),
    # Season 9
    ("Season 9", [
        ("TheButterShave.htm", "The Butter Shave"),
        ("TheVoice.htm", "The Voice"),
        ("TheSerenityNow.htm", "The Serenity Now"),
        ("TheBlood.html", "The Blood"),
        ("TheJunkMail.htm", "The Junk Mail"),
        ("TheMervGriffinShow.htm", "The Merv Griffin Show"),
        ("TheSlicer.html", "The Slicer"),
        ("TheBetrayal.htm", "The Betrayal"),
        ("TheApology.htm", "The Apology"), # Note: duplicate name from S8
        ("TheStrike.htm", "The Strike"),
        ("TheSubway.htm", "The Subway"), # Note: duplicate with Season 3
        ("TheReversePeephole.htm", "The Reverse Peephole"),  # Fixed URL based on discovery
        ("TheCartoon.htm", "The Cartoon"),
        ("TheStrongbox.htm", "The Strong Box"),
        ("TheWizard.htm", "The Wizard"),
        ("TheBurning.html", "The Burning"),
        ("ThePuertoRicanDay.htm", "The Puerto Rican Day"),
        ("The-Clip-Show-1.html", "The Chronicle (Part 1)"),  # Fixed URL based on discovery
        ("The-Clip-Show-2.html", "The Chronicle (Part 2)"),  # Added part 2 based on discovery
        ("TheFinale.htm", "The Finale")
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

def try_alternate_extensions(script_file, episode_title):
    """Try alternate file extensions if the main one fails"""
    alternates = []
    
    # If .htm, try .html and vice versa
    base_name = script_file.rsplit('.', 1)[0]
    if script_file.endswith('.htm'):
        alternates.append((f"{base_name}.html", episode_title))
    elif script_file.endswith('.html'):
        alternates.append((f"{base_name}.htm", episode_title))
    
    return alternates

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
    
    # Track successful URLs for reporting
    successful_urls = []
    failed_urls = []
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
                    
                    # If failed, try alternate extensions (.htm vs .html)
                    if not html_content:
                        alternates = try_alternate_extensions(script_file, episode_title)
                        for alt_script, _ in alternates:
                            alt_url = urllib.parse.urljoin(BASE_URL, alt_script.strip())
                            logger.info(f"Trying alternate URL: {alt_url}")
                            html_content = get_page_content(alt_url)
                            if html_content:
                                url = alt_url  # Use the successful URL
                                break
                    
                    if not html_content:
                        logger.error(f"Failed to download {episode_title} - URL may be invalid")
                        failed_urls.append((season_name, episode_title, url))
                        scripts_failed += 1
                        pbar.update(1)
                        continue
                    
                    # Extract script text
                    script_content = extract_script_content(html_content)
                    
                    # Check if content is too short (might be empty or error page)
                    if len(script_content) < 500:
                        logger.warning(f"Script content for {episode_title} seems too short ({len(script_content)} chars)")
                    
                    # Save script to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {episode_title}\n")
                        f.write(f"Season: {season_name}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(script_content)
                    scripts_downloaded += 1
                    successful_urls.append((season_name, episode_title, url))
                    logger.info(f"Saved script: {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing script {episode_title}: {e}")
                    failed_urls.append((season_name, episode_title, url if 'url' in locals() else "Unknown URL"))
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
        
        # Write out failed URLs for later reference
        if failed_urls:
            f.write("\nFailed URLs:\n")
            for season, title, url in failed_urls:
                f.write(f"- [{season}] {title}: {url}\n")
    
    return scripts_failed == 0

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
                        # Try alternate extension
                        alternates = try_alternate_extensions(script_file, episode_title)
                        alternate_found = False
                        for alt_script, _ in alternates:
                            alt_url = urllib.parse.urljoin(BASE_URL, alt_script.strip())
                            content = get_page_content(alt_url)
                            if content:
                                alternate_found = True
                                break
                        
                        if not alternate_found:
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

def list_available_seasons():
    """Print available seasons for download"""
    print("\nAvailable seasons:")
    for i, (season_name, episodes) in enumerate(EPISODES):
        print(f"{i+1}. {season_name}: {len(episodes)} episodes")
    print(f"0. All seasons ({sum(len(episodes) for _, episodes in EPISODES)} episodes)")

if __name__ == "__main__":
    import argparse
    
    # Print startup message to ensure script is running
    print("=" * 60)
    print("SEINFELD SCRIPTS DOWNLOADER (IMPROVED VERSION)")
    print("=" * 60)
    print("This script will download scripts from seinfeldscripts.com")
    print("It includes fixes for invalid URLs and better error handling")
    print()
    
    parser = argparse.ArgumentParser(description='Download Seinfeld scripts from seinfeldscripts.com')
    parser.add_argument('-s', '--season', type=int, help='Season number to download (1-9), or 0 for all seasons')
    parser.add_argument('-l', '--list', action='store_true', help='List available seasons')
    parser.add_argument('-f', '--force', action='store_true', help='Force re-download of existing scripts')
    parser.add_argument('-v', '--verify', action='store_true', help='Verify links without downloading')
    parser.add_argument('--check-all', action='store_true', help='Check all links (use with --verify)')
    
    args = parser.parse_args()
    
    print("Starting Seinfeld Scripts Downloader...")
    if args.list:
        list_available_seasons()
        exit(0)
    
    if args.verify:
        success = verify_links(args.check_all)
        exit(0 if success else 1)
    
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
        logger.error("Script download failed but some scripts were downloaded")






















