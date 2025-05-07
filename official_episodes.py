# This script manually lists the official Seinfeld episodes based on research

# Season 3 episodes (The pimple doesn't exist)
season3 = [
    "The Note", 
    "The Truth", 
    "The Pen", 
    "The Dog",
    "The Library", 
    "The Parking Garage", 
    "The Cafe",
    "The Tape",
    "The Nose Job",
    "The Alternate Side",
    "The Red Dot",
    "The Subway",
    "The Pez Dispenser", # This is a real episode, "The Pimple" doesn't exist
    "The Suicide",
    "The Fix-Up",
    "The Boyfriend (Part 1)",
    "The Boyfriend (Part 2)",
    "The Limo",
    "The Good Samaritan",
    "The Letter",
    "The Parking Space",
    "The Keys"
]

# Season 4 episodes (No "The Show" or "The Handlebar")
season4 = [
    "The Trip (Part 1)",
    "The Trip (Part 2)",
    "The Pitch",
    "The Ticket",
    "The Wallet",
    "The Watch",
    "The Bubble Boy",
    "The Cheever Letters",
    "The Opera",
    "The Virgin",
    "The Contest",
    "The Airport",
    "The Pick",
    "The Movie",  # This is the real name, not "The Show"
    "The Visa",
    "The Shoes",
    "The Outing",
    "The Old Man", # This is a real episode, not "The Handlebar"
    "The Implant",
    "The Junior Mint",
    "The Smelly Car",
    "The Handicap Spot",
    "The Pilot (Part 1)",
    "The Pilot (Part 2)"
]

# Season 6 episodes (No "The Dip" - it's "The Diplomat's Club")
season6 = [
    "The Chaperone",
    "The Big Salad",
    "The Pledge Drive",
    "The Chinese Woman",
    "The Couch",
    "The Gymnast",
    "The Soup",
    "The Mom & Pop Store",
    "The Secretary",
    "The Race",
    "The Switch",
    "The Label Maker",
    "The Scofflaw",
    "The Highlights of a Hundred",  # This might be the real name for a clip show
    "The Beard",
    "The Kiss Hello",
    "The Doorman",
    "The Jimmy",
    "The Doodle",
    "The Fusilli Jerry",
    "The Diplomat's Club",  # This is the real name, not "The Dip"
    "The Face Painter",
    "The Understudy"
]

# Season 8 episodes
season8 = [
    "The Foundation",
    "The Soul Mate",
    "The Bizarro Jerry",
    "The Little Kicks",
    "The Package",
    "The Fatigues",
    "The Checks",
    "The Chicken Roaster",
    "The Abstinence",
    "The Andrea Doria",
    "The Little Jerry",
    "The Money",
    "The Comeback",
    "The Van Buren Boys",
    "The Susie",
    "The Pothole",
    "The English Patient",
    "The Nap",
    "The Yada Yada",
    "The Millennium",
    "The Muffin Tops",
    "The Summer of George"
]

print("Official Seinfeld Episodes for selected seasons:")
print("\nSeason 3:")
for episode in season3:
    print(f"- {episode}")
    
print("\nSeason 4:")
for episode in season4:
    print(f"- {episode}")
    
print("\nSeason 6:")
for episode in season6:
    print(f"- {episode}")
    
print("\nSeason 8:")
for episode in season8:
    print(f"- {episode}")
