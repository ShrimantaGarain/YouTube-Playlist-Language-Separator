# 🎵 YouTube Playlist Language Separator

**Automatically detect the language of every song in any YouTube playlist** — specially built for **Indian/Desi music** (Bollywood, DHH, Punjabi, Tamil, Telugu, and 12+ regional languages).

Tired of mixed-language playlists? This tool fetches your entire playlist using the YouTube API and uses a **local LLM (Ollama)** to intelligently classify each track as **Hindi, Punjabi, English, Tamil, Telugu**, etc., with smart artist/channel priority rules.

---

## ✨ Features

- Full YouTube playlist fetching (handles 1000+ videos)
- Intelligent language detection using **local Ollama** (no API costs)
- Strongest priority on **Channel/Artist** (T-Series → Hindi, Speed Records → Punjabi, etc.)
- Smart English-title traps (e.g., "Baby Doll", "No Cap", "Shape of You" still detected correctly)
- Multi-threaded processing (6–12 workers)
- Automatic post-processing overrides for common mistakes
- Exports to **Excel** (with fallback to CSV)
- Clean summary + top 15 preview

---

## 🚀 Quick Start

1. Clone the repo
```bash
git clone https://github.com/yourusername/youtube-playlist-language-separator.git
cd youtube-playlist-language-separator
2. Install dependencies
Bashpip install pandas tqdm google-api-python-client google-auth-oauthlib google-auth ollama openpyxl
3. Setup Ollama
Bash# Install Ollama from https://ollama.com
ollama pull llama3.1:8b        # Recommended (fast & accurate)
# Alternatives: llama3.2:3b (super fast), qwen2.5:7b, gemma2:9b
4. YouTube API Setup

Go to Google Cloud Console
Create a project → Enable YouTube Data API v3
Create OAuth 2.0 Client ID (Desktop app)
Download client_secrets.json and place it in the project folder


💻 Usage
Bashpython youtube_playlist_language_classifier.py
Just paste any YouTube playlist URL or ID when prompted.
Example:
textEnter YouTube playlist URL or ID: https://www.youtube.com/playlist?list=PL1234567890

📁 Output

playlist_songs.xlsx → Full table with columns:
Video_ID, Title, Channel, URL, Detected_Language

Beautiful console summary showing English vs Non-English count + full language breakdown


⚙️ Configuration (top of the script)
PythonMODEL_NAME = "llama3.1:8b"      # Change model here
MAX_WORKERS = 6                 # Increase if you have strong CPU/GPU
BATCH_SLEEP = 0.3               # Reduce for faster run (0.1–0.2)
You can easily add more override keywords in the override() function.

🧠 Why This Works So Well

Channel is given highest priority (most reliable signal)
Special handling for English-titled Desi songs (very common in Bollywood/DHH)
Romanized Hindi/Punjabi clue detection
Manual overrides for known tricky channels (Seedhe Maut, Sidhu Moose Wala, etc.)


📸 Example Output
text✅ Fetched 248 songs.

Top 15 rows:
Title                          Channel               Detected_Language
...                            T-Series              Hindi
...                            Speed Records         Punjabi
...                            Aditya Music          Telugu
...

🇬🇧 English: 12 | 🌍 Non-English: 236

=== LANGUAGE SUMMARY ===
Hindi       142
Punjabi      68
Telugu       19
Tamil        11
English      12
Other         8

🔧 Tech Stack

Python 3
YouTube Data API v3
Ollama (local LLM)
pandas + openpyxl
ThreadPoolExecutor + tqdm


⭐ Contributing
Feel free to:

Add new language overrides
Support more regional languages
Add automatic playlist splitting feature
Switch to Grok / OpenRouter / Gemini API

Pull requests are welcome!

📄 License
MIT License — feel free to use, modify, and share.

Made with ❤️ for the Desi music community
Star the repo if it helped you organize your playlists! 🌟
text---

**How to use it:**
1. Create a new GitHub repo (suggested name: `youtube-playlist-language-separator` or `desi-playlist-language-detector`)
2. Add the script as `youtube_playlist_language_classifier.py`
3. Paste the above content into `README.md`
4. Commit & push

