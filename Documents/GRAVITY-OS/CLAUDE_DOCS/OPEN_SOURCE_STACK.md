# GRAVITY — Open Source Stack
**Every tool, what it does, how it connects, what you need to use it, alternatives, and unusual options worth knowing about.**
Last updated: June 2026

---

## How To Read This Document

Each tool entry follows the same structure:
- **What it does in Gravity** — the specific job it has in this project
- **How it connects** — which part of the system it plugs into
- **What you need** — install command, any config, any credentials
- **Code pattern** — the exact usage pattern in Gravity
- **Alternatives** — other tools that do the same job
- **Unique/cool options** — lesser-known tools worth considering

---

---

# SECTION 1 — AI / INFERENCE

---

## 1.1 Groq — Primary AI Provider (Development)

**Licence:** Free tier (commercial)
**Cost:** £0 — 14,400 requests/day on free tier
**Repo/Site:** https://groq.com

### What it does in Gravity
Runs all AI inference during development and beta. Powers the onboarding conversation engine, nudge decision pipeline, nudge content generation, silent profile extraction, and check-in conversations. Every call that currently says `client.complete()` in `core/ai_client.py` goes through Groq.

### How it connects
`core/ai_client.py` → `AIClient` class → `GROQ_API_KEY` in `.env` → Groq cloud API → llama-3.3-70b-versatile model

### What you need
```bash
pip install groq
```
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
AI_PROVIDER=groq
```
Get key: https://console.groq.com → API Keys → Create

### Code pattern
Already implemented in `core/ai_client.py`. The abstraction means you never call Groq directly — everything goes through `AIClient.complete(system_prompt, messages)`.

### Alternatives
| Tool | Cost | Quality | Notes |
|---|---|---|---|
| Anthropic Claude API | ~£0.85/user/month | Best | Production target — swap by changing AI_PROVIDER=anthropic |
| Ollama (local) | Free | Good | Self-hosted, no internet needed, already on mj-notarobot |
| Together AI | Free tier | Good | Similar to Groq, alternative free tier |
| Mistral API | Free tier | Good | European provider, GDPR-friendly |
| OpenRouter | Free tier | Varies | Routes to multiple providers, free credits |

### Unique options
- **Cerebras** — new entrant, claims fastest inference in the world (1000+ tokens/sec), has free tier
- **Fireworks AI** — very fast, supports function calling well, free tier available
- **Perplexity API** — includes web search built in, interesting for the research feature

---

## 1.2 Ollama — Local AI (Dev / Offline)

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/ollama/ollama

### What it does in Gravity
Runs AI models locally on `mj-notarobot` via Tailscale. Used for development without burning Groq rate limits, prompt engineering sessions, and offline development. Also a fallback if Groq is down.

### How it connects
Same `AIClient` abstraction — set `AI_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://vx1-dev.tail972d72.ts.net:11434` in `.env`. The code path in `ai_client.py` needs to be built (currently stubbed) using the Ollama Python library.

### What you need
```bash
pip install ollama
```
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://vx1-dev.tail972d72.ts.net:11434
OLLAMA_MODEL=llama3.1:8b
```
On the server: `ollama pull llama3.1:8b`

### Code pattern
```python
import ollama

response = ollama.chat(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Hello"}]
)
text = response['message']['content']
```

### Alternatives
- **LM Studio** — GUI for local models, good for testing prompts visually
- **Jan** — open source local AI desktop app, similar to LM Studio
- **GPT4All** — runs on CPU only, works on any machine, slower but no GPU needed

### Unique options
- **Llamafile** — single executable file that bundles a model, runs anywhere with zero setup, no install
- **MLX** — Apple's ML framework, runs models natively on Apple Silicon at near-GPU speed. On your MacBook Air this would be significantly faster than standard Ollama

---

---

# SECTION 2 — VOICE

---

## 2.1 OpenAI Whisper — Speech to Text

**Licence:** MIT
**Cost:** Free (local) or via API (~£0.004/min)
**Repo:** https://github.com/openai/whisper

### What it does in Gravity
Converts spoken audio from the device microphone into text for processing by the AI brain. Used for: voice onboarding answers, voice check-ins, adding tasks/reminders by voice, asking Gravity questions.

### How it connects
```
Microphone (RPi MEMS mic)
→ sounddevice (audio capture)
→ Whisper (transcription, runs on device or backend)
→ text string
→ core/ai_client.py (same pipeline as typed text)
→ AI response
→ Piper TTS (spoken back to user)
```

Lives in: `firmware/voice/stt.py` (to be built, Stage 2)

### What you need
```bash
pip install openai-whisper
pip install sounddevice
```
No API key needed for local use. Models download automatically on first run.

```python
import whisper

model = whisper.load_model("tiny")  # 39MB — fast on RPi
# OR
model = whisper.load_model("base")  # 74MB — better accuracy

