# API Call Documentation - Sentiment Analysis

## Backend ↔ Frontend Connection

### Call 3A: Sentiment Analysis Data
**Backend**: `backend/api/main.py` → `get_sentiment_analysis()` endpoint  
**Frontend**: `frontend/src/app/dashboard/sentiment/page.tsx` → `useEffect()` data fetching  
**Path**: `GET /api/sentiment-analysis`

**Purpose**: Load sentiment analysis data for trend visualization and detailed breakdown

---

### Call 3B: Sentiment Examples Data
**Backend**: `backend/api/main.py` → `get_sentiment_examples()` endpoint  
**Frontend**: `frontend/src/app/dashboard/sentiment/page.tsx` → `useEffect()` data fetching  
**Path**: `GET /api/sentiment-examples`

**Purpose**: Load real conversation examples for interactive tilted scroll cards

---

## Data Processing Pipeline:

### **Step 1: Chunk-Level Analysis**
- **Input**: 29,568 text chunks from `master_transcripts.pkl`
- **Processing**: TextBlob sentiment analysis on each chunk
- **Classification**: Positive (>0.1), Negative (<-0.1), Neutral (-0.1 to 0.1)
- **Output**: Individual chunk sentiments with confidence scores

### **Step 2: File-Level Aggregation**
- **Aggregation**: Group chunks by source file
- **Calculations**: Count positive/negative/neutral, average polarity/confidence
- **Percentages**: Calculate sentiment distribution percentages
- **Net Sentiment**: Positive count minus negative count

### **Step 3: Example Extraction**
- **Filtering**: Select high-confidence examples (>0.3 confidence)
- **Truncation**: Limit text to 200 characters for display
- **Categorization**: Group by sentiment type for tilted scroll display

---

## API Structures:

### **Sentiment Analysis Endpoint:**
```typescript
GET /api/sentiment-analysis → List[SentimentAnalysisData]

interface SentimentAnalysisData {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  positive: number              // Count of positive chunks
  negative: number              // Count of negative chunks
  neutral: number               // Count of neutral chunks
  total_chunks: number          // Total chunks in file
  positive_pct: number          // Percentage positive
  negative_pct: number          // Percentage negative
  neutral_pct: number           // Percentage neutral
  avg_polarity: number          // Average polarity (-1 to 1)
  avg_confidence: number        // Average confidence (0 to 1)
  net_sentiment: number         // positive - negative
}
```

### **Sentiment Examples Endpoint:**
```typescript
GET /api/sentiment-examples → Record<string, List[SentimentExample]>

interface SentimentExample {
  text: string                  // Conversation excerpt (truncated to 200 chars)
  confidence: number            // Sentiment confidence (0 to 1)
  speaker: string               // Speaker identification
  filename: string              // Source file
  patient_id: string            // Patient identifier
}
```

## Response Examples:

### **Sentiment Analysis Response:**
```json
[
  {
    "patient_id": "VR001",
    "week_label": "Week 1", 
    "session_type": "Exposure on Own",
    "condition": "VR",
    "filename": "vr001_EP1_clean.docx",
    "positive": 45,
    "negative": 8,
    "neutral": 67,
    "total_chunks": 120,
    "positive_pct": 37.5,
    "negative_pct": 6.7,
    "neutral_pct": 55.8,
    "avg_polarity": 0.156,
    "avg_confidence": 0.423,
    "net_sentiment": 37
  }
]
```

### **Sentiment Examples Response:**
```json
{
  "positive": [
    {
      "text": "That was really helpful, I feel much better about trying that technique.",
      "confidence": 0.789,
      "speaker": "Unknown",
      "filename": "vr001_EP1_clean.docx", 
      "patient_id": "VR001"
    }
  ],
  "negative": [
    {
      "text": "I'm really struggling with this, it's making me anxious.",
      "confidence": 0.654,
      "speaker": "Unknown",
      "filename": "vr002_ER2_clean.docx",
      "patient_id": "VR002"
    }
  ],
  "neutral": [
    {
      "text": "Let's move on to the next exercise in the session.",
      "confidence": 0.234,
      "speaker": "Unknown", 
      "filename": "vr003_EP3_clean.docx",
      "patient_id": "VR003"
    }
  ]
}
```

## Frontend Integration:

### **Data Flow:**
1. **Parallel Fetching**: Both endpoints called simultaneously via `Promise.all()`
2. **State Management**: Separate state for analysis data and examples
3. **Visualization**: Analysis data → charts, Examples data → tilted scroll cards
4. **Filtering**: All data filtered by participant/session/condition
5. **Real-time Updates**: Charts and cards update instantly on filter changes

### **Chart Data Preparation:**
- **Line Chart**: Aggregates sentiment counts by week for trend visualization
- **Radial Chart**: Totals all sentiments for overall distribution
- **Tables**: Direct display of file-level sentiment breakdowns
- **Tilted Cards**: Interactive display of real conversation examples

### **Performance Optimization:**
- **Chunked Processing**: 29,568 chunks processed in ~30 seconds (one-time)
- **API Caching**: Results cached in JSON files for instant API responses
- **Frontend Filtering**: Client-side filtering for immediate responsiveness
- **Example Limiting**: Max 50 examples per sentiment type for optimal performance
