#!/usr/bin/env python3
import json
import os
import re
from docx import Document
from collections import defaultdict

# Disfluencies from word_count_updater.py
DISFLUENCIES = {"um", "umm", "uh", "uhh", "uhhh", "er", "err", "erm", "ah", "ahh", "hm", "hmm", "mhm", "mm", "mmm", "eh", "ehm", "em"}

def read_docx(file_path):
    """Read content from Word document"""
    try:
        doc = Document(file_path)
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def extract_participant_id(text):
    """Extract participant ID from transcript"""
    match = re.search(r'vr(?:x)?\d+', text, re.IGNORECASE)
    return match.group(0).lower() if match else None

def extract_metadata(filename):
    """Extract metadata from filename"""
    # Session Type
    if 'EP' in filename:
        session_type = 'EP'
    elif 'ER' in filename:
        session_type = 'ER'
    elif 'baseline' in filename:
        session_type = 'baseline'
    elif 'Final Interview' in filename or 'final_interview' in filename:
        session_type = 'final_interview'
    else:
        session_type = 'unknown'
    
    # Week Label
    week_match = re.search(r'(EP|ER)(\d+)', filename)
    week_label = f"Week {week_match.group(2)}" if week_match else "Unknown"
    
    # Condition (VR vs Tablet assumption)
    condition = "VR" if 'EP' in filename else "Tablet"
    
    return session_type, week_label, condition

def clean_and_count_words(segment):
    """Clean word count excluding disfluencies and brackets"""
    segment = re.sub(r'\[.*?\]', '', segment)
    words = segment.strip().split()
    words = [w for w in words if w.lower() not in DISFLUENCIES]
    return len(words)

def count_disfluencies(segment):
    """Count disfluencies in segment"""
    words = segment.split()
    return sum(1 for w in words if w.lower() in DISFLUENCIES)

def count_sentences(segment):
    """Count sentences in segment"""
    if not segment.strip():
        return 0
    sentences = re.split(r'[.!?]+', segment.strip())
    return len([s for s in sentences if s.strip()])

def count_questions(segment):
    """Count questions in segment"""
    return segment.count('?')

def count_nonverbal_cues(segment):
    """Count nonverbal cues in brackets"""
    return len(re.findall(r'\[(.*?)\]', segment))

def analyze_transcript(file_path):
    """Analyze single transcript file"""
    content = read_docx(file_path)
    if not content:
        return None
    
    participant_id = extract_participant_id(content)
    if not participant_id:
        return None
    
    filename = os.path.basename(file_path)
    session_type, week_label, condition = extract_metadata(filename)
    
    # Extract speaker segments
    caregiver_pattern = f"{participant_id}_c:"
    plwd_pattern = f"{participant_id}_p:"
    
    caregiver_segments = re.findall(f"{caregiver_pattern}(.*?)(?={participant_id}_[cp]:|$)", content, re.DOTALL | re.IGNORECASE)
    plwd_segments = re.findall(f"{plwd_pattern}(.*?)(?={participant_id}_[cp]:|$)", content, re.DOTALL | re.IGNORECASE)
    
    # Calculate metrics
    caregiver_turns = len(caregiver_segments)
    plwd_turns = len(plwd_segments)
    
    caregiver_words = sum(clean_and_count_words(seg) for seg in caregiver_segments)
    plwd_words = sum(clean_and_count_words(seg) for seg in plwd_segments)
    
    caregiver_sentences = sum(count_sentences(seg) for seg in caregiver_segments)
    plwd_sentences = sum(count_sentences(seg) for seg in plwd_segments)
    
    caregiver_questions = sum(count_questions(seg) for seg in caregiver_segments)
    plwd_questions = sum(count_questions(seg) for seg in plwd_segments)
    
    caregiver_disfluencies = sum(count_disfluencies(seg) for seg in caregiver_segments)
    plwd_disfluencies = sum(count_disfluencies(seg) for seg in plwd_segments)
    
    caregiver_nonverbal = sum(count_nonverbal_cues(seg) for seg in caregiver_segments)
    plwd_nonverbal = sum(count_nonverbal_cues(seg) for seg in plwd_segments)
    
    # Additional metrics
    total_words = caregiver_words + plwd_words
    total_turns = caregiver_turns + plwd_turns
    avg_words_per_turn = total_words / total_turns if total_turns > 0 else 0
    caregiver_words_per_utterance = caregiver_words / caregiver_turns if caregiver_turns > 0 else 0
    plwd_words_per_utterance = plwd_words / plwd_turns if plwd_turns > 0 else 0
    
    return {
        "patient_id": participant_id,
        "week_label": week_label,
        "session_type": session_type,
        "condition": condition,
        "filename": filename,
        "caregiver_turns": caregiver_turns,
        "plwd_turns": plwd_turns,
        "caregiver_words": caregiver_words,
        "plwd_words": plwd_words,
        "caregiver_sentences": caregiver_sentences,
        "plwd_sentences": plwd_sentences,
        "plwd_nonverbal": plwd_nonverbal,
        "caregiver_nonverbal": caregiver_nonverbal,
        "caregiver_questions": caregiver_questions,
        "plwd_questions": plwd_questions,
        "caregiver_disfluencies": caregiver_disfluencies,
        "plwd_disfluencies": plwd_disfluencies,
        "avg_words_per_turn": round(avg_words_per_turn, 2),
        "caregiver_words_per_utterance": round(caregiver_words_per_utterance, 2),
        "plwd_words_per_utterance": round(plwd_words_per_utterance, 2)
    }

def process_all_files():
    """Process all transcript files"""
    data_dir = "data"
    results = []
    
    for participant_dir in os.listdir(data_dir):
        participant_path = os.path.join(data_dir, participant_dir)
        if os.path.isdir(participant_path):
            for session_type in os.listdir(participant_path):
                session_path = os.path.join(participant_path, session_type)
                if os.path.isdir(session_path):
                    for file_name in os.listdir(session_path):
                        if file_name.endswith('.docx'):
                            file_path = os.path.join(session_path, file_name)
                            result = analyze_transcript(file_path)
                            if result:
                                results.append(result)
                                print(f"✅ Processed: {file_name}")
                            else:
                                print(f"❌ Failed: {file_name}")
    
    return results

def save_results(results):
    """Save results to JSON file"""
    output_dir = "backend/outputfile"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "metrics_output.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Saved {len(results)} records to {output_file}")

def main():
    """Main execution"""
    print("🔄 Processing transcript files...")
    results = process_all_files()
    
    print(f"📊 Processed {len(results)} files")
    save_results(results)
    print("✅ Complete!")

if __name__ == "__main__":
    main()
