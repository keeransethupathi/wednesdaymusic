/**
 * Wednesday Songs - Modern Web Music Player Application
 * Connects directly to Vercel Serverless API (/api/*)
 */

// Application State
const state = {
  currentTrack: null,
  isPlaying: false,
  queue: [],
  history: [],
  isShuffle: false,
  isRepeat: false,
  activeTab: "tamil",
  currentView: "home",
  activeLyricsTrackId: null
};

// DOM Element Selectors
const elements = {
  audio: document.getElementById("audio-engine"),
  greetingTitle: document.getElementById("greeting-title"),
  
  // Search & Navigation
  searchInput: document.getElementById("search-input"),
  searchBtn: document.getElementById("search-btn"),
  navHome: document.getElementById("nav-home"),
  navSearchResults: document.getElementById("nav-search-results"),
  viewHome: document.getElementById("view-home"),
  viewSearch: document.getElementById("view-search"),
  searchTitle: document.getElementById("search-title"),
  searchCountLabel: document.getElementById("search-count-label"),
  searchResultsList: document.getElementById("search-results-list"),
  
  // Trending Tabs & Grid
  genreTabs: document.getElementById("genre-tabs"),
  trendingGrid: document.getElementById("trending-grid"),
  btnQuickPlayFeatured: document.getElementById("btn-quick-play-featured"),
  
  // Right Now Playing Spotlight
  spotlightEmpty: document.getElementById("spotlight-empty"),
  spotlightActive: document.getElementById("spotlight-active"),
  spotlightArt: document.getElementById("spotlight-art"),
  spotlightTitle: document.getElementById("spotlight-title"),
  spotlightArtist: document.getElementById("spotlight-artist"),
  spotlightAlbum: document.getElementById("spotlight-album"),
  spotlightLyricsSnippet: document.getElementById("spotlight-lyrics-snippet"),
  btnOpenFullLyrics: document.getElementById("btn-open-full-lyrics"),
  sideLiveEq: document.getElementById("side-live-eq"),
  pulseDisc: document.getElementById("pulse-disc"),
  
  // Bottom Player Dock
  dockThumb: document.getElementById("dock-thumb"),
  dockTitle: document.getElementById("dock-title"),
  dockArtist: document.getElementById("dock-artist"),
  btnPlayPause: document.getElementById("btn-play-pause"),
  iconPlay: document.getElementById("icon-play"),
  iconPause: document.getElementById("icon-pause"),
  btnPrev: document.getElementById("btn-prev"),
  btnNext: document.getElementById("btn-next"),
  btnShuffle: document.getElementById("btn-shuffle"),
  btnRepeat: document.getElementById("btn-repeat"),
  
  // Progress Bar
  currentTimeLabel: document.getElementById("current-time"),
  totalTimeLabel: document.getElementById("total-time"),
  seekTrack: document.getElementById("seek-track"),
  seekFill: document.getElementById("seek-fill"),
  seekHandle: document.getElementById("seek-handle"),
  
  // Volume Controls
  volumeSlider: document.getElementById("volume-slider"),
  btnVolumeIcon: document.getElementById("btn-volume-icon"),
  iconVolHigh: document.getElementById("icon-vol-high"),
  iconVolMute: document.getElementById("icon-vol-mute"),
  
  // Queue & Lyrics Buttons
  btnToggleQueue: document.getElementById("btn-toggle-queue"),
  btnDockQueue: document.getElementById("btn-dock-queue"),
  btnToggleLyrics: document.getElementById("btn-toggle-lyrics"),
  btnDockLyrics: document.getElementById("btn-dock-lyrics"),
  topQueueBadge: document.getElementById("top-queue-badge"),
  sidebarQueueCount: document.getElementById("sidebar-queue-count"),
  sidebarQueueList: document.getElementById("sidebar-queue-list"),
  sidebarClearQueue: document.getElementById("sidebar-clear-queue"),
  
  // Modals
  lyricsModal: document.getElementById("lyrics-modal"),
  btnCloseLyrics: document.getElementById("btn-close-lyrics"),
  lyricsBody: document.getElementById("lyrics-body"),
  lyricsModalTitle: document.getElementById("lyrics-modal-title"),
  lyricsModalSubtitle: document.getElementById("lyrics-modal-subtitle"),
  
  queueModal: document.getElementById("queue-modal"),
  btnCloseQueue: document.getElementById("btn-close-queue"),
  modalQueueList: document.getElementById("modal-queue-list"),
  queueModalCount: document.getElementById("queue-modal-count"),
  btnClearModalQueue: document.getElementById("btn-clear-modal-queue"),
  
  // Toast Container
  toastContainer: document.getElementById("toast-container")
};

