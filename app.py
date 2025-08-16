import os
import io
from flask import Flask, jsonify, send_from_directory, abort, Response
from flask_cors import CORS
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

MUSIC_DIRECTORY = "/home/cw1a/Music"

@app.route('/')
def serve_index():
    """Serves the main index.html file."""
    return send_from_directory('.', 'index.html')

@app.route('/api/songs')
def list_songs():
    """
    API endpoint to list all available songs.
    It recursively scans the MUSIC_DIRECTORY for .mp3 files.
    """
    songs = []
    if not os.path.exists(MUSIC_DIRECTORY):
        print(f"Warning: Music directory '{MUSIC_DIRECTORY}' not found.")
        return jsonify([])

    for root, _, files in os.walk(MUSIC_DIRECTORY):
        for filename in files:
            if filename.lower().endswith('.mp3'):
                full_path = os.path.join(root, filename)
                
                # Create a URL-friendly relative path
                relative_path = os.path.relpath(full_path, MUSIC_DIRECTORY)
                relative_path_for_url = relative_path.replace('\\', '/')
                
                try:
                    audio_tags = EasyID3(full_path)
                    title = audio_tags.get('title', [os.path.splitext(filename)[0]])[0]
                    artist = audio_tags.get('artist', ['Unknown Artist'])[0]
                except Exception:
                    title = os.path.splitext(filename)[0]
                    artist = "Unknown Artist"

                songs.append({
                    "id": relative_path_for_url,
                    "title": title,
                    "artist": artist,
                    "src": f"/music/{relative_path_for_url}",
                    "albumArt": f"/art/{relative_path_for_url}"
                })
    
    songs.sort(key=lambda x: x['title'])
    return jsonify(songs)

@app.route('/music/<path:filepath>')
def serve_music(filepath):
    """Serves a music file from any subdirectory of the music directory."""
    return send_from_directory(MUSIC_DIRECTORY, filepath)

@app.route('/art/<path:filepath>')
def serve_art(filepath):
    """
    Dynamically extracts and serves the embedded album art from a specific audio file.
    """
    file_path = os.path.join(MUSIC_DIRECTORY, filepath)

    if not os.path.exists(file_path):
        abort(404, description="Audio file not found")

    try:
        audio = MP3(file_path, ID3=ID3)
        # Look for album art in the APIC frame
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                return Response(tag.data, mimetype=tag.mime)
        
        # If no art is found after checking
        abort(404, description="No embedded album art found")

    except Exception as e:
        print(f"Error extracting art from {filepath}: {e}")
        abort(500, description="Error processing audio file")


if __name__ == '__main__':
    # --- Instructions ---
    # 1. Install required libraries: pip install Flask Flask-Cors mutagen
    # 2. Create a 'music' directory in the same folder as this script.
    # 3. Place your .mp3 files directly inside the 'music' directory.
    #    The album art, title, and artist should be embedded in the MP3's metadata.
    #
    # Example Structure:
    # ./
    # |- app.py
    # |- index.html
    # |- music/
    #    |- Camellia - Versus!.mp3
    #    |- Another Artist - Another Song.mp3
    app.run(debug=True, port=3333)