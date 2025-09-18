# API Overview

Base URL: `http://localhost:8000`

## Core
- GET / — Health message
- GET /api/patients — List of patient summaries
- GET /api/patients/{id} — Single patient summary
- GET /api/questions-analysis — File-level questions/words/turns with derived rates

## Sentiment
- GET /api/sentiment-analysis — File-level sentiment metrics
- GET /api/sentiment-examples — Example utterances by sentiment type

## Nonverbal
- GET /api/nonverbal — Per-file counts and rates of normalized nonverbal cues
- GET /api/nonverbal-examples — Example excerpts grouped by cue type

## Word Repeats
- GET /api/word-repeats — Per-file immediate repeat counts and rates
- GET /api/word-repeats-examples — Example repeated word contexts

## Disfluency
- GET /api/disfluency — Per-file disfluency counts and rates
- GET /api/disfluency-examples — Example excerpts (enhanced turns or fallback)

## Topics
- GET /api/topics-summary — Topics list and per-file topic shares/switches
- GET /api/topics-examples — Topic and transition examples

## Turn Taking (New)
- GET /api/turn-taking — Exact overlapping speech counts and engagement metrics per file
  - Overlap computed as sum of '/' occurrences per file from enhanced turn texts; fallback to processed_data/master_transcripts.pkl

## Data Dependencies
- Located under backend/outputfile/ and processed_data/ as described in checkpoints.
