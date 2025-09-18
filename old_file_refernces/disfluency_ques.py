import pandas as pd
import json
import re
import os
from collections import defaultdict, Counter

# Input/output file paths
ENRICHED_TURNS_PATH = "enriched_turns.csv"
CLASSIFIED_OUTPUT_PATH = "classified_output_1.json"
OUTPUT_JSON_PATH = "enhanced_transcript_analysis.json"

def load_data():
    """Load the CSV and JSON data files"""
    turns_df = pd.read_csv(ENRICHED_TURNS_PATH)
    
    with open(CLASSIFIED_OUTPUT_PATH, 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    
    # Create a mapping of filenames to their metadata
    file_metadata = {item['filename']: item for item in classified_data}
    
    return turns_df, file_metadata

def detect_disfluencies(text):
    """
    Detect only filled pause disfluencies in text
    Returns a list of tuples (disfluency_type, disfluency_text)
    """
    if not isinstance(text, str):
        return []
        
    disfluencies = []
    
    # Replace apostrophe encoding to avoid false positives
    text = text.replace("/2019s", "'")
    
    # Only define filled pause patterns
    filled_pause_pattern = r'\b(um|umm|uh|uhh|uhhh|er|err|erm|ah|ahh|hm|hmm|mhm|mm|mmm|eh|ehm|em)\b'
    
    # Find filled pauses
    matches = re.finditer(filled_pause_pattern, text, re.IGNORECASE)
    for match in matches:
        disfluencies.append(('filled_pause', match.group()))
    
    return disfluencies

def detect_nonverbal_cues(text):
    """Extract non-verbal cues denoted by [cue]"""
    if not isinstance(text, str):
        return []
        
    cues = []
    bracket_pattern = r'\[(.*?)\]'
    matches = re.finditer(bracket_pattern, text)
    
    for match in matches:
        cue = match.group(1).lower().strip()
        if cue:
            cues.append(cue)
    
    return cues

def identify_question_response_pairs(turns_df):
    """
    Identify question-response pairs in the turns dataframe
    Returns two dictionaries mapping (file_name, turn_id) to boolean flags for questions and responses
    """
    is_question = {}
    is_response = {}
    
    # Sort by participant_id, file_name, and turn_index for proper sequence
    sorted_df = turns_df.sort_values(['participant_id', 'file_name', 'turn_index'])
    
    prev_row = None
    prev_was_question = False
    
    for _, row in sorted_df.iterrows():
        file_name = row['file_name']
        turn_id = row['turn_index']
        turn_key = (file_name, turn_id)  # Make key unique across files
        turn_text = str(row['turn_text']) if isinstance(row['turn_text'], str) else ""
        
        # Mark if this turn is a question (only count explicit question marks)
        has_question_mark = '?' in turn_text
        is_question[turn_key] = has_question_mark
        
        # Mark if this turn is a response to a previous question
        is_response[turn_key] = False
        
        if prev_row is not None:
            # Only check for responses within the same file
            if (row['file_name'] == prev_row['file_name'] and
                prev_was_question and row['speaker'] != prev_row['speaker']):
                is_response[turn_key] = True
        
        # Update for next iteration
        prev_row = row
        prev_was_question = has_question_mark
    
    return is_question, is_response

def process_turns(turns_df, file_metadata):
    """Process all turns to enhance with disfluency, question-response pairs, and non-verbal cues"""
    
    # Identify question-response pairs
    is_question, is_response = identify_question_response_pairs(turns_df)
    
    # Initialize results structure organized by file
    results = defaultdict(lambda: {
        "metadata": {},
        "turns": [],
        "stats": {
            "disfluencies": defaultdict(int),
            "nonverbal_cues": defaultdict(int),
            "questions": 0,
            "responses": 0,
            "caregiver_disfluencies": 0,
            "plwd_disfluencies": 0
        }
    })
    
    # Process each turn
    for _, row in turns_df.iterrows():
        # Get file information
        file_name = row['file_name']
        turn_id = row['turn_index']
        
        # Clean the turn text by handling apostrophes
        turn_text = str(row['turn_text']).replace("/2019s", "'") if isinstance(row['turn_text'], str) else ""
        
        # Update file metadata from classified data
        if file_name in file_metadata:
            results[file_name]["metadata"] = file_metadata[file_name]
        
        # Detect disfluencies
        disfluencies = detect_disfluencies(turn_text)
        
        # Detect non-verbal cues
        nonverbal_cues = detect_nonverbal_cues(turn_text) + (
            row['nonverbal_tags'].split(',') if isinstance(row['nonverbal_tags'], str) and row['nonverbal_tags'] else []
        )
        
        # Add enhanced turn data
        turn_key = (file_name, turn_id)  # Use same key format as identify_question_response_pairs
        turn_data = {
            "turn_id": turn_id,
            "speaker": row['speaker'],
            "text": turn_text,
            "is_question": is_question.get(turn_key, False),
            "is_response": is_response.get(turn_key, False),
            "disfluencies": [{"type": d_type, "text": d_text} for d_type, d_text in disfluencies],
            "nonverbal_cues": nonverbal_cues
        }
        
        results[file_name]["turns"].append(turn_data)
        
        # Update statistics
        for d_type, d_text in disfluencies:
            results[file_name]["stats"]["disfluencies"][d_type] += 1
            
            # Count disfluencies by speaker type
            if row['speaker'] == 'caregiver':
                results[file_name]["stats"]["caregiver_disfluencies"] += 1
            else:
                results[file_name]["stats"]["plwd_disfluencies"] += 1
                
        for cue in nonverbal_cues:
            results[file_name]["stats"]["nonverbal_cues"][cue] += 1
            
        if is_question.get(turn_key, False):
            results[file_name]["stats"]["questions"] += 1
            
        if is_response.get(turn_key, False):
            results[file_name]["stats"]["responses"] += 1
    
    # Aggregate results by participant
    participant_results = defaultdict(lambda: {
        "files": [],
        "aggregate_stats": {
            "disfluencies": defaultdict(int),
            "nonverbal_cues": defaultdict(int),
            "questions": 0,
            "responses": 0,
            "caregiver_disfluencies": 0,
            "plwd_disfluencies": 0,
            "file_count": 0
        }
    })
    
    for file_name, file_data in results.items():
        if "metadata" in file_data and "patient_id" in file_data["metadata"]:
            patient_id = file_data["metadata"]["patient_id"]
            
            # Add file to participant's files
            participant_results[patient_id]["files"].append(file_name)
            participant_results[patient_id]["aggregate_stats"]["file_count"] += 1
            
            # Aggregate statistics
            for d_type, count in file_data["stats"]["disfluencies"].items():
                participant_results[patient_id]["aggregate_stats"]["disfluencies"][d_type] += count
                
            for cue, count in file_data["stats"]["nonverbal_cues"].items():
                participant_results[patient_id]["aggregate_stats"]["nonverbal_cues"][cue] += count
                
            participant_results[patient_id]["aggregate_stats"]["questions"] += file_data["stats"]["questions"]
            participant_results[patient_id]["aggregate_stats"]["responses"] += file_data["stats"]["responses"]
            participant_results[patient_id]["aggregate_stats"]["caregiver_disfluencies"] += file_data["stats"]["caregiver_disfluencies"]
            participant_results[patient_id]["aggregate_stats"]["plwd_disfluencies"] += file_data["stats"]["plwd_disfluencies"]
    
    # Combine file and participant results
    combined_results = {
        "by_file": dict(results),
        "by_participant": dict(participant_results)
    }
    
    return combined_results

def main():
    # Load data
    print("Loading data...")
    turns_df, file_metadata = load_data()
    
    # Process turns
    print("Processing turns...")
    results = process_turns(turns_df, file_metadata)
    
    # Save results to JSON file
    print(f"Saving results to {OUTPUT_JSON_PATH}...")
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("Done!")

if __name__ == "__main__":
    main()