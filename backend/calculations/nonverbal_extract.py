#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict
from docx import Document

# Normalization from fix_nonverbal_cues.py (condensed)
def normalize_nonverbal_cue(cue: str):
    if not cue or not isinstance(cue, str):
        return None
    cue_lower = cue.lower().strip()
    cue_clean = re.sub(r'^\[|\]$', '', cue_lower)

    normalizations = {
        r'^inaudible.*': 'inaudible',
        r'^(long\s+)?pause.*': 'pause',
        r'^(laugh|laughter|laughing|laughs|chuckle|chuckles|chuckling|giggle|giggles|giggling).*': 'laughter',
        r'^(cough|coughs|coughing).*': 'coughing',
        r'^(sigh|sighs|sighing).*': 'sighing',
        r'^(nod|nods|nodding).*': 'nodding',
        r'^(shake|shakes|shaking)\s+(head|heads).*': 'shaking_head',
        r'^(hum|hums|humming).*': 'humming',
        r'^(sing|sings|singing).*': 'singing',
        r'^(mumble|mumbles|mumbling).*': 'mumbling',
        r'^(yawn|yawns|yawning).*': 'yawning',
        r'^(gesture|gestures|gesturing).*': 'gesturing',
        r'^(point|points|pointing).*': 'pointing',
        r'^(clap|claps|clapping).*': 'clapping',
        r'^(smile|smiles|smiling)(?!.*camera).*': 'smiling',
        r'^(dance|dances|dancing).*': 'dancing',
        r'^(-{1,3}|–{1,3}|—{1,3})$': 'interruption',
        r'^(\.{3,}|…+)$': 'trailing_off',
    }

    for pattern, replacement in normalizations.items():
        if re.match(pattern, cue_clean):
            return replacement

    exclusion_patterns = [
        r'speaking.*\{.*\}',
        r'speaking.*(spanish|portuguese|russian|mandarin|english)',
        r'translat(e|ing)', r'researcher', r'research coordinator', r'coordinator',
        r'camera', r'video', r'screen', r'recording', r'vr\d+_[cp]', r'name$', r'friend$',
        r'day program leader', r'if participant', r'for example', r'reads (on|sign)', r'.{50,}'
    ]
    for pattern in exclusion_patterns:
        if re.search(pattern, cue_clean):
            return None
    return cue_clean

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
    # Find segments between speaker tags
    regex = re.compile(f"({re.escape(caregiver_pattern)}|{re.escape(plwd_pattern)})(.*?)((?={re.escape(participant_id)}_[cp]:)|$)", re.DOTALL | re.IGNORECASE)
    turns = []
    for m in regex.finditer(text):
        tag = m.group(1).lower()
        content = m.group(2).strip()
        speaker = 'caregiver' if tag.endswith('_c:') else 'plwd'
        turns.append({'speaker': speaker, 'text': content})
    return turns

def extract_cues_from_text(text: str):
    # Find bracketed cues [ ... ]
    raw_cues = re.findall(r'\[(.+?)\]', text)
    normalized = []
    for cue in raw_cues:
        n = normalize_nonverbal_cue(cue)
        if n:
            normalized.append(n)
    return normalized

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

                out_turns = []
                cue_totals = defaultdict(int)
                for t in turns:
                    cues = extract_cues_from_text(t['text'])
                    for c in cues:
                        cue_totals[c] += 1
                    out_turns.append({
                        'speaker': t['speaker'],
                        'text': t['text'][:500],
                        'nonverbal_cues': cues,
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
                        'nonverbal_cues': dict(cue_totals)
                    },
                    'turns': out_turns,
                }

    return { 'by_file': by_file }

def main():
    data = process_all()
    out_dir = os.path.join(os.path.dirname(__file__), '../outputfile')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'enhanced_transcript_analysis_fixed.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {out_path} with {len(data.get('by_file', {}))} files")

if __name__ == '__main__':
    main()


