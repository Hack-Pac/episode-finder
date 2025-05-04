# Seinfeld Episode Finder

A web app that helps you find Seinfeld episodes based on scene descriptions using Google's Gemini AI. First scrapes episode descriptions from seinfeldscripts.com, then uses Gemini to find matching episodes and enhances results with IMDb ratings and air dates.

## Setup

1. Clone the repository
2. Set up the environment (from project root):
   ```bash
   python -m venv venv
   # Windows (run this)
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env and add your Gemini API key
   ```

3. Install all dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Scrape episode descriptions:
   ```bash
   python scripts/seinfeld_scraper.py
   ```

5. Run the application:
   ```bash
   cd backend && python app.py
   ```

5. Open `http://localhost:5000` in your browser

## Usage

1. Describe the Seinfeld scene you're looking for
2. Click "Find Episode" to search
3. View the matching episodes with IMDb ratings and air dates

## Additional Features

### Standalone IMDb Rating Lookup
You can look up IMDb ratings directly:
```bash
python scripts/get_imdb_rating.py <season> <episode>
# Example: python scripts/get_imdb_rating.py 4 11
```

## Development

- Backend: 
  - Flask app in `backend/` serving API and static files
  - Seinfeld scraper in `scripts/seinfeld_scraper.py`
  - Episode finder in `scripts/find_episode.py`
  - IMDb rating fetcher in `scripts/get_imdb_rating.py`
- Frontend: Static files served through Flask from `frontend/`
- Data: Scraped episode descriptions stored in `data/seinfeld_descriptions.txt`
- Uses TailwindCSS and DaisyUI for styling
- Gemini API for natural language processing

## Features

- Scene-based episode search using AI
- Episode descriptions from seinfeldscripts.com
- IMDb ratings and air dates for matched episodes
- Clean, responsive web interface

## Requirements

- Python 3.8+
- Google Gemini API key
- Internet connection for IMDb lookups
- Modern web browser

