#!/usr/bin/env python3
import os
from pathlib import Path
import together
from dotenv import load_dotenv
import logging
import re
import sys
from pathlib import Path
import json
#add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from scripts.get_imdb_rating import get_rating

#setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
def load_descriptions():
    """load scraped seinfeld descriptions"""
    try:
        descriptions_file = Path("data/seinfeld_descriptions.txt")
        if not descriptions_file.exists():
            logger.error("descriptions file not found. run seinfeld_scraper.py first")
            return None
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"failed to load descriptions: {e}")
        return None
def find_episode(scene_description):
    """find seinfeld episode based on scene description"""
    try:
        # Setup Together.ai
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key or api_key == 'none':
            logger.error("TOGETHER_API_KEY not found in .env")
            return None
            
        # Configure Together client
        logger.info("Configuring Together.ai API")
        together.api_key = api_key
        # Load descriptions and split into chunks
        descriptions = load_descriptions()
        if not descriptions:
            return None
            
        # Split descriptions into chunks of approximately 20 episodes each
        episode_chunks = descriptions.split('\n\n')
        chunk_size = 20
        chunks = ['\n\n'.join(episode_chunks[i:i + chunk_size]) 
                 for i in range(0, len(episode_chunks), chunk_size)]
        
        all_matches = []
        for chunk in chunks:
            #craft prompt with Llama instruction format for this chunk
            prompt = f"""[INST] Task: Find matching Seinfeld episodes based on a scene description.

EPISODE DESCRIPTIONS:
{chunk}
SCENE TO MATCH:
{scene_description}

INSTRUCTIONS:
1. Return ONLY matching episode numbers and names
2. If no matches found, respond: "No matching episodes found."
3. Format matches as "Season X Episode Y: Title"
4. No explanations or additional text

Your response: [/INST]"""
            
            # Generate content using Together's API
            logger.info("Generating content for chunk")
            output = together.Complete.create(
                prompt=prompt,
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                max_tokens=256,
                temperature=0.5,
                stop=["[INST]", "INSTRUCTIONS:", "Your response:"],
            )
            
            # Extract response text
            if output and 'output' in output and output['output'] and output['output']['choices']:
                text = output['output']['choices'][0]['text'].strip()
                if text != "No matching episodes found.":
                    all_matches.append(text)
        # Combine results
        if not all_matches:
            text = "No matching episodes found."
        else:
            text = "\n".join(all_matches)
        #try to parse season and episode numbers from response
        if text != "No matching episodes found.":
            #look for patterns like "Season X Episode Y" or "SxEY"
            ep_matches = re.finditer(r'(?:Season\s*(\d+).*?Episode\s*(\d+)|S(\d+)E(\d+))', text)
            enhanced_results = []
            for match in ep_matches:
                season = match.group(1) or match.group(3)
                episode = match.group(2) or match.group(4)
                if season and episode:
                    #get rating info
                    rating_info = get_rating(int(season), int(episode))
                    if rating_info:
                        enhanced_results.append(
                            f"{text}\n"
                            f"IMDb Rating: {rating_info['rating']}/10 ({rating_info['votes']} votes)\n"
                            f"Original Air Date: {rating_info['air_date']}"
                        )
                        break  #just enhance the first match for now
            return enhanced_results[0] if enhanced_results else text
        return text
    except Exception as e:
        logger.error(f"error finding episode: {e}")
        return None
if __name__ == "__main__":
    #example usage
    scene = input("Describe the Seinfeld scene: ")
    result = find_episode(scene)
    if result:
        print("\nMatching Episode:")
        print(result)
    else:
        print("\nFailed to find episodes. Check the logs for details.")

















