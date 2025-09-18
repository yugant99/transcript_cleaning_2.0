import json
import os
import re
from transcript_insight import read_docx

# Load the existing insights file
INSIGHT_JSON_PATH = "/Users/yuganthareshsoni/transcript_dashboard/transcript_insights_updated.json"
DATA_DIR = "/Users/yuganthareshsoni/transcript_dashboard/data"

# regex to capture the participant id
def extract_participant_id(text):
    match = re.search(r'vr(?:x)?\d+', text, re.IGNORECASE)
    return match.group(0).lower() if match else None

# Set of disfluencies to ignore
DISFLUENCIES = set(["um", "umm", "uh", "uhh", "uhhh", "er", "err", "erm", "ah", "ahh", "hm", "hmm", "mhm", "mm", "mmm", "eh", "ehm", "em"])

# Clean and tokenize segment: remove brackets and disfluencies
def clean_and_count_words(segment):
    # Remove [] words ( Imp)
    segment = re.sub(r'\[.*?\]', '', segment)
    # Tokenize by whitespace
    words = segment.strip().split()
    #capture words that are not disfluencies 
    words = [w for w in words if w.lower() not in DISFLUENCIES]
    return len(words)

# Extract speaker segments and count words accurately
def count_words_per_speaker(transcript, participant_id):
    caregiver_pattern = f"{participant_id}_c:"
    plwd_pattern = f"{participant_id}_p:"

    caregiver_segments = re.findall(f"{caregiver_pattern}(.*?)(?={participant_id}_[cp]:|$)", transcript, re.DOTALL | re.IGNORECASE)
    plwd_segments = re.findall(f"{plwd_pattern}(.*?)(?={participant_id}_[cp]:|$)", transcript, re.DOTALL | re.IGNORECASE)

    caregiver_words = sum(clean_and_count_words(seg) for seg in caregiver_segments)
    plwd_words = sum(clean_and_count_words(seg) for seg in plwd_segments)

    return caregiver_words, plwd_words

# Load the JSON
with open(INSIGHT_JSON_PATH, 'r') as f:
    insights = json.load(f)

not_updated_files = []

# Traverse JSON and update word counts
for participant_id in insights:
    for session_type in insights[participant_id]:
        for file_name, file_data in insights[participant_id][session_type].items():
            full_path = os.path.join(DATA_DIR, participant_id, session_type, file_name)
            if not os.path.exists(full_path):
                not_updated_files.append((file_name, "File not found"))
                continue

            transcript = read_docx(full_path)
            extracted_id = extract_participant_id(transcript)
            if not extracted_id:
                not_updated_files.append((file_name, "Could not extract participant ID"))
                continue

            caregiver_words, plwd_words = count_words_per_speaker(transcript, extracted_id)

            try:
                insights[participant_id][session_type][file_name]["basic_statistics"]["caregiver_words"] = caregiver_words
                insights[participant_id][session_type][file_name]["basic_statistics"]["plwd_words"] = plwd_words
            except KeyError:
                not_updated_files.append((file_name, "Missing basic_statistics block"))

# Save updated JSON
with open(INSIGHT_JSON_PATH, 'w') as f:
    json.dump(insights, f, indent=2)

# Debug output
print("Update complete.")
if not_updated_files:
    print("\nFiles not updated:")
    for name, reason in not_updated_files:
        print(f"- {name}: {reason}")
