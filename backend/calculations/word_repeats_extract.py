#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict
from docx import Document

DISFLUENCY_MARKERS = {
    'um','uh','er','ah','you','know','i','mean','sort','of','kind','of','well','so','basically'
}

def read_docx_text(file_path: str) -> str:
    try:
        doc = Document(file_path)
        return '\n'.join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def extract_participant_id(text: str):
    m = re.search(r'vr(?:x)?\d+', text, re.IGNORECASE)
    return m.group(0).lower() if m else None

def extract_metadata_from_filename(filename: str):
    session_type = 'unknown'
    if 'EP' in filename:
        session_type = 'EP'
    elif 'ER' in filename:
        session_type = 'ER'
    elif 'baseline' in filename.lower():
        session_type = 'baseline'
    elif 'Final Interview' in filename or 'final_interview' in filename:
        session_type = 'final_interview'

    week_match = re.search(r'(EP|ER)(\d+)', filename)
    week_label = f"Week {week_match.group(2)}" if week_match else "Unknown"
    condition = "VR" if 'EP' in filename else "Tablet"
    return session_type, week_label, condition

def split_turns(text: str, participant_id: str):
    caregiver_pattern = f"{participant_id}_c:"
    plwd_pattern = f"{participant_id}_p:"
    regex = re.compile(f"({re.escape(caregiver_pattern)}|{re.escape(plwd_pattern)})(.*?)((?={re.escape(participant_id)}_[cp]:)|$)", re.DOTALL | re.IGNORECASE)
    turns = []
    for m in regex.finditer(text):
        tag = m.group(1).lower()
        content = m.group(2).strip()
        speaker = 'caregiver' if tag.endswith('_c:') else 'plwd'
        turns.append({'speaker': speaker, 'text': content})
    return turns

def clean_text_remove_brackets(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'\(.*?\)', ' ', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def tokenize_basic(text: str):
    if not text:
        return []
    words = text.lower().split()
    words = [re.sub(rf"^[^\w]+|[^\w]+$", '', w) for w in words]
    words = [w for w in words if w]
    return words

def detect_immediate_repeats(words):
    if len(words) < 2:
        return []
    repeats = []
    i = 0
    while i < len(words) - 1:
        current_word = words[i]
        if current_word in DISFLUENCY_MARKERS:
            i += 1
            continue
        if current_word == words[i+1]:
            repeat_count = 1
            j = i + 1
            while j < len(words) and words[j] == current_word:
                repeat_count += 1
                j += 1
            start_idx = max(0, i - 5)
            end_idx = min(len(words), j + 5)
            context_words = words[start_idx:end_idx]
            highlighted = []
            for idx, w in enumerate(context_words):
                actual_idx = start_idx + idx
                if i <= actual_idx < j:
                    highlighted.append(f"**{w}**")
                else:
                    highlighted.append(w)
            repeats.append({
                'word': current_word,
                'count': repeat_count,
                'position': i,
                'context': ' '.join(highlighted)
            })
            i = j
        else:
            i += 1
    return repeats

def process_all(root_data_dir: str = os.path.join(os.path.dirname(__file__), '../../data')):
    by_file = {}
    for participant in os.listdir(root_data_dir):
        p_path = os.path.join(root_data_dir, participant)
        if not os.path.isdir(p_path):
            continue
        for session_dir in os.listdir(p_path):
            s_path = os.path.join(p_path, session_dir)
            if not os.path.isdir(s_path):
                continue
            for fname in os.listdir(s_path):
                if not fname.endswith('.docx'):
                    continue
                fpath = os.path.join(s_path, fname)
                text = read_docx_text(fpath)
                if not text:
                    continue
                participant_id = extract_participant_id(text) or 'unknown'
                session_type, week_label, condition = extract_metadata_from_filename(fname)
                turns = split_turns(text, participant_id)

                caregiver_total = 0
                plwd_total = 0
                by_word = defaultdict(int)
                out_turns = []

                for t in turns:
                    cleaned = clean_text_remove_brackets(t['text'])
                    words = tokenize_basic(cleaned)
                    reps = detect_immediate_repeats(words)
                    # total repeats: sum(extra occurrences)
                    extra_count = sum(r['count'] - 1 for r in reps)
                    if t['speaker'] == 'caregiver':
                        caregiver_total += extra_count
                    else:
                        plwd_total += extra_count
                    for r in reps:
                        by_word[r['word']] += (r['count'] - 1)
                    if reps:
                        out_turns.append({
                            'speaker': t['speaker'],
                            'text': cleaned[:500],
                            'repeats': reps[:10],
                        })

                by_file[fname] = {
                    'metadata': {
                        'patient_id': participant_id.upper(),
                        'session_type': session_type,
                        'week_label': week_label,
                        'condition': condition,
                        'filename': fname,
                    },
                    'stats': {
                        'repeats': {
                            'caregiver_total': caregiver_total,
                            'plwd_total': plwd_total,
                            'by_word': dict(sorted(by_word.items(), key=lambda x: x[1], reverse=True))
                        }
                    },
                    'turns': out_turns[:200]
                }

    return { 'by_file': by_file }

def main():
    data = process_all()
    out_dir = os.path.join(os.path.dirname(__file__), '../outputfile')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'word_repeats.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {out_path} with {len(data.get('by_file', {}))} files")

if __name__ == '__main__':
    main()


