#!/usr/bin/env python3
"""
Script to find missing Seinfeld episodes by comparing with the official list
"""

import os
import re
from pathlib import Path

# Set the base directory to ensure we're looking in the right place
BASE_DIR = Path(r'c:\Users\sebas\Programming\episode-finder')

# Official episodes from the website (extracted manually from the fetched content)
official_episodes = [
    'The Seinfeld Chronicles', 'The Stakeout', 'The Robbery', 'Male Unbonding', 'The Stock Tip',
    'The Ex-Girlfriend', 'The Pony Remark', 'The Jacket', 'The Phone Message', 'The Apartment',
    'The Statue', 'The Revenge', 'The Heart Attack', 'The Deal', 'The Baby Shower', 
    'The Chinese Restaurant', 'The Busboy', 'The Note', 'The Truth', 'The Pen',
    'The Dog', 'The Library', 'The Parking Garage', 'The Cafe', 'The Tape', 
    'The Nose Job', 'The Stranded', 'The Alternate Side', 'The Red Dot', 'The Subway',
    'The Pez Dispenser', 'The Suicide', 'The Fix-Up', 'The Boyfriend (1)', 'The Boyfriend (2)',
    'The Limo', 'The Good Samaritan', 'The Letter', 'The Parking Spot', 'The Keys',
    'The Trip (1)', 'The Trip (2)', 'The Pitch', 'The Ticket', 'The Wallet',
    'The Watch', 'The Bubble Boy', 'The Cheever Letters', 'The Opera', 'The Virgin',
    'The Contest', 'The Airport', 'The Pick', 'The Movie', 'The Visa',
    'The Shoes', 'The Outing', 'The Old Man', 'The Implant', 'The Junior Mint',
    'The Smelly Car', 'The Handicap Spot', 'The Pilot (1)', 'The Pilot (2)', 'The Mango',
    'The Puffy Shirt', 'The Glasses', 'The Sniffing Accountant', 'The Bris', 'The Lip Reader',
    'The Non-Fat Yogurt', 'The Barber', 'The Masseuse', 'The Cigar Store Indian', 'The Conversion',
    'The Stall', 'The Dinner Party', 'The Marine Biologist', 'The Pie', 'The Stand-In',
    'The Wife', 'The Raincoats (1)', 'The Raincoats (2)', 'The Fire', 'The Hamptons',
    'The Opposite', 'The Chaperone', 'The Big Salad', 'The Pledge Drive', 'The Chinese Woman',
    'The Couch', 'The Gymnast', 'The Soup', 'The Mom & Pop Store', 'The Secretary',
    'The Race', 'The Switch', 'The Label Maker', 'The Scofflaw', 'Highlights of 100 (1)',
    'Highlights of 100 (2)', 'The Beard', 'The Kiss Hello', 'The Doorman', 'The Jimmy',
    'The Doodle', 'The Fusilli Jerry', "The Diplomat's Club", 'The Face Painter', 'The Understudy',
    'The Engagement', 'The Postponement', 'The Maestro', 'The Wink', 'The Hot Tub',
    'The Soup Nazi', 'The Secret Code', 'The Pool Guy', 'The Sponge', 'The Gum',
    'The Rye', 'The Caddy', 'The Seven', 'The Cadillac (1)', 'The Cadillac (2)',
    'The Shower Head', 'The Doll', 'The Friars Club', 'The Wig Master', 'The Calzone',
    'The Bottle Deposit (1)', 'The Bottle Deposit (2)', 'The Wait Out', 'The Invitations', 'The Foundation',
    'The Soul Mate', 'The Bizarro Jerry', 'The Little Kicks', 'The Package', 'The Fatigues',
    'The Checks', 'The Chicken Roaster', 'The Abstinence', 'The Andrea Doria', 'The Little Jerry',
    'The Money', 'The Comeback', 'The Van Buren Boys', 'The Susie', 'The Pothole',
    'The English Patient', 'The Nap', 'The Yada Yada', 'The Millennium', 'The Muffin Tops',
    'The Summer of George', 'The Butter Shave', 'The Voice', 'The Serenity Now', 'The Blood',
    'The Junk Mail', 'The Merv Griffin Show', 'The Slicer', 'The Betrayal', 'The Apology',
    'The Strike', 'The Dealership', 'The Reverse Peephole', 'The Cartoon', 'The Strongbox',
    'The Wizard', 'The Burning', 'The Bookstore', 'The Frogger', 'The Maid',
    'The Puerto Rican Day', 'The Clip Show (1)', 'The Clip Show (2)', 'The Finale (1)', 'The Finale (2)'
]

