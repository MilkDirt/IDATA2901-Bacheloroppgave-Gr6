# Bachelor Gruppe 6 — AI-assistert byggesaksbehandling

Dette prosjektet er en bacheloroppgave utviklet i samarbeid med Multiconsult. Målet er å bruke kunstig intelligens til å effektivisere arbeid med byggesøknader og bygningsvisualisering.

Prosjektet består av to deler som jobber sammen:

---

## Rapport

- Første utkast til teoridelen finnes i [`rapport/teori-del.md`](rapport/teori-del.md)

---

## Del 1 — RAG-system (spørsmål/svar på dokumenter)

Et nettbasert system der brukere kan logge inn og stille spørsmål til PDF-dokumenter — for eksempel lover, forskrifter eller byggesøknader. Systemet finner relevante avsnitt i dokumentene og genererer et svar ved hjelp av en språkmodell fra NTNUs IDUN-infrastruktur.

Brukere kan organisere samtalene sine i prosjekter, og all historikk lagres automatisk.

**Teknologi:** FastAPI · SQLite · FAISS · React · NTNU IDUN (LLM)

### Oppsett
```
pip install -r requirements.txt
# Legg til NTNU_API_KEY og NTNU_BASE_URL i .env (se .env_example)
# Legg PDF-filer i data/
python -m src.ingest.build_index
uvicorn src.api.main:app --reload
or
py -m uvicorn src.api.main:app --reload

6. Open http://127.0.0.1:8000/docs to ask questions via the API
```
```
cd frontend && npm install && npm run dev
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
