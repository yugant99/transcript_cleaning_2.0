import streamlit as st
import pandas as pd
import json

# --- Loaders ---

def load_classified_data(classified_json_path):
    with open(classified_json_path, 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    return classified_data


def load_enriched_data(enriched_json_path):
    with open(enriched_json_path, 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)
    return enriched_data

# --- Paths to your JSON files ---
CLASSIFIED_JSON_PATH = "classified_output_1.json"
ENRICHED_JSON_PATH = "transcript_insights_updated.json"  # change if needed
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"
NONVERBAL_ANALYSIS_PATH = "enhanced_transcript_analysis_fixed.json"  # For nonverbal cues

# --- Main Streamlit App ---

def main():
    st.title("Overall Summary")

    classified_data = load_classified_data(CLASSIFIED_JSON_PATH)
    enriched_data = load_enriched_data(ENRICHED_JSON_PATH)
    enhanced_data = load_enriched_data(ENHANCED_ANALYSIS_PATH)
    
    # Load nonverbal data if available
    try:
        nonverbal_data = load_enriched_data(NONVERBAL_ANALYSIS_PATH)
    except:
        nonverbal_data = None
        st.warning("Nonverbal analysis data not available - some columns will show 0.")

    if not classified_data or not enriched_data:
        st.warning("No analysis data available.")
        return

    # Filter out Final Interview files
    classified_data = [f for f in classified_data if not f.get("final_interview", False) 
                      and f.get("session_type", "") != "Final Interview"]

    # Get unique patient IDs
    patient_ids = sorted(set(f['patient_id'] for f in classified_data if f.get('patient_id')))

    for patient_id in patient_ids:
        with st.expander(f"Patient {patient_id}", expanded=False):
            patient_files = [f for f in classified_data if f.get('patient_id') == patient_id]

            basic_stats_data = []

            for file in patient_files:
                filename = file['filename']
                session_type = file.get('session_type', 'Unknown')
                condition_type = file.get('condition_type', 'Unknown')
                condition_value = file.get('condition_value', 'Unknown').strip()  # Get condition value
                week = file.get('week', 'Unknown')
                
                # Format week label for display
                week_label = "Final Interview" if week is None or week == "None" else f"Week {week}"

                # Find corresponding enriched metrics
                enriched_patient_data = None
                # Find patient section inside enriched_data
                if patient_id in enriched_data:
                    for session_category in enriched_data[patient_id].values():
                        if filename in session_category:
                            enriched_patient_data = session_category[filename]
                            break

                if enriched_patient_data and 'basic_statistics' in enriched_patient_data:
                    stats = enriched_patient_data['basic_statistics']
                else:
                    stats = {}

                # Get basic turn and word data
                caregiver_turns = stats.get('caregiver_turns', 0)
                plwd_turns = stats.get('plwd_turns', 0)
                caregiver_words = stats.get('caregiver_words', 0)
                plwd_words = stats.get('plwd_words', 0)

                # Get all requested metrics from enhanced analysis
                caregiver_questions = 0
                plwd_questions = 0
                caregiver_disfluencies = 0
                plwd_disfluencies = 0
                caregiver_nonverbal = 0
                plwd_nonverbal = 0
                caregiver_sentences = 0
                plwd_sentences = 0
                pain_mentions = 0
                comfort_mentions = 0
                
                # Get questions, disfluencies, sentences, and pain/comfort mentions from enhanced_transcript_analysis.json
                if 'by_file' in enhanced_data and filename in enhanced_data['by_file']:
                    file_data = enhanced_data['by_file'][filename]
                    
                    # Process each turn to count questions, disfluencies, sentences, and pain/comfort mentions
                    if 'turns' in file_data:
                        for turn in file_data['turns']:
                            speaker = turn.get('speaker', '').lower()
                            is_question = turn.get('is_question', False)
                            disfluencies = turn.get('disfluencies', [])
                            text = turn.get('text', '').lower()
                            
                            # Count sentences by speaker (split on sentence-ending punctuation)
                            if text.strip():
                                # Simple sentence counting: split on . ! ? and count non-empty segments
                                import re
                                sentences = re.split(r'[.!?]+', text.strip())
                                sentence_count = len([s for s in sentences if s.strip()])
                                
                                if speaker == 'caregiver':
                                    caregiver_sentences += sentence_count
                                elif speaker == 'plwd':
                                    plwd_sentences += sentence_count
                            
                            # Count questions by speaker
                            if is_question:
                                if speaker == 'caregiver':
                                    caregiver_questions += 1
                                elif speaker == 'plwd':
                                    plwd_questions += 1
                            
                            # Count disfluencies by speaker
                            if disfluencies and len(disfluencies) > 0:
                                if speaker == 'caregiver':
                                    caregiver_disfluencies += len(disfluencies)
                                elif speaker == 'plwd':
                                    plwd_disfluencies += len(disfluencies)
                            
                            # Count pain/comfort mentions (simple keyword matching)
                            pain_keywords = ['pain', 'hurt', 'ache', 'sore', 'uncomfortable', 'discomfort']
                            comfort_keywords = ['comfortable', 'good', 'nice', 'pleasant', 'enjoy', 'happy', 'relaxed']
                            
                            for keyword in pain_keywords:
                                if keyword in text:
                                    pain_mentions += text.count(keyword)
                            
                            for keyword in comfort_keywords:
                                if keyword in text:
                                    comfort_mentions += text.count(keyword)
                
                # Get nonverbal cues from fixed analysis if available
                if nonverbal_data and 'by_file' in nonverbal_data and filename in nonverbal_data['by_file']:
                    nonverbal_file_data = nonverbal_data['by_file'][filename]
                    
                    if 'turns' in nonverbal_file_data:
                        for turn in nonverbal_file_data['turns']:
                            speaker = turn.get('speaker', '').lower()
                            nonverbal_cues = turn.get('nonverbal_cues', [])
                            
                            # Count nonverbal cues by speaker
                            if nonverbal_cues and len(nonverbal_cues) > 0:
                                if speaker == 'caregiver':
                                    caregiver_nonverbal += len(nonverbal_cues)
                                elif speaker == 'plwd':
                                    plwd_nonverbal += len(nonverbal_cues)

                # Calculate average words per turn and per utterance (sentence)
                total_turns = caregiver_turns + plwd_turns
                total_words = caregiver_words + plwd_words
                
                # Avg words per turn (for whole conversation)
                avg_words_per_turn = round(total_words / total_turns, 2) if total_turns > 0 else 0
                
                # Avg words per utterance/sentence by speaker
                caregiver_words_per_utterance = round(caregiver_words / caregiver_sentences, 2) if caregiver_sentences > 0 else 0
                plwd_words_per_utterance = round(plwd_words / plwd_sentences, 2) if plwd_sentences > 0 else 0

                basic_stats_data.append({
                    'Patient ID': patient_id,
                    'Week': week,
                    'Week Label': week_label,
                    'Session Type': session_type,
                    'Condition Type': condition_type,
                    'Condition': condition_value,
                    'Filename': filename,
                    'Caregiver Turns': caregiver_turns,
                    'PLWD Turns': plwd_turns,
                    'Caregiver Words': caregiver_words,
                    'PLWD Words': plwd_words,
                    'Caregiver Sentences': caregiver_sentences,
                    'PLWD Sentences': plwd_sentences,
                    'PLWD Nonverbal': plwd_nonverbal,
                    'Caregiver Nonverbal': caregiver_nonverbal,
                    'Pain Mentions': pain_mentions,
                    'Comfort Mentions': comfort_mentions,
                    'Caregiver Questions': caregiver_questions,
                    'PLWD Questions': plwd_questions,
                    'Caregiver Disfluencies': caregiver_disfluencies,
                    'PLWD Disfluencies': plwd_disfluencies,
                    'Avg Words per Turn': avg_words_per_turn,
                    'Caregiver Words per Utterance': caregiver_words_per_utterance,
                    'PLWD Words per Utterance': plwd_words_per_utterance
                })

            df_basic_stats = pd.DataFrame(basic_stats_data)

            if 'Week' in df_basic_stats.columns and not df_basic_stats.empty:
                try:
                    df_basic_stats['Week'] = pd.to_numeric(df_basic_stats['Week'], errors='ignore')
                    df_basic_stats = df_basic_stats.sort_values('Week')
                except:
                    df_basic_stats = df_basic_stats.sort_values('Week', key=lambda x: x.astype(str))
            
            # Organize columns for the combined table - only requested columns
            display_cols = ['Week Label', 'Session Type', 'Condition', 'Filename',
                          'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
                          'Caregiver Sentences', 'PLWD Sentences',
                          'PLWD Nonverbal', 'Caregiver Nonverbal',
                          'Pain Mentions', 'Comfort Mentions', 
                          'Caregiver Questions', 'PLWD Questions',
                          'Caregiver Disfluencies', 'PLWD Disfluencies',
                          'Avg Words per Turn', 'Caregiver Words per Utterance', 'PLWD Words per Utterance']
            
            # Display a single combined table
            st.subheader("Basic Statistics Summary")
            st.caption("Pain/Comfort mentions are detected using keyword matching. Nonverbal cues include laughter, sighs, pauses, etc.")
            st.dataframe(df_basic_stats[display_cols].style.set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
                        use_container_width=True)

if __name__ == "__main__":
    main()
