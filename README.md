# Bachelor Gruppe 6 — AI-assistert byggesaksbehandling

Dette prosjektet er en bacheloroppgave utviklet i samarbeid med Multiconsult. Målet er å bruke kunstig intelligens til å effektivisere arbeid med byggesøknader og bygningsvisualisering.

Prosjektet består av to deler som jobber sammen:

---

## Del 1 — RAG-system (spørsmål/svar på dokumenter)

Et nettbasert system der brukere kan logge inn og stille spørsmål til PDF-dokumenter — for eksempel lover, forskrifter eller byggesøknader. Systemet finner relevante avsnitt i dokumentene og genererer et svar ved hjelp av en språkmodell fra NTNUs IDUN-infrastruktur.

Brukere kan organisere samtalene sine i prosjekter, og all historikk lagres automatisk.

**Teknologi:** FastAPI · SQLite · FAISS · React · NTNU IDUN (LLM)

### Oppsett med NTNU API
```
1. installer requirements: pip install -r requirements.txt
2. Legg til NTNU_API_KEY og NTNU_BASE_URL i .env (se .env_example)
3. Legg PDF-filer i data/
4. python -m src.ingest.build_index
5. Kjøre backend: Først bytt til backend mappe med "cd /Backend"
så kjør backenden med:
uvicorn src.api.main:app --reload
eller
py -m uvicorn src.api.main:app --reload
6. Kjøre frontend: Last ned og kjør frontend med "cd /Frontend && npm install && npm run dev"
7. Open http://127.0.0.1:8000/docs to ask questions via the API
```
```

```

---
### Oppsett med annen API
```
1. installer requirements: pip install -r requirements.txt
2. Lag en .env fil i /Backend mappen (kopier fra .env.example) Variabel navnene trenger ikke å endres selvom du ikke bruker NTNU API.
3. Bytt ut NTNU_API_KEY og NTNU_BASE_URL med din egen leverandør. Eksempler:
OpenAI:
NTNU_API_KEY=sk-...
NTNU_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
OpenRouter:
NTNU_API_KEY=sk-or-v1-...
NTNU_BASE_URL=https://openrouter.ai/api/v1
CHAT_MODEL=anthropic/claude-3.5-sonnet
EMBED_MODEL=openai/text-embedding-3-small
Lokal Ollama (gratis, kjører på egen maskin):
NTNU_API_KEY=ollama
NTNU_BASE_URL=http://localhost:11434/v1
CHAT_MODEL=llama3.2
EMBED_MODEL=nomic-embed-text
4. Legg PDF-filer i data/
5.python -m src.ingest.build_index
(NB: Hvis du bytter EMBED_MODEL senere må du kjøre denne på nytt)
6. Kjøre backend: Først bytt til backend mappe med "cd /Backend"
så kjør backenden med:
uvicorn src.api.main:app --reload
eller
py -m uvicorn src.api.main:app --reload
7. Kjøre frontend: Last ned og kjør frontend med "cd /Frontend && npm install && npm run dev"
8. Open http://127.0.0.1:8000/docs to ask questions via the API
```
```

```

---


## Del 2 — Rhino Plugin (bygningsgenerering og terreng)

Et plugin for Rhino 8 som lar konstruksjonsstudenter visualisere bygninger i et realistisk terreng. Studenten tegner et skjelett (bounding box) i Rhino, og pluginet genererer vegger, vinduer og tak automatisk basert på en tekstbeskrivelse. En språkmodell bestemmer arkitektoniske parametere som vindusandel og veggtykkelse.

Terrenget hentes som høydedata fra Kartverket og dekkes med satellittfoto fra ESRI. Bygget plasseres automatisk på riktig høyde i terrenget.

**Teknologi:** Rhino 8 · RhinoCommon · Kartverket WMS · ESRI World Imagery · FastAPI

### Oppsett
Åpne Rhino 8 og kjør `rhino/plugin_panel.py` via **Tools → PythonScript → Run**.
Backend-serveren må kjøre for at AI-parametrene skal fungere.

---

## Krav

- Python 3.11+, Node.js 18+, Rhino 8
- NTNU IDUN API-tilgang
