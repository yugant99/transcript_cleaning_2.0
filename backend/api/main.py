#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import re
import pickle
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI(title="NLP Analysis API", version="1.0.0")

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientData(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_turns: int
    plwd_turns: int
    caregiver_words: int
    plwd_words: int
    caregiver_sentences: int
    plwd_sentences: int
    plwd_nonverbal: int
    caregiver_nonverbal: int
    caregiver_questions: int
    plwd_questions: int
    caregiver_disfluencies: int
    plwd_disfluencies: int
    avg_words_per_turn: float
    caregiver_words_per_utterance: float
    plwd_words_per_utterance: float
    pain_mentions: int = 0
    comfort_mentions: int = 0

class PatientSummary(BaseModel):
    patient_id: str
    total_sessions: int
    total_weeks: int
    ep_sessions: int
    er_sessions: int
    total_words: int
    data: List[PatientData]

class QuestionAnalysisData(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_turns: int
    plwd_turns: int
    caregiver_words: int
    plwd_words: int
    caregiver_questions: int
    plwd_questions: int
    total_questions: int
    caregiver_question_rate: float
    plwd_question_rate: float
    overall_question_rate: float
    answer_ratio: float

class SentimentAnalysisData(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    positive: int
    negative: int
    neutral: int
    total_chunks: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_polarity: float
    avg_confidence: float
    net_sentiment: int

class SentimentExample(BaseModel):
    text: str
    confidence: float
    speaker: str
    filename: str
    patient_id: str

class NonverbalRecord(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_nonverbal: int
    plwd_nonverbal: int
    total_nonverbal: int
    total_words: int
    nonverbal_rate: float
    cue_counts: Dict[str, int]

class NonverbalExample(BaseModel):
    cue_type: str
    text: str
    speaker: str
    filename: str
    patient_id: str
    week_label: str
    session_type: str
    condition: str

class WordRepeatRecord(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_repeats: int
    plwd_repeats: int
    total_repeats: int
    total_words: int
    repeat_rate: float
    by_word: Dict[str, int]

class WordRepeatExample(BaseModel):
    word: str
    context: str
    speaker: str
    filename: str
    patient_id: str
    week_label: str
    session_type: str
    condition: str

class TopicFileRow(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    top_topics: List[int]
    topic_share: Dict[str, float]
    total_chunks: int
    switch_count: int

class TopicSummary(BaseModel):
    topics: List[Dict[str, Any]]

class DisfluencyRecord(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_disfluencies: int
    plwd_disfluencies: int
    total_disfluencies: int
    total_words: int
    disfluency_rate: float

class DisfluencyExample(BaseModel):
    disfluency_type: str
    text: str
    speaker: str
    filename: str
    patient_id: str
    week_label: str
    session_type: str
    condition: str

class TurnTakingRecord(BaseModel):
    patient_id: str
    week_label: str
    session_type: str
    condition: str
    filename: str
    caregiver_turns: int
    plwd_turns: int
    caregiver_words: int
    plwd_words: int
    overlapping_speech: int
    turn_diff: int
    word_diff: int
    dominance_ratio: float

def load_metrics_data():
    """Load metrics from calculations output"""
    metrics_path = os.path.join(os.path.dirname(__file__), "../outputfile/metrics_output.json")
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metrics data not found")

def load_semantic_data():
    """Load semantic analysis data"""
    semantic_path = os.path.join(os.path.dirname(__file__), "../outputfile/semantic_analysis.json")
    try:
        with open(semantic_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_sentiment_data():
    """Load sentiment analysis data"""
    sentiment_path = os.path.join(os.path.dirname(__file__), "../outputfile/sentiment_analysis.json")
    try:
        with open(sentiment_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sentiment data not found")

def load_enhanced_fixed_nonverbal():
    """Load normalized nonverbal data produced by fix_nonverbal_cues.py.
    Searches common locations and returns the JSON dict or {} if not found.
    """
    candidates = [
        os.path.join(os.path.dirname(__file__), "../outputfile/enhanced_transcript_analysis_fixed.json"),
        os.path.join(os.path.dirname(__file__), "../outputfile/enhanced_transcript_analysis.json"),
        os.path.join(os.path.dirname(__file__), "../../enhanced_transcript_analysis_fixed.json"),
        os.path.join(os.path.dirname(__file__), "../../enhanced_transcript_analysis.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

def load_enhanced_turns_any():
    """Load enhanced turn-level JSON if available for examples (nonverbal/disfluency).
    Returns dict or {}.
    """
    candidates = [
        os.path.join(os.path.dirname(__file__), "../outputfile/enhanced_transcript_analysis_fixed.json"),
        os.path.join(os.path.dirname(__file__), "../outputfile/enhanced_transcript_analysis.json"),
        os.path.join(os.path.dirname(__file__), "../../enhanced_transcript_analysis_fixed.json"),
        os.path.join(os.path.dirname(__file__), "../../enhanced_transcript_analysis.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

def load_processed_master() -> Dict[str, Any]:
    """Load processed_data/master_transcripts.pkl if available."""
    base_dir = os.path.join(os.path.dirname(__file__), "../../processed_data")
    pkl_path = os.path.join(base_dir, "master_transcripts.pkl")
    if os.path.exists(pkl_path):
        try:
            with open(pkl_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return {}
    return {}

def load_word_repeats_json():
    candidates = [
        os.path.join(os.path.dirname(__file__), "../outputfile/word_repeats.json"),
        os.path.join(os.path.dirname(__file__), "../../word_repeats.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

def load_topic_model_json():
    candidates = [
        os.path.join(os.path.dirname(__file__), "../outputfile/topic_model.json"),
        os.path.join(os.path.dirname(__file__), "../../topic_model.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

def load_enhanced_questions():
    """Optionally load enhanced question counts derived from turn-level annotations.
    Expected structure (flexible):
    {
      "by_file": {
        "<filename>": { "turns": [{"speaker": "caregiver"|"plwd", "is_question": true|false}, ...] }
      }
    }
    Returns mapping: { filename: {"caregiver_questions": int, "plwd_questions": int} }
    """
    enhanced_path = os.path.join(os.path.dirname(__file__), "../outputfile/enhanced_transcript_analysis.json")
    if not os.path.exists(enhanced_path):
        return {}
    try:
        with open(enhanced_path, 'r') as f:
            data = json.load(f)
        result = {}
        by_file = data.get('by_file') if isinstance(data, dict) else None
        if isinstance(by_file, dict):
            for fname, file_data in by_file.items():
                turns = file_data.get('turns', []) if isinstance(file_data, dict) else []
                c_q = 0
                p_q = 0
                for t in turns:
                    if not isinstance(t, dict):
                        continue
                    if t.get('is_question'):
                        speaker = str(t.get('speaker', '')).lower()
                        if speaker == 'caregiver':
                            c_q += 1
                        elif speaker == 'plwd':
                            p_q += 1
                result[fname] = {"caregiver_questions": c_q, "plwd_questions": p_q}
        return result
    except Exception:
        # Fail silently; fall back to baseline counts
        return {}

def merge_data():
    """Merge metrics and semantic data exactly like 02_summary.py"""
    metrics_data = load_metrics_data()
    semantic_data = load_semantic_data()
    
    # Create lookup for semantic data
    semantic_lookup = {item['filename']: item for item in semantic_data}
    
    # Merge data
    merged_data = []
    for metric in metrics_data:
        semantic = semantic_lookup.get(metric['filename'], {})
        
        merged_record = PatientData(
            patient_id=metric['patient_id'],
            week_label=metric['week_label'],
            session_type=metric['session_type'],
            condition=metric['condition'],
            filename=metric['filename'],
            caregiver_turns=metric['caregiver_turns'],
            plwd_turns=metric['plwd_turns'],
            caregiver_words=metric['caregiver_words'],
            plwd_words=metric['plwd_words'],
            caregiver_sentences=metric['caregiver_sentences'],
            plwd_sentences=metric['plwd_sentences'],
            plwd_nonverbal=metric['plwd_nonverbal'],
            caregiver_nonverbal=metric['caregiver_nonverbal'],
            caregiver_questions=metric['caregiver_questions'],
            plwd_questions=metric['plwd_questions'],
            caregiver_disfluencies=metric['caregiver_disfluencies'],
            plwd_disfluencies=metric['plwd_disfluencies'],
            avg_words_per_turn=metric['avg_words_per_turn'],
            caregiver_words_per_utterance=metric['caregiver_words_per_utterance'],
            plwd_words_per_utterance=metric['plwd_words_per_utterance'],
            pain_mentions=semantic.get('pain_mentions', 0),
            comfort_mentions=semantic.get('comfort_mentions', 0)
        )
        merged_data.append(merged_record)
    
    return merged_data

def group_by_patient(data: List[PatientData]) -> List[PatientSummary]:
    """Group data by patient exactly like 02_summary.py"""
    patient_groups = {}
    
    for record in data:
        patient_id = record.patient_id
        if patient_id not in patient_groups:
            patient_groups[patient_id] = []
        patient_groups[patient_id].append(record)
    
    # Create patient summaries
    summaries = []
    for patient_id, records in patient_groups.items():
        # Calculate unique weeks
        weeks = set()
        ep_count = 0
        er_count = 0
        total_words = 0
        
        for record in records:
            # Extract week number from week_label
            if record.week_label.startswith("Week"):
                try:
                    week_num = int(record.week_label.split()[1])
                    weeks.add(week_num)
                except:
                    pass
            
            if record.session_type == 'EP':
                ep_count += 1
            elif record.session_type == 'ER':
                er_count += 1
                
            total_words += record.caregiver_words + record.plwd_words
        
        # Sort records by week
        records.sort(key=lambda x: x.week_label)
        
        summary = PatientSummary(
            patient_id=patient_id,
            total_sessions=len(records),
            total_weeks=len(weeks),
            ep_sessions=ep_count,
            er_sessions=er_count,
            total_words=total_words,
            data=records
        )
        summaries.append(summary)
    
    # Sort by patient_id
    summaries.sort(key=lambda x: x.patient_id)
    return summaries

def build_filename_metadata_lookup(metrics: List[PatientData]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for m in metrics:
        lookup[m.filename] = {
            'patient_id': m.patient_id,
            'week_label': m.week_label,
            'session_type': m.session_type,
            'condition': m.condition,
        }
    return lookup

@app.get("/")
async def root():
    return {"message": "NLP Analysis API is running"}

@app.get("/api/patients", response_model=List[PatientSummary])
async def get_all_patients():
    """Get all patients with their complete data - matches 02_summary.py structure"""
    try:
        merged_data = merge_data()
        patient_summaries = group_by_patient(merged_data)
        return patient_summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/api/patients/{patient_id}", response_model=PatientSummary)
async def get_patient(patient_id: str):
    """Get specific patient data"""
    try:
        merged_data = merge_data()
        patient_data = [record for record in merged_data if record.patient_id == patient_id]
        
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_summaries = group_by_patient(patient_data)
        return patient_summaries[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/api/questions-analysis", response_model=List[QuestionAnalysisData])
async def get_questions_analysis():
    """Get questions and answers analysis data for all files"""
    try:
        merged_data = merge_data()
        
        qa_analysis = []
        enhanced_q = load_enhanced_questions()
        for record in merged_data:
            # Optionally override question counts with enhanced file if present
            caregiver_q = record.caregiver_questions
            plwd_q = record.plwd_questions
            override = enhanced_q.get(record.filename)
            if override:
                caregiver_q = override.get('caregiver_questions', caregiver_q)
                plwd_q = override.get('plwd_questions', plwd_q)

            total_questions = caregiver_q + plwd_q
            total_words = record.caregiver_words + record.plwd_words
            
            caregiver_question_rate = (caregiver_q / (record.caregiver_words + 1e-9)) * 100
            plwd_question_rate = (plwd_q / (record.plwd_words + 1e-9)) * 100
            overall_question_rate = (total_questions / (total_words + 1e-9)) * 100
            
            answer_ratio = plwd_q / total_questions if total_questions > 0 else 0.5
            
            qa_record = QuestionAnalysisData(
                patient_id=record.patient_id,
                week_label=record.week_label,
                session_type=record.session_type,
                condition=record.condition,
                filename=record.filename,
                caregiver_turns=record.caregiver_turns,
                plwd_turns=record.plwd_turns,
                caregiver_words=record.caregiver_words,
                plwd_words=record.plwd_words,
                caregiver_questions=caregiver_q,
                plwd_questions=plwd_q,
                total_questions=total_questions,
                caregiver_question_rate=round(caregiver_question_rate, 2),
                plwd_question_rate=round(plwd_question_rate, 2),
                overall_question_rate=round(overall_question_rate, 2),
                answer_ratio=round(answer_ratio, 3)
            )
            qa_analysis.append(qa_record)
        
        qa_analysis.sort(key=lambda x: (x.patient_id, x.week_label))
        return qa_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing questions analysis: {str(e)}")

@app.get("/api/sentiment-analysis", response_model=List[SentimentAnalysisData])
async def get_sentiment_analysis():
    """Get sentiment analysis data for all files"""
    try:
        sentiment_data = load_sentiment_data()
        file_sentiment = sentiment_data.get('file_sentiment_summary', {})
        
        sentiment_analysis = []
        for filename, data in file_sentiment.items():
            metadata = data['metadata']
            
            sentiment_record = SentimentAnalysisData(
                patient_id=metadata['patient_id'],
                week_label=metadata['week_label'],
                session_type=metadata['session_type'],
                condition=metadata['condition'],
                filename=metadata['filename'],
                positive=data['positive'],
                negative=data['negative'],
                neutral=data['neutral'],
                total_chunks=data['total_chunks'],
                positive_pct=data['positive_pct'],
                negative_pct=data['negative_pct'],
                neutral_pct=data['neutral_pct'],
                avg_polarity=data['avg_polarity'],
                avg_confidence=data['avg_confidence'],
                net_sentiment=data['net_sentiment']
            )
            sentiment_analysis.append(sentiment_record)
        
        sentiment_analysis.sort(key=lambda x: (x.patient_id, x.week_label))
        return sentiment_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing sentiment analysis: {str(e)}")

@app.get("/api/sentiment-examples", response_model=Dict[str, List[SentimentExample]])
async def get_sentiment_examples():
    """Get sentiment examples for each sentiment type"""
    try:
        sentiment_data = load_sentiment_data()
        examples = sentiment_data.get('sentiment_examples', {})
        
        formatted_examples = {}
        for sentiment_type, example_list in examples.items():
            formatted_examples[sentiment_type] = [
                SentimentExample(
                    text=ex['text'],
                    confidence=ex['confidence'],
                    speaker=ex['speaker'],
                    filename=ex['filename'],
                    patient_id=ex['patient_id']
                ) for ex in example_list[:50]  # Limit to 50 examples per type
            ]
        
        return formatted_examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing sentiment examples: {str(e)}")

@app.get("/api/nonverbal", response_model=List[NonverbalRecord])
async def get_nonverbal_summary():
    """Compute per-file nonverbal stats using normalized cues and metrics words."""
    try:
        # Load base metrics and metadata
        merged = merge_data()
        filename_meta = build_filename_metadata_lookup(merged)

        # Map total words per file
        words_by_file: Dict[str, int] = {}
        for m in merged:
            words_by_file[m.filename] = m.caregiver_words + m.plwd_words

        # Load normalized nonverbal data
        enhanced = load_enhanced_fixed_nonverbal()
        by_file = enhanced.get('by_file', {}) if isinstance(enhanced, dict) else {}

        records: List[NonverbalRecord] = []
        for fname, file_data in by_file.items():
            turns = file_data.get('turns', []) if isinstance(file_data, dict) else []
            caregiver_count = 0
            plwd_count = 0
            cue_counts: Dict[str, int] = {}
            for t in turns:
                if not isinstance(t, dict):
                    continue
                cues = t.get('nonverbal_cues', []) or []  # already normalized by fixer
                speaker = str(t.get('speaker', '')).lower()
                for cue in cues:
                    cue_norm = str(cue).lower()
                    cue_counts[cue_norm] = cue_counts.get(cue_norm, 0) + 1
                    if speaker == 'caregiver':
                        caregiver_count += 1
                    elif speaker == 'plwd':
                        plwd_count += 1

            meta = filename_meta.get(fname)
            if not meta:
                # Skip files without metrics (no words -> cannot compute rate reliably)
                continue
            total_words = words_by_file.get(fname, 0)
            total_nonverbal = caregiver_count + plwd_count
            rate = (total_nonverbal / (total_words + 1e-9)) * 100.0

            records.append(NonverbalRecord(
                patient_id=meta['patient_id'],
                week_label=meta['week_label'],
                session_type=meta['session_type'],
                condition=meta['condition'],
                filename=fname,
                caregiver_nonverbal=caregiver_count,
                plwd_nonverbal=plwd_count,
                total_nonverbal=total_nonverbal,
                total_words=total_words,
                nonverbal_rate=round(rate, 2),
                cue_counts=cue_counts,
            ))

        records.sort(key=lambda x: (x.patient_id, x.week_label))
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing nonverbal summary: {str(e)}")

@app.get("/api/nonverbal-examples", response_model=Dict[str, List[NonverbalExample]])
async def get_nonverbal_examples():
    """Return examples per cue type, limited per type."""
    try:
        merged = merge_data()
        filename_meta = build_filename_metadata_lookup(merged)
        enhanced = load_enhanced_fixed_nonverbal()
        by_file = enhanced.get('by_file', {}) if isinstance(enhanced, dict) else {}

        examples: Dict[str, List[NonverbalExample]] = {}
        for fname, file_data in by_file.items():
            turns = file_data.get('turns', []) if isinstance(file_data, dict) else []
            meta = filename_meta.get(fname)
            if not meta:
                continue
            for t in turns:
                if not isinstance(t, dict):
                    continue
                cues = t.get('nonverbal_cues', []) or []
                text = t.get('text', '') or ''
                speaker = str(t.get('speaker', '')).lower() or 'unknown'
                for cue in cues:
                    cue_norm = str(cue).lower()
                    lst = examples.setdefault(cue_norm, [])
                    if len(lst) >= 50:
                        continue
                    lst.append(NonverbalExample(
                        cue_type=cue_norm,
                        text=text[:300],
                        speaker=speaker,
                        filename=fname,
                        patient_id=meta['patient_id'],
                        week_label=meta['week_label'],
                        session_type=meta['session_type'],
                        condition=meta['condition'],
                    ))

        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing nonverbal examples: {str(e)}")

@app.get("/api/word-repeats", response_model=List[WordRepeatRecord])
async def get_word_repeats():
    try:
        merged = merge_data()
        words_by_file = {m.filename: m.caregiver_words + m.plwd_words for m in merged}
        meta_lookup = build_filename_metadata_lookup(merged)
        wr = load_word_repeats_json()
        by_file = wr.get('by_file', {}) if isinstance(wr, dict) else {}
        records: List[WordRepeatRecord] = []
        for fname, file_data in by_file.items():
            stats = (file_data or {}).get('stats', {}).get('repeats', {})
            caregiver_total = int(stats.get('caregiver_total', 0))
            plwd_total = int(stats.get('plwd_total', 0))
            by_word = stats.get('by_word', {})
            meta = meta_lookup.get(fname)
            if not meta:
                continue
            total_words = int(words_by_file.get(fname, 0))
            total_repeats = caregiver_total + plwd_total
            rate = (total_repeats / (total_words + 1e-9)) * 100.0
            records.append(WordRepeatRecord(
                patient_id=meta['patient_id'],
                week_label=meta['week_label'],
                session_type=meta['session_type'],
                condition=meta['condition'],
                filename=fname,
                caregiver_repeats=caregiver_total,
                plwd_repeats=plwd_total,
                total_repeats=total_repeats,
                total_words=total_words,
                repeat_rate=round(rate, 2),
                by_word=by_word,
            ))
        records.sort(key=lambda x: (x.patient_id, x.week_label))
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing word repeats: {str(e)}")

@app.get("/api/word-repeats-examples", response_model=List[WordRepeatExample])
async def get_word_repeats_examples():
    try:
        merged = merge_data()
        meta_lookup = build_filename_metadata_lookup(merged)
        wr = load_word_repeats_json()
        by_file = wr.get('by_file', {}) if isinstance(wr, dict) else {}
        out: List[WordRepeatExample] = []
        for fname, file_data in by_file.items():
            turns = (file_data or {}).get('turns', [])
            meta = meta_lookup.get(fname)
            if not meta:
                continue
            for t in turns:
                repeats = t.get('repeats', []) or []
                for r in repeats[:3]:  # limit examples per turn
                    out.append(WordRepeatExample(
                        word=r.get('word', ''),
                        context=r.get('context', ''),
                        speaker=t.get('speaker', 'unknown'),
                        filename=fname,
                        patient_id=meta['patient_id'],
                        week_label=meta['week_label'],
                        session_type=meta['session_type'],
                        condition=meta['condition'],
                    ))
        return out[:500]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing word repeats examples: {str(e)}")

@app.get("/api/disfluency", response_model=List[DisfluencyRecord])
async def get_disfluency_summary():
    """Compute per-file disfluency stats from metrics words and counts."""
    try:
        merged = merge_data()
        records: List[DisfluencyRecord] = []
        for m in merged:
            total_words = m.caregiver_words + m.plwd_words
            total_disf = (m.caregiver_disfluencies or 0) + (m.plwd_disfluencies or 0)
            rate = (total_disf / (total_words + 1e-9)) * 100.0
            records.append(DisfluencyRecord(
                patient_id=m.patient_id,
                week_label=m.week_label,
                session_type=m.session_type,
                condition=m.condition,
                filename=m.filename,
                caregiver_disfluencies=m.caregiver_disfluencies,
                plwd_disfluencies=m.plwd_disfluencies,
                total_disfluencies=total_disf,
                total_words=total_words,
                disfluency_rate=round(rate, 2),
            ))
        records.sort(key=lambda x: (x.patient_id, x.week_label))
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing disfluency summary: {str(e)}")

@app.get("/api/disfluency-examples", response_model=List[DisfluencyExample])
async def get_disfluency_examples():
    """Return disfluency examples using enhanced turn-level data if present.
    Falls back to empty list if not available.
    """
    try:
        merged = merge_data()
        meta_lookup = build_filename_metadata_lookup(merged)
        enhanced = load_enhanced_turns_any()
        by_file = enhanced.get('by_file', {}) if isinstance(enhanced, dict) else {}
        out: List[DisfluencyExample] = []
        # First try enhanced turns if present
        for fname, file_data in by_file.items():
            turns = (file_data or {}).get('turns', [])
            meta = meta_lookup.get(fname)
            if not meta:
                continue
            for t in turns:
                disfs = t.get('disfluencies', []) or []
                if not disfs:
                    continue
                speaker = str(t.get('speaker', 'unknown')).lower() or 'unknown'
                text = t.get('text', '') or ''
                for d in disfs[:3]:
                    out.append(DisfluencyExample(
                        disfluency_type=str(d.get('type', 'unknown')),
                        text=text[:300],
                        speaker=speaker,
                        filename=fname,
                        patient_id=meta['patient_id'],
                        week_label=meta['week_label'],
                        session_type=meta['session_type'],
                        condition=meta['condition'],
                    ))
        if out:
            return out[:500]

        # Fallback: scan processed_data chunks for filled pauses
        master = load_processed_master()
        chunk_meta_list = master.get('chunk_metadata', []) if isinstance(master, dict) else []
        filled_pause_pattern = re.compile(r"\b(um|umm|uh|uhh|uhhh|er|err|erm|ah|ahh|hm|hmm|mhm|mm|mmm|eh|ehm|em)\b", re.IGNORECASE)
        for cm in chunk_meta_list:
            try:
                file_meta = cm.get('file_metadata', {})
                fname = file_meta.get('filename')
                if not fname:
                    continue
                meta = meta_lookup.get(fname)
                if not meta:
                    continue
                text = cm.get('chunk_text', '') or ''
                if not text:
                    continue
                if not filled_pause_pattern.search(text):
                    continue
                # crude speaker heuristic
                lower = text.lower()
                speaker = 'caregiver' if '_c:' in lower else 'plwd' if '_p:' in lower else 'unknown'
                out.append(DisfluencyExample(
                    disfluency_type='filled_pause',
                    text=text[:300],
                    speaker=speaker,
                    filename=fname,
                    patient_id=meta['patient_id'],
                    week_label=meta['week_label'],
                    session_type=meta['session_type'],
                    condition=meta['condition'],
                ))
                if len(out) >= 500:
                    break
            except Exception:
                continue
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing disfluency examples: {str(e)}")

@app.get("/api/topics-summary", response_model=Dict[str, Any])
async def get_topics_summary():
    try:
        tm = load_topic_model_json()
        topics = tm.get('topics', [])
        by_file = tm.get('by_file', {})
        rows: List[TopicFileRow] = []
        for fname, data in by_file.items():
            meta = data.get('metadata', {})
            topic_share = data.get('topic_share', {})
            top_topics = data.get('top_topics', [])
            switch_count = sum((data.get('switch_counts', {}) or {}).values())
            total_chunks = sum((data.get('topic_counts', {}) or {}).values())
            rows.append(TopicFileRow(
                patient_id=meta.get('patient_id', ''),
                week_label=meta.get('week_label', ''),
                session_type=meta.get('session_type', ''),
                condition=meta.get('condition', ''),
                filename=meta.get('filename', fname),
                top_topics=top_topics,
                topic_share=topic_share,
                total_chunks=total_chunks,
                switch_count=switch_count,
            ))
        rows.sort(key=lambda x: (x.patient_id, x.week_label))
        return { 'topics': topics, 'rows': rows }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing topics summary: {str(e)}")

@app.get("/api/topics-examples", response_model=Dict[str, Any])
async def get_topics_examples():
    try:
        tm = load_topic_model_json()
        examples = tm.get('examples', {})
        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing topics examples: {str(e)}")

def _compute_overlaps_from_enhanced() -> Dict[str, Any]:
    enhanced = load_enhanced_turns_any()
    by_file = enhanced.get('by_file', {}) if isinstance(enhanced, dict) else {}
    overlaps: Dict[str, int] = {}
    for fname, file_data in by_file.items():
        turns = (file_data or {}).get('turns', [])
        total = 0
        for t in turns:
            try:
                txt = (t or {}).get('text', '') or ''
                total += txt.count('/')
            except Exception:
                continue
        overlaps[fname] = total
    return overlaps

def _compute_overlaps_from_master() -> Dict[str, int]:
    master = load_processed_master()
    chunk_meta_list = master.get('chunk_metadata', []) if isinstance(master, dict) else []
    overlaps: Dict[str, int] = {}
    for cm in chunk_meta_list:
        try:
            file_meta = cm.get('file_metadata', {}) or {}
            fname = file_meta.get('filename')
            if not fname:
                continue
            txt = (cm.get('chunk_text') or '') or ''
            if not txt:
                continue
            overlaps[fname] = overlaps.get(fname, 0) + txt.count('/')
        except Exception:
            continue
    return overlaps

def _get_overlap_map() -> Dict[str, int]:
    overlaps = _compute_overlaps_from_enhanced()
    # If enhanced not available or empty, fallback to master
    if not overlaps:
        overlaps = _compute_overlaps_from_master()
    return overlaps

@app.get("/api/turn-taking", response_model=List[TurnTakingRecord])
async def get_turn_taking():
    try:
        merged = merge_data()
        overlaps = _get_overlap_map()

        # Index by filename for quick lookup
        by_filename: Dict[str, PatientData] = {m.filename: m for m in merged}

        records: List[TurnTakingRecord] = []
        for fname, m in by_filename.items():
            # Optional: filter Final Interview on client for consistency with other pages
            overlap = int(overlaps.get(fname, 0))
            turn_diff = int(m.caregiver_turns) - int(m.plwd_turns)
            word_diff = int(m.caregiver_words) - int(m.plwd_words)
            dominance = float(m.caregiver_turns / (m.plwd_turns + 1e-9))
            records.append(TurnTakingRecord(
                patient_id=m.patient_id,
                week_label=m.week_label,
                session_type=m.session_type,
                condition=m.condition,
                filename=m.filename,
                caregiver_turns=m.caregiver_turns,
                plwd_turns=m.plwd_turns,
                caregiver_words=m.caregiver_words,
                plwd_words=m.plwd_words,
                overlapping_speech=overlap,
                turn_diff=turn_diff,
                word_diff=word_diff,
                dominance_ratio=round(dominance, 3),
            ))

        records.sort(key=lambda x: (x.patient_id, x.week_label))
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing turn taking: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
