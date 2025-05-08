//grab dom elements
const keywordForm = document.getElementById('keywordForm')
const results = document.getElementById('results')
const loading = document.getElementById('loading')
const error = document.getElementById('error')
const errorMessage = document.getElementById('errorMessage')
const resultsContent = document.getElementById('resultsContent')

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






































































































































