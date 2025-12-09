import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  CloudUpload, 
  Search, 
  Gear, 
  ArrowCounterclockwise, 
  PlayFill, 
  Sliders, 
  XLg,
  CheckCircleFill,
  ExclamationCircleFill
} from 'react-bootstrap-icons';
import './App.css';

const API_URL = "http://127.0.0.1:8000";

function App() {
  // --- STATE MANAGEMENT ---
  const [status, setStatus] = useState("startup"); 
  const [progress, setProgress] = useState(0);
  const [filename, setFilename] = useState("");
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [videoBlobUrl, setVideoBlobUrl] = useState(null);

  // UI State
  const [showAdvancedUpload, setShowAdvancedUpload] = useState(false);
  const [showSearchFilters, setShowSearchFilters] = useState(false);

  // Data State
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  
  // Settings
  const [frameInterval, setFrameInterval] = useState(1.0);
  const [visualWeight, setVisualWeight] = useState(1.0);
  const [textWeight, setTextWeight] = useState(1.0);

  const videoRef = useRef(null);

  // --- POLLING & INIT ---
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get(`${API_URL}/status`, { timeout: 2000 });
        setIsBackendOnline(true);
        if (res.data.status !== status) setStatus(res.data.status);
        if (res.data.progress !== progress) setProgress(res.data.progress);
        if (res.data.filename) setFilename(res.data.filename);
      } catch (err) {
        setIsBackendOnline(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 1000); 
    return () => clearInterval(interval);
  }, [status, progress]);

  // --- HANDLERS ---
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !isBackendOnline) return;

    const localUrl = URL.createObjectURL(file);
    setVideoBlobUrl(localUrl);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("frame_interval", frameInterval);

    try {
      setStatus("uploading");
      await axios.post(`${API_URL}/upload`, formData);
      setStatus("processing");
    } catch (err) {
      alert("Upload failed");
      setStatus("no_index");
    }
  };

  const handleHardReset = async () => {
    try {
      await axios.post(`${API_URL}/reset`);
      setStatus("no_index");
      setFilename("");
      setProgress(0);
      setResults([]);
      setVideoBlobUrl(null);
      setQuery("");
    } catch (err) { alert("Reset failed"); }
  };

  const handleSearch = async () => {
    if (!query) return;
    try {
      const res = await axios.get(`${API_URL}/search`, {
        params: { q: query, visual_weight: visualWeight, text_weight: textWeight }
      });
      setResults(res.data);
    } catch (err) { console.error(err); }
  };

  const jumpToTimestamp = (seconds) => {
    if (videoRef.current) {
      if (videoRef.current.readyState === 0) {
        alert("Video is not loaded. Please upload the file again.");
        return;
      }
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(e => console.error(e));
      
      // Smooth scroll to video if needed, but in this layout video is always visible
    }
  };

  // --- RENDERERS ---

  const renderHeader = () => (
    <header className="header">
      <div className="brand">
        <PlayFill className="brand-logo" size={24} />
        <span>DeepSearch</span>
      </div>
      <div className={`status-badge ${isBackendOnline ? 'online' : 'offline'}`}>
        <div className="status-dot"></div>
        {isBackendOnline ? "System Ready" : "Backend Offline"}
      </div>
    </header>
  );

  const renderUploadView = () => (
    <div className="hero-view">
      <label className={`upload-card ${!isBackendOnline ? 'disabled' : ''}`}>
        <input 
          type="file" hidden onChange={handleUpload} accept="video/*" 
          disabled={!isBackendOnline} 
        />
        <CloudUpload size={48} className="upload-icon" />
        <div className="hero-title">
          {isBackendOnline ? "Upload Video" : "Connection Lost"}
        </div>
        <div className="hero-subtitle">
          {isBackendOnline ? "MP4, MOV supported • Max 1080p" : "Please start the Python API"}
        </div>
      </label>

      <button 
        className="settings-trigger" 
        onClick={() => setShowAdvancedUpload(!showAdvancedUpload)}
      >
        <Gear size={14} /> Configure Indexing
      </button>

      {showAdvancedUpload && (
        <div className="settings-panel">
          <div className="slider-group">
            <label>
              <span>Frame Sampling Interval</span>
              <span>{frameInterval}s</span>
            </label>
            <input 
              type="range" min="0.5" max="5.0" step="0.5" 
              value={frameInterval} 
              onChange={(e) => setFrameInterval(e.target.value)} 
            />
          </div>
        </div>
      )}
    </div>
  );
  
  const renderLoadingView = () => (
    <div className="hero-view">
      <div className="loading-view-wrapper">
        <div className="loading-grid">
          
          {/* LEFT SIDE: The Serious Progress Bar */}
          <div className="loading-left">
            <div className="hero-title">Indexing {filename}</div>
            <div className="hero-subtitle">
              {status === "uploading" ? "Uploading to server..." : "Extracting multimodal features..."}
            </div>
            
            <div className="progress-track">
              <div className="progress-bar" style={{width: `${progress}%`}}></div>
            </div>
            
            <div style={{fontSize: '0.9rem', color: '#888', marginBottom: '20px', display: 'flex', justifyContent: 'space-between'}}>
              <span>Status: {status === "processing" ? "Analyzing" : "Waiting"}</span>
              <span>{progress}%</span>
            </div>

            <button className="cancel-btn" onClick={handleHardReset}>
              Cancel Operation
            </button>
          </div>

          {/* RIGHT SIDE: Keyboard Cat */}
          <div className="loading-right">
            <div>
                <div className="meme-card">
                  <iframe 
                    width="100%" 
                    height="100%" 
                    src="https://www.youtube.com/embed/3Ee0xokxshY?autoplay=1&mute=1&controls=1&loop=1&playlist=3Ee0xokxshY" 
                    title="Loading Meme" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowFullScreen
                  ></iframe>
                </div>
                <div className="meme-caption">
                    "Play him off, Keyboard Cat" (While you wait)
                </div>
            </div>
          </div>

        </div>
      </div>
    </div>
);

  const renderWorkspace = () => (
    <>
      <div className="workspace">
        {/* Left: Cinema Stage */}
        <div className="video-stage">
          {videoBlobUrl ? (
            <video ref={videoRef} controls src={videoBlobUrl} />
          ) : (
            <div style={{color: '#444', textAlign: 'center'}}>
              <ExclamationCircleFill size={32} style={{marginBottom: '10px'}}/>
              <div>Session Restored</div>
              <div style={{fontSize: '0.8rem', marginTop: '5px'}}>Re-upload video to view</div>
            </div>
          )}
        </div>

        {/* Right: Results Stream */}
        <div className="results-sidebar">
          <div className="results-header">Search Results</div>
          
          {results.length === 0 && (
            <div style={{padding: '40px 20px', textAlign: 'center', color: '#444'}}>
              <Search size={24} style={{marginBottom: '10px', opacity: 0.5}}/>
              <p style={{fontSize: '0.9rem'}}>Enter a query below to find scenes.</p>
            </div>
          )}

          {results.map((res, idx) => (
            <div key={idx} className="result-item" onClick={() => jumpToTimestamp(res.timestamp)}>
              <img src={`${API_URL}/${res.preview_path}`} className="result-thumb" alt="scene" />
              <div className="result-meta">
                <span className="result-time">
                  {new Date(res.timestamp * 1000).toISOString().substr(11, 8)}
                </span>
                <span className="result-text">"{res.transcript_snippet}"</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Floating Command Bar */}
      <div className="command-bar-container">
        {showSearchFilters && (
          <div className="weights-popover">
            <div className="popover-header">Search Priority</div>
            <div className="slider-group">
              <label><span>Visual Match</span><span>{visualWeight}x</span></label>
              <input type="range" min="0" max="3" step="0.1" value={visualWeight} onChange={e => setVisualWeight(e.target.value)} />
            </div>
            <div className="slider-group" style={{marginTop: '16px'}}>
              <label><span>Text Match</span><span>{textWeight}x</span></label>
              <input type="range" min="0" max="3" step="0.1" value={textWeight} onChange={e => setTextWeight(e.target.value)} />
            </div>
          </div>
        )}

        <div className="command-bar">
          <Search className="search-icon" size={18} />
          <input 
            className="command-input"
            placeholder="Search for a scene..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            autoFocus
          />
          
          <button 
            className={`action-btn ${showSearchFilters ? 'active' : ''}`}
            onClick={() => setShowSearchFilters(!showSearchFilters)}
            title="Adjust Filters"
          >
            <Sliders size={16} />
          </button>
          
          <button 
            className="action-btn"
            onClick={handleHardReset}
            title="New Upload / Reset"
          >
            <ArrowCounterclockwise size={16} />
          </button>
        </div>
      </div>
    </>
  );

  // --- MAIN RENDER ---
  return (
    <div className="app-container">
      {renderHeader()}
      
      {(status === "startup" || status === "no_index") && renderUploadView()}
      {(status === "uploading" || status === "processing") && renderLoadingView()}
      {(status === "completed" || status === "failed") && renderWorkspace()}
    </div>
  );
}

export default App;