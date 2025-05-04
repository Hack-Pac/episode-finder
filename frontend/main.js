//grab dom elements
const form = document.getElementById('searchForm')
const results = document.getElementById('results')
const loading = document.getElementById('loading')
const error = document.getElementById('error')
const errorMessage = document.getElementById('errorMessage')
const resultsContent = document.getElementById('resultsContent')

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
        const episodeInfo = resultsContent.querySelector('.episode-info')
        const ratingInfo = resultsContent.querySelector('.rating-info')
        const airDate = resultsContent.querySelector('.air-date')
        
        //parse result text
        const lines = data.results.split('\n')
        //show episode info
        episodeInfo.textContent = lines[0]  //first line is episode info
        
        //check for rating info
        if (lines.length > 1) {
            const ratingLine = lines[1]
            const airDateLine = lines[2]
            
            if (ratingLine.includes('IMDb Rating:')) {
                ratingInfo.classList.remove('hidden')
                ratingInfo.querySelector('.rating-text').textContent = ratingLine.replace('IMDb Rating:', '').trim()
            } else {
                ratingInfo.classList.add('hidden')
            }
            
            if (airDateLine && airDateLine.includes('Original Air Date:')) {
                airDate.classList.remove('hidden')
                airDate.textContent = airDateLine
            } else {
                airDate.classList.add('hidden')
            }
        } else {
            ratingInfo.classList.add('hidden')
            airDate.classList.add('hidden')
        }
        results.classList.remove('hidden')
    } catch (err) {
        //handle errors
        errorMessage.textContent = err.message
        error.classList.remove('hidden')
    } finally {
        //hide loading
        loading.classList.add('hidden')
    }
})

























