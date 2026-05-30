import os
from ytmusicapi import YTMusic

# Check for existing authenticated session
SESSION_FILE = "browser.json"
if os.path.exists(SESSION_FILE):
    try:
        yt = YTMusic(SESSION_FILE)
        print("[Music Manager] Connected to YouTube Pro using authenticated session.")
    except Exception as e:
        print(f"[Music Manager] Failed to load session file, falling back to public: {e}")
        yt = YTMusic()
else:
    yt = YTMusic()

def is_pro_connected():
    """Verify if an authenticated session file is active."""
    return os.path.exists(SESSION_FILE)

def setup_pro_connection(headers_raw_text):
    """
    Initialize browser headers file and validate connection.
    Returns (success_bool, message_string).
    """
    global yt
    if not headers_raw_text.strip():
        return False, "Headers cannot be empty."
        
    try:
        # Create browser.json file using raw headers
        YTMusic.setup(filepath=SESSION_FILE, headers_raw=headers_raw_text)
        
        # Test loading the file and query account library to verify
        test_client = YTMusic(SESSION_FILE)
        test_client.get_library(limit=1)
        
        # Success: update active client reference
        yt = test_client
        return True, "Successfully authenticated YouTube Pro!"
    except Exception as e:
        # Cleanup failed file
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except:
                pass
        # Fallback to public client
        yt = YTMusic()
        return False, f"Authentication failed: {str(e)}"

def disconnect_pro():
    """Delete authenticated session file and reset client reference."""
    global yt
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except:
            pass
    yt = YTMusic()

def search_songs(query, limit=15):
    """
    Search the public YouTube Music catalog for songs.
    Returns a list of parsed track dictionaries.
    """
    if not query.strip():
        return []
        
    try:
        results = yt.search(query, filter="videos", limit=limit)
        songs = []
        for r in results:
            video_id = r.get("videoId")
            if not video_id:
                continue
                
            # Combine artist names
            artists = r.get("artists", [])
            artist_name = ", ".join([a.get("name", "Unknown") for a in artists]) if artists else "Unknown Artist"
            
            # Fetch high-quality thumbnail
            thumbnails = r.get("thumbnails", [])
            thumb_url = ""
            if thumbnails:
                # Get the largest available thumbnail
                thumb_url = thumbnails[-1].get("url", "")
                
            # Parse album name
            album = "Single"
            if r.get("album"):
                album = r.get("album", {}).get("name", "Single")
                
            songs.append({
                "video_id": video_id,
                "title": r.get("title", "Unknown Song"),
                "artist": artist_name,
                "album": album,
                "thumbnail": thumb_url,
                "duration": r.get("duration", "3:00")
            })
        return songs
    except Exception as e:
        print(f"[Music Manager] Error searching for '{query}': {e}")
        return []

def get_lyrics(video_id):
    """
    Retrieve lyrics for a song using its YouTube videoId.
    Returns the lyrics text or an error message.
    """
    if not video_id:
        return "No track active."
        
    try:
        # 1. Fetch the watch playlist to get the lyrics browseId
        watch_playlist = yt.get_watch_playlist(videoId=video_id)
        lyrics_browse_id = watch_playlist.get("lyrics")
        
        # 2. Query the lyrics if available
        if lyrics_browse_id:
            lyrics_data = yt.get_lyrics(lyrics_browse_id)
            return lyrics_data.get("lyrics", "No lyrics text found.")
        else:
            return "Lyrics not available for this track."
    except Exception as e:
        return f"Could not retrieve lyrics. (Note: Not all tracks support lyrics on YouTube Music)"

def get_mood_playlist(mood):
    """
    Curate a list of tracks based on a mood/genre.
    This dynamically queries the public catalog for themed search results.
    """
    return search_songs(f"{mood} music", limit=10)

def get_library_playlists():
    """Retrieve the authenticated user's library playlists."""
    try:
        results = yt.get_library_playlists(limit=25)
        playlists = []
        for r in results:
            thumbnails = r.get("thumbnails", [])
            thumb_url = thumbnails[-1].get("url", "") if thumbnails else ""
            playlists.append({
                "id": r.get("playlistId"),
                "title": r.get("title", "Untitled Playlist"),
                "thumbnail": thumb_url,
                "count": r.get("count", "0")
            })
        return playlists
    except Exception as e:
        print(f"[Music Manager] Error retrieving library playlists: {e}")
        return []

def get_playlist_tracks(playlist_id):
    """Retrieve and parse tracks inside a specific playlist."""
    if not playlist_id:
        return []
        
    try:
        playlist_data = yt.get_playlist(playlist_id)
        tracks = []
        for t in playlist_data.get("tracks", []):
            video_id = t.get("videoId")
            if not video_id:
                continue
            artists = t.get("artists", [])
            artist_name = ", ".join([a.get("name", "Unknown") for a in artists]) if artists else "Unknown Artist"
            thumbnails = t.get("thumbnails", [])
            thumb_url = thumbnails[-1].get("url", "") if thumbnails else ""
            
            tracks.append({
                "video_id": video_id,
                "title": t.get("title", "Unknown Track"),
                "artist": artist_name,
                "album": t.get("album", {}).get("name", "Playlist") if t.get("album") else "Playlist",
                "thumbnail": thumb_url,
                "duration": t.get("duration", "3:00")
            })
        return tracks
    except Exception as e:
        print(f"[Music Manager] Error loading tracks for playlist {playlist_id}: {e}")
        return []
