# Step 5 — Full Dashboard Context and How-To

This document provides a complete, self-contained overview of the current codebase, data generation steps, APIs, and UI pages. You can start from scratch using only this file.

## Repository Layout (key parts)

- backend/
  - api/main.py — FastAPI app with all endpoints
  - calculations/
    - calculations.py — metrics extractor (DOCX → metrics_output.json)
    - nonverbal_extract.py — normalized nonverbal cues (→ enhanced_transcript_analysis_fixed.json)
    - word_repeats_extract.py — immediate repeats (→ word_repeats.json)
    - topic_extract.py — embeddings clustering + labels (→ topic_model.json)
  - outputfile/
    - metrics_output.json
    - sentiment_analysis.json
    - semantic_analysis.json
    - enhanced_transcript_analysis_fixed.json
    - word_repeats.json
    - topic_model.json
- frontend/
  - src/app/dashboard/
    - questions/page.tsx
    - sentiment/page.tsx
    - lexical/page.tsx
    - nonverbal/page.tsx
    - word-repeats/page.tsx
    - topics/page.tsx
  - src/components/ui/app-sidebar.tsx — sidebar navigation

## Environment Setup

```bash
cd /Users/yuganthareshsoni/transcript_dashboard_new
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt fastapi uvicorn[standard] textblob scikit-learn python-docx numpy
```

## Data Generation (run as needed)

Each extractor writes to backend/outputfile/ and the frontend pages rely on these JSONs.

```bash
# 1) Metrics (speaker counts, words, etc.)
python backend/calculations/calculations.py

# 2) Nonverbal cues (normalized)
python backend/calculations/nonverbal_extract.py
# Output: backend/outputfile/enhanced_transcript_analysis_fixed.json

# 3) Word repeats (immediate back-to-back repeats)
python backend/calculations/word_repeats_extract.py
# Output: backend/outputfile/word_repeats.json

# 4) Topic model (embedding clusters + TF‑IDF labels)
python backend/calculations/topic_extract.py
# Output: backend/outputfile/topic_model.json
```

## Backend — Endpoints (FastAPI)

- Patients & Core:
  - GET /api/patients
  - GET /api/patients/{id}
  - GET /api/questions-analysis
- Sentiment:
  - GET /api/sentiment-analysis
  - GET /api/sentiment-examples
- Nonverbal:
  - GET /api/nonverbal
  - GET /api/nonverbal-examples
- Word Repeats:
  - GET /api/word-repeats
  - GET /api/word-repeats-examples
- Topics:
  - GET /api/topics-summary
  - GET /api/topics-examples

- Turn Taking (new):
  - GET /api/turn-taking — overlapping speech totals per file and engagement metrics

Start the API:
```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend — Dashboard Pages

Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

Navigate to:
- /dashboard/questions — Question & answer patterns
- /dashboard/sentiment — Sentiment across files with examples
- /dashboard/lexical — Lexical metrics (4 charts + file-wise table)
- /dashboard/nonverbal — Nonverbal analysis (4 charts + table + examples)
- /dashboard/word-repeats — Immediate repeats (2 charts + table + examples)
- /dashboard/topics — Topic Explorer (4 charts + table + examples)
- /dashboard/turn-taking — Turn Taking Ratio (tables + dynamic scatter)
- /dashboard/glossary — Explanations/Glossary for all dashboard pages

All pages:
- Use multi-select filters (participant/session/condition)
- Provide legends and hover tooltips on charts
- Include file-wise tables with consistent styling

## Formulas & Definitions

- Lexical (from /api/questions-analysis):
  - Word Ratio = PLWD_words / Total_words
  - Caregiver Density = caregiver_words / caregiver_turns
  - PLWD Density = plwd_words / plwd_turns
  - Question/Word Ratio = (caregiver_q + plwd_q) / Total_words
  - Word counts exclude disfluencies and bracketed content
- Nonverbal:
  - Nonverbal Rate = Total_nonverbal_cues / Total_words × 100
  - Cues are normalized (e.g., laugh/laughing → laughter) via nonverbal_extract.py logic
- Word Repeats:
  - Immediate back-to-back repetition detection
  - Disfluencies ignored (um/uh/er/etc.)
  - Repeat Rate = Total_repeats / Total_words × 100
- Topics:
  - MiniBatchKMeans on precomputed embeddings from processed_data/master_transcripts.pkl
  - Topic labels from cluster-level TF‑IDF top terms
  - Per-file topic shares & topic switch counts (A→B)

## Troubleshooting

- Empty Nonverbal page → ensure enhanced_transcript_analysis_fixed.json exists
- Empty Word Repeats/Topics → re-run their extractors
- CORS is configured for http://localhost:3000/3001

## Notes

- processed_data/ contains embeddings and chunk metadata used by topic extractor
- No LLM calls are required; everything is computed locally

You can reproduce the full dashboard by following the steps above without any external context.
