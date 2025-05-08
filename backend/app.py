from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Load environment variables from .env
load_dotenv()
# Debug log for environment variables
print("Debug: TOGETHER_API_KEY present:", bool(os.getenv('TOGETHER_API_KEY')))
#add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
#import our modules
from scripts.find_episode import find_episode
from scripts.find_episode_by_keywords import find_episodes_by_keywords
from scripts.get_imdb_rating import get_rating # Import get_rating

#init flask app
app = Flask(__name__, static_folder='../frontend')
CORS(app) #enable cors for all routes
#serve frontend
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)
@app.route('/api/search', methods=['POST'])
def search_episode():
    try:
        data = request.json
        description = data.get('description')
        test_mode = data.get('test_mode', False)  # Optional parameter to enable test mode
        
        if not description:
            return jsonify({'error': 'missing description'}), 400
        # Add a max length for the description to prevent token limit issues
        if len(description) > 500:
            description = description[:500]
            
        #use our specialized seinfeld finder
        result = find_episode(description, test_mode=test_mode)
        if result is None:
            return jsonify({
                'error': 'failed to search episodes',
                'message': 'check server logs for details'
            }), 500
            
        #log success for monitoring
        logger.info(f"Successfully found episodes for scene: {description[:50]}...")
        return jsonify({
            'success': True,
            'results': result
        })
    except Exception as e:
        #log the error in prod
        return jsonify({
            'error': str(e),
            'message': 'failed to process request'
        }), 500
@app.route('/api/test', methods=['GET'])
def test_default_episode():
    """Test endpoint to directly check get_imdb_rating functionality."""
    test_season = 4
    test_episode_identifier = "The Contest"  # Can be an episode number (e.g., 11) or title

    logger.info(f"Executing /api/test for S{test_season}E{test_episode_identifier} using get_rating directly.")
    
    imdb_data = get_rating(test_season, test_episode_identifier)
    
    if imdb_data is None:
        logger.error(f"/api/test: get_rating returned None for S{test_season}E{test_episode_identifier}.")
        return jsonify({
            'success': False,
            'test_parameters': {'season': test_season, 'episode_identifier': test_episode_identifier},
            'message': 'IMDb data fetching failed: get_rating returned None. Check server logs for get_imdb_rating.py errors.',
            'imdb_data': None
        }), 500

    # Check for completeness of critical IMDb data
    rating_ok = imdb_data.get('rating') not in [None, 'N/A', '']
    image_ok = imdb_data.get('image_url') not in [None, '']
    imdb_url_ok = imdb_data.get('imdb_url') not in [None, '']
    
    status_message = "IMDb data retrieved."
    is_complete = True

    if not (rating_ok and image_ok and imdb_url_ok):
        status_message = "IMDb data retrieved but appears incomplete (missing/empty rating, image_url, or imdb_url). `get_imdb_rating.py` may need updates."
        is_complete = False
        logger.warning(f"/api/test: IMDb data for S{test_season}E{test_episode_identifier} is incomplete. Rating OK: {rating_ok}, Image OK: {image_ok}, IMDb URL OK: {imdb_url_ok}")
    else:
        status_message = "IMDb data retrieved successfully and appears complete."
        logger.info(f"/api/test: IMDb data for S{test_season}E{test_episode_identifier} appears complete.")

    logger.debug(f"/api/test: Full IMDb data for S{test_season}E{test_episode_identifier}: {imdb_data}")

    return jsonify({
        'success': is_complete,
        'test_parameters': {'season': test_season, 'episode_identifier': test_episode_identifier},
        'message': status_message,
        'imdb_data': imdb_data
    })

@app.route('/api/keyword-search', methods=['POST'])
def search_by_keywords():
    """Search for episodes based on keywords"""
    try:
        data = request.json
        keywords = data.get('keywords')
        max_results = data.get('maxResults', 5)  # Default to 5 results
        
        if not keywords:
            return jsonify({'error': 'missing keywords'}), 400
            
        # Add a max length for keywords to prevent processing issues
        if len(keywords) > 200:
            keywords = keywords[:200]
        # Search episodes by keywords
        results = find_episodes_by_keywords(keywords, max_results)
        
        if not results:
            return jsonify({
                'success': True,
                'results': "No episodes found matching your keywords."
            })
            
        # Format the results into a single string to match the existing API format
        formatted_results = "\n\n".join(results)
        # Log success for monitoring
        logger.info(f"Successfully found episodes for keywords: {keywords[:50]}...")
        
        return jsonify({
            'success': True,
            'results': formatted_results
        })
    except Exception as e:
        # Log the error
        logger.error(f"Error in keyword search: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'failed to process keyword search request'
        }), 500

if __name__ == '__main__':
    #run in debug mode for dev
    app.run(debug=True)












































































