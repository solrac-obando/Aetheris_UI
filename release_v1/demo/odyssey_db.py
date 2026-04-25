"""
Aetheris Odyssey Database Generator.
Generates a SQLite database with 100 diverse media entries (Movies, Series, Games).

Schema: title, rating (0-10), year (1900-2026), votes (0-3M), 
        and a 4D genre_vector [Action, SciFi, Drama, Comedy].
"""
import sqlite3
import os
import random
import json

# Seed for reproducibility
random.seed(42)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'odyssey.db')

# Genre vectors: [Action, SciFi, Drama, Comedy]
GENRE_PROFILES = {
    'action':       [0.9, 0.3, 0.2, 0.1],
    'scifi':        [0.4, 0.95, 0.3, 0.1],
    'drama':        [0.1, 0.1, 0.95, 0.2],
    'comedy':       [0.1, 0.1, 0.2, 0.95],
    'thriller':     [0.7, 0.2, 0.6, 0.05],
    'horror':       [0.5, 0.3, 0.4, 0.05],
    'romance':      [0.05, 0.05, 0.8, 0.4],
    'animation':    [0.2, 0.3, 0.3, 0.7],
    'fantasy':      [0.6, 0.7, 0.3, 0.2],
    'documentary':  [0.05, 0.1, 0.7, 0.1],
}

MEDIA_TEMPLATES = {
    'movie': [
        "The {Adj} {Noun}", "Rise of the {Noun}", "{Noun} Wars",
        "The Last {Noun}", "{Adj} {Noun}: Reloaded", "Beyond the {Noun}",
        "{Noun} Protocol", "The {Adj} Legacy", "{Noun} Rising",
        "Shadow of the {Noun}", "The {Adj} Code", "{Noun} Unleashed",
    ],
    'series': [
        "{Noun}: The Series", "The {Adj} Chronicles", "{Noun} Files",
        "Tales of {Noun}", "The {Noun} Dynasty", "{Adj} {Noun} Season",
        "Inside {Noun}", "The {Noun} Project", "{Noun} Network",
    ],
    'game': [
        "{Noun} Quest", "The {Adj} {Noun}", "{Noun} Legends",
        "{Noun} Online", "Age of {Noun}", "{Noun} Arena",
        "The {Adj} Dungeon", "{Noun} Tactics", "{Noun} Frontier",
    ],
}

ADJECTIVES = [
    "Dark", "Eternal", "Silent", "Crimson", "Frozen", "Golden", "Hidden",
    "Lost", "Ancient", "Infinite", "Broken", "Savage", "Mystic", "Iron",
    "Crystal", "Shadow", "Wild", "Noble", "Fierce", "Brave",
]

NOUNS = [
    "Kingdom", "Storm", "Empire", "Dragon", "Phoenix", "Titan", "Nexus",
    "Horizon", "Vortex", "Citadel", "Forge", "Abyss", "Odyssey", "Zenith",
    "Pulse", "Echo", "Blade", "Star", "Moon", "Sun", "Comet", "Nebula",
    "Galaxy", "Portal", "Relic", "Artifact", "Legend", "Prophecy",
]


def generate_entries(count=100):
    """Generate diverse media entries with realistic data."""
    entries = []
    media_types = list(MEDIA_TEMPLATES.keys())
    genres = list(GENRE_PROFILES.keys())
    
    for i in range(count):
        media_type = media_types[i % len(media_types)]
        genre = genres[i % len(genres)]
        
        # Generate title
        template = random.choice(MEDIA_TEMPLATES[media_type])
        title = template.format(
            Adj=random.choice(ADJECTIVES),
            Noun=random.choice(NOUNS)
        )
        
        # Add subtitle for uniqueness
        if i >= len(ADJECTIVES) * len(NOUNS):
            title = f"{title} {i+1}"
        
        # Rating: weighted toward 6-9 range
        rating = min(10.0, max(1.0, random.gauss(7.2, 1.5)))
        rating = round(rating, 1)
        
        # Year: 1950-2026, weighted toward recent
        year = int(min(2026, max(1950, random.gauss(2005, 20))))
        
        # Votes: 0-3M, log-normal distribution
        votes = int(max(100, min(3_000_000, random.lognormvariate(12, 2))))
        
        # Genre vector with some noise
        base_vector = GENRE_PROFILES[genre][:]
        genre_vector = [
            round(max(0.0, min(1.0, v + random.gauss(0, 0.1))), 2)
            for v in base_vector
        ]
        
        entries.append({
            'id': i + 1,
            'title': title,
            'type': media_type,
            'genre': genre,
            'rating': rating,
            'year': year,
            'votes': votes,
            'genre_vector': json.dumps(genre_vector),
        })
    
    return entries


def create_database(db_path=None, entries=None):
    """Create the Odyssey SQLite database."""
    if db_path is None:
        db_path = DATABASE_PATH
    if entries is None:
        entries = generate_entries(100)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS media")
    cursor.execute("""
        CREATE TABLE media (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            genre TEXT NOT NULL,
            rating REAL NOT NULL,
            year INTEGER NOT NULL,
            votes INTEGER NOT NULL,
            genre_vector TEXT NOT NULL
        )
    """)
    
    for entry in entries:
        cursor.execute("""
            INSERT INTO media (id, title, type, genre, rating, year, votes, genre_vector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry['id'], entry['title'], entry['type'], entry['genre'],
            entry['rating'], entry['year'], entry['votes'], entry['genre_vector']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Created {db_path} with {len(entries)} entries")
    return db_path


if __name__ == '__main__':
    create_database()
