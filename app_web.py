import json
import os
import random
import sqlite3
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_FILE = "urls.db"
PORT = 8000
BASE_URL = f"http://localhost:{PORT}/"

def init_db():
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
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def shorten(url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute("SELECT short_code FROM urls WHERE original_url = ?", (url,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return BASE_URL + row[0]
    
    # Handle collisions
    while True:
        code = generate_short_code()
        cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (code,))
        if not cursor.fetchone():
            break
            
    cursor.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)", (code, url))
    conn.commit()
    conn.close()
    return BASE_URL + code

def expand(code):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE short_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


class URLShortenerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract code from path
        parsed_path = urlparse(self.path)
        code = parsed_path.path.strip("/")
        
        if not code:
            # Home Page HTML form
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
                <head><title>URL Shortener</title></head>
                <body style="font-family: Arial, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333;">
                    <div style="max-width: 500px; margin: auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #4CAF50;">URL Shortener Service</h2>
                        <form action="/shorten" method="POST">
                            <input type="url" name="url" placeholder="Paste your URL here" style="width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px;" required>
                            <input type="submit" value="Shorten URL" style="width: 100%; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">
                        </form>
                    </div>
                </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
            return

        # Try to redirect to original URL
        original_url = expand(code)
        if original_url:
            self.send_response(302)
            self.send_header("Location", original_url)
            self.end_headers()
        else:
            self.send_error(404, "URL Not Found")

    def do_POST(self):
        if self.path == "/shorten":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse form data
            params = parse_qs(post_data)
            url_to_shorten = params.get('url', [None])[0]
            
            if url_to_shorten:
                shortened = shorten(url_to_shorten)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                response_html = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333;">
                        <div style="max-width: 500px; margin: auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <h2 style="color: #4CAF50;">URL Shortener Service</h2>
                            <p>Original: <a href="{url_to_shorten}" style="color: #2196F3;">{url_to_shorten}</a></p>
                            <p>Shortened URL: <strong><a href="{shortened}" style="color: #4CAF50;">{shortened}</a></strong></p>
                            <p><a href="/" style="color: #888; text-decoration: none;">← Go Back</a></p>
                        </div>
                    </body>
                </html>
                """
                self.wfile.write(response_html.encode("utf-8"))
            else:
                self.send_error(400, "Missing URL parameter")


def run():
    init_db()
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, URLShortenerHandler)
    print(f"Starting server on port {PORT}... Open {BASE_URL} in your browser.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
