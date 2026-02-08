# IDATA2901-Bacheloroppgave-Gr6

First part of this project is a Retrieval-Augmented Generation (RAG) system for answering questions based on PDF documents.

Requirements:
- Python 3.11 or newer
- NTNU IDUN API access (API key)

How to Setup and run (PowerShell):

1. Install dependencies:
pip install -r requirements.txt

2. Create a `.env` file in the project root (see `.env_example`) and add:
NTNU_API_KEY=sk-...
NTNU_BASE_URL=https://llm.hpc.ntnu.no/v1

3. Place PDF documents in the `data/` folder

4. Build the vector index:
python -m src.ingest.build_index

5. Start the API:
uvicorn src.api.main:app --reload

6. Open http://127.0.0.1:8000/docs to ask questions via the API
