# Bygg & Terreng Plugin — Rhino 8

Et Python basert Rhino-plugin for AI assistert 3D terreng og bygningsgenerering.
Utviklet som del av en bacheloroppgave i Dataingeniør ved NTNU Ålesund.

---

## Oversikt

Pluginet genererer realistisk 3D-terreng fra norske høydedata, legger satellittbilde over terrenget, og plasserer AI-generert bygningsgeometri direkte på terrenget. Alt kjører inne i Rhino 8 gjennom et flytende panel.

---

## Krav

- Rhino 8
- Internettilkobling (for terreng- og satellittdata)
- FastAPI-backend kjørende lokalt på `http://localhost:8000` (for AI-bygningsparametere)

---

## Teknologi

| Komponent | Teknologi |
|---|---|
| 3D-miljø | Rhino 8 / IronPython |
| Høydedata | Kartverket WCS — NHM DTM |
| Satellittbilde | ESRI World Imagery |
| AI-parametere | FastAPI + lokal LLM-backend |

---

## Hvordan kjøre

1. Åpne Rhino 8
2. Skriv `RunPythonScript` i kommandolinjen
3. Velg `plugin_panel.py` fra `main/` mappen i `src/` folder
5. Plugin-panelet åpnes og forblir aktivt for hele sesjonen

---

## Arbeidsflyt

1. **Terreng** — Skriv inn GPS-koordinater og størrelse, hent høydeterreng fra Kartverket
2. **Satellitt** — Legg satellittbilde over terrenget (bytt til *Rendered* visning)
3. **Bygg** — Velg en boks i Rhino, generer vegger, vinduer og tak via AI
4. **Plassering** — Plasser bygget på terrenget med automatisk terrengtilpasning
