# API Call Documentation - Questions & Answers Analysis

## Backend ↔ Frontend Connection

### Call 2: Questions Analysis Data
**Backend**: `backend/api/main.py` → `get_questions_analysis()` endpoint  
**Frontend**: `frontend/src/app/dashboard/questions/page.tsx` → `useEffect()` data fetching  
**Path**: `GET /api/questions-analysis`

**Purpose**: Load question analysis data for interactive visualizations and detailed tables

---

### Data Flow:
1. **Backend Processing**: 
   - Merges `metrics_output.json` + `semantic_analysis.json`
   - Calculates question rates per 100 words
   - Computes caregiver vs PLWD engagement ratios
   - Returns structured question analysis data

2. **Frontend Consumption**:
   - `questions/page.tsx` fetches from `/api/questions-analysis`
   - Renders line chart showing question trends over time
   - Displays radar chart for multi-dimensional analysis
   - Shows detailed tables with file-wise breakdowns

### API Structure:
```typescript
GET /api/questions-analysis → List[QuestionAnalysisData]

interface QuestionAnalysisData {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_turns: number
  plwd_turns: number
  caregiver_words: number
  plwd_words: number
  caregiver_questions: number
  plwd_questions: number
  total_questions: number
  caregiver_question_rate: number    // Questions per 100 words
  plwd_question_rate: number         // Questions per 100 words  
  overall_question_rate: number      // Total questions per 100 words
  answer_ratio: number               // PLWD questions / total questions
}
```

### Response Example:
```json
[
  {
    "patient_id": "VR001",
    "week_label": "Week 1",
    "session_type": "Exposure on Own",
    "condition": "VR",
    "filename": "vr001_EP1_clean.docx",
    "caregiver_turns": 45,
    "plwd_turns": 38,
    "caregiver_words": 892,
    "plwd_words": 456,
    "caregiver_questions": 12,
    "plwd_questions": 8,
    "total_questions": 20,
    "caregiver_question_rate": 1.35,
    "plwd_question_rate": 1.75,
    "overall_question_rate": 1.48,
    "answer_ratio": 0.4
  }
]
```

### Key Metrics:
- **Question Rates**: Questions per 100 words (normalized for comparison)
- **Answer Ratio**: Proportion of questions asked by PLWD vs caregiver
- **Engagement Patterns**: Turn-taking and interaction analysis
- **Temporal Trends**: Changes across weeks and sessions