result = model.transcribe("audio.wav")
text = result["text"]
```

### Model size guide
| Model | Size | Speed on RPi | Accuracy |
|---|---|---|---|
| tiny | 39MB | ~0.5s | Good for clear speech |
| base | 74MB | ~1s | Better accent handling |
| small | 244MB | ~3s | Very good |
| medium | 769MB | Too slow for RPi | Use on backend server |

### Alternatives
| Tool | Licence | Notes |
|---|---|---|
| Vosk | Apache 2.0 | Very lightweight, runs on RPi Zero (15MB model), offline, slightly lower accuracy |
| DeepSpeech (Mozilla) | MPL 2.0 | Older but proven, runs on RPi |
| Coqui STT | MPL 2.0 | Fork of DeepSpeech, better maintained |
| Google Speech-to-Text API | Paid | £0.004/15sec, cloud only, high accuracy |
| faster-whisper | MIT | CTranslate2-optimised Whisper, 4x faster, same accuracy, highly recommended |

### Unique options
- **faster-whisper** — drop-in replacement for Whisper, 4x faster on same hardware, same API. This is probably the right choice for production: `pip install faster-whisper`
- **whisper.cpp** — C++ port of Whisper, runs on ESP32-S3 directly (limited models), enables fully offline voice on the production chip
- **WhisperX** — adds word-level timestamps and speaker diarisation, useful if you want to track exactly when the user said what

---

## 2.2 Piper TTS — Text to Speech

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/rhasspy/piper

### What it does in Gravity
Converts AI response text into spoken audio played through the device speaker. Makes Gravity conversational — user speaks, Gravity speaks back. Used for nudges delivered by voice, check-in conversations, answers to questions.

### How it connects
```
AI response text (string)
→ Piper TTS (synthesis, runs on device)
→ WAV audio bytes
→ simpleaudio / pygame.mixer (playback through speaker)
```

Lives in: `firmware/voice/tts.py` (to be built, Stage 2)

### What you need
```bash
pip install piper-tts
```
Download a voice model:
```bash
# UK English female voice — sounds natural, not robotic
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx.json
```

```python
from piper import PiperVoice
import wave, io

voice = PiperVoice.load("en_GB-jenny_dioco-medium.onnx")

with io.BytesIO() as wav_io:
    with wave.open(wav_io, "wb") as wav_file:
        voice.synthesize("You haven't moved in 4 hours.", wav_file)
    audio_bytes = wav_io.getvalue()
# Play audio_bytes through speaker
```

### Voice options (UK English)
- `en_GB-jenny_dioco-medium` — natural female, recommended
- `en_GB-alan-medium` — male voice
- `en_GB-northern_english_male-medium` — regional accent, character
- `en_US-lessac-medium` — American if preferred

### Alternatives
| Tool | Licence | Notes |
|---|---|---|
| Coqui TTS | MPL 2.0 | More voices, more control, heavier |
| Festival TTS | Free | Old, robotic sounding, runs anywhere |
| espeak-ng | GPL | Very lightweight (works on ESP32), sounds synthetic |
| ElevenLabs API | Paid | Best quality available, £0.30/1000 chars, good for demos |
| Google Cloud TTS | Paid | WaveNet voices, high quality, £0.004/1000 chars |

### Unique options
- **StyleTTS2** — state of the art open source TTS, natural prosody, emotion-aware, heavier but runs on server
- **MetaVoice** — open source, 1B parameter model, very natural sounding, Apache 2.0, server-side
- **Bark** — open source by Suno, can do emotion/tone/non-verbal sounds, interesting for milestone celebrations

---

## 2.3 OpenWakeWord — Wake Word Detection

**Licence:** Apache 2.0
**Cost:** Free
**Repo:** https://github.com/dscripka/openWakeWord

### What it does in Gravity
Listens passively for the wake phrase "Hey Gravity" (or similar) so the device knows when to start recording. Without this, the microphone would be on constantly and every sound would be processed — impractical and privacy-invasive.

### How it connects
```
Microphone (always on, low power)
→ OpenWakeWord (streaming audio analysis, very low CPU)
→ Wake word detected
→ LED/visual indicator on display (listening state)
→ sounddevice records until silence
→ Whisper transcribes
→ AI pipeline
```

### What you need
```bash
pip install openwakeword
```

```python
from openwakeword.model import Model
import numpy as np

# Load pre-trained model or custom "Hey Gravity" model
model = Model(wakeword_models=["hey_jarvis"])  # placeholder until custom model trained

def process_audio_chunk(audio_chunk):
    predictions = model.predict(audio_chunk)
    if predictions["hey_jarvis"] > 0.5:
        # Wake word detected
        start_recording()
