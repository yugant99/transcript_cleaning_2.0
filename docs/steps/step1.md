# Step 1: DOCX to Dashboard Processing Pipeline

## Overview
Transform 176 transcript DOCX files into an interactive dashboard with 14 analysis pages.

## Processing Flow

### Phase 1: Data Extraction (5 minutes)
```python
# 1. Parse all DOCX files
for file in all_docx_files:
    text = extract_docx_content(file)
    chunks = split_into_sentences(text)
    metadata = extract_file_info(file)  # participant, session_type, etc.
```

### Phase 2: Embeddings Creation (3 minutes)
```python
# 2. Create vector embeddings for semantic search
model = SentenceTransformer('all-MiniLM-L6-v2')  # Local, fast
embeddings = model.encode(all_text_chunks)
faiss_index = faiss.IndexFlatIP(384)
faiss_index.add(embeddings)
```

### Phase 3: Pre-compute Basic Metrics (2 minutes)
```python
# 3. Extract rule-based metrics (no LLM needed)
metrics = {
    "turn_taking": count_speaker_changes(text),
    "word_counts": analyze_vocabulary(text),
    "questions": extract_question_patterns(text),
    "disfluencies": detect_speech_patterns(text),
    "nonverbal_cues": extract_annotations(text)
}
```

### Phase 4: Master File Creation (1 minute)
```python
# 4. Save everything for instant dashboard loading
master_data = {
    "embeddings": embeddings_array,
    "faiss_index": search_index,
    "metadata": file_metadata,
    "metrics": pre_computed_metrics,
    "text_chunks": all_text_chunks
}
pickle.save(master_data, "processed_transcripts.pkl")
```

### Phase 5: Dashboard Runtime (Real-time)
```python
# 5. Dashboard queries
data = load_master_data()  # Instant loading

# Filter by participant/session (instant)
filtered = filter_data(participant="vr001", session="baseline")

# Semantic search (milliseconds)
results = faiss_search(query_embedding, top_k=10)

# LLM analysis (only when needed, 2-3 seconds)
insights = llm_analyze(relevant_chunks)
```

## Dashboard Pages

### Instant Loading (Pre-computed):
1. Overall Summary
2. Turn-Taking and Engagement Analysis  
3. Word Repeats Analysis
4. Lexical Diversity Analysis
5. Questions & Answers Analysis
6. Disfluency Analysis

### LLM-Powered (On-demand):
7. Caregiver-PLWD Interaction Analysis
8. Sentiment Analysis
9. Nonverbal Communication Analysis
10. Memory Analysis
11. VR Experience Analysis
12. Topic Explorer
13. Custom Query
14. Total View (combined insights)

## Key Benefits
- **Fast**: 10 minutes total processing, then instant queries
- **Cost-effective**: LLM only for complex analysis
- **Interactive**: Real-time filtering by participant/session/condition
- **Scalable**: Easy to add more files or metrics

## File Structure After Processing
```
processed_data/
├── master_transcripts.pkl     # All embeddings + metrics
├── faiss_index.bin           # Search index
└── metadata.json             # File mappings
```

## Next Steps
- Implement Phase 1: DOCX extraction script
- Test embedding creation on sample files
- Build basic dashboard framework