import os
import sys
import time
import requests
from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# Add parent directory to path so music_manager can be imported cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import music_manager
except ImportError:
    # If deployed inside vercel where api is root
    try:
        from . import music_manager
    except ImportError:
        import music_manager

app = FastAPI(title="Wednesday Songs API", version="2.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory TTL cache for quick catalog responses
CACHE = {}
CACHE_TTL = 3600  # 1 hour

def get_cached(key):
    if key in CACHE:
        val, expire_time = CACHE[key]
        if time.time() < expire_time:
            return val
        else:
            del CACHE[key]
    return None

def set_cached(key, val, ttl=CACHE_TTL):
    CACHE[key] = (val, time.time() + ttl)

TRENDING_QUERIES = {
    "tamil": "latest tamil hit songs",
    "hindi": "latest hindi hit songs",
    "malayalam": "latest malayalam hit songs",
    "telugu": "latest telugu hit songs",
    "trending": "latest trending songs"
}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Wednesday Songs API", "platform": "Vercel"}

@app.get("/api/search")
def search_songs(q: str = Query(..., min_length=1), limit: int = Query(15, ge=1, le=50)):
    cache_key = f"search:{q.strip().lower()}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        return {"results": cached, "cached": True}

    try:
        results = music_manager.search_songs(q.strip(), limit=limit)
        set_cached(cache_key, results, ttl=1800)
        return {"results": results, "cached": False}
    except Exception as e:
        print(f"[API] Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trending")
def get_trending(tab: str = Query("tamil"), limit: int = Query(12, ge=1, le=30)):
    tab_lower = tab.lower()
    query_str = TRENDING_QUERIES.get(tab_lower, TRENDING_QUERIES["trending"])
    cache_key = f"trending:{tab_lower}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        return {"results": cached, "tab": tab_lower, "cached": True}

    try:
        results = music_manager.search_songs(query_str, limit=limit)
        set_cached(cache_key, results, ttl=3600)
        return {"results": results, "tab": tab_lower, "cached": False}
    except Exception as e:
        print(f"[API] Trending error for {tab}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lyrics")
def get_song_lyrics(track_id: str = Query(...)):
    cache_key = f"lyrics:{track_id}"
    cached = get_cached(cache_key)
    if cached is not None:
        return {"lyrics": cached, "track_id": track_id}

    try:
        lyrics = music_manager.get_lyrics(track_id)
        set_cached(cache_key, lyrics, ttl=7200)
        return {"lyrics": lyrics, "track_id": track_id}
    except Exception as e:
        print(f"[API] Lyrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lyrics")

@app.get("/api/proxy-audio")
def proxy_audio(request: Request, url: str = Query(...)):
    """
    Stream audio directly through the backend serverless proxy.
    This resolves CORS issues, corporate firewall blocks (e.g. Fortinet), and enables Range requests for seeking.
    """
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid audio URL")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.jiosaavn.com/"
    }

    # Forward client Range header if seeking
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    try:
        upstream = requests.get(url, headers=headers, stream=True, timeout=15)
        
        # Prepare response headers
        response_headers = {
            "Content-Type": upstream.headers.get("Content-Type", "audio/mp4"),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400"
        }
        if "Content-Range" in upstream.headers:
            response_headers["Content-Range"] = upstream.headers["Content-Range"]
        if "Content-Length" in upstream.headers:
            response_headers["Content-Length"] = upstream.headers["Content-Length"]

        status_code = upstream.status_code if upstream.status_code in [200, 206] else 200

        def stream_content():
            for chunk in upstream.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        return StreamingResponse(
            stream_content(),
            status_code=status_code,
            headers=response_headers,
            media_type=response_headers["Content-Type"]
        )
    except Exception as e:
        print(f"[API Proxy] Failed to stream audio: {e}")
        raise HTTPException(status_code=502, detail="Failed to stream audio from source")

# Mount static files when running locally or directly
public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
if os.path.isdir(public_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="static")