```

### Training a custom "Hey Gravity" model
OpenWakeWord supports training with ~30 positive samples (recordings of "Hey Gravity") and uses synthetic negative examples. This is achievable in a few hours with their training script. A custom wake word makes the product feel distinctly Gravity rather than generic.

### Alternatives
| Tool | Licence | Notes |
|---|---|---|
| Picovoice Porcupine | Free tier (3 wake words) | More polished, better accuracy, closed source |
| Snowboy | Apache 2.0 | Deprecated but still works, needs cloud training |
| Precise (Mycroft) | Apache 2.0 | Open source, requires more training data |
| PocketSphinx | BSD | Old, CPU-friendly, lower accuracy |

### Unique options
- **Wyoming Protocol** — open standard for voice satellite devices (used in Home Assistant), worth considering as a base architecture for the entire voice pipeline
- **Willow** — open source voice assistant hardware/software stack, built for ESP32-S3 specifically, could provide ready-made firmware components

---

---

# SECTION 3 — WEATHER & ENVIRONMENTAL DATA

---

## 3.1 Open-Meteo — Weather

**Licence:** CC BY 4.0 (non-commercial free, commercial via subscription)
**Cost:** £0 for non-commercial / under 10,000 daily calls
**Site:** https://open-meteo.com

### What it does in Gravity
Provides current conditions and forecasts. Used for: showing temperature on the A1 ambient screen, nudges like "rain at 3pm — your run should be this morning", adjusting backlight based on sunrise/sunset, correlating weather patterns with habit completion in the 6-month review.

### How it connects
Backend FastAPI service (`integrations/weather.py`) → Open-Meteo API → cached in Redis (1-hour TTL) → delivered to device via layout JSON → shown in ambient screen rim label

### What you need
No API key. No account. Just an HTTP call.

```python
import httpx

async def get_weather(lat: float, lon: float) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,precipitation,wind_speed_10m",
                "daily": "sunrise,sunset,precipitation_probability_max,temperature_2m_max,temperature_2m_min",
                "forecast_days": 3,
                "timezone": "Europe/London"
            }
        )
        return r.json()

# Weather code → glyph mapping for the display
WEATHER_GLYPHS = {
    0: "☀",   # Clear sky
    1: "🌤",  # Mainly clear
    2: "⛅",  # Partly cloudy
    3: "☁",   # Overcast
    61: "🌧",  # Rain
    71: "❄",  # Snow
    95: "⛈",  # Thunderstorm
}
```

### What the data enables
- Current temp on ambient screen: `temperature_2m`
- Weather glyph: `weather_code`
- Rain nudge: `precipitation_probability_max` > 60% → morning outdoor activity alert
- Auto dim: `sunrise`/`sunset` → schedule backlight reduction
- Pattern analysis: correlate `temperature_2m` with gym completion in 6-month review

### Alternatives
| Tool | Cost | Notes |
|---|---|---|
| wttr.in | Free | Terminal-focused weather API, simple queries, no key |
| 7timer.info | Free | Astronomical/outdoor focus, good for activity planning |
| Norwegian Met (Yr.no) | Free | High quality European data, CC licence |
| OpenWeatherMap | Free tier (1000 calls/day) | More data points, requires API key |
| Pirate Weather | Free tier | Open source recreation of Dark Sky API |

### Unique options
- **Meteostat** — historical weather data going back decades, free Python library. Useful for the 6-month review: "Your gym attendance correlates with temperature drops below 10°C"
- **Open-Meteo Air Quality** — PM2.5, pollen, UV index — same API, no key. Could add "air quality poor today — consider indoor workout" nudge
- **Sunrise-Sunset API** (sunrise-sunset.org) — just sunrise/sunset times, ultra-minimal, no key needed at all

---

---

# SECTION 4 — FITNESS & HEALTH

---

## 4.1 react-native-health — Apple HealthKit

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/agencyenterprise/react-native-health

### What it does in Gravity
Reads health data from Apple Health on iOS devices. Steps, workouts, sleep, heart rate, active energy, weight. This is the primary fitness data source for iOS users. Data flows from the phone to the backend where it informs nudge decisions and goal progress.

### How it connects
```
Apple Health (on iPhone)
→ react-native-health (React Native app, iOS only)
→ POST /integrations/health/sync (backend API, daily or on-demand)
→ PostgreSQL habit_logs / health_data tables
→ nudge_engine.py reads this data
→ display layout updates
```

### What you need
In the React Native app:
```bash
npm install react-native-health
```
Requires: HealthKit entitlement in Apple developer account, user permission request in app.

```javascript
import AppleHealthKit from 'react-native-health';

const PERMS = {
  permissions: {
    read: [
      AppleHealthKit.Constants.Permissions.Steps,
      AppleHealthKit.Constants.Permissions.SleepAnalysis,
      AppleHealthKit.Constants.Permissions.Workout,
      AppleHealthKit.Constants.Permissions.HeartRate,
      AppleHealthKit.Constants.Permissions.ActiveEnergyBurned,
    ]
  }
};