// Fallback high-contrast SVG thumbnail
const FALLBACK_THUMB = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150' viewBox='0 0 150 150'><rect width='150' height='150' rx='8' fill='%23111827'/><text x='50%' y='50%' font-size='42' dominant-baseline='middle' text-anchor='middle' fill='%2300d2c4'>🎵</text></svg>";

/* ==========================================================================
   Initialization
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  updateTimeGreeting();
  setupEventListeners();
  setupAudioListeners();
  loadTrendingTracks("tamil");
});

function updateTimeGreeting() {
  const hour = new Date().getHours();
  let greeting = "Good Evening";
  if (hour < 12) greeting = "Good Morning";
  else if (hour < 17) greeting = "Good Afternoon";
  if (elements.greetingTitle) elements.greetingTitle.textContent = greeting;
}

/* ==========================================================================
   Catalog & API Operations
   ========================================================================== */

async function loadTrendingTracks(tab) {
  state.activeTab = tab;
  renderSkeletonCards(8);

  try {
    const res = await fetch(`/api/trending?tab=${tab}&limit=12`);
    if (!res.ok) throw new Error("Catalog service error");
    const data = await res.json();
    renderTrackGrid(data.results || []);
  } catch (err) {
    console.error("Error loading trending:", err);
    elements.trendingGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #9ca3af;">
        <p>⚠️ Unable to reach Wednesday Songs catalog. Please check your internet connection.</p>
        <button class="primary-btn" style="margin-top: 12px;" onclick="loadTrendingTracks('${tab}')">Try Again</button>
      </div>
    `;
  }
}

async function performSearch(query) {
  if (!query || !query.trim()) return;
  const q = query.trim();

  switchView("search");
  elements.searchTitle.textContent = `Results for "${q}"`;
  elements.searchCountLabel.textContent = "Searching catalog...";
  elements.searchResultsList.innerHTML = `
    <div class="spinner-container">
      <div class="spinner"></div>
      <p>Searching Wednesday Songs catalog...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=25`);
    if (!res.ok) throw new Error("Search service error");
    const data = await res.json();
    const results = data.results || [];
    renderSearchResults(results, q);
  } catch (err) {
    console.error("Search error:", err);
    elements.searchResultsList.innerHTML = `
      <div style="text-align: center; padding: 40px; color: #9ca3af;">
        <p>⚠️ Could not complete search query. Try another keyword or retry.</p>
      </div>
    `;
  }
}

async function fetchLyrics(track) {
  if (!track || !track.track_id) return;
  state.activeLyricsTrackId = track.track_id;
  
  elements.spotlightLyricsSnippet.textContent = "Fetching lyrics...";
  elements.lyricsBody.innerHTML = `
    <div class="spinner-container">
      <div class="spinner"></div>
      <p>Loading lyrics for "${escapeHtml(track.title)}"...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/lyrics?track_id=${encodeURIComponent(track.track_id)}`);
    const data = await res.json();
    const lyrics = data.lyrics || "Lyrics not available for this song.";
    
    // Update snippet
    elements.spotlightLyricsSnippet.textContent = lyrics;
    // Update modal
    elements.lyricsBody.textContent = lyrics;
  } catch (err) {
    console.warn("Lyrics fetch error:", err);
    elements.spotlightLyricsSnippet.textContent = "Lyrics not available.";
    elements.lyricsBody.textContent = "Lyrics could not be loaded.";
  }
}

/* ==========================================================================
   Audio Engine & Playback Helpers
   ========================================================================== */

function playTrack(track, forceProxy = false) {
  if (!track) return;

  // Add previous track to history
  if (state.currentTrack && state.currentTrack.track_id !== track.track_id) {
    state.history.push(state.currentTrack);
    if (state.history.length > 50) state.history.shift();
  }

  state.currentTrack = track;
  updateUIOnTrackChange(track);

  let streamUrl = track.stream_url;
  // If no stream URL or proxy forced, stream through backend proxy
  if (!streamUrl || forceProxy) {
    streamUrl = `/api/proxy-audio?url=${encodeURIComponent(track.stream_url || "")}`;
  }

  elements.audio.src = streamUrl;
  elements.audio.play()
    .then(() => {
      state.isPlaying = true;
      updatePlayPauseButton();
    })
    .catch((err) => {
      console.warn("Direct stream blocked, falling back to serverless proxy...", err);
      if (!forceProxy && track.stream_url) {
        // Automatically fallback to proxy if direct fails (CORS, Fortinet, etc.)
        playTrack(track, true);
      } else {
        showToast("Error starting playback for this track.");
      }
    });

  // Fetch lyrics
  fetchLyrics(track);
}

function togglePlayPause() {
  if (!state.currentTrack) {
    // If no song playing, play the first track from trending
    const firstCard = document.querySelector(".track-card");
    if (firstCard && firstCard._trackData) {
      playTrack(firstCard._trackData);
    }
    return;
  }

  if (state.isPlaying) {
    elements.audio.pause();
    state.isPlaying = false;
  } else {
    elements.audio.play()
      .then(() => {
        state.isPlaying = true;
      })
      .catch((err) => console.error("Playback error:", err));
  }
  updatePlayPauseButton();
}

function playNextTrack() {
  if (state.isRepeat && state.currentTrack) {
    elements.audio.currentTime = 0;
    elements.audio.play();
    return;
  }

  if (state.queue.length > 0) {
    let nextTrack;
    if (state.isShuffle) {
      const randIdx = Math.floor(Math.random() * state.queue.length);
      nextTrack = state.queue.splice(randIdx, 1)[0];
    } else {
      nextTrack = state.queue.shift();
    }
    updateQueueUI();
    playTrack(nextTrack);
    showToast(`Playing: ${nextTrack.title}`);
  } else {
    showToast("Queue is empty. Select a new track!");
  }
}

function playPreviousTrack() {
  if (elements.audio.currentTime > 4) {
    // Restart song if played more than 4 seconds
    elements.audio.currentTime = 0;
    return;
  }

  if (state.history.length > 0) {
    const prevTrack = state.history.pop();
    playTrack(prevTrack);
  } else {
    showToast("No previous tracks in history.");
  }
}

function addToQueue(track) {
  state.queue.push(track);
  updateQueueUI();
  showToast(`Added to Queue: ${track.title}`);
}

function clearQueue() {
  state.queue = [];
  updateQueueUI();
  showToast("Queue cleared");
}

/* ==========================================================================
   UI Rendering & Updates
   ========================================================================== */

function updatePlayPauseButton() {
  if (state.isPlaying) {
    elements.iconPlay.style.display = "none";
    elements.iconPause.style.display = "block";
    document.body.classList.add("is-playing");
  } else {
    elements.iconPlay.style.display = "block";
    elements.iconPause.style.display = "none";
    document.body.classList.remove("is-playing");
  }
}

function updateUIOnTrackChange(track) {
  const thumbUrl = track.thumbnail || FALLBACK_THUMB;

  // Dock Bottom Player
  elements.dockThumb.src = thumbUrl;
  elements.dockTitle.textContent = track.title || "Unknown Title";
  elements.dockArtist.textContent = track.artist || "Unknown Artist";
  elements.totalTimeLabel.textContent = track.duration || "0:00";

  // Right Spotlight Panel
  elements.spotlightEmpty.style.display = "none";
  elements.spotlightActive.style.display = "flex";
  elements.spotlightArt.src = thumbUrl;
  elements.spotlightTitle.textContent = track.title;
  elements.spotlightArtist.textContent = track.artist;
  elements.spotlightAlbum.textContent = track.album || "Single";
  
  // Modal Lyrics Title
  elements.lyricsModalTitle.textContent = track.title;
  elements.lyricsModalSubtitle.textContent = track.artist;
}

function updateQueueUI() {
  const count = state.queue.length;
  elements.topQueueBadge.textContent = count;
  elements.sidebarQueueCount.textContent = count;
  elements.queueModalCount.textContent = `${count} songs up next`;

  // Sidebar Queue
  if (count === 0) {
    elements.sidebarQueueList.innerHTML = `<p class="empty-hint">Queue is empty</p>`;
    elements.sidebarClearQueue.style.display = "none";
  } else {
    elements.sidebarClearQueue.style.display = "block";
    elements.sidebarQueueList.innerHTML = state.queue.slice(0, 4).map((t, idx) => `
      <div class="sidebar-queue-item">
        <span style="color: var(--accent); font-weight: 700; width: 14px;">${idx + 1}</span>
        <div class="sidebar-queue-meta">
          <div class="sidebar-queue-song">${escapeHtml(t.title)}</div>
          <div class="sidebar-queue-artist">${escapeHtml(t.artist)}</div>
        </div>
      </div>
    `).join("");

    if (count > 4) {
      elements.sidebarQueueList.innerHTML += `
        <div style="font-size: 11px; color: var(--text-muted); text-align: center; padding-top: 4px;">
          + ${count - 4} more tracks
        </div>
      `;
    }
  }

  // Modal Queue
  if (count === 0) {
    elements.modalQueueList.innerHTML = `<p class="empty-hint">Queue is currently empty. Add tracks to play next!</p>`;
  } else {
    elements.modalQueueList.innerHTML = state.queue.map((t, idx) => `
      <div class="queue-modal-item">
        <span style="color: var(--accent); font-weight: 700; width: 20px;">${idx + 1}</span>
        <img class="queue-modal-art" src="${t.thumbnail || FALLBACK_THUMB}" alt="Thumb" onerror="this.src='${FALLBACK_THUMB}'">
        <div class="queue-modal-meta">
          <div class="queue-modal-title">${escapeHtml(t.title)}</div>
          <div class="queue-modal-artist">${escapeHtml(t.artist)}</div>
        </div>
        <button class="queue-remove-btn" title="Remove" onclick="removeFromQueue(${idx})">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
    `).join("");
  }
}

window.removeFromQueue = function(idx) {
  state.queue.splice(idx, 1);
  updateQueueUI();
};

function renderTrackGrid(tracks) {
  if (!tracks || tracks.length === 0) {
    elements.trendingGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #9ca3af;">
        No tracks found for this category.
      </div>
    `;
    return;
  }

  elements.trendingGrid.innerHTML = "";
  tracks.forEach((track) => {
    const card = document.createElement("div");
    card.className = "track-card";
    card._trackData = track;

    card.innerHTML = `
      <div class="card-img-wrap">
        <img src="${track.thumbnail || FALLBACK_THUMB}" alt="${escapeHtml(track.title)}" loading="lazy" onerror="this.src='${FALLBACK_THUMB}'">
        <button class="card-overlay-btn" title="Play">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        </button>
      </div>
      <div class="card-title" title="${escapeHtml(track.title)}">${escapeHtml(track.title)}</div>
      <div class="card-artist" title="${escapeHtml(track.artist)}">${escapeHtml(track.artist)}</div>
      <div class="card-actions">
        <span class="card-duration">${track.duration || "3:00"}</span>
        <button class="card-queue-btn" title="Add to Queue">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
    `;

    // Click on card or overlay play button -> play track
    card.addEventListener("click", (e) => {
      if (e.target.closest(".card-queue-btn")) {
        addToQueue(track);
        return;
      }
      playTrack(track);
    });

    elements.trendingGrid.appendChild(card);
  });
}

