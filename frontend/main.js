//grab dom elements
const sceneForm = document.getElementById('sceneForm')
const keywordForm = document.getElementById('keywordForm')
const results = document.getElementById('results')
const loading = document.getElementById('loading')
const error = document.getElementById('error')
const errorMessage = document.getElementById('errorMessage')
const resultsContent = document.getElementById('resultsContent')

// Search History Management
class SearchHistory {
    constructor() {
        this.maxHistory = 10;
        this.storageKey = 'seinfeld_search_history';
        this.init();
    }
    
    init() {
        this.createHistoryUI();
        this.loadHistory();
    }
    
    add(query, type = 'scene', result = null) {
        const history = this.get();
        const entry = {
            query: query.trim(),
            type,
            hasResult: !!result,
            timestamp: Date.now(),
            id: Date.now().toString()
        };
        
        // Remove duplicates and add new entry at top
        const filtered = history.filter(item => 
            item.query.toLowerCase() !== query.toLowerCase().trim() || item.type !== type
        );
        filtered.unshift(entry);
        
        // Keep only latest entries
        const trimmed = filtered.slice(0, this.maxHistory);
        localStorage.setItem(this.storageKey, JSON.stringify(trimmed));
        
        this.updateHistoryUI();
    }
    
    get() {
        try {
            return JSON.parse(localStorage.getItem(this.storageKey)) || [];
        } catch {
            return [];
        }
    }
    
    clear() {
        localStorage.removeItem(this.storageKey);
        this.updateHistoryUI();
    }
    
    createHistoryUI() {
        // Add history section to the page
        const historyHTML = `
            <div id="searchHistory" class="mb-6 hidden">
                <div class="glass-effect rounded-xl p-4">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-lg font-semibold text-white flex items-center">
                            <i class="fas fa-history mr-2"></i>
                            Recent Searches
                        </h3>
                        <button id="clearHistory" class="text-sm text-white opacity-60 hover:opacity-100 transition-opacity">
                            <i class="fas fa-trash mr-1"></i>
                            Clear
                        </button>
                    </div>
                    <div id="historyList" class="space-y-2">
                        <!-- History items will be inserted here -->
                    </div>
                </div>
            </div>
        `;
        
        // Insert before the main tabs
        const tabsContainer = document.querySelector('.tabs');
        tabsContainer.insertAdjacentHTML('beforebegin', historyHTML);
        
        // Add event listeners
        document.getElementById('clearHistory').addEventListener('click', () => {
            this.clear();
        });
    }
    
    updateHistoryUI() {
        const history = this.get();
        const historyContainer = document.getElementById('searchHistory');
        const historyList = document.getElementById('historyList');
        
        if (history.length === 0) {
            historyContainer.classList.add('hidden');
            return;
        }
        
        historyContainer.classList.remove('hidden');
        historyList.innerHTML = '';
        
        history.forEach(entry => {
            const timeAgo = this.getTimeAgo(entry.timestamp);
            const typeIcon = entry.type === 'scene' ? 'fas fa-brain' : 'fas fa-search';
            const resultIcon = entry.hasResult ? 'fas fa-check-circle text-green-400' : 'fas fa-times-circle text-red-400';
            
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors';
            historyItem.innerHTML = `
                <div class="flex items-center flex-1 min-w-0">
                    <i class="${typeIcon} text-blue-400 mr-3 flex-shrink-0"></i>
                    <div class="flex-1 min-w-0">
                        <div class="text-white truncate font-medium">${this.escapeHtml(entry.query)}</div>
                        <div class="text-xs text-white/60 flex items-center mt-1">
                            <span class="capitalize">${entry.type} search</span>
                            <span class="mx-2">•</span>
                            <span>${timeAgo}</span>
                        </div>
                    </div>
                </div>
                <div class="flex items-center space-x-2 flex-shrink-0">
                    <i class="${resultIcon} text-sm" title="${entry.hasResult ? 'Found result' : 'No result'}"></i>
                    <button class="delete-history text-white/40 hover:text-red-400 transition-colors" data-id="${entry.id}">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
            `;
            
            // Add click to search again
            historyItem.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-history')) {
                    this.executeHistorySearch(entry);
                }
            });
            
            // Add delete functionality
            historyItem.querySelector('.delete-history').addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteEntry(entry.id);
            });
            
            historyList.appendChild(historyItem);
        });
    }
    
    deleteEntry(id) {
        const history = this.get();
        const filtered = history.filter(entry => entry.id !== id);
        localStorage.setItem(this.storageKey, JSON.stringify(filtered));
        this.updateHistoryUI();
    }
    
    executeHistorySearch(entry) {
        // Switch to appropriate tab
        const sceneTab = document.querySelector('[data-tab="scene"]');
        const keywordTab = document.querySelector('[data-tab="keyword"]');
        
        if (entry.type === 'scene') {
            sceneTab.click();
            document.getElementById('description').value = entry.query;
            document.getElementById('sceneForm').dispatchEvent(new Event('submit'));
        } else {
            keywordTab.click();
            document.getElementById('keywords').value = entry.query;
            document.getElementById('keywordForm').dispatchEvent(new Event('submit'));
        }
    }
    
    loadHistory() {
        this.updateHistoryUI();
    }
    
    getTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return new Date(timestamp).toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize search history
const searchHistory = new SearchHistory()

