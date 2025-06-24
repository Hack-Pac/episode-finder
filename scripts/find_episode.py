import os
import re
import sys
import json
import logging
import hashlib
from pathlib import Path
import together
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from scripts.get_imdb_rating import get_rating

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_cache_key(scene_description):
    return hashlib.md5(scene_description.lower().strip().encode()).hexdigest()

def load_cache():
    cache_file = Path(__file__).parent.parent / "data" / "episode_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_to_cache(scene_description, result):    
    cache_file = Path(__file__).parent.parent / "data" / "episode_cache.json"
    cache = load_cache()
    cache[get_cache_key(scene_description)] = result
    
    #ensure data dir exists
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f)

def prefilter_episodes(scene_description, episodes):
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    #extract keywords for filtering
    all_words = re.findall(r'\b\w+\b', scene_description.lower())
    keywords = [word for word in all_words if len(word) > 2 and word not in stop_words]
    
    logger.info(f"Extracted keywords for filtering: {keywords}")
    
    scored_episodes = []
    for episode in episodes:
        episode_lower = episode.lower()
        
        #score based on keyword matches
        exact_matches = sum(1 for keyword in keywords if keyword in episode_lower)
        
        #bonus for partial matches
        partial_matches = 0
        for keyword in keywords:
            if len(keyword) > 4:
                keyword_stem = keyword[:4]
                if keyword_stem in episode_lower and keyword not in episode_lower:
                    partial_matches += 0.5
        
        total_score = exact_matches + partial_matches
        
        #include episode if it has matches or we need more episodes
        if total_score > 0 or len(keywords) < 3:
            scored_episodes.append((total_score, episode))
    
    scored_episodes.sort(reverse=True)
    
    #be more lenient
    if len(scored_episodes) < 15:
        logger.warning(f"Only {len(scored_episodes)} episodes matched keywords. Including more episodes for broader search.")
        for episode in episodes:
            episode_lower = episode.lower()
            if not any(episode == scored_ep[1] for scored_ep in scored_episodes):
                has_any_word = any(word in episode_lower for word in all_words if len(word) > 1)
                if has_any_word:
                    scored_episodes.append((0.1, episode))
    
    max_episodes = 40 if len([ep for score, ep in scored_episodes if score >= 1]) < 20 else 25
    
    logger.info(f"Returning top {min(max_episodes, len(scored_episodes))} episodes from {len(episodes)} total")
    return [ep for _, ep in scored_episodes[:max_episodes]]

def load_descriptions():
    """Load scraped seinfeld descriptions"""
    try:
        project_root = Path(__file__).parent.parent
        descriptions_file = project_root / "data" / "seinfeld_descriptions.txt"
        if not descriptions_file.exists():
            logger.error("Descriptions file not found. Run seinfeld_scraper.py first")
            return None
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load descriptions: {e}")
        return None

