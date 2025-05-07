//grab dom elements
const form = document.getElementById('searchForm')
const keywordForm = document.getElementById('keywordForm')
const tabDescription = document.getElementById('tab-description')
const tabKeywords = document.getElementById('tab-keywords')
const results = document.getElementById('results')
const loading = document.getElementById('loading')
const error = document.getElementById('error')
const errorMessage = document.getElementById('errorMessage')
const resultsContent = document.getElementById('resultsContent')

// Tab switching functionality
tabDescription.addEventListener('click', () => {
    tabDescription.classList.add('tab-active')
    tabKeywords.classList.remove('tab-active')
    form.classList.remove('hidden')
    keywordForm.classList.add('hidden')
})

tabKeywords.addEventListener('click', () => {
    tabKeywords.classList.add('tab-active')
    tabDescription.classList.remove('tab-active')
    keywordForm.classList.remove('hidden')
    form.classList.add('hidden')
})

//handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault()
    
    //get form data
    const description = document.getElementById('description').value
    //reset states
    results.classList.add('hidden')
    error.classList.add('hidden')
    loading.classList.remove('hidden')
    try {
        //call backend
        const response = await fetch('http://localhost:5000/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description,
            }),
        })
        
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.error || 'failed to find episodes')
        }
        //show results
        displayResults(data.results)
    } catch (err) {
        //handle errors
        errorMessage.textContent = err.message
        error.classList.remove('hidden')
    } finally {
        //hide loading
        loading.classList.add('hidden')
    }
})

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
    } catch (err) {
        // Handle errors
        errorMessage.textContent = err.message
        error.classList.remove('hidden')
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
        
        // Handle rating display
        if (ratingLine) {
            ratingInfo.classList.remove('hidden')
            ratingInfo.querySelector('.rating-text').textContent = ratingLine.replace('IMDb Rating:', '').trim()
        } else {
            ratingInfo.classList.add('hidden')
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






























































