AppleHealthKit.initHealthKit(PERMS, (err) => {
  if (err) return;

  // Get today's steps
  AppleHealthKit.getStepCount({date: new Date().toISOString()}, (err, results) => {
    const steps = results.value;
    // POST to backend
  });
});
```

### Alternatives
| Tool | Platform | Notes |
|---|---|---|
| Google Fit REST API | Android | Free, OAuth2, similar data |
| react-native-google-fit | Android | React Native wrapper for Google Fit |
| Strava API | Both | Richer workout data, community features |
| Fitbit API | Both | If user has Fitbit device |
| Garmin Connect API | Both | If user has Garmin device |

### Unique options
- **Oura API** — Oura Ring sleep and readiness data, genuinely the best sleep tracking available, free API for ring owners. Gravity could use Oura's readiness score to adjust goal intensity on low-recovery days
- **WHOOP API** — Similar to Oura, strain and recovery focused, popular with fitness-serious users
- **Terra API** — Unified API for 50+ fitness devices (Garmin, Oura, Polar, Fitbit etc), one integration instead of many. Free tier available.

---

## 4.2 Wger — Exercise Database

**Licence:** AGPL / Free
**Cost:** Free (public API) or self-hosted
**Site:** https://wger.de | **Repo:** https://github.com/wger-project/wger

### What it does in Gravity
Open source workout/exercise database. When a user's goal involves fitness, Gravity can suggest specific exercises, build workout plans, and track against a structured programme. The database includes exercises, muscle groups, equipment types, and nutritional data.

### How it connects
Backend `integrations/fitness.py` → Wger REST API → AI context for goal-related suggestions → delivered as structured workout plans in the app

### What you need
No auth needed for read-only public API.
```python
import httpx

async def search_exercises(query: str) -> list:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://wger.de/api/v2/exercise/search/",
            params={"term": query, "language": "english", "format": "json"}
        )
        return r.json()["suggestions"]

async def get_exercise_detail(exercise_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://wger.de/api/v2/exercise/{exercise_id}/")
        return r.json()
```

### Alternatives
- **ExerciseDB API** (RapidAPI) — large exercise database with GIFs, free tier
- **API-Ninjas Exercises** — simple, free tier
- **Self-curated JSON** — for Gravity's needs a curated set of ~200 exercises is more than enough and removes any dependency

---

---

# SECTION 5 — WEB SEARCH & RESEARCH

---

## 5.1 SearXNG — Self-Hosted Web Search

**Licence:** AGPL 3.0
**Cost:** Free (self-hosted on your Hetzner VPS)
**Repo:** https://github.com/searxng/searxng

### What it does in Gravity
Powers the agentic research feature. When a user asks Gravity to research something related to their goal, the backend searches the web, pulls relevant results, and synthesises them with the AI. Example: "Find me the best 5km training plan for a beginner" → SearXNG searches → AI synthesises → structured plan delivered to app.

### How it connects
```
User voice/text request → AI identifies research intent
→ backend calls SearXNG (localhost:8080 on VPS)
→ SearXNG aggregates results from Google, Bing, DuckDuckGo, Wikipedia
→ raw results passed to AI for synthesis
→ synthesised answer + sources returned to user
```

### What you need
Deploy on Hetzner VPS alongside FastAPI:
```bash
# Add to docker-compose.yml
searxng:
  image: searxng/searxng:latest
  ports: ["8080:8080"]
  environment:
    - SEARXNG_SECRET=your_random_secret
  volumes:
    - ./searxng:/etc/searxng
```

```python
import httpx

async def web_search(query: str, num_results: int = 5) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "http://localhost:8080/search",
            params={
                "q": query,
                "format": "json",
                "categories": "general",
            }
        )
        data = r.json()
        return [
            {"title": r["title"], "url": r["url"], "snippet": r.get("content", "")}
            for r in data.get("results", [])[:num_results]
        ]
```

### Alternatives
| Tool | Cost | Notes |
|---|---|---|
| Tavily API | £0.01/search | Purpose-built for AI agents, clean results |
| Brave Search API | Free tier (2000/month) | Privacy-focused, no tracking |
| DuckDuckGo (unofficial) | Free | No official API, scraping-based |
| Serper API | Free tier (2500/month) | Google results via API |
| Bing Web Search | Free tier (1000/month) | Microsoft, reliable |

### Unique options
- **Kagi API** — highest quality search available, ad-free index, ~£0.025/search, worth it for research quality
- **Jina AI Reader** — takes a URL, returns clean markdown content. Perfect for: search finds article → Jina extracts the text cleanly → AI summarises. Free tier: `https://r.jina.ai/{url}`
- **Firecrawl** — open source web scraper that extracts clean content from any URL for AI consumption, self-hostable

---

## 5.2 Jina AI Reader — Web Content Extraction

**Licence:** Apache 2.0
**Cost:** Free tier (generous)
**Site:** https://jina.ai/reader

### What it does in Gravity
Takes a URL and returns clean, AI-readable markdown — strips ads, navigation, footers, all the noise. Essential companion to SearXNG: search finds relevant pages, Jina extracts clean content for the AI to read.

### How it connects
```
SearXNG returns [url1, url2, url3]
→ Jina reader fetches each URL
→ Returns clean markdown
→ AI reads and synthesises
→ Summary delivered to user
```