# Season mapping (episode number to season)
episode_to_season = {
    'The Seinfeld Chronicles': 1, 'The Stakeout': 1, 'The Robbery': 1, 'Male Unbonding': 1, 'The Stock Tip': 1,
    'The Ex-Girlfriend': 2, 'The Pony Remark': 2, 'The Jacket': 2, 'The Phone Message': 2, 'The Apartment': 2,
    'The Statue': 2, 'The Revenge': 2, 'The Heart Attack': 2, 'The Deal': 2, 'The Baby Shower': 2, 
    'The Chinese Restaurant': 2, 'The Busboy': 2, 'The Note': 3, 'The Truth': 3, 'The Pen': 3,
    'The Dog': 3, 'The Library': 3, 'The Parking Garage': 3, 'The Cafe': 3, 'The Tape': 3, 
    'The Nose Job': 3, 'The Stranded': 3, 'The Alternate Side': 3, 'The Red Dot': 3, 'The Subway': 3,
    'The Pez Dispenser': 3, 'The Suicide': 3, 'The Fix-Up': 3, 'The Boyfriend (1)': 3, 'The Boyfriend (2)': 3,
    'The Limo': 3, 'The Good Samaritan': 3, 'The Letter': 3, 'The Parking Spot': 3, 'The Keys': 3,
    'The Trip (1)': 4, 'The Trip (2)': 4, 'The Pitch': 4, 'The Ticket': 4, 'The Wallet': 4,
    'The Watch': 4, 'The Bubble Boy': 4, 'The Cheever Letters': 4, 'The Opera': 4, 'The Virgin': 4,
    'The Contest': 4, 'The Airport': 4, 'The Pick': 4, 'The Movie': 4, 'The Visa': 4,
    'The Shoes': 4, 'The Outing': 4, 'The Old Man': 4, 'The Implant': 4, 'The Junior Mint': 4,
    'The Smelly Car': 4, 'The Handicap Spot': 4, 'The Pilot (1)': 4, 'The Pilot (2)': 4, 'The Mango': 5,
    'The Puffy Shirt': 5, 'The Glasses': 5, 'The Sniffing Accountant': 5, 'The Bris': 5, 'The Lip Reader': 5,
    'The Non-Fat Yogurt': 5, 'The Barber': 5, 'The Masseuse': 5, 'The Cigar Store Indian': 5, 'The Conversion': 5,
    'The Stall': 5, 'The Dinner Party': 5, 'The Marine Biologist': 5, 'The Pie': 5, 'The Stand-In': 5,
    'The Wife': 5, 'The Raincoats (1)': 5, 'The Raincoats (2)': 5, 'The Fire': 5, 'The Hamptons': 5,
    'The Opposite': 5, 'The Chaperone': 6, 'The Big Salad': 6, 'The Pledge Drive': 6, 'The Chinese Woman': 6,
    'The Couch': 6, 'The Gymnast': 6, 'The Soup': 6, 'The Mom & Pop Store': 6, 'The Secretary': 6,
    'The Race': 6, 'The Switch': 6, 'The Label Maker': 6, 'The Scofflaw': 6, 'Highlights of 100 (1)': 6,
    'Highlights of 100 (2)': 6, 'The Beard': 6, 'The Kiss Hello': 6, 'The Doorman': 6, 'The Jimmy': 6,
    'The Doodle': 6, 'The Fusilli Jerry': 6, "The Diplomat's Club": 6, 'The Face Painter': 6, 'The Understudy': 6,
    'The Engagement': 7, 'The Postponement': 7, 'The Maestro': 7, 'The Wink': 7, 'The Hot Tub': 7,
    'The Soup Nazi': 7, 'The Secret Code': 7, 'The Pool Guy': 7, 'The Sponge': 7, 'The Gum': 7,
    'The Rye': 7, 'The Caddy': 7, 'The Seven': 7, 'The Cadillac (1)': 7, 'The Cadillac (2)': 7,
    'The Shower Head': 7, 'The Doll': 7, 'The Friars Club': 7, 'The Wig Master': 7, 'The Calzone': 7,
    'The Bottle Deposit (1)': 7, 'The Bottle Deposit (2)': 7, 'The Wait Out': 7, 'The Invitations': 7, 'The Foundation': 8,
    'The Soul Mate': 8, 'The Bizarro Jerry': 8, 'The Little Kicks': 8, 'The Package': 8, 'The Fatigues': 8,
    'The Checks': 8, 'The Chicken Roaster': 8, 'The Abstinence': 8, 'The Andrea Doria': 8, 'The Little Jerry': 8,
    'The Money': 8, 'The Comeback': 8, 'The Van Buren Boys': 8, 'The Susie': 8, 'The Pothole': 8,
    'The English Patient': 8, 'The Nap': 8, 'The Yada Yada': 8, 'The Millennium': 8, 'The Muffin Tops': 8,
    'The Summer of George': 8, 'The Butter Shave': 9, 'The Voice': 9, 'The Serenity Now': 9, 'The Blood': 9,
    'The Junk Mail': 9, 'The Merv Griffin Show': 9, 'The Slicer': 9, 'The Betrayal': 9, 'The Apology': 9,
    'The Strike': 9, 'The Dealership': 9, 'The Reverse Peephole': 9, 'The Cartoon': 9, 'The Strongbox': 9,
    'The Wizard': 9, 'The Burning': 9, 'The Bookstore': 9, 'The Frogger': 9, 'The Maid': 9,
    'The Puerto Rican Day': 9, 'The Clip Show (1)': 9, 'The Clip Show (2)': 9, 'The Finale (1)': 9, 'The Finale (2)': 9
}