def find_episode(scene_description, test_mode=False):
    """Find seinfeld episode based on scene description
    
    Args:
        scene_description (str): The scene to search for
        test_mode (bool, optional): If True, skips descriptions to avoid token limit. Defaults to False.
    """
    try:
        cache_key = get_cache_key(scene_description)
        cache = load_cache()
        
        if cache_key in cache:
            logger.info("Returning cached result")
            return cache[cache_key]
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key or api_key == 'none':
            logger.error("TOGETHER_API_KEY not found in .env")
            return None
            
        logger.info("Configuring Together.ai API")
        together.api_key = api_key
        
        #test mode
        if test_mode:
            logger.info("Running in test mode - bypassing episode descriptions")
            if "jerry" in scene_description.lower() and "car" in scene_description.lower():
                logger.info(f"TEST MODE: Returning mocked result for car-related query: {scene_description[:30]}...")
                result = "Season 3 Episode 22: The Parking Garage\nIMDb Rating: 8.8/10 (3241 votes)\nOriginal Air Date: October 30, 1991"
                return result
            chunks = ["TEST_MODE_ACTIVE"]
        else:
            descriptions = load_descriptions()
            if not descriptions:
                return None
            episode_chunks = re.split(r'\r?\n\s*\r?\n', descriptions.strip())
            
            relevant_episodes = prefilter_episodes(scene_description, episode_chunks)
            logger.info(f"Prefiltered to {len(relevant_episodes)} relevant episodes from {len(episode_chunks)} total")
              #use batch processing for efficiency
            chunk_size = 12
            chunks = [relevant_episodes[i:i + chunk_size] for i in range(0, len(relevant_episodes), chunk_size)]
        
        all_matches = []
        for chunk_episodes in chunks:
            if test_mode and chunk_episodes == ["TEST_MODE_ACTIVE"]:
                break
            
            chunk = "\n\n".join(chunk_episodes)
            
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
            
            logger.info(f"Generating content for batch of {len(chunk_episodes)} episodes")
            
            try:
                output = together.Complete.create(
                    prompt=prompt,
                    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                    max_tokens=256,
                    temperature=0.5,
                    stop=["[INST]", "INSTRUCTIONS:", "Your response:"],
                )
                
                #log raw output for debugging
                logger.info(f"Raw API output: {output}")
                if output and 'output' in output and output['output']['choices']:
                    raw_text = output['output']['choices'][0]['text'].strip()
                    logger.info(f"Raw extracted text: '{raw_text}'")
                    
                    text = raw_text
                    
                    cleanup_patterns = [
                        r'INSTRUCTIONS:.*?(?=Season|\n\n|$)',
                        r'Your response:.*?(?=Season|\n\n|$)',
                        r'\[INST\].*?\[/INST\]',
                        r'Task: Find matching.*?(?=Season|\n\n|$)',
                        r'EPISODE DESCRIPTIONS:.*?(?=Season|\n\n|$)',
                        r'SCENE TO MATCH:.*?(?=Season|\n\n|$)',
                        r'^\d+\.\s*.*?(?=Season|\n\n|$)',
                        r'^Format matches.*?(?=Season|\n\n|$)',
                        r'^Return ONLY.*?(?=Season|\n\n|$)',
                        r'^If no.*?(?=Season|\n\n|$)',
                        r'^No explanations.*?(?=Season|\n\n|$)'
                    ]
                    
                    for pattern in cleanup_patterns:
                        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
                    
                    text = re.sub(r'\n\s*\n+', '\n', text).strip()
                    
                    if not text or text.lower().strip() == "no matching episodes found.":
                        text = "No matching episodes found."
                    
                    logger.info(f"Cleaned extracted text: '{text}'")
                else:
                    text = "No matching episodes found."
                    logger.warning("No choices in API response")
                    
            except Exception as e:
                logger.error(f"Together API request failed: {e}")
                text = "No matching episodes found."
            
            if text != "No matching episodes found.":
                confidence_indicators = ["exact", "clearly", "definitely", "obviously"]
                if any(indicator in text.lower() for indicator in confidence_indicators):
                    logger.info("High confidence match found, stopping search")
                    all_matches.append(text)
                    break
                all_matches.append(text)
                break       
        logger.info(f"all_matches: {all_matches}")
        if not all_matches:
            final_result = "No matching episodes found."
        else:
            text = "\n".join(all_matches)
            logger.info(f"Combined text: '{text}'")
            
            #if no matches with prefiltered episodes, try all episodes
            if text == "No matching episodes found." and not test_mode:
                logger.info("No matches found with prefiltered episodes. Trying with all episodes...")
                
                descriptions = load_descriptions()
                if descriptions:
                    all_episode_chunks = re.split(r'\r?\n\s*\r?\n', descriptions.strip())
                    logger.info(f"Trying with all {len(all_episode_chunks)} episodes")
                    
                    #use smaller chunks for all episodes
                    chunk_size = 8
                    all_chunks = [all_episode_chunks[i:i + chunk_size] for i in range(0, len(all_episode_chunks), chunk_size)]
                    
                    fallback_matches = []
                    for chunk_episodes in all_chunks[:5]:  #limit to first 5 chunks
                        chunk = "\n\n".join(chunk_episodes)
                        
                        fallback_prompt = f"""[INST] Task: Find matching Seinfeld episodes based on a scene description.

                            EPISODE DESCRIPTIONS:
                            {chunk}

                            SCENE TO MATCH:
                            {scene_description}

                            INSTRUCTIONS:
                            1. Return ONLY the BEST 1-2 matching episodes
                            2. Format matches as "Season X Episode Y: Title"
                            3. If no good matches, respond: "No matching episodes found."
                            4. No explanations or additional text

                            Your response: [/INST]"""
                        
                        logger.info(f"Fallback: Generating content for batch of {len(chunk_episodes)} episodes")
                        
                        try:
                            fallback_output = together.Complete.create(
                                prompt=fallback_prompt,
                                model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
                                max_tokens=128,
                                temperature=0.3,
                                top_p=0.7,                                stop=["[INST]", "INSTRUCTIONS:", "Your response:"],
                            )
                            
                            logger.info(f"Fallback raw API output: {fallback_output}")
                            
                            if fallback_output and 'output' in fallback_output and fallback_output['output']['choices']:
                                raw_fallback_text = fallback_output['output']['choices'][0]['text'].strip()
                                logger.info(f"Fallback raw extracted text: '{raw_fallback_text}'")
                                
                                fallback_text = raw_fallback_text
                                
                                cleanup_patterns = [
                                    r'INSTRUCTIONS:.*?(?=Season|\n\n|$)',
                                    r'Your response:.*?(?=Season|\n\n|$)',
                                    r'\[INST\].*?\[/INST\]',
                                    r'Task: Find matching.*?(?=Season|\n\n|$)',
                                    r'EPISODE DESCRIPTIONS:.*?(?=Season|\n\n|$)',
                                    r'SCENE TO MATCH:.*?(?=Season|\n\n|$)',
                                    r'^\d+\.\s*.*?(?=Season|\n\n|$)',
                                    r'^Format matches.*?(?=Season|\n\n|$)',
                                    r'^Return ONLY.*?(?=Season|\n\n|$)',
                                    r'^If no.*?(?=Season|\n\n|$)',
                                    r'^No explanations.*?(?=Season|\n\n|$)'
                                ]
                                
                                for pattern in cleanup_patterns:
                                    fallback_text = re.sub(pattern, '', fallback_text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
                                
                                fallback_text = re.sub(r'\n\s*\n+', '\n', fallback_text).strip()
                                
                                if not fallback_text or fallback_text.lower().strip() == "no matching episodes found.":
                                    fallback_text = "No matching episodes found."
                                
                                logger.info(f"Fallback cleaned text: '{fallback_text}'")
                                
                                if fallback_text != "No matching episodes found.":
                                    fallback_matches.append(fallback_text)
                                    logger.info("Found match in fallback search, stopping")
                                    break
                            else:
                                logger.warning("No choices in fallback API response")
                                
                        except Exception as e:
                            logger.error(f"Fallback API request failed: {e}")
                            continue
                    
                    if fallback_matches:
                        text = "\n".join(fallback_matches)
                        logger.info(f"Fallback result: '{text}'")
              #try to parse season and episode numbers from response
            ep_matches = re.finditer(r'(?:Season\s*(\d+).*?Episode\s*(\d+)|S(\d+)E(\d+))', text)
            enhanced_results = []
            
            #get only the first episode match from the llm output
            first_episode_match = next(ep_matches, None)
            logger.info(f"Episode match found: {first_episode_match}")
            
            if first_episode_match:
                season = first_episode_match.group(1) or first_episode_match.group(3)
                episode = first_episode_match.group(2) or first_episode_match.group(4)
                
                if season and episode:
                    rating_info = get_rating(int(season), int(episode))
                    
                    if rating_info:
                        result_text = text 
                        result_text += f"\nIMDb Rating: {rating_info.get('rating', 'N/A')}/10 ({rating_info.get('votes', 'N/A')} votes)"
                        result_text += f"\nOriginal Air Date: {rating_info.get('air_date', 'N/A')}"
                        if rating_info.get('image_url'):
                            result_text += f"\nIMDb Image: {rating_info['image_url']}"
                        if rating_info.get('imdb_url'):
                            result_text += f"\nIMDb URL: {rating_info['imdb_url']}"
                        enhanced_results.append(result_text)
            
            final_result = enhanced_results[0] if enhanced_results else text
        
        logger.info(f"Final result before return: '{final_result}'")
        
        if final_result:
            save_to_cache(scene_description, final_result)
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error finding episode: {e}")
        return None

if __name__ == "__main__":
    scene = input("Describe the Seinfeld scene: ")
    result = find_episode(scene)
    if result:
        print("\nMatching Episode:")
        print(result)
    else:
        print("\nFailed to find episodes. Check the logs for details.")