### What you need
No setup. Just prepend `https://r.jina.ai/` to any URL.
```python
import httpx

async def extract_page_content(url: str) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain"}
        )
        return r.text  # Clean markdown, ready for AI
```

---

---

# SECTION 6 — KNOWLEDGE BASE & MEMORY

---

## 6.1 pgvector — Vector Search in PostgreSQL

**Licence:** PostgreSQL Licence (MIT-like)
**Cost:** Free (extension for your existing Postgres)
**Repo:** https://github.com/pgvector/pgvector

### What it does in Gravity
Stores embeddings of user conversations, goals, uploaded documents, and notes. Enables semantic search — "find memories similar to this situation" — which is how Gravity's long-term memory system works. Instead of searching by keyword, it searches by meaning.

### How it connects
```
User conversation turn / uploaded doc / goal note
→ sentence-transformers generates embedding (384-dimension vector)
→ stored in PostgreSQL memories table with pgvector
→ At query time: embed the current context
→ pgvector similarity search returns most relevant memories
→ injected into AI context for the current call
```

### What you need
```bash
# Install extension (run once on PostgreSQL)
CREATE EXTENSION IF NOT EXISTS vector;

# Install Python client
pip install pgvector sqlalchemy
```

```sql
-- Create memories table
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    content TEXT,
    embedding vector(384),
    memory_type VARCHAR(50),  -- 'conversation', 'goal', 'document', 'pattern'
    created_at TIMESTAMP DEFAULT NOW(),
    relevance_score FLOAT DEFAULT 1.0
);

-- Create index for fast similarity search
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);
```

```python
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def store_memory(user_id: int, content: str, memory_type: str):
    embedding = embedder.encode(content).tolist()
    # INSERT into memories table

def recall_similar(user_id: int, query: str, limit: int = 5) -> list[str]:
    query_embedding = embedder.encode(query).tolist()
    # SELECT content FROM memories WHERE user_id = ?
    # ORDER BY embedding <=> query_embedding LIMIT ?
    # Returns most semantically similar memories
```

### Alternatives
| Tool | Cost | Notes |
|---|---|---|
| ChromaDB | Free, self-hosted | Purpose-built vector DB, simpler API, slightly less scalable |
| Qdrant | Free, self-hosted | High performance vector DB, good for production scale |
| Weaviate | Free, self-hosted | Feature-rich, complex to deploy |
| FAISS (Meta) | Free, in-process | No database, just in-memory index, good for prototyping |
| LanceDB | Free, self-hosted | New, very fast, embedded (no server needed) |

---

## 6.2 sentence-transformers — Local Embeddings

**Licence:** Apache 2.0
**Cost:** Free (runs locally, no API)
**Repo:** https://github.com/UKPLab/sentence-transformers

### What it does in Gravity
Converts text into numerical vectors (embeddings) that capture semantic meaning. Required by pgvector — you generate an embedding before storing a memory, and generate one at query time to find similar memories. Runs entirely locally, no API cost, no rate limits.

### How it connects
Every memory storage and retrieval operation in the backend.

### What you need
```bash
pip install sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer

# Load once at startup, reuse
embedder = SentenceTransformer("all-MiniLM-L6-v2")
# Model downloads automatically on first use (80MB)

# Generate embedding
embedding = embedder.encode("User avoids gym on Fridays consistently")
# Returns numpy array of 384 floats
```

### Model options
| Model | Size | Speed | Quality | Use case |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | 80MB | Very fast | Good | Default choice for Gravity |
| all-mpnet-base-v2 | 420MB | Medium | Better | If quality matters more |
| paraphrase-multilingual-MiniLM | 117MB | Fast | Good multilingual | If supporting non-English |

### Alternatives
- **OpenAI Embeddings API** — best quality, £0.00013/1000 tokens, needs internet
- **Cohere Embed API** — good quality, free tier
- **Nomic Embed** — open source, runs locally, competitive with OpenAI quality

---

## 6.3 PyMuPDF — PDF Processing

**Licence:** AGPL 3.0 (free for open source use)
**Cost:** Free
**Repo:** https://github.com/pymupdf/PyMuPDF

### What it does in Gravity
Extracts text, tables, and images from PDFs that users upload. Core to the agentic research feature — user uploads study notes, a CV, a business plan, a training programme — Gravity reads it, understands it, and uses it to provide better advice and tracking.

### How it connects
```
User uploads PDF via app
→ Backend receives file
→ PyMuPDF extracts text page by page
→ Text chunked (500 tokens per chunk)
→ Each chunk embedded with sentence-transformers
→ Stored in memories table (pgvector)
→ Available for AI recall in future conversations
```

### What you need
```bash
pip install pymupdf
```

```python
import fitz  # PyMuPDF import name

def extract_pdf_text(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_pdf_chunks(file_path: str, chunk_size: int = 500) -> list[str]:
    text = extract_pdf_text(file_path)
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks
```