# Clean up episode names to handle minor differences
def normalize_episode_name(name):
    # Handle variations in naming
    name = name.lower()
    name = name.replace('(part ', '(').replace('part', '').replace('(pt', '(')
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# Get our existing episodes
existing_episodes = {}
for season_num in range(1, 10):
    season_dir = BASE_DIR / f'data/scripts/Season {season_num}'
    if season_dir.exists():
        for file_path in season_dir.glob('*.txt'):
            episode_name = file_path.stem
            existing_episodes[normalize_episode_name(episode_name)] = {
                'original_name': episode_name,
                'file_path': str(file_path)
            }

# Find missing episodes
missing_episodes = []
for episode in official_episodes:
    normalized_name = normalize_episode_name(episode)
    if normalized_name not in existing_episodes:
        season_num = episode_to_season.get(episode, '?')
        missing_episodes.append({
            'name': episode,
            'season': season_num,
            'normalized_name': normalized_name
        })

# Print results
print(f'Total official episodes: {len(official_episodes)}')
print(f'Existing episodes: {len(existing_episodes)}')
print(f'Missing episodes: {len(missing_episodes)}')
print('\nMissing episodes:')
for episode in missing_episodes:
    print(f"- {episode['name']} (Season {episode['season']})")

# Check for potential name mismatches
print("\nPotential name variations (checking for similar episodes):")
for missing in missing_episodes:
    for existing_norm, existing_info in existing_episodes.items():
        # Check for partial matches that might be the same episode with different naming
        if (missing['normalized_name'] in existing_norm or
            existing_norm in missing['normalized_name'] or
            (len(missing['normalized_name']) > 5 and 
             sum(c1 == c2 for c1, c2 in zip(missing['normalized_name'], existing_norm)) / 
             max(len(missing['normalized_name']), len(existing_norm)) > 0.7)):
            print(f"Missing: {missing['name']} might match existing: {existing_info['original_name']}")
