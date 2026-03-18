import os
import pickle
import time
import pandas as pd
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import ollama

# ========================== CONFIG ==========================
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Recommended models (pull with: ollama pull <name>)
# llama3.2:3b  → fastest
# llama3.1:8b  → best balance (default)
# qwen2.5:7b  → very accurate
MODEL_NAME = "llama3.1:8b"

MAX_WORKERS = 8          # 6–12 based on your CPU
BATCH_SLEEP = 0.2        # gentle delay (0.15–0.3)

# ========================== YOUTUBE SETUP ==========================
def get_youtube_service():
    creds = None
    token_file = 'token.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'wb') as f:
            pickle.dump(creds, f)
    return build('youtube', 'v3', credentials=creds)

def extract_playlist_id(url):
    if 'list=' in url:
        return parse_qs(urlparse(url).query)['list'][0]
    return url.strip()

def fetch_playlist(youtube, playlist_id):
    print("🔄 Fetching playlist...")
    videos = []
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        resp = request.execute()
        for item in resp.get('items', []):
            videos.append({
                'Video_ID': item['snippet']['resourceId']['videoId'],
                'Title': item['snippet']['title'],
                'Channel': item['snippet'].get('videoOwnerChannelTitle', 'Unknown'),
                'URL': f"https://youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
            })
        request = youtube.playlistItems().list_next(request, resp)
    return pd.DataFrame(videos)

# ========================== CLASSIFICATION ==========================
def classify_song(row, model_name):
    prompt = f"""You are a specialist in Indian/Desi music language detection across all genres: Bollywood, DHH, Punjabi, Tamil/Telugu, regional, etc.
Strict priority order:
1. CHANNEL / ARTIST is the strongest clue — trust it over title.
2. English/exotic titles DO NOT mean English (many Desi songs use English titles intentionally).
3. Use romanized clues and artist knowledge.
4. Ignore junk like "(Official Video)", "Lyrics", "4K", etc.
5. Mixed? Choose dominant language (Hindi default for Bollywood/DHH).

Answer ONLY with one of these (exactly one word):
English, Hindi, Punjabi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Bhojpuri, Urdu, Odia, Haryanvi, Other

Title: {row['Title']}
Channel: {row['Channel']}
"""

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.0, 'num_ctx': 8192}
        )
        lang = response['message']['content'].strip()
        lang_map = {'Hinglish': 'Hindi', 'Hindi English': 'Hindi', 'Eng': 'English', 'Mix': 'Hindi', 'Mixed': 'Hindi', '': 'Other'}
        return lang_map.get(lang, lang.title())
    except Exception as e:
        print(f"⚠️ Error on '{row['Title'][:60]}...': {e}")
        return "Other"

def classify_with_ollama(df, model_name=MODEL_NAME):
    print(f"🧠 Classifying {len(df)} songs with {model_name} ({MAX_WORKERS} workers)...")
   
    languages = [None] * len(df)
   
    def process(idx_row):
        idx, row = idx_row
        lang = classify_song(row, model_name)
        time.sleep(BATCH_SLEEP)
        return idx, lang

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process, (i, row)) for i, row in df.iterrows()]
        for future in tqdm(as_completed(futures), total=len(df), desc="Progress", unit="song"):
            try:
                idx, lang = future.result()
                languages[idx] = lang
            except Exception as e:
                print(f"Future error: {e}")

    df['Detected_Language'] = [l if l else "Other" for l in languages]

    # ===================== POST-PROCESSING OVERRIDES =====================
    def override(row):
        title_l = row['Title'].lower()
        ch_l = row['Channel'].lower()
        
        if any(kw in title_l for kw in ['baby doll', 'saturday', 'high heels', 'love you', 'party all night', 'shape of you', 'exotic', 'no cap', 'agency', 'hustle', 'ring ring', 'baby', 'monopoly', 'together forever']):
            if any(x in ch_l for x in ['t-series', 'zee', 'sony music', 'tips', 'yrf', 'seedhe maut', 'krsna', 'divine', 'raftaar', 'emiway']):
                return 'Hindi'
        
        if any(kw in title_l for kw in ['jatt', 'mundian', 'moose', 'bhangra', 'tell me', 'moor', 'rang kala', 'prada']):
            if any(x in ch_l for x in ['speed records', 'white hill', 'jass', 'moosewala']):
                return 'Punjabi'
        
        if 'seedhe maut' in ch_l or 'dhh' in ch_l:
            return 'Hindi'
        if 'speed records' in ch_l or 'punjabi' in ch_l:
            return 'Punjabi'
        
        return row['Detected_Language']

    df['Detected_Language'] = df.apply(override, axis=1)
    return df

# ========================== MAIN ==========================
if __name__ == "__main__":
    print("🎵 YouTube Playlist Language Separator (FINAL VERSION)\n")
    
    playlist_url = input("Enter YouTube playlist URL or ID: ").strip()
    playlist_id = extract_playlist_id(playlist_url)
    
    youtube = get_youtube_service()
    df = fetch_playlist(youtube, playlist_id)
    print(f"✅ Fetched {len(df)} songs.\n")
    
    df = classify_with_ollama(df)
    
    # ===================== SAVE =====================
    excel_file = "playlist_songs.xlsx"
    try:
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"📊 Saved: {excel_file}")
    except Exception as e:
        print(f"Excel failed: {e}")
        csv_file = "playlist_songs.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"→ Saved as {csv_file} instead")
    
    # ===================== SUMMARY =====================
    print("\nTop 15 rows:")
    print(df[['Title', 'Channel', 'Detected_Language']].head(15))
    print("...")
    
    eng = (df['Detected_Language'] == 'English').sum()
    print(f"\n🇬🇧 English: {eng} | 🌍 Non-English: {len(df) - eng}")
    
    print("\n=== LANGUAGE SUMMARY ===")
    print(df['Detected_Language'].value_counts().to_string())
    
    print("\n✅ Done! Open the file, review, and enjoy your clean Desi playlists!")