### Alternatives
- **pdfplumber** — better table extraction, slightly slower
- **pdfminer.six** — pure Python, no C dependencies, easier to install
- **pypdf** — lightweight, basic extraction, good for simple PDFs
- **Marker** — new open source PDF to markdown converter, best quality for complex PDFs

---

## 6.4 WeasyPrint — Document Generation

**Licence:** BSD
**Cost:** Free
**Repo:** https://github.com/Kozea/WeasyPrint

### What it does in Gravity
Generates downloadable PDF documents for users. When a user asks Gravity to compile a study plan, a savings summary, a 6-month review report, or a training programme — WeasyPrint renders it to a polished PDF they can download via the app.

### How it connects
```
User requests a document ("compile my 6-month review as PDF")
→ AI generates structured content (via Jinja2 template)
→ WeasyPrint renders HTML template + content → PDF
→ PDF saved to /tmp or object storage
→ Download link sent to app
```

### What you need
```bash
pip install weasyprint jinja2
```

```python
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates/"))

def generate_review_pdf(user_data: dict) -> bytes:
    template = env.get_template("6_month_review.html")
    html_content = template.render(**user_data)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
```

Template example (`templates/6_month_review.html`):
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'JetBrains Mono', monospace; background: #f4f2ea; color: #14130d; }
    h1 { font-size: 24px; }
  </style>
</head>
<body>
  <h1>{{ user.name }} — 6 Month Review</h1>
  <p>Goal: {{ goal.statement }}</p>
  <p>Achievement: {{ goal.completion_pct }}%</p>
  ...
</body>
</html>
```

---

---

# SECTION 7 — CALENDAR

---

## 7.1 CalDAV — Universal Calendar Protocol

**Licence:** Open standard
**Cost:** Free
**Python library:** `pip install caldav`
**Repo:** https://github.com/python-caldav/caldav

### What it does in Gravity
Connects to any CalDAV-compatible calendar — iCloud, Google Calendar, Nextcloud, Fastmail, ProtonMail, etc. Pulls events to understand the user's schedule and upcoming commitments. Used for: avoiding nudges during meetings, surfacing "you have a deadline tomorrow" context, detecting free time windows.

### How it connects
Backend `integrations/calendar.py` → CalDAV library → user's calendar → events cached in Postgres (today only) → AI context building → nudge decision engine

### What you need
```bash
pip install caldav icalendar
```

iCloud setup (most common for iOS users):
```python
import caldav
from datetime import datetime, timedelta

# iCloud CalDAV URL format
client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username="user@icloud.com",
    password="app-specific-password"  # Generated in Apple ID settings
)

principal = client.principal()
calendars = principal.calendars()

# Get today's events
today = datetime.now()
tomorrow = today + timedelta(days=1)
events = []
for cal in calendars:
    for event in cal.date_search(start=today, end=tomorrow):
        events.append(event.vobject_instance.vevent)
```

Google Calendar (preferred for Android users): Use Google Calendar API with OAuth2 — already in requirements.txt via `google-api-python-client`.

### Alternatives
- **Google Calendar API** — better for Android/Google users, richer API, OAuth2
- **Microsoft Graph API** — for Outlook/Microsoft 365 calendar users
- **icalendar library** — parse `.ics` file exports from any calendar without live sync
- **Nextcloud** — self-hosted calendar if privacy-conscious users want no cloud dependency

---

---

# SECTION 8 — COMPUTER VISION

---

## 8.1 OpenCV — Computer Vision

**Licence:** Apache 2.0
**Cost:** Free
**Repo:** https://github.com/opencv/opencv

### What it does in Gravity (Stage 4)
Processes camera feed from the device for presence detection. Is someone at their desk? Have they picked up their phone? Are they away from the device? This context makes nudges more accurate — Gravity doesn't nudge you when you're clearly working.

### How it connects
```
Camera module (RPi camera or OV2640 on ESP32-CAM)
→ OpenCV (frame capture + basic analysis on device)
→ if complex analysis needed: frame sent to backend
→ classification result (present/absent/phone-in-hand)
→ nudge decision engine receives as context
```

### What you need
```bash
pip install opencv-python-headless  # headless = no GUI, for server/RPi
```

```python
import cv2
import numpy as np