function renderSearchResults(tracks, query) {
  elements.searchCountLabel.textContent = `Found ${tracks.length} tracks`;

  if (tracks.length === 0) {
    elements.searchResultsList.innerHTML = `
      <div style="text-align: center; padding: 40px; color: #9ca3af;">
        <p>No tracks found matching "${escapeHtml(query)}". Try another search term!</p>
      </div>
    `;
    return;
  }

  elements.searchResultsList.innerHTML = "";
  tracks.forEach((track) => {
    const row = document.createElement("div");
    row.className = "track-row";
    row.innerHTML = `
      <img class="track-row-art" src="${track.thumbnail || FALLBACK_THUMB}" alt="Thumb" onerror="this.src='${FALLBACK_THUMB}'">
      <div class="track-row-meta">
        <div class="track-row-title">${escapeHtml(track.title)}</div>
        <div class="track-row-artist">${escapeHtml(track.artist)}</div>
      </div>
      <div class="track-row-album">${escapeHtml(track.album || "Single")}</div>
      <div class="track-row-duration">${track.duration || "3:00"}</div>
      <div class="track-row-actions">
        <button class="row-action-btn play-now">Play</button>
        <button class="row-action-btn add-queue">+ Queue</button>
      </div>
    `;

    row.querySelector(".play-now").addEventListener("click", (e) => {
      e.stopPropagation();
      playTrack(track);
    });

    row.querySelector(".add-queue").addEventListener("click", (e) => {
      e.stopPropagation();
      addToQueue(track);
    });

    row.addEventListener("click", () => playTrack(track));
    elements.searchResultsList.appendChild(row);
  });
}

