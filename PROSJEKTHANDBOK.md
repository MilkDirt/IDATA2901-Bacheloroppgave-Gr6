# Prosjekthåndbok

## Formål

Dette dokumentet beskriver hvordan bachelorprosjektet er bygget opp, hvilke deler løsningen består av, og hvordan prosjektet kjøres og vedlikeholdes i dette repositoryet.

## Prosjektoversikt

Prosjektet er utviklet som en bacheloroppgave i samarbeid med Multiconsult og består av to hoveddeler:

1. **RAG-system for byggesaksbehandling**
   - Nettløsning for innlogging, prosjekter, samtaler og spørsmål/svar mot dokumenter
   - Bruker FastAPI i backend og React/Vite i frontend
2. **Rhino-plugin for terreng og bygningsgenerering**
   - Plugin for Rhino 8 som genererer terreng og bygningsgeometri med støtte fra backend

## Repository-struktur

| Mappe | Innhold |
| --- | --- |
| `Backend/` | FastAPI-applikasjon, indeksering av dokumenter, database og API-tester |
| `Frontend/` | React/Vite-klient for brukergrensesnittet |
| `rhino-plugin/` | Rhino 8-plugin for terreng- og bygningsgenerering |
| `README.md` | Kort oversikt og oppstartsinstruksjoner |

## Teknologistakk

- **Backend:** FastAPI, SQLAlchemy, SQLite, FAISS, OpenAI-kompatibelt NTNU IDUN-endepunkt
- **Frontend:** React, Vite, React Router
- **Plugin:** Rhino 8, RhinoCommon / IronPython
- **Eksterne tjenester:** Kartverket, ESRI World Imagery, NTNU IDUN

## Krav

- Python 3.11 eller nyere
- Node.js 18 eller nyere
- Rhino 8
- Tilgang til NTNU IDUN (`NTNU_API_KEY` og `NTNU_BASE_URL`)

## Oppsett og kjøring

### Backend

```bash
cd Backend
pip install -r requirements.txt
python -m src.ingest.build_index
uvicorn src.api.main:app --reload
```

Opprett en `.env`-fil basert på `.env.example` og legg inn nødvendige NTNU-variabler før oppstart.

### Frontend

```bash
cd Frontend
npm ci
npm run dev
```

### Rhino-plugin

Åpne Rhino 8 og kjør `plugin_panel.py` fra `rhino-plugin/src/main/` via **Tools → PythonScript → Run**. Backend må være startet dersom AI-parametere skal brukes.

## Kvalitetssikring

Følgende kommandoer brukes i repositoryet for lokal verifisering:

### Backend

```bash
cd Backend
python -m pytest
```

### Frontend

```bash
cd Frontend
npm run lint
npm run build
```

## Dokumentasjon

- `README.md` gir en kort introduksjon til hele prosjektet
- `rhino-plugin/README.md` beskriver pluginet og arbeidsflyten i Rhino
- Denne håndboken fungerer som samlet oversikt for struktur, oppsett og vedlikehold
