import os
import requests
from jiosaavnpy import JioSaavn

# Initialize JioSaavn client
jio = JioSaavn()
print("[Music Manager] Connected to Wednesday Songs client.")

def is_pro_connected():
    """Wednesday Songs does not require authenticated user session files in this client."""
    return False

def setup_pro_connection(headers_raw_text):
    """Wednesday Songs does not require custom browser header files."""
    return False, "Pro authentication is not supported or required on Wednesday Songs."

def disconnect_pro():
    """Placeholder for backward compatibility."""
    pass

def search_songs(query, limit=15):
    """
    Search the JioSaavn catalog for songs.
    Returns a list of parsed track dictionaries.
    """
    if not query.strip():
        return []
        
    try:
        results = jio.search_songs(query, limit=limit)
        songs = []
        for r in results:
            track_id = r.get("track_id")
            if not track_id:
                continue
                
            title = r.get("title", "Unknown Song")
            
            # Extract artists
            artist_name = r.get("primary_artists", "Unknown Artist")
            if not artist_name:
                artist_name = "Unknown Artist"
                
            # Extract album
            album = r.get("album_name", "Single")
            if not album:
                album = "Single"
                
            # Fetch high-quality thumbnail (prefer 500x500, then 150x150, then 50x50)
            thumbnails_data = r.get("thumbnails", {})
            quality_data = thumbnails_data.get("quality", {}) if isinstance(thumbnails_data, dict) else {}
            thumb_url = quality_data.get("500x500") or quality_data.get("150x150") or quality_data.get("50x50") or ""
            
            # Fetch stream URL (prefer very_high_quality 320kbps, down to low_quality)
            stream_urls_data = r.get("stream_urls", {})
            stream_url = ""
            if isinstance(stream_urls_data, dict):
                stream_url = (stream_urls_data.get("very_high_quality") or 
                              stream_urls_data.get("high_quality") or 
                              stream_urls_data.get("medium_quality") or 
                              stream_urls_data.get("low_quality") or "")
                
            # Parse duration from seconds to MM:SS format
            duration_secs_str = r.get("duration", "180")
            try:
                duration_secs = int(duration_secs_str)
                minutes = duration_secs // 60
                seconds = duration_secs % 60
                duration_str = f"{minutes}:{seconds:02d}"
            except:
                duration_str = "3:00"
                
            songs.append({
                "track_id": track_id,
                "title": title,
                "artist": artist_name,
                "album": album,
                "thumbnail": thumb_url,
                "duration": duration_str,
                "stream_url": stream_url
            })
        return songs
    except Exception as e:
        print(f"[Music Manager] Error searching for '{query}': {e}")
        return []

def get_lyrics(track_id):
    """
    Retrieve lyrics for a song using its JioSaavn track ID.
    Returns the lyrics text or an error message.
    """
    if not track_id:
        return "No track active."
        
    try:
        url = f"https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&ctx=web6dot0&api_version=4&_format=json&lyrics_id={track_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and data.get("status") != "failure":
                lyrics_html = data.get("lyrics", "")
                if lyrics_html:
                    # Replace HTML line breaks with newlines
                    lyrics = (lyrics_html
                              .replace("<br>", "\n")
                              .replace("<br/>", "\n")
                              .replace("<br />", "\n"))
                    return lyrics
            return "Lyrics not available for this track on Wednesday Songs."
        return "Could not retrieve lyrics from Wednesday Songs."
    except Exception as e:
        print(f"[Music Manager] Error loading lyrics for track {track_id}: {e}")
        return "Could not retrieve lyrics."

def get_mood_playlist(mood):
    """
    Curate a list of tracks based on a mood/genre.
    This dynamically queries the catalog for themed search results.
    """
    return search_songs(f"{mood} music", limit=10)

def get_library_playlists():
    """JioSaavn client does not support custom library playlists in this version."""
    return []

def get_playlist_tracks(playlist_id, limit=100):
    """
    Retrieve tracks from a JioSaavn playlist using its token/public ID.
    Returns a list of parsed track dictionaries.
    """
    if not playlist_id:
        return []
        
    try:
        url = f"https://www.jiosaavn.com/api.php?__call=webapi.get&type=playlist&token={playlist_id}&_format=json&cc=in&n={limit}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return []
            
        data = res.json()
        raw_songs = data.get("songs", [])
        parsed_songs = []
        
        for s in raw_songs:
            track_id = s.get("id")
            if not track_id:
                continue
                
            title = s.get("song", "Unknown Song")
            
            # Extract artists
            artist_name = s.get("primary_artists", "Unknown Artist")
            if not artist_name:
                artist_name = "Unknown Artist"
                
            # Extract album
            album = s.get("album", "Single")
            if not album:
                album = "Single"
                
            # Fetch high-quality thumbnail
            thumb_url = s.get("image", "")
            if thumb_url and "-150x150." in thumb_url:
                thumb_url = thumb_url.replace("-150x150.", "-500x500.")
            elif thumb_url and "-50x50." in thumb_url:
                thumb_url = thumb_url.replace("-50x50.", "-500x500.")
                
            # Decrypt stream URL
            stream_url = ""
            enc_url = s.get("encrypted_media_url", "")
            if enc_url:
                try:
                    decrypted_urls = jio.decrypt_stream_url(enc_url, True)
                    if isinstance(decrypted_urls, dict):
                        stream_url = (decrypted_urls.get("very_high_quality") or 
                                      decrypted_urls.get("high_quality") or 
                                      decrypted_urls.get("medium_quality") or 
                                      decrypted_urls.get("low_quality") or "")
                except Exception as e:
                    print(f"[Music Manager] Error decrypting stream URL for song {track_id}: {e}")
            
            # Parse duration from seconds to MM:SS format
            duration_secs_str = s.get("duration", "180")
            try:
                duration_secs = int(duration_secs_str)
                minutes = duration_secs // 60
                seconds = duration_secs % 60
                duration_str = f"{minutes}:{seconds:02d}"
            except:
                duration_str = "3:00"
                
            parsed_songs.append({
                "track_id": track_id,
                "title": title,
                "artist": artist_name,
                "album": album,
                "thumbnail": thumb_url,
                "duration": duration_str,
                "stream_url": stream_url
            })
            
        return parsed_songs
    except Exception as e:
        print(f"[Music Manager] Error loading playlist tracks for {playlist_id}: {e}")
        return []