function renderSkeletonCards(count = 6) {
  let html = `<div class="skeleton-loader">`;
  for (let i = 0; i < count; i++) {
    html += `<div class="skeleton-card"></div>`;
  }
  html += `</div>`;
  elements.trendingGrid.innerHTML = html;
}

function switchView(viewName) {
  state.currentView = viewName;
  if (viewName === "home") {
    elements.viewHome.classList.add("active");
    elements.viewSearch.classList.remove("active");
    elements.navHome.classList.add("active");
    elements.navSearchResults.classList.remove("active");
  } else {
    elements.viewHome.classList.remove("active");
    elements.viewSearch.classList.add("active");
    elements.navHome.classList.remove("active");
    elements.navSearchResults.classList.add("active");
  }
}

/* ==========================================================================
   Event Handlers & Interactivity
   ========================================================================== */

function setupAudioListeners() {
  const { audio } = elements;

  audio.addEventListener("timeupdate", () => {
    if (!audio.duration || isNaN(audio.duration)) return;
    const progress = (audio.currentTime / audio.duration) * 100;
    elements.seekFill.style.width = `${progress}%`;
    elements.seekHandle.style.left = `${progress}%`;
    elements.currentTimeLabel.textContent = formatTime(audio.currentTime);
  });

  audio.addEventListener("loadedmetadata", () => {
    elements.totalTimeLabel.textContent = formatTime(audio.duration);
  });

  audio.addEventListener("ended", () => {
    playNextTrack();
  });

  audio.addEventListener("play", () => {
    state.isPlaying = true;
    updatePlayPauseButton();
  });

  audio.addEventListener("pause", () => {
    state.isPlaying = false;
    updatePlayPauseButton();
  });
}

