import streamlit as st
import os
import importlib
import music_manager
import streamlit.components.v1 as components
import base64
import requests

# Force reload of music_manager to pick up updates without server restart
importlib.reload(music_manager)

@st.cache_data(show_spinner=False, ttl=1800, max_entries=50)
def get_media_bytes(url):
    """Fetch media content (audio) in the backend to bypass client-side Fortinet blocks."""
    if not url:
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.content
    except Exception as e:
        print(f"[Backend Proxy] Error fetching media: {e}")
    return None

@st.cache_data(show_spinner=False, ttl=1800, max_entries=100)
def get_image_base64_uri(url):
    """Fetch image in the backend and convert to base64 Data URI to bypass Fortinet blocks."""
    if not url:
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            encoded = base64.b64encode(res.content).decode("utf-8")
            content_type = res.headers.get("Content-Type", "image/jpeg")
            return f"data:{content_type};base64,{encoded}"
    except Exception as e:
        print(f"[Backend Proxy] Error base64-encoding image: {e}")
    return url  # Fallback to original URL

# Page configurations
st.set_page_config(
    page_title="Wednesday Songs",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom JioSaavn-style glassmorphic dark mode styling and bottom player iframe positioning
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0b0f19 !important; /* JioSaavn Slate Blue */
        color: #ffffff !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible !important;}

    /* Hide the close button when sidebar is open */
    section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
    section[data-testid="stSidebar"] [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Hide the auto-next trigger button wrapper container completely */
    div.element-container:has(button[key="auto_next_trigger"]),
    button[key="auto_next_trigger"],
    button[aria-label="AutoNextTrigger"] {
        display: none !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* Sidebar JioSaavn branding */
    section[data-testid="stSidebar"] {
        background-color: #070a13 !important; /* Sidebar Dark Slate */
        border-right: 1px solid #1a2235 !important;
        padding-top: 10px;
    }

    /* Padding to avoid layout overlapping */
    div.block-container {
        padding-top: 30px !important;
    }

    /* Styled cards for albums and tracks */
    .track-row {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        border-radius: 8px;
        background-color: #111827;
        border: 1px solid #1a2235;
        margin-bottom: 8px;
        transition: background-color 0.2s, border-color 0.2s;
    }
    .track-row:hover {
        background-color: #1f2937;
        border-color: #00d2c4;
    }
    .track-image {
        width: 50px;
        height: 50px;
        border-radius: 6px;
        object-fit: cover;
        margin-right: 16px;
    }
    .track-meta {
        flex-grow: 1;
        overflow: hidden;
    }
    .track-title {
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .track-artist {
        font-size: 13px;
        color: #9ca3af;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Album cards grid */
    .album-card {
        background-color: #111827;
        border: 1px solid #1a2235;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s, border-color 0.2s;
        cursor: pointer;
    }
    .album-card:hover {
        background-color: #1f2937;
        border-color: #00d2c4;
        transform: translateY(-4px);
    }
    .album-image {
        width: 100%;
        aspect-ratio: 1;
        border-radius: 8px;
        object-fit: cover;
        margin-bottom: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    .album-title {
        font-size: 14px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Pulsing Visualizer Style */
    .visualizer-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 180px;
        margin-top: 20px;
    }
    .pulse-disc {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: radial-gradient(circle, #00d2c4 30%, #070a13 100%);
        box-shadow: 0 0 20px #00d2c4;
        animation: pulse-visual 1.8s infinite ease-in-out;
    }
    @keyframes pulse-visual {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 10px rgba(0, 210, 196, 0.5);
        }
        50% {
            transform: scale(1.08);
            box-shadow: 0 0 35px rgba(0, 210, 196, 0.9);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 10px rgba(0, 210, 196, 0.5);
        }
    }

    /* Custom styles for Streamlit buttons in sidebar */
    .stButton>button {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #1a2235 !important;
        border-radius: 20px !important;
        transition: all 0.2s !important;
    }
    .stButton>button:hover {
        background-color: #374151 !important;
        border-color: #00d2c4 !important;
    }
</style>
""", unsafe_allow_html=True)



# Initialize session state variables
if "current_track" not in st.session_state:
    st.session_state.current_track = None
if "queue" not in st.session_state:
    st.session_state.queue = []
if "history" not in st.session_state:
    st.session_state.history = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "lyrics" not in st.session_state:
    st.session_state.lyrics = None
if "active_view" not in st.session_state:
    st.session_state.active_view = "Home"
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

# Playback helper logic
def play_track(track):
    """Set the active track and push the previous track to history."""
    if st.session_state.current_track:
        if not st.session_state.history or st.session_state.history[-1]["track_id"] != st.session_state.current_track["track_id"]:
            st.session_state.history.append(st.session_state.current_track)
            if len(st.session_state.history) > 50:
                st.session_state.history.pop(0)
                
    st.session_state.current_track = track
    st.session_state.lyrics = None
    st.session_state.is_playing = True

def add_to_queue(track):
    """Add a track to the play next queue."""
    st.session_state.queue.append(track)
    st.toast(f"Added to Queue: {track['title']}")

def skip_next_track():
    """Skip to the next song in the queue."""
    if st.session_state.queue:
        next_track = st.session_state.queue.pop(0)
        play_track(next_track)
    else:
        st.toast("Queue is empty. Select a new song!")

def skip_prev_track():
    """Go back to the previously played track."""
    if st.session_state.history:
        prev_track = st.session_state.history.pop()
        st.session_state.current_track = prev_track
        st.session_state.lyrics = None
        st.session_state.is_playing = True
    else:
        st.toast("No previous tracks in history.")



# --- SIDEBAR Layout ---
st.sidebar.markdown("<h2 style='color:#00d2c4; font-weight:800; margin-bottom:15px; text-align:center;'>🎵 WEDNESDAY SONGS</h2>", unsafe_allow_html=True)

# 1. Search Bar at the VERY TOP of the sidebar aligned side-by-side using columns
st.sidebar.markdown("<p style='color:#9ca3af; font-size:0.75rem; font-weight:700; margin-left:5px;'>SEARCH CATALOG</p>", unsafe_allow_html=True)
col_search_in, col_search_btn = st.sidebar.columns([0.76, 0.24])

search_input = col_search_in.text_input("Search catalog", placeholder="Search songs, artists...", label_visibility="collapsed")
search_clicked = col_search_btn.button("🔍", key="sidebar_search_button", use_container_width=True)

if search_clicked or (search_input and search_input != st.session_state.get("last_search", "")):
    if search_input.strip():
        st.session_state.last_search = search_input
        with st.spinner("Searching Wednesday Songs..."):
            st.session_state.search_results = music_manager.search_songs(search_input.strip())
            st.session_state.results_title = f"Search Results for '{search_input.strip()}'"
            st.session_state.active_view = "Search Results"
            st.rerun()

st.sidebar.markdown("<hr style='border-color:#1a2235; margin: 15px 0;'/>", unsafe_allow_html=True)

st.sidebar.markdown("<p style='color:#9ca3af; font-size:0.75rem; font-weight:700; margin-top:15px; margin-left:5px;'>YOUR LIBRARY</p>", unsafe_allow_html=True)
if st.sidebar.button("🏠 Home Dashboard", use_container_width=True):
    st.session_state.active_view = "Home"
    st.rerun()



# Queue Display
st.sidebar.markdown("<p style='color:#9ca3af; font-size:0.75rem; font-weight:700; margin-top:25px; margin-left:5px;'>PLAYING NEXT</p>", unsafe_allow_html=True)
if st.session_state.queue:
    for idx, q_track in enumerate(st.session_state.queue[:4]):
        st.sidebar.markdown(f"""
        <div style="font-size:0.85rem; color:#ffffff; padding:4px 8px; border-radius:4px; margin-bottom:4px; background:#111827; border: 1px solid #1a2235; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            {idx+1}. <b>{q_track['title']}</b><br>
            <span style="color:#9ca3af; font-size:0.75rem;">{q_track['artist']}</span>
        </div>
        """, unsafe_allow_html=True)
    if len(st.session_state.queue) > 4:
        st.sidebar.markdown(f"<p style='color:#9ca3af; font-size:0.75rem; text-align:center;'>+ {len(st.session_state.queue)-4} more songs</p>", unsafe_allow_html=True)
    if st.sidebar.button("Clear Queue", use_container_width=True):
        st.session_state.queue = []
        st.rerun()
else:
    st.sidebar.markdown("<p style='color:#4b5563; font-size:0.8rem; margin-left:5px;'>Queue is empty.</p>", unsafe_allow_html=True)

# Hidden auto-next trigger button
if st.sidebar.button("AutoNextTrigger", key="auto_next_trigger"):
    skip_next_track()
    st.rerun()

# --- MAIN PANEL LAYOUT ---
col_main, col_player = st.columns([0.7, 0.3])

with col_main:
    # Main Content Area
    if st.session_state.active_view == "Home":
        st.markdown("<h1>Good Afternoon</h1>", unsafe_allow_html=True)

        # Popular quick play tracklist
        st.markdown("<h3 style='margin-top:40px; margin-bottom:15px;'>Trending Tracks</h3>", unsafe_allow_html=True)
        
        tab_names = ["Tamil 🌟", "Hindi", "Malayalam", "Telugu", "Trending Now"]
        tabs = st.tabs(tab_names)
        
        queries = {
            "Tamil 🌟": {"query": "latest tamil hit songs", "key": "trending_tamil"},
            "Hindi": {"query": "latest hindi hit songs", "key": "trending_hindi"},
            "Malayalam": {"query": "latest malayalam hit songs", "key": "trending_malayalam"},
            "Telugu": {"query": "latest telugu hit songs", "key": "trending_telugu"},
            "Trending Now": {"query": "latest trending songs", "key": "trending_now"}
        }
        
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                config = queries[tab_name]
                cache_key = config["key"]
                if cache_key not in st.session_state:
                    with st.spinner(f"Fetching {tab_name} tracks..."):
                        st.session_state[cache_key] = music_manager.search_songs(config["query"], limit=20)
                
                tracks = st.session_state[cache_key]
                if not tracks:
                    st.info(f"No tracks found for {tab_name}.")
                else:
                    for track in tracks:
                        col_img, col_det, col_act = st.columns([0.08, 0.72, 0.20])
                        col_img.image(get_image_base64_uri(track["thumbnail"]), width=50)
                        col_det.markdown(f"<b>{track['title']}</b><br><span style='color:#9ca3af; font-size:0.85rem;'>{track['artist']} &nbsp;|&nbsp; {track['album']}</span>", unsafe_allow_html=True)
                        
                        c_play, c_queue = col_act.columns(2)
                        if c_play.button("▶️ Play", key=f"trend_play_{cache_key}_{track['track_id']}"):
                            play_track(track)
                            st.rerun()
                        if c_queue.button("➕ Queue", key=f"trend_q_{cache_key}_{track['track_id']}"):
                            add_to_queue(track)
                            st.rerun()

        # Featured Tamil Playlists Section
        st.markdown("<h3 style='margin-top:40px; margin-bottom:15px;'>Featured Tamil Playlists</h3>", unsafe_allow_html=True)
        
        playlists_data = [
            {"title": 'Therific Theme', "token": ',JL,xvmQHE0_', "image": 'https://c.saavncdn.com/editorial/TherificTheme_20260528051116_500x500.jpg'},
            {"title": "Let's Play - Vijay", "token": '-KAZYpBulyM_', "image": 'https://c.saavncdn.com/editorial/Let_sPlayVijay_20250217095544_500x500.jpg'},
            {"title": 'Viral Nation', "token": 'tfVkYjaAbZJieSJqt9HmOQ__', "image": 'https://c.saavncdn.com/editorial/ViralNation_20260603114636_500x500.jpg'},
            {"title": 'Semma Mass - Tamil', "token": 'R2ISZzIDGJc_', "image": 'https://c.saavncdn.com/editorial/SemmaMassTamil_20260518135619_500x500.jpg'},
            {"title": 'Best of Romance - Tamil', "token": 'P2sTu90EH1sZmWp1Op3nVA__', "image": 'https://c.saavncdn.com/editorial/BestofRomanceTamil_20260422094532_500x500.jpg'},
            {"title": 'ArtistOne Finds', "token": 'nOyNH0fuWtGP3AiNrzXpzA__', "image": 'https://c.saavncdn.com/editorial/ArtistOneFinds_20260612061156_500x500.jpg'},
            {"title": "Let's Play - Anirudh Ravichander - Tamil", "token": 'ePUVUJs1h,E_', "image": 'https://c.saavncdn.com/editorial/Let_sPlayAnirudhRavichanderTamil_20250217095503_500x500.jpg'},
            {"title": 'Top Kuthu - Tamil', "token": 'CNVzQf7lvT8wkg5tVhI3fw__', "image": 'https://c.saavncdn.com/editorial/TopKuthuTamil_20260422094846_500x500.jpg'},
            {"title": "Let's Play - Rajinikanth", "token": 'hVwUe6exUYM_', "image": 'https://c.saavncdn.com/editorial/Let_sPlayRajinikanth_20250218065230_500x500.jpg'},
            {"title": 'MGR Philosophical Songs - Tamil', "token": 'DWnFgpgW3PwGSw2I1RxdhQ__', "image": 'https://c.saavncdn.com/editorial/MGRPhilosophicalSongsTamil_20251209063307_500x500.jpg'},
            {"title": "Let's Play - Pradeep Ranganathan", "token": 'pfqtqaCDk6apJ,OEBt5Zbg__', "image": 'https://c.saavncdn.com/editorial/Let_sPlayPradeepRanganathan_20260403085039_500x500.jpg'},
            {"title": "Let's Play - A.R. Rahman", "token": '9qHvXYY4r,JFo9wdEAzFBA__', "image": 'https://c.saavncdn.com/editorial/Let_sPlayA-R-Rahman_20231218061538_500x500.jpg'},
            {"title": 'Tamil Hit Songs', "token": 'QbD85KAEmtcZmWp1Op3nVA__', "image": 'https://c.saavncdn.com/editorial/TamilHitSongs_20250217095444_500x500.jpg'},
            {"title": 'Iravaaga Nee', "token": '5NTonN-oTdpuOxiEGmm6lQ__', "image": 'https://c.saavncdn.com/editorial/IravaagaNee_20260302042438_500x500.jpg'},
            {"title": 'Dance in Love - Tamil', "token": 'Le-woPWglF1ieSJqt9HmOQ__', "image": 'https://c.saavncdn.com/editorial/DanceinLoveTamil_20260305071023_500x500.jpg'},
            {"title": 'Mazhai Melodies', "token": 'nCKY99zWUMQ_', "image": 'https://c.saavncdn.com/editorial/MazhaiMelodies_20251201153855_500x500.jpg'},
            {"title": "Let's Play - Sai Abhyankkar", "token": 'At02y,UCrb,QbUI04mhbCA__', "image": 'https://c.saavncdn.com/editorial/Let_sPlaySaiAbhyankkar_20251028120032_500x500.jpg'},
            {"title": "Let's Play - Sivakarthikeyan", "token": 'Ml,4H8ou2pM_', "image": 'https://c.saavncdn.com/editorial/Let_sPlaySivakarthikeyan_20250211135435_500x500.jpg'},
            {"title": "Let's Play - Suriya", "token": 'VvbhxbsrhEg_', "image": 'https://c.saavncdn.com/editorial/Let_sPlaySuriya_20250217095552_500x500.jpg'},
            {"title": 'Manam Virumbum Melody', "token": 'JLxZmGNZvU4_', "image": 'https://c.saavncdn.com/editorial/ManamVirumbumMelody_20260105090923_500x500.jpg'},
            {"title": 'Trending POP - Tamil', "token": '5z8vKjNnhmIGSw2I1RxdhQ__', "image": 'https://c.saavncdn.com/editorial/TrendingPOPTamil_20260422094931_500x500.jpg'},
            {"title": 'Motivational Hits - Tamil', "token": 'jMHINeLYW1eO0eMLZZxqsA__', "image": 'https://c.saavncdn.com/editorial/MotivationalHitsTamil_20251126081151_500x500.jpg'},
            {"title": 'Pudhu Jodi', "token": 'K2ClpzkOqzTfemJ68FuXsA__', "image": 'https://c.saavncdn.com/editorial/PudhuJodi_20260225035907_500x500.jpg'},
            {"title": 'Chartbusters 2024 - Tamil', "token": 'AeFkwBP3WxIrMQGDkCmGvg__', "image": 'https://c.saavncdn.com/editorial/Chartbusters2024Tamil_20241205112832_500x500.jpg'},
            {"title": 'Anirudh Ravichander - Party Songs - Tamil', "token": 'TUXyju4uMac_', "image": 'https://c.saavncdn.com/editorial/AnirudhDanceSongsTamil_20240213054952_500x500.jpg'},
            {"title": "Let's Play - Ajith Kumar", "token": 'oAj,lBFGWbU_', "image": 'https://c.saavncdn.com/editorial/Let_sPlayAjithKumar_20250310083422_500x500.jpg'},
            {"title": 'Mann Vasanai - Tamil', "token": 'FSoXzFcf8jMGSw2I1RxdhQ__', "image": 'https://c.saavncdn.com/editorial/MannVasanaiTamil_20260225035901_500x500.jpg'},
            {"title": 'Mazhai Dance', "token": 'c5gIC3jvDZZuOxiEGmm6lQ__', "image": 'https://c.saavncdn.com/editorial/MazhaiDance_20260225035856_500x500.jpg'},
            {"title": 'A.R. Rahman - Party Songs - Tamil', "token": 'GbtG0AkkczPfemJ68FuXsA__', "image": 'https://c.saavncdn.com/editorial/A-R-RahmanDanceSongsTamil_20240213060615_500x500.jpg'},
            {"title": 'Dance Queens - Tamil', "token": '2uwAUQjOVlnfemJ68FuXsA__', "image": 'https://c.saavncdn.com/editorial/DanceQueensTamil_20251209063316_500x500.jpg'},
        ]
        
        # Display in 4 columns
        rows = [playlists_data[i:i+4] for i in range(0, len(playlists_data), 4)]
        for row_idx, row in enumerate(rows):
            cols = st.columns(4)
            for col, p in zip(cols, row):
                with col:
                    st.markdown(f"""
                    <div class="album-card">
                        <img class="album-image" src="{get_image_base64_uri(p['image'])}" alt="{p['title']}">
                        <div class="album-title">{p['title']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Open Playlist", key=f"playlist_btn_{p['token']}_{row_idx}", use_container_width=True):
                        with st.spinner(f"Loading {p['title']}..."):
                            st.session_state.search_results = music_manager.get_playlist_tracks(p['token'])
                            st.session_state.results_title = p['title']
                            st.session_state.active_view = "Search Results"
                            st.rerun()



    elif st.session_state.active_view == "Search Results":
        title = st.session_state.get("results_title", "Search Results")
        st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#9ca3af; margin-bottom:25px;'>Found {len(st.session_state.search_results)} tracks</p>", unsafe_allow_html=True)
        
        if not st.session_state.search_results:
            st.info("No tracks found. Try searching for something else in the sidebar!")
        else:
            for idx, track in enumerate(st.session_state.search_results):
                st.markdown(f"""
                <div class="track-row">
                    <img class="track-image" src="{get_image_base64_uri(track['thumbnail'])}" alt="Thumb">
                    <div class="track-meta">
                        <div class="track-title">{track['title']}</div>
                        <div class="track-artist">{track['artist']} &nbsp;|&nbsp; {track['album']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_play, col_queue, col_duration = st.columns([0.15, 0.15, 0.70])
                if col_play.button("▶️ Play Now", key=f"play_{track['track_id']}_{idx}"):
                    play_track(track)
                    st.rerun()
                if col_queue.button("➕ Add to Queue", key=f"queue_{track['track_id']}_{idx}"):
                    add_to_queue(track)
                    st.rerun()

with col_player:
    # Active Playing Widget (Right Panel / "Right Tab")
    if st.session_state.current_track:
        track = st.session_state.current_track
        st.markdown("<div style='background-color:#111827; border:1px solid #1a2235; border-radius:12px; padding:20px; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<p style='color:#00d2c4; font-size:0.85rem; font-weight:800; margin-bottom:15px;'>NOW PLAYING</p>", unsafe_allow_html=True)
        
        st.image(get_image_base64_uri(track["thumbnail"]), use_container_width=True)
        st.markdown(f"<h3 style='margin: 12px 0 2px 0; color:#ffffff; font-size:1.2rem;'>{track['title']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#9ca3af; font-size:0.9rem; margin-bottom:20px;'>{track['artist']}</p>", unsafe_allow_html=True)
        
        # Audio Player controls: Prev, Play/Pause, Next, Stop
        c_prev, c_play_pause, c_next, c_stop = st.columns(4)
        
        if c_prev.button("⏮️", key="main_prev", use_container_width=True):
            skip_prev_track()
            st.rerun()
            
        # Play/Pause toggle
        if st.session_state.is_playing:
            if c_play_pause.button("⏸️", key="main_pause", use_container_width=True):
                st.session_state.is_playing = False
                st.rerun()
        else:
            if c_play_pause.button("▶️", key="main_play", use_container_width=True):
                st.session_state.is_playing = True
                st.rerun()
                
        if c_next.button("⏭️", key="main_next", use_container_width=True):
            skip_next_track()
            st.rerun()
            
        if c_stop.button("⏹️", key="main_stop", use_container_width=True):
            st.session_state.current_track = None
            st.session_state.is_playing = False
            st.rerun()
            
        st.markdown("<hr style='border-color:#1a2235; margin: 15px 0;'/>", unsafe_allow_html=True)
        
        # Audio Stream Playback Component
        if st.session_state.is_playing:
            if track.get("stream_url"):
                # Fetch audio stream bytes in backend to bypass firewall blocks
                with st.spinner("Buffering audio stream..."):
                    audio_bytes = get_media_bytes(track["stream_url"])
                
                if audio_bytes:
                    st.audio(audio_bytes, autoplay=True, format="audio/mp4")
                else:
                    st.audio(track["stream_url"], autoplay=True, format="audio/mp4")
                
                # Auto-play next song when current finishes
                components.html(f"""
                <script>
                    function setupAutoNext() {{
                        const parentDoc = window.parent.document;
                        
                        function getTriggerBtn() {{
                            const buttons = parentDoc.querySelectorAll('button');
                            for (const btn of buttons) {{
                                if (btn.textContent.includes('AutoNextTrigger')) {{
                                    return btn;
                                }}
                            }}
                            return null;
                        }}
                        
                        // Repeatedly check for audio elements and bind onended
                        const intervalId = setInterval(() => {{
                            const triggerBtn = getTriggerBtn();
                            const audios = parentDoc.querySelectorAll('audio');
                            if (audios.length > 0 && triggerBtn) {{
                                const audio = audios[audios.length - 1];
                                // Prevent multiple bindings
                                if (!audio.dataset.onendedBound) {{
                                    audio.onended = function() {{
                                        console.log("[AutoNext] Audio completed. Clicking trigger button.");
                                        triggerBtn.click();
                                    }};
                                    audio.dataset.onendedBound = "true";
                                    console.log("[AutoNext] Bound onended event successfully.");
                                }}
                            }}
                        }}, 500);
                        
                        // Clean up interval on page unload
                        window.addEventListener('unload', () => clearInterval(intervalId));
                    }}
                    setupAutoNext();
                </script>
                """, height=0)
            else:
                st.warning("No streaming URL available for this track.")
        else:
            st.info("Playback Paused.")
            
        # Fetch and display lyrics
        if st.session_state.is_playing:
            if st.session_state.lyrics is None:
                with st.spinner("Fetching lyrics..."):
                    st.session_state.lyrics = music_manager.get_lyrics(track["track_id"])
            
            with st.expander("📝 View Song Lyrics", expanded=False):
                st.markdown(f"<div style='font-size:0.85rem; text-align:left; max-height:220px; overflow-y:auto; line-height:1.5; color:#e5e7eb; white-space:pre-line;'>{st.session_state.lyrics}</div>", unsafe_allow_html=True)
            
        # Pulsing visualizer
        if st.session_state.is_playing:
            st.markdown("""
            <div class="visualizer-container" style="height: 110px; margin-top: 15px;">
                <div class="pulse-disc" style="width: 70px; height: 70px;"></div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Empty placeholder state for right panel
        st.markdown("""
        <div style="background-color:#111827; border: 1px dashed #4b5563; border-radius:12px; padding:35px; text-align:center; color:#9ca3af; height: 100%;">
            <h4 style="margin:0; color:#4b5563;">🎵 No Song Playing</h4>
            <p style="margin:5px 0 0 0; font-size:0.85rem;">Select a track to start streaming!</p>
        </div>
        """, unsafe_allow_html=True)