# Motion detection — is anyone present?
def detect_presence(cap: cv2.VideoCapture) -> bool:
    _, frame1 = cap.read()
    _, frame2 = cap.read()
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return any(cv2.contourArea(c) > 1000 for c in contours)
```

### Alternatives
- **MediaPipe** (Google, Apache 2.0) — higher-level CV: pose estimation, hand tracking, face detection. More useful for Gravity than raw OpenCV
- **YOLO (Ultralytics)** — object detection, can detect phones, people, laptops — MIT licence for YOLOv8
- **TensorFlow Lite** — runs ML models on RPi/ESP32 for on-device classification

### Unique options
- **Moondream** — tiny vision language model (1.8B params), can answer questions about images ("Is the person holding a phone?"), runs on RPi 4, Apache 2.0. More capable than classification models for nuanced presence detection
- **CLIP (OpenAI)** — understand image content semantically, MIT licence, runs locally
- **Frigate** — open source NVR with ML detection, designed for RPi, production-ready presence detection

---

---

# SECTION 9 — BACKEND INFRASTRUCTURE

---

## 9.1 FastAPI — Backend Framework

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/tiangolo/fastapi

Already chosen. No alternatives needed — it's the right tool. Async, fast, automatic OpenAPI docs, native WebSocket support.

---

## 9.2 Redis — Cache + Pub/Sub

**Licence:** BSD (v7 and below) / SSPL (v7.4+)
**Cost:** Free (self-hosted)

Use Redis 7.0 or earlier to stay on BSD licence. Handles: user context cache, nudge cooldowns, WebSocket session management, real-time event pub/sub between backend and devices.

**Unique option: Valkey** — community fork of Redis after the licence change, 100% BSD, drop-in replacement, backed by Linux Foundation. Consider using Valkey instead of Redis to avoid future licence concerns.

---

## 9.3 Celery — Task Queue

**Licence:** BSD
**Cost:** Free

Handles background jobs: nightly AI context rebuild, integration syncs, 6-month cycle triggers, pattern detection batch jobs.

**Alternative: APScheduler** — simpler, already in requirements.txt, better for a smaller task queue. Use APScheduler first, migrate to Celery if job volume grows.

**Unique option: Huey** — minimal task queue, much simpler than Celery, Redis-backed, perfect for Gravity's scale.

---

## 9.4 SearXNG — Already covered in Section 5.

---

## 9.5 Caddy — Web Server + SSL

**Licence:** Apache 2.0
**Cost:** Free
**Repo:** https://github.com/caddyserver/caddy

Sits in front of FastAPI on the Hetzner VPS. Handles: automatic HTTPS (Let's Encrypt), reverse proxy, request logging. Zero configuration for SSL — it just works.

```bash
# Caddyfile — that's literally all you need for HTTPS
api.gravity.app {
    reverse_proxy localhost:8000
}
```

---

---

# SECTION 10 — AUDIO / REWARDS

---

## 10.1 simpleaudio — Audio Playback

**Licence:** BSD
**Cost:** Free
**Repo:** https://github.com/hamiltron/py-simple-audio

### What it does in Gravity
Plays reward sounds and notification tones through the device speaker. Completion chimes, streak milestone sounds, nudge audio alerts, morning brief tone.

### What you need
```bash
pip install simpleaudio
```

```python
import simpleaudio as sa