function setupEventListeners() {
  // Navigation
  elements.navHome.addEventListener("click", () => switchView("home"));
  elements.navSearchResults.addEventListener("click", () => switchView("search"));

  // Search input
  elements.searchBtn.addEventListener("click", () => performSearch(elements.searchInput.value));
  elements.searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") performSearch(elements.searchInput.value);
  });

  // Trending tabs
  elements.genreTabs.addEventListener("click", (e) => {
    const tabBtn = e.target.closest(".tab-btn");
    if (!tabBtn) return;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    tabBtn.classList.add("active");
    const tab = tabBtn.getAttribute("data-tab");
    loadTrendingTracks(tab);
  });

  // Quick Play Featured Banner button
  elements.btnQuickPlayFeatured.addEventListener("click", () => {
    const firstCard = document.querySelector(".track-card");
    if (firstCard && firstCard._trackData) {
      playTrack(firstCard._trackData);
    }
  });

  // Playback Controls
  elements.btnPlayPause.addEventListener("click", togglePlayPause);
  elements.btnNext.addEventListener("click", playNextTrack);
  elements.btnPrev.addEventListener("click", playPreviousTrack);

  // Shuffle & Repeat
  elements.btnShuffle.addEventListener("click", () => {
    state.isShuffle = !state.isShuffle;
    elements.btnShuffle.classList.toggle("active", state.isShuffle);
    showToast(state.isShuffle ? "Shuffle On" : "Shuffle Off");
  });

  elements.btnRepeat.addEventListener("click", () => {
    state.isRepeat = !state.isRepeat;
    elements.btnRepeat.classList.toggle("active", state.isRepeat);
    showToast(state.isRepeat ? "Repeat On" : "Repeat Off");
  });

  // Seek Bar Drag / Click
  elements.seekTrack.addEventListener("click", (e) => {
    if (!elements.audio.duration) return;
    const rect = elements.seekTrack.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    elements.audio.currentTime = pos * elements.audio.duration;
  });

  // Volume Controls
  elements.volumeSlider.addEventListener("input", (e) => {
    const vol = parseFloat(e.target.value);
    elements.audio.volume = vol;
    updateVolumeIcon(vol);
  });

  elements.btnVolumeIcon.addEventListener("click", () => {
    if (elements.audio.volume > 0) {
      elements.audio._lastVolume = elements.audio.volume;
      elements.audio.volume = 0;
      elements.volumeSlider.value = 0;
      updateVolumeIcon(0);
    } else {
      const restored = elements.audio._lastVolume || 0.8;
      elements.audio.volume = restored;
      elements.volumeSlider.value = restored;
      updateVolumeIcon(restored);
    }
  });

  // Modals (Lyrics & Queue)
  const openLyrics = () => {
    elements.lyricsModal.style.display = "flex";
    if (state.currentTrack && state.activeLyricsTrackId !== state.currentTrack.track_id) {
      fetchLyrics(state.currentTrack);
    }
  };
  const closeLyrics = () => { elements.lyricsModal.style.display = "none"; };

  const openQueue = () => { elements.queueModal.style.display = "flex"; };
  const closeQueue = () => { elements.queueModal.style.display = "none"; };

  elements.btnToggleLyrics.addEventListener("click", openLyrics);
  elements.btnDockLyrics.addEventListener("click", openLyrics);
  elements.btnOpenFullLyrics.addEventListener("click", openLyrics);
  elements.btnCloseLyrics.addEventListener("click", closeLyrics);

  elements.btnToggleQueue.addEventListener("click", openQueue);
  elements.btnDockQueue.addEventListener("click", openQueue);
  elements.btnCloseQueue.addEventListener("click", closeQueue);

  elements.sidebarClearQueue.addEventListener("click", clearQueue);
  elements.btnClearModalQueue.addEventListener("click", clearQueue);

  // Close modals on background click
  window.addEventListener("click", (e) => {
    if (e.target === elements.lyricsModal) closeLyrics();
    if (e.target === elements.queueModal) closeQueue();
  });

  // Keyboard Shortcuts
  window.addEventListener("keydown", (e) => {
    // Avoid triggering when user is typing in search input
    if (e.target === elements.searchInput) return;

    switch (e.key) {
      case " ":
        e.preventDefault();
        togglePlayPause();
        break;
      case "n":
      case "N":
        playNextTrack();
        break;
      case "p":
      case "P":
        playPreviousTrack();
        break;
      case "m":
      case "M":
        elements.btnVolumeIcon.click();
        break;
      case "l":
      case "L":
        elements.lyricsModal.style.display === "flex" ? closeLyrics() : openLyrics();
        break;
      case "q":
      case "Q":
        elements.queueModal.style.display === "flex" ? closeQueue() : openQueue();
        break;
      case "ArrowLeft":
        if (elements.audio.currentTime) {
          elements.audio.currentTime = Math.max(0, elements.audio.currentTime - 5);
        }
        break;
      case "ArrowRight":
        if (elements.audio.currentTime && elements.audio.duration) {
          elements.audio.currentTime = Math.min(elements.audio.duration, elements.audio.currentTime + 5);
        }
        break;
    }
  });
}

function updateVolumeIcon(vol) {
  if (vol === 0) {
    elements.iconVolHigh.style.display = "none";
    elements.iconVolMute.style.display = "block";
  } else {
    elements.iconVolHigh.style.display = "block";
    elements.iconVolMute.style.display = "none";
  }
}

/* ==========================================================================
   Utilities
   ========================================================================== */

function formatTime(seconds) {
  if (isNaN(seconds) || seconds < 0) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, function(m) {
    switch (m) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case "'": return '&#39;';
      default: return m;
    }
  });
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 2400);
}
