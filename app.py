import streamlit as st
import os
import music_manager

# Page configurations
st.set_page_config(
    page_title="YouTube Music Connect",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Spotify-style dark mode styling and fixed bottom player iframe positioning
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #121212 !important; /* Spotify Main Gray */
        color: #ffffff !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar Spotify branding */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important; /* Spotify Sidebar Dark */
        border-right: 1px solid #282828 !important;
        padding-top: 10px;
    }

    /* Padding to avoid layout overlapping with player */
    div.block-container {
        padding-top: 30px !important;
    }

    /* Styled cards for albums and tracks */
    .track-row {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        border-radius: 6px;
        background-color: #181818;
        border: 1px solid #282828;
        margin-bottom: 8px;
        transition: background-color 0.2s;
    }
    .track-row:hover {
        background-color: #282828;
    }
    .track-image {
        width: 50px;
        height: 50px;
        border-radius: 4px;
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
        color: #b3b3b3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Album cards grid */
    .album-card {
        background-color: #181818;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
        cursor: pointer;
    }
    .album-card:hover {
        background-color: #282828;
        transform: translateY(-4px);
    }
    .album-image {
        width: 100%;
        aspect-ratio: 1;
        border-radius: 6px;
        object-fit: cover;
        margin-bottom: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
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
        background: radial-gradient(circle, #1db954 30%, #191414 100%);
        box-shadow: 0 0 20px #1db954;
        animation: pulse-visual 1.8s infinite ease-in-out;
    }
    @keyframes pulse-visual {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 10px rgba(29, 185, 84, 0.5);
        }
        50% {
            transform: scale(1.08);
            box-shadow: 0 0 35px rgba(29, 185, 84, 0.9);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 10px rgba(29, 185, 84, 0.5);
        }
    }

    /* Custom styles for Streamlit buttons in sidebar */
    .stButton>button {
        background-color: #282828 !important;
        color: #ffffff !important;
        border: 1px solid #282828 !important;
        border-radius: 20px !important;
        transition: all 0.2s !important;
    }
    .stButton>button:hover {
        background-color: #3e3e3e !important;
        border-color: #ffffff !important;
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
        if not st.session_state.history or st.session_state.history[-1]["video_id"] != st.session_state.current_track["video_id"]:
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
st.sidebar.markdown("<h2 style='color:#1db954; font-weight:800; margin-bottom:15px; text-align:center;'>🎵 YT MUSIC</h2>", unsafe_allow_html=True)

# 1. Search Bar at the VERY TOP of the sidebar aligned side-by-side using columns
st.sidebar.markdown("<p style='color:#b3b3b3; font-size:0.75rem; font-weight:700; margin-left:5px;'>SEARCH CATALOG</p>", unsafe_allow_html=True)
col_search_in, col_search_btn = st.sidebar.columns([0.76, 0.24])

search_input = col_search_in.text_input("Search catalog", placeholder="Search songs, artists...", label_visibility="collapsed")
search_clicked = col_search_btn.button("🔍", key="sidebar_search_button", use_container_width=True)

if search_clicked or (search_input and search_input != st.session_state.get("last_search", "")):
    if search_input.strip():
        st.session_state.last_search = search_input
        with st.spinner("Searching YouTube Music..."):
            st.session_state.search_results = music_manager.search_songs(search_input.strip())
            st.session_state.active_view = "Search Results"
            st.rerun()

st.sidebar.markdown("<hr style='border-color:#282828; margin: 15px 0;'/>", unsafe_allow_html=True)

# YouTube Pro connection removed

st.sidebar.markdown("<p style='color:#b3b3b3; font-size:0.75rem; font-weight:700; margin-top:15px; margin-left:5px;'>YOUR LIBRARY</p>", unsafe_allow_html=True)
if st.sidebar.button("🏠 Home Dashboard", use_container_width=True):
    st.session_state.active_view = "Home"
    st.rerun()

# Playlists button removed

# Pre-seeded Genre Buttons
st.sidebar.markdown("<p style='color:#b3b3b3; font-size:0.75rem; font-weight:700; margin-top:15px; margin-left:5px;'>MOODS & GENRES</p>", unsafe_allow_html=True)
col_l, col_r = st.sidebar.columns(2)
if col_l.button("Lo-Fi Beats", use_container_width=True):
    with st.spinner("Loading playlist..."):
        st.session_state.search_results = music_manager.get_mood_playlist("lofi beats")
        st.session_state.active_view = "Search Results"
        st.rerun()
if col_r.button("Synthwave", use_container_width=True):
    with st.spinner("Loading playlist..."):
        st.session_state.search_results = music_manager.get_mood_playlist("synthwave retro")
        st.session_state.active_view = "Search Results"
        st.rerun()
if col_l.button("Chillout", use_container_width=True):
    with st.spinner("Loading playlist..."):
        st.session_state.search_results = music_manager.get_mood_playlist("ambient chillout")
        st.session_state.active_view = "Search Results"
        st.rerun()
if col_r.button("Top Hits", use_container_width=True):
    with st.spinner("Loading playlist..."):
        st.session_state.search_results = music_manager.get_mood_playlist("popular hit songs")
        st.session_state.active_view = "Search Results"
        st.rerun()

# Queue Display
st.sidebar.markdown("<p style='color:#b3b3b3; font-size:0.75rem; font-weight:700; margin-top:25px; margin-left:5px;'>PLAYING NEXT</p>", unsafe_allow_html=True)
if st.session_state.queue:
    for idx, q_track in enumerate(st.session_state.queue[:4]):
        st.sidebar.markdown(f"""
        <div style="font-size:0.85rem; color:#ffffff; padding:4px 8px; border-radius:4px; margin-bottom:4px; background:#181818; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            {idx+1}. <b>{q_track['title']}</b><br>
            <span style="color:#b3b3b3; font-size:0.75rem;">{q_track['artist']}</span>
        </div>
        """, unsafe_allow_html=True)
    if len(st.session_state.queue) > 4:
        st.sidebar.markdown(f"<p style='color:#b3b3b3; font-size:0.75rem; text-align:center;'>+ {len(st.session_state.queue)-4} more songs</p>", unsafe_allow_html=True)
    if st.sidebar.button("Clear Queue", use_container_width=True):
        st.session_state.queue = []
        st.rerun()
else:
    st.sidebar.markdown("<p style='color:#535353; font-size:0.8rem; margin-left:5px;'>Queue is empty.</p>", unsafe_allow_html=True)

# Now Playing moved to the right panel

# --- MAIN PANEL LAYOUT ---
col_main, col_player = st.columns([0.7, 0.3])

with col_main:
    # 2. Main Content Area
    if st.session_state.active_view == "Home":
        st.markdown("<h1>Good Afternoon</h1>", unsafe_allow_html=True)


        # Popular quick play tracklist
        st.markdown("<h3 style='margin-top:40px; margin-bottom:15px;'>Trending Tracks</h3>", unsafe_allow_html=True)
        trending_query = "latest tamil hit songs 2026"
        
        if "trending_cache" not in st.session_state:
            st.session_state.trending_cache = music_manager.search_songs(trending_query, limit=5)
            
        for track in st.session_state.trending_cache:
            col_img, col_det, col_act = st.columns([0.08, 0.72, 0.20])
            col_img.image(track["thumbnail"], width=50)
            col_det.markdown(f"<b>{track['title']}</b><br><span style='color:#b3b3b3; font-size:0.85rem;'>{track['artist']}</span>", unsafe_allow_html=True)
            
            c_play, c_queue = col_act.columns(2)
            if c_play.button("▶️ Play", key=f"trend_play_{track['video_id']}"):
                play_track(track)
                st.rerun()
            if c_queue.button("➕ Queue", key=f"trend_q_{track['video_id']}"):
                add_to_queue(track)
                st.rerun()

    elif st.session_state.active_view == "Search Results":
        st.markdown(f"<h1>Search Results</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#b3b3b3; margin-bottom:25px;'>Found {len(st.session_state.search_results)} tracks</p>", unsafe_allow_html=True)
        
        if not st.session_state.search_results:
            st.info("No tracks found. Try searching for something else in the sidebar!")
        else:
            for idx, track in enumerate(st.session_state.search_results):
                st.markdown(f"""
                <div class="track-row">
                    <img class="track-image" src="{track['thumbnail']}" alt="Thumb">
                    <div class="track-meta">
                        <div class="track-title">{track['title']}</div>
                        <div class="track-artist">{track['artist']} &nbsp;|&nbsp; {track['album']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_play, col_queue, col_duration = st.columns([0.15, 0.15, 0.70])
                if col_play.button("▶️ Play Now", key=f"play_{track['video_id']}_{idx}"):
                    play_track(track)
                    st.rerun()
                if col_queue.button("➕ Add to Queue", key=f"queue_{track['video_id']}_{idx}"):
                    add_to_queue(track)
                    st.rerun()

with col_player:
    # Active Playing Widget (Right Panel / "Right Tab")
    if st.session_state.current_track:
        track = st.session_state.current_track
        st.markdown("<div style='background-color:#181818; border:1px solid #282828; border-radius:12px; padding:20px; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<p style='color:#1db954; font-size:0.85rem; font-weight:800; margin-bottom:15px;'>NOW PLAYING</p>", unsafe_allow_html=True)
        
        st.image(track["thumbnail"], use_container_width=True)
        st.markdown(f"<h3 style='margin: 12px 0 2px 0; color:#ffffff; font-size:1.2rem;'>{track['title']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#b3b3b3; font-size:0.9rem; margin-bottom:20px;'>{track['artist']}</p>", unsafe_allow_html=True)
        
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
            
        st.markdown("<hr style='border-color:#282828; margin: 15px 0;'/>", unsafe_allow_html=True)
        
        # Collapsed Video Player
        if st.session_state.is_playing:
            with st.expander("📺 View Video Stream", expanded=False):
                st.video(f"https://www.youtube.com/watch?v={track['video_id']}", autoplay=True)
        else:
            st.info("Playback Paused.")
            
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
        <div style="background-color:#181818; border: 1px dashed #535353; border-radius:12px; padding:35px; text-align:center; color:#b3b3b3; height: 100%;">
            <h4 style="margin:0; color:#535353;">🎵 No Song Playing</h4>
            <p style="margin:5px 0 0 0; font-size:0.85rem;">Select a track to start streaming!</p>
        </div>
        """, unsafe_allow_html=True)
