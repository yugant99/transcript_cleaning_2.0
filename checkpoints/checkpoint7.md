# Checkpoint 7: Lexical, Nonverbal, Word Repeats, Topic Explorer Completed

## Major Additions Since Checkpoint 6

### New Frontend Pages
- frontend/src/app/dashboard/lexical/page.tsx — Lexical Diversity (4 charts + file-wise table)
- frontend/src/app/dashboard/nonverbal/page.tsx — Non Verbal Analysis (4 charts + examples + table)
- frontend/src/app/dashboard/word-repeats/page.tsx — Word Repeats (2 charts + examples + table)
- frontend/src/app/dashboard/topics/page.tsx — Topic Explorer (4 charts + examples + table)
- Sidebar updated in frontend/src/components/ui/app-sidebar.tsx to include all pages

### New Backend Extractors (Data Generators)
- backend/calculations/nonverbal_extract.py → backend/outputfile/enhanced_transcript_analysis_fixed.json
  - Parses DOCX turns, normalizes nonverbal cues, aggregates per file
- backend/calculations/word_repeats_extract.py → backend/outputfile/word_repeats.json
  - Detects immediate word repetitions (excludes disfluency markers), aggregates per file
- backend/calculations/topic_extract.py → backend/outputfile/topic_model.json
  - Clusters embeddings (MiniBatchKMeans), labels topics via TF‑IDF, aggregates per file and topic switches

### Backend API Endpoints (FastAPI)
- Added in backend/api/main.py:
  - Nonverbal:
    - GET /api/nonverbal — per-file nonverbal stats (+rate using metrics words)
    - GET /api/nonverbal-examples — examples grouped by cue type
  - Word Repeats:
    - GET /api/word-repeats — per-file repeats + repeat rate
    - GET /api/word-repeats-examples — repeated word contexts
  - Topics:
    - GET /api/topics-summary — { topics, rows } per-file topic shares, switches
    - GET /api/topics-examples — examples by topic and by transition
  - Pre-existing:
    - Patients, Questions Analysis, Sentiment Analysis, Sentiment Examples

## Data Files Produced
- backend/outputfile/metrics_output.json (existing)
- backend/outputfile/sentiment_analysis.json (existing)
- backend/outputfile/semantic_analysis.json (existing)
- backend/outputfile/enhanced_transcript_analysis_fixed.json (new; 176 files)
- backend/outputfile/word_repeats.json (new; 176 files)
- backend/outputfile/topic_model.json (new; 15 topics, 176 files)

## Key Formulas & Logic
- Lexical (frontend, from /api/questions-analysis):
  - Word Ratio = PLWD_words / Total_words
  - Caregiver Density = caregiver_words / caregiver_turns
  - PLWD Density = plwd_words / plwd_turns
  - Question/Word Ratio = (caregiver_q + plwd_q) / Total_words
  - Word counts exclude disfluencies and bracketed content (as in calculations.py)
- Nonverbal:
  - Nonverbal Rate = Total_nonverbal_cues / Total_words × 100
  - Normalization rules from fix_nonverbal_cues.py (variations mapped to canonical cues)
- Word Repeats:
  - Immediate repeats detection (back-to-back identical words), excludes common disfluencies
  - Repeat Rate = Total_repeats / Total_words × 100
- Topics:
  - Clustering precomputed chunk embeddings (MiniBatchKMeans, k≈15)
  - Topic labels from TF‑IDF top terms; per-file topic shares and switch counts

## How to Generate & Launch

1) Environment
```bash
cd /Users/yuganthareshsoni/transcript_dashboard_new
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt fastapi uvicorn[standard] textblob scikit-learn python-docx numpy
```

2) Generate JSON outputs (run as needed)
```bash
# Metrics (if missing)
python backend/calculations/calculations.py

# Nonverbal (normalized cues)
python backend/calculations/nonverbal_extract.py

# Word repeats
python backend/calculations/word_repeats_extract.py

# Topics from embeddings
python backend/calculations/topic_extract.py
```

3) Start servers
```bash
# Backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm install
npm run dev
```

4) Navigate
- /dashboard/questions
- /dashboard/sentiment
- /dashboard/lexical
- /dashboard/nonverbal
- /dashboard/word-repeats
- /dashboard/topics

## UX Consistency
- All charts include legends + hover tooltips
- Multi-select filters (participant, session, condition)
- File-wise tables styled with borders, hover, and color accents

## Notes & Troubleshooting
- If Non Verbal page is empty, ensure enhanced_transcript_analysis_fixed.json exists in backend/outputfile/
- If Word Repeats or Topics show empty, re-run their extractors
- CORS for http://localhost:3000/3001 already configured

—
All pages now deliver end-to-end analytics backed by reproducible extractors, consistent APIs, and unified UI patterns.