def play_completion_chime():
    wave_obj = sa.WaveObject.from_wave_file("sounds/completion.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()  # or non-blocking: just wave_obj.play()
```

### Sound file sources (Creative Commons)
- **Freesound.org** — largest CC sound library, search "chime", "notification", "success"
- **Mixkit** — free sound effects, commercial OK
- **ZapSplat** — free tier, high quality notifications/UI sounds

### Alternatives
- **pygame.mixer** — already installed (Pygame dep), can also play audio
- **playsound** — single function, minimal, cross-platform
- **pydub** — full audio processing library, good if you want to generate tones programmatically

### Unique options
- **Suno Bark** — open source, can generate expressive audio clips from text descriptions: "a soft satisfying completion chime" → actual audio. Interesting for personalised reward sounds
- **Generate tones in code** — numpy + simpleaudio can generate sine waves, making entirely custom reward sounds without any audio files:
```python
import numpy as np
import simpleaudio as sa

def play_tone(frequency: float = 440, duration: float = 0.3, volume: float = 0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = (np.sin(2 * np.pi * frequency * t) * volume * 32767).astype(np.int16)
    # Fade out to avoid click
    fade = np.linspace(1, 0, len(wave) // 4)
    wave[-len(fade):] = (wave[-len(fade):] * fade).astype(np.int16)
    play_obj = sa.play_buffer(wave, 1, 2, sample_rate)
    play_obj.wait_done()

# Usage:
play_tone(880, 0.15)  # Quick high ping — task completed
play_tone(440, 0.5)   # Lower tone — nudge
```

---

---

# SECTION 11 — APP (REACT NATIVE)

---

## 11.1 Expo — React Native Framework

**Licence:** MIT
**Cost:** Free (EAS Build has paid tier, but local builds are free)
**Site:** https://expo.dev

Removes almost all native iOS/Android complexity. Use Expo Router (file-based navigation), Expo SecureStore (JWT tokens), Expo Notifications (push). Build locally with `expo run:ios` and `expo run:android`.

---

## 11.2 react-native-usage-stats — Android Screen Time

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/nileshthummar/react-native-usage-stats

Gets per-app usage duration on Android without any API key or permission beyond `PACKAGE_USAGE_STATS` (user grants via settings). This is the closest thing to Apple Screen Time available on Android for third-party apps.

---

## 11.3 Zustand — State Management

**Licence:** MIT
**Cost:** Free
**Repo:** https://github.com/pmndrs/zustand

Minimal Redux alternative. No boilerplate. Gravity's app state (current user, device connection status, habits, goals) fits cleanly in Zustand stores.

---

---

# SECTION 12 — UNIQUE & EXPERIMENTAL OPTIONS

Tools that aren't in the current plan but are worth knowing about. Some of these could make Gravity meaningfully different.

---

## 12.1 Home Assistant — Smart Home Integration

**Licence:** Apache 2.0
**Site:** https://home-assistant.io

If a user runs Home Assistant, Gravity could integrate as a dashboard device. Show home automation context on the display — "last person left the house" trigger, presence detection via existing sensors, morning routine automation. Gravity becomes part of a broader ambient intelligence layer.

---

## 12.2 Mopidy — Music Playback Server

**Licence:** Apache 2.0
**Repo:** https://github.com/mopidy/mopidy

Open source music server. If Gravity adds a "focus music" feature — playing ambient/focus music through the device speaker during work sessions — Mopidy handles playback and integrates with Spotify, local files, YouTube Music. The Spotify API already in the plan could route through Mopidy.

---

## 12.3 n8n — Workflow Automation (Self-Hosted Zapier)

**Licence:** Fair-code (free to self-host)
**Repo:** https://github.com/n8n-io/n8n

The IFTTT/Zapier alternative that runs on your own server. Deploy alongside FastAPI on Hetzner. Users can build custom automation workflows connecting Gravity to anything — "when I complete my gym habit, post to Discord", "when my savings goal hits 50%, send me an email". Removes the need to build custom integrations for niche services.

---

## 12.4 Metabase — Analytics Dashboard

**Licence:** AGPL (free)
**Repo:** https://github.com/metabase/metabase

Open source business intelligence tool. Connect it to your PostgreSQL and get instant dashboards — user retention, habit completion rates, nudge effectiveness, most common avoidance patterns. Deploy on Hetzner. Gives you the analytics layer without writing any dashboard code.

---

## 12.5 Postal — Self-Hosted Email

**Licence:** MIT
**Repo:** https://github.com/postalserver/postal

Self-hosted transactional email server. Replace SendGrid/Mailgun for sending password reset, weekly summaries, 6-month review reports to users. Zero ongoing cost. Needs careful setup (SPF/DKIM/DMARC records) but fully controllable.

---

## 12.6 Livekit — Real-Time Voice/Video Infrastructure

**Licence:** Apache 2.0
**Repo:** https://github.com/livekit/livekit

Open source WebRTC infrastructure. If Gravity ever adds real-time voice calls between the device and backend (lower latency than HTTP), LiveKit handles the WebRTC complexity. Also relevant if you want to add a "voice assistant" mode where conversations happen in real time rather than turn-by-turn.

---

## 12.7 Temporal — Workflow Orchestration

**Licence:** MIT
**Repo:** https://github.com/temporalio/temporal

Durable workflow execution. For Gravity's long-running processes — 6-month goal cycles, nightly batch jobs, multi-step onboarding flows — Temporal ensures they complete even if the server crashes mid-execution. More robust than Celery for critical workflows. Probably overkill until scale but worth knowing.

---

## 12.8 Typesense — Fast Search

**Licence:** GPL 3.0
**Repo:** https://github.com/typesense/typesense

Self-hosted Algolia alternative. If the app gets a search feature — searching through a user's goals, notes, habits history — Typesense provides sub-10ms search with typo tolerance. Much simpler than Elasticsearch for Gravity's scale.

---

---

# QUICK REFERENCE — INSTALL ALL

```bash
# Stage 0 (current — AI brain)
pip install groq anthropic python-dotenv pydantic rich pytest

# Stage 1 (backend)
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic redis celery

# Stage 1 (integrations)
pip install caldav icalendar google-api-python-client httpx

# Stage 2 (display + simulator)
pip install pillow pygame

# Stage 2 (knowledge base + memory)
pip install pgvector sentence-transformers chromadb pymupdf weasyprint jinja2

# Stage 3 (voice)
pip install openai-whisper faster-whisper piper-tts sounddevice simpleaudio openwakeword

# Stage 3 (research + web)
# SearXNG deployed via Docker (no pip install)
# Jina reader — no install, just HTTP calls

# Stage 4 (computer vision)
pip install opencv-python-headless mediapipe

# Analytics
pip install pandas scipy  # pattern detection

# React Native app
# npm install react-native-health react-native-usage-stats zustand @tanstack/react-query
```

---

# TOTAL MONTHLY COST AT SCALE

| Service | Cost |
|---|---|
| Hetzner CX22 VPS | £4.50/month |
| AI inference (100 active users × £0.85) | £85/month |
| Everything else | £0 |
| **Total** | **~£89.50/month** |

At 100 paying users × £4.99/month = **£499 revenue**
Margin after infrastructure: **~£410/month (82%)**

