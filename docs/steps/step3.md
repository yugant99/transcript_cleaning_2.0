# Step 3: Embeddings-Based Semantic Analysis

## Current Status
- ✅ Base metrics calculated (19/21 fields)
- ✅ 29,568 text chunks with embeddings ready
- ⏳ Need semantic analysis for final 2 fields

## Remaining Fields to Calculate

### **Pain Mentions**
- **Method**: FAISS semantic search + targeted LLM analysis
- **Query**: "pain hurt discomfort sore ache tired stiff"
- **Process**: Find relevant chunks → Count mentions

### **Comfort Mentions** 
- **Method**: FAISS semantic search + targeted LLM analysis
- **Query**: "comfortable good pleasant relaxed better nice"
- **Process**: Find relevant chunks → Count mentions

## Implementation Strategy

### **Phase 3A: Smart Semantic Search**
```python
# Use existing embeddings
chunks = load_from_pkl('processed_data/master_transcripts.pkl')
faiss_index = load('processed_data/faiss_index.bin')

# Find relevant chunks (not entire files)
pain_chunks = semantic_search("pain discomfort", top_k=100)
comfort_chunks = semantic_search("comfortable pleasant", top_k=100)
```

### **Phase 3B: Targeted LLM Analysis**
```python
# Send ONLY relevant chunks to LLM
results = analyze_chunks_with_llm(pain_chunks + comfort_chunks)
# Cost: $2 instead of $25
# Time: 5 minutes instead of 90 minutes
```

### **Phase 3C: Results Integration**
```python
# Merge with existing metrics_output.json
final_metrics = merge_semantic_results(base_metrics, semantic_results)
# Save complete 21/21 field dataset
```

## Expected Output
**Complete dashboard dataset**: All 21 fields calculated for 176 files

## Tools Needed
- OpenRouter API (one-time semantic analysis)
- FAISS for efficient similarity search
- Existing embeddings infrastructure

## Timeline
- **Phase 3A**: 30 minutes (search implementation)
- **Phase 3B**: 5 minutes (LLM analysis)
- **Phase 3C**: 15 minutes (data integration)
- **Total**: ~1 hour to complete all metrics
