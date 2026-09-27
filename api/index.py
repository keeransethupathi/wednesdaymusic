import os
import sys
import time
import requests
from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# Add api directory and parent directory to path so music_manager can be imported cleanly
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import music_manager
except ImportError:
    try:
        from . import music_manager
    except Exception as e:
        print(f"Import error: {e}")

app = FastAPI(title="Wednesday Songs API", version="2.0.0")

@app.middleware("http")
async def vercel_routing_middleware(request: Request, call_next):
    raw_path = request.scope.get("path", "")
    matched_path = request.headers.get("x-matched-path")
    query_path = request.query_params.get("__path__")

    target_path = None
    if matched_path:
        target_path = matched_path
    elif query_path:
        target_path = query_path if query_path.startswith("/") else f"/api/{query_path}"
    elif raw_path.startswith("/api/index.py"):
        sub = raw_path[len("/api/index.py"):]
        target_path = sub if sub else "/"
    elif raw_path.startswith("/api/index"):
        sub = raw_path[len("/api/index"):]
        target_path = sub if sub else "/"

    if target_path:
        if not target_path.startswith("/"):
            target_path = "/" + target_path
        request.scope["path"] = target_path

    return await call_next(request)

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
@app.get("/health")
@app.get("/api")
@app.get("/")
def health_check():
    return {"status": "ok", "service": "Wednesday Songs API", "platform": "Vercel"}

@app.get("/api/search")
@app.get("/search")
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
@app.get("/trending")
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
@app.get("/lyrics")
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
@app.get("/proxy-audio")
def proxy_audio(request: Request, url: str = Query(...)):
    """
    Stream audio directly through the backend serverless proxy.
    Resolves CORS issues, 403 Forbidden hotlink blocks, corporate firewalls (e.g. Fortinet), and enables Range requests for seeking.
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
        
        # Bypass 403 Forbidden hotlink restriction if triggered
        if upstream.status_code in [403, 401]:
            alt_headers = {
                "User-Agent": "JioSaavn/6.1.0 Android/10",
                "Accept": "*/*"
            }
            if range_header:
                alt_headers["Range"] = range_header
            upstream = requests.get(url, headers=alt_headers, stream=True, timeout=15)
        
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

@app.get("/api/proxy-image")
@app.get("/proxy-image")
def proxy_image(url: str = Query(...)):
    """
    Proxy thumbnail images through backend to bypass 403 Forbidden hotlink prevention or corporate firewalls.
    """
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid image URL")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.jiosaavn.com/"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code in [403, 401]:
            # Fallback retry without referer
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            
        if res.status_code == 200:
            return Response(
                content=res.content,
                media_type=res.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=604800"}
            )
    except Exception as e:
        print(f"[Proxy Image Error] {e}")

    raise HTTPException(status_code=502, detail="Failed to fetch image")


# Mount static files when running locally (not on Vercel deployment)
if os.environ.get("VERCEL") != "1":
    public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
    if os.path.isdir(public_dir):
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=public_dir, html=True), name="static")

