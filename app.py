import sqlite3
import string
import random
import os

DB_FILE = "urls.db"
BASE_URL = "http://short.ly/"

def init_db():
    """Initialise la base de données SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    """Génère un code aléatoire composé de lettres et de chiffres."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def shorten(url):
    """
    Raccourcit une URL donnée en générant un code unique.
    Gère les collisions en générant un nouveau code si celui-ci existe déjà.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Vérifie si l'URL a déjà été raccourcie
    cursor.execute("SELECT short_code FROM urls WHERE original_url = ?", (url,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return BASE_URL + row[0]
    
    # Génère un code unique et gère les collisions
    while True:
        code = generate_short_code()
        cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (code,))
        if not cursor.fetchone():
            break
            
    # Insère la nouvelle association
    cursor.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)", (code, url))
    conn.commit()
    conn.close()
    
    return BASE_URL + code

def expand(short_url):
    """
    Retourne l'URL originale associée à l'URL raccourcie.
    Retourne None si le code n'est pas trouvé.
    """
    if not short_url.startswith(BASE_URL):
        return None
        
    code = short_url.replace(BASE_URL, "")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE short_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None

if __name__ == "__main__":
    init_db()
    
    # Test simple du fonctionnement
    test_url = "https://www.deepmind.com/research/highlighted-creative-work"
    print(f"URL originale : {test_url}")
    
    short_url = shorten(test_url)
    print(f"URL raccourcie : {short_url}")
    
    original_url = expand(short_url)
    print(f"URL retrouvée : {original_url}")
    
    # Test de gestion de collision / doublons
    short_url_duplicate = shorten(test_url)
    print(f"Vérification doublon (doit être identique) : {short_url_duplicate}")