// Handle keyword form submission
keywordForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    
    // Get form data
    const keywords = document.getElementById('keywords').value
    
    // Reset states
    results.classList.add('hidden')
    error.classList.add('hidden')
    loading.classList.remove('hidden')
    
    try {
        // Call backend keyword search endpoint
        const response = await fetch('http://localhost:5000/api/keyword-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords,
                maxResults: 5
            }),
        })
        
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.error || 'Failed to find episodes')
        }
        // Show results
        displayResults(data.results)
        
        // Add to search history
        searchHistory.add(keywords, 'keyword', data.results);
        
    } catch (err) {
        // Handle errors
        errorMessage.textContent = err.message
        error.classList.remove('hidden')
        
        // Add failed search to history
        searchHistory.add(keywords, 'keyword', null);
    } finally {
        // Hide loading
        loading.classList.add('hidden')
    }
})
// Function to display results (common for both search types)
function displayResults(resultsText) {
    const episodeInfo = resultsContent.querySelector('.episode-info')
    const ratingInfo = resultsContent.querySelector('.rating-info')
    const airDate = resultsContent.querySelector('.air-date')
    
    // Clear any existing image
    const existingImage = resultsContent.querySelector('.episode-image')
    if (existingImage) {
        existingImage.remove()
    }
    
    // Clear any existing IMDb link
    const existingLink = resultsContent.querySelector('.imdb-link')
    if (existingLink) {
        existingLink.remove()
    }
    
    // Parse result text
    const lines = resultsText.split('\n')
    // Show episode info
    episodeInfo.textContent = lines[0]  // First line is episode info
    
    // Check for rating info and other metadata
    if (lines.length > 1) {
        const ratingLine = lines.find(line => line.includes('IMDb Rating:'))
        const airDateLine = lines.find(line => line.includes('Original Air Date:'))
        const keywordMatchLine = lines.find(line => line.includes('Matched'))
        const keywordsFoundLine = lines.find(line => line.includes('Keywords found:'))
        const imageLine = lines.find(line => line.includes('IMDb Image:'))
        const imdbUrlLine = lines.find(line => line.includes('IMDb URL:'))
        
        // Handle rating display
        if (ratingLine) {
            ratingInfo.classList.remove('hidden')
            ratingInfo.querySelector('.rating-text').textContent = ratingLine.replace('IMDb Rating:', '').trim()
        } else {
            ratingInfo.classList.add('hidden')
        }
        
        // Handle image display if available
        if (imageLine) {
            const imageUrl = imageLine.replace('IMDb Image:', '').trim()
            const imageContainer = document.createElement('div')
            imageContainer.classList.add('episode-image', 'mt-4', 'mb-4', 'flex', 'justify-center')
            
            const img = document.createElement('img')
            img.src = imageUrl
            img.alt = episodeInfo.textContent
            img.classList.add('rounded-lg', 'shadow-lg', 'max-h-64')
            
            imageContainer.appendChild(img)
            resultsContent.insertBefore(imageContainer, ratingInfo)
        }
        
        // Handle IMDb link if available
        if (imdbUrlLine) {
            const imdbUrl = imdbUrlLine.replace('IMDb URL:', '').trim()
            const linkContainer = document.createElement('div')
            linkContainer.classList.add('imdb-link', 'mt-2', 'mb-4', 'text-center')
            
            const link = document.createElement('a')
            link.href = imdbUrl
            link.target = '_blank'
            link.rel = 'noopener noreferrer'
            link.classList.add('text-blue-500', 'hover:underline')
            link.textContent = 'View on IMDb'
            
            linkContainer.appendChild(link)
            resultsContent.insertBefore(linkContainer, airDate.parentNode.contains(airDate) ? airDate : null)
        }
        
        // Handle additional info display (air date or keywords)
        if (airDateLine) {
            airDate.classList.remove('hidden')
            airDate.textContent = airDateLine
        } else if (keywordMatchLine) {
            // For keyword search, show match statistics
            const keywordInfo = document.createElement('div')
            keywordInfo.classList.add('keyword-stats')
            // Bold the match statistics
            const matchStats = document.createElement('div')
            matchStats.classList.add('font-bold', 'text-sm')
            matchStats.textContent = keywordMatchLine
            keywordInfo.appendChild(matchStats)
            
            // Add keyword details
            if (keywordsFoundLine) {
                const keywordDetails = document.createElement('div')
                keywordDetails.classList.add('text-sm', 'text-base-content/80')
                keywordDetails.textContent = keywordsFoundLine
                keywordInfo.appendChild(keywordDetails)
            }
            // Replace airDate content with keyword info
            airDate.classList.remove('hidden')
            airDate.innerHTML = ''
            airDate.appendChild(keywordInfo)
        } else {
            airDate.classList.add('hidden')
        }
    } else {
        ratingInfo.classList.add('hidden')
        airDate.classList.add('hidden')
    }
    
    results.classList.remove('hidden')
}

// Update scene form handler (find the existing sceneForm addEventListener and modify it)
sceneForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    
    const description = document.getElementById('description').value
    results.classList.add('hidden')
    error.classList.add('hidden')
    loading.classList.remove('hidden')
    
    try {
        const response = await fetch('http://localhost:5000/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description,
                test_mode: false
            }),
        })
        
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.error || 'Failed to find episode')
        }
        
        displayResults(data.results)
        
        // Add to search history
        searchHistory.add(description, 'scene', data.results);
        
    } catch (err) {
        errorMessage.textContent = err.message
        error.classList.remove('hidden')
        
        // Add failed search to history
        searchHistory.add(description, 'scene', null);
    } finally {
        loading.classList.add('hidden')
    }
})
