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
        if not description:
            return jsonify({'error': 'missing description'}), 400
            
        #use our specialized seinfeld finder
        result = find_episode(description)
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
if __name__ == '__main__':
    #run in debug mode for dev
    app.run(debug=True)










