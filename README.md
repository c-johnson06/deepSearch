# DeepSearch | Multimodal Video Intelligence Engine

**DeepSearch** is a local, privacy-focused semantic search engine for video archives. Unlike traditional keyword search (which relies on filenames or manual tags), DeepSearch uses **Multimodal AI (CLIP + Whisper)** to index the actual visual and auditory content of a video.

Users can query their footage using natural language (e.g., *"Red car driving in the rain"* or *"Discussion about climate change"*) and instantly jump to the exact timestamp where that event occurs.

---

## 🚀 Key Features

* **Semantic Video Search:** Find scenes based on visual description, not just metadata.
* **Hybrid Search Fusion:** Adjustable sliders allow users to weight **Visual matches** vs. **Audio/Transcript matches** in real-time.
* **Local Processing:** Runs entirely on-premise (no API keys required). Utilizes local GPU acceleration (CUDA) for <100ms inference.
* **Smart Indexing Pipeline:**
    * **Vision:** OpenAI CLIP (ViT-B/32) extracts embeddings from keyframes.
    * **Audio:** OpenAI Whisper generates timestamps and transcripts.
    * **Storage:** `pgvector` (PostgreSQL) stores high-dimensional vectors for cosine similarity search.
* **Command Center UI:** A modern, dark-mode React interface with real-time indexing progress, "Meme Mode" loading states, and an embedded video player.

---

## 🛠️ Tech Stack

* **Frontend:** React 18, Axios, CSS Modules (Vercel-style aesthetics).
* **Backend:** Python 3.11, FastAPI, Uvicorn.
* **AI Models:** PyTorch, OpenAI CLIP, OpenAI Whisper, Sentence-Transformers.
* **Database:** PostgreSQL with `pgvector` extension (running via Docker).
* **Infrastructure:** FFmpeg (media processing), Docker Compose.

---

## ⚙️ Prerequisites

Before running the project, ensure you have the following installed:

1. **Docker Desktop** (Required for the Vector Database).
2. **Python 3.10+**.
3. **Node.js & npm** (For the frontend).
4. **FFmpeg** (Must be added to your System PATH).
    * *Windows:* `winget install Gyan.FFmpeg`
5. **NVIDIA GPU** (Recommended, but works on CPU with slower indexing).

---

## 📥 Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/deepsearch.git](https://github.com/yourusername/deepsearch.git)
cd deepsearch
```

### 2. Start the Database
Spin up the PostgreSQL container with vector support.
```bash
docker-compose up -d
```

### 3. Setup backend environment
Windows
```bash
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies (GPU version recommended)
```bash
pip install torch torchvision --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)
pip install fastapi "uvicorn[standard]" python-multipart opencv-python "psycopg[binary]" sentence-transformers transformers openai-whisper
```

### 4. Setup frontend environment
```bash
cd frontend
npm install
```
## Usage

### 1. Start backend server
```bash
python api/main.py
```
### 2. Start frontend server
```bash
cd frontend
npm start
```

### 3. Open the app in your browser
Open http://localhost:3000 in your browser to use the app.

### 4. Upload a video
Click on the upload video button and adjust frame rate sampling rate as needed.

### 5. Search the video
Enter any query and click search to generate timestamps of the query in the video.
Adjust the weight of text and visual similarity as needed.