# API Call Documentation

## Backend ↔ Frontend Connections

### Call 1: Patient Summary Data
**Backend**: `backend/api/main.py` → `get_all_patients()` endpoint  
**Frontend**: `frontend/src/app/dashboard/page.tsx` → `useEffect()` data fetching  
**Path**: `GET /api/patients`

**Purpose**: Load all patient data with complete metrics for dashboard cards and tables

---

### Data Flow:
1. **Backend Processing**: 
   - `backend/api/main.py` merges `metrics_output.json` + `semantic_analysis.json`
   - Groups by patient exactly like `02_summary.py`
   - Returns structured patient summaries

2. **Frontend Consumption**:
   - `dashboard/page.tsx` fetches from `/api/patients` 
   - Renders animated cards with patient summaries
   - Shows modal tables with complete data on card click

### API Structure:
```
GET /api/patients → List[PatientSummary]
GET /api/patients/{patient_id} → PatientSummary
```

---

## **Complete API Endpoints (Updated)**

### **Patient Overview:**
- `GET /api/patients` → All patients with summary data
- `GET /api/patients/{patient_id}` → Individual patient details

### **Questions & Answers Analysis:**
- `GET /api/questions-analysis` → Question engagement metrics per file

### **Sentiment Analysis:**
- `GET /api/sentiment-analysis` → Sentiment breakdown per file
- `GET /api/sentiment-examples` → Real conversation examples by sentiment type

### **Backend Processing:**
- **Base Metrics**: `calculations.py` → `metrics_output.json` (176 files)
- **Semantic Analysis**: `semantic_analysis.py` → `semantic_analysis.json` (176 files)  
- **Sentiment Analysis**: `sentiment_calc.py` → `sentiment_analysis.json` (29,568 chunks → 176 files)

### **Frontend Pages:**
- **Dashboard**: `/dashboard` → Patient overview with animated cards
- **Questions**: `/dashboard/questions` → Question analysis with charts and tables
- **Sentiment**: `/dashboard/sentiment` → Sentiment analysis with visualizations and examples
