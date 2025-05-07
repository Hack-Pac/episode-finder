import requests
from bs4 import BeautifulSoup

# Get the Wikipedia page for Seinfeld episodes
url = "https://en.wikipedia.org/wiki/List_of_Seinfeld_episodes"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all season tables (they use wikitable class)
tables = soup.find_all("table", class_="wikitable plainrowheaders")

print("Official Seinfeld Episodes:")

# Process the first 9 tables (9 seasons)
for i, table in enumerate(tables[:9], 1):
    print(f"\nSeason {i}:")
    
    # Find all rows except header
    rows = table.find_all("tr")[1:]
    
    # Extract episode titles from each row
    for row in rows:
        # Episode titles are in th cells with a tags
        th = row.find("th")
        if th:
            title_cell = th.find("a")
            if title_cell:
                print(f"- {title_cell.text}")
