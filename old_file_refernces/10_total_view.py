import streamlit as st
import pandas as pd
import json
import plotly.express as px
import numpy as np
from collections import defaultdict

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"
TRANSCRIPT_INSIGHTS_PATH = "transcript_insights_updated.json"
NONVERBAL_ANALYSIS_PATH = "enhanced_transcript_analysis_fixed.json"  # For nonverbal cues

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_total_view_data(selected_patients, selected_sessions, selected_conditions):
    # Load data from all sources
    classified_data = load_json(CLASSIFIED_PATH)
    enhanced_data = load_json(ENHANCED_ANALYSIS_PATH)
    transcript_insights = load_json(TRANSCRIPT_INSIGHTS_PATH)
    
    # Load nonverbal data if available
    try:
        nonverbal_data = load_json(NONVERBAL_ANALYSIS_PATH)
    except:
        nonverbal_data = None
    
    # Process data for analysis
    total_view_rows = []
    
    # Process each file in classified data
    for file in classified_data:
        # Skip Final Interview files
        if file.get("final_interview", False) or file.get("session_type", "") == "Final Interview":
            continue
            
        patient_id = file.get('patient_id', 'Unknown')
        filename = file.get('filename')
        session_type = file.get('session_type', 'Unknown')
        condition_value = file.get('condition_value', 'Unknown')
        week = file.get('week', 'Unknown')
        
        # Apply filters
        if selected_patients and patient_id not in selected_patients:
            continue
        if selected_sessions and session_type not in selected_sessions:
            continue
        if selected_conditions and condition_value not in selected_conditions:
            continue
        
        # Initialize metrics
        caregiver_turns = 0
        plwd_turns = 0
        caregiver_words = 0
        plwd_words = 0
        caregiver_questions = 0
        plwd_questions = 0
        caregiver_disfluencies = 0
        plwd_disfluencies = 0
        caregiver_nonverbal = 0
        plwd_nonverbal = 0
        pain_mentions = 0
        comfort_mentions = 0
        
        # Get turns and words from transcript_insights
        if patient_id in transcript_insights:
            for session_category in transcript_insights[patient_id].values():
                if filename in session_category:
                    file_data = session_category[filename]
                    
                    # Extract basic statistics if available
                    if 'basic_statistics' in file_data:
                        stats = file_data['basic_statistics']
                        caregiver_turns = stats.get('caregiver_turns', 0)
                        plwd_turns = stats.get('plwd_turns', 0)
                        caregiver_words = stats.get('caregiver_words', 0)
                        plwd_words = stats.get('plwd_words', 0)
                    
                    break
        
        # Initialize sentence counters
        caregiver_sentences = 0
        plwd_sentences = 0
        
        # Get questions, disfluencies, sentence counts, and pain/comfort mentions from enhanced_transcript_analysis
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
        
        # Add row to dataset
        total_view_rows.append({
            'Patient ID': patient_id,
            'Session Type': session_type,
            'Condition': condition_value,
            'Week': week,
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
    
    # Create DataFrame
    df_total_view = pd.DataFrame(total_view_rows)
    
    return df_total_view

def main():
    st.title("Total View")
    
    # Load data
    classified_data = load_json(CLASSIFIED_PATH)
    
    # Filter out Final Interview files from filter options
    non_final_classified = [f for f in classified_data if not f.get("final_interview", False) 
                           and f.get("session_type", "") != "Final Interview"]
    
    # Get filter options
    all_patients = sorted(set(f['patient_id'] for f in non_final_classified if f.get('patient_id')))
    all_sessions = sorted(set(f['session_type'] for f in non_final_classified if f.get('session_type')))
    all_conditions = sorted(set(f.get('condition_value', '') for f in non_final_classified if f.get('condition_value')))
    
    # Create filters
    st.sidebar.header("Filters")
    selected_patients = st.sidebar.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    selected_sessions = st.sidebar.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    selected_conditions = st.sidebar.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Extract data
    df_total_view = extract_total_view_data(selected_patients, selected_sessions, selected_conditions)
    
    if df_total_view.empty:
        st.info("No data available for selected filters.")
        return
    
    # Display file-level data
    st.header("File-Level Data")
    st.caption("Pain/Comfort mentions are detected using keyword matching. Nonverbal cues include laughter, sighs, pauses, etc.")
    st.dataframe(df_total_view, use_container_width=True)
    
    # Create week-wise summary
    st.header("Week-wise Summary")
    df_week_summary = df_total_view.groupby('Week').agg({
        'Caregiver Turns': 'sum',
        'PLWD Turns': 'sum',
        'Caregiver Words': 'sum',
        'PLWD Words': 'sum',
        'Caregiver Sentences': 'sum',
        'PLWD Sentences': 'sum',
        'PLWD Nonverbal': 'sum',
        'Caregiver Nonverbal': 'sum',
        'Pain Mentions': 'sum',
        'Comfort Mentions': 'sum',
        'Caregiver Questions': 'sum',
        'PLWD Questions': 'sum',
        'Caregiver Disfluencies': 'sum',
        'PLWD Disfluencies': 'sum'
    }).reset_index()
    
    # Add average words per turn
    df_week_summary['Caregiver Words per Turn'] = (
        df_week_summary['Caregiver Words'] / df_week_summary['Caregiver Turns']
    ).round(2)
    df_week_summary['PLWD Words per Turn'] = (
        df_week_summary['PLWD Words'] / df_week_summary['PLWD Turns']
    ).round(2)
    
    # Add overall averages
    df_week_summary['Avg Words per Turn'] = (
        (df_week_summary['Caregiver Words'] + df_week_summary['PLWD Words']) / 
        (df_week_summary['Caregiver Turns'] + df_week_summary['PLWD Turns'])
    ).round(2)
    
    # Add words per utterance (sentence) by speaker
    df_week_summary['Caregiver Words per Utterance'] = (
        df_week_summary['Caregiver Words'] / df_week_summary['Caregiver Sentences']
    ).round(2)
    df_week_summary['PLWD Words per Utterance'] = (
        df_week_summary['PLWD Words'] / df_week_summary['PLWD Sentences']
    ).round(2)
    
    # Sort by week
    df_week_summary = df_week_summary.sort_values('Week')
    
    # Display week-wise summary
    st.dataframe(df_week_summary, use_container_width=True)
    
    # Create condition-wise summary
    st.header("Condition-wise Summary")
    df_condition_summary = df_total_view.groupby('Condition').agg({
        'Caregiver Turns': 'sum',
        'PLWD Turns': 'sum',
        'Caregiver Words': 'sum',
        'PLWD Words': 'sum',
        'Caregiver Sentences': 'sum',
        'PLWD Sentences': 'sum',
        'PLWD Nonverbal': 'sum',
        'Caregiver Nonverbal': 'sum',
        'Pain Mentions': 'sum',
        'Comfort Mentions': 'sum',
        'Caregiver Questions': 'sum',
        'PLWD Questions': 'sum',
        'Caregiver Disfluencies': 'sum',
        'PLWD Disfluencies': 'sum'
    }).reset_index()
    
    # Add average words per turn
    df_condition_summary['Caregiver Words per Turn'] = (
        df_condition_summary['Caregiver Words'] / df_condition_summary['Caregiver Turns']
    ).round(2)
    df_condition_summary['PLWD Words per Turn'] = (
        df_condition_summary['PLWD Words'] / df_condition_summary['PLWD Turns']
    ).round(2)
    
    # Add overall averages
    df_condition_summary['Avg Words per Turn'] = (
        (df_condition_summary['Caregiver Words'] + df_condition_summary['PLWD Words']) / 
        (df_condition_summary['Caregiver Turns'] + df_condition_summary['PLWD Turns'])
    ).round(2)
    
    # Add words per utterance (sentence) by speaker
    df_condition_summary['Caregiver Words per Utterance'] = (
        df_condition_summary['Caregiver Words'] / df_condition_summary['Caregiver Sentences']
    ).round(2)
    df_condition_summary['PLWD Words per Utterance'] = (
        df_condition_summary['PLWD Words'] / df_condition_summary['PLWD Sentences']
    ).round(2)
    
    # Display condition-wise summary
    st.dataframe(df_condition_summary, use_container_width=True)
    
    # Create session type summary
    st.header("Session Type Summary")
    df_session_summary = df_total_view.groupby('Session Type').agg({
        'Caregiver Turns': 'sum',
        'PLWD Turns': 'sum',
        'Caregiver Words': 'sum',
        'PLWD Words': 'sum',
        'Caregiver Sentences': 'sum',
        'PLWD Sentences': 'sum',
        'PLWD Nonverbal': 'sum',
        'Caregiver Nonverbal': 'sum',
        'Pain Mentions': 'sum',
        'Comfort Mentions': 'sum',
        'Caregiver Questions': 'sum',
        'PLWD Questions': 'sum',
        'Caregiver Disfluencies': 'sum',
        'PLWD Disfluencies': 'sum'
    }).reset_index()
    
    # Add average words per turn
    df_session_summary['Caregiver Words per Turn'] = (
        df_session_summary['Caregiver Words'] / df_session_summary['Caregiver Turns']
    ).round(2)
    df_session_summary['PLWD Words per Turn'] = (
        df_session_summary['PLWD Words'] / df_session_summary['PLWD Turns']
    ).round(2)
    
    # Add overall averages
    df_session_summary['Avg Words per Turn'] = (
        (df_session_summary['Caregiver Words'] + df_session_summary['PLWD Words']) / 
        (df_session_summary['Caregiver Turns'] + df_session_summary['PLWD Turns'])
    ).round(2)
    
    # Add words per utterance (sentence) by speaker
    df_session_summary['Caregiver Words per Utterance'] = (
        df_session_summary['Caregiver Words'] / df_session_summary['Caregiver Sentences']
    ).round(2)
    df_session_summary['PLWD Words per Utterance'] = (
        df_session_summary['PLWD Words'] / df_session_summary['PLWD Sentences']
    ).round(2)
    
    # Display session type summary
    st.dataframe(df_session_summary, use_container_width=True)
    
    # Add visualizations
    st.header("Visualizations")
    
    # Create tabs for different visualizations
    viz_tabs = st.tabs(["Caregiver vs PLWD", "Metrics by Week", "Metrics by Condition", "Metrics by Session Type"])
    
    with viz_tabs[0]:
        # Caregiver vs PLWD comparison
        st.subheader("Caregiver vs PLWD Comparison")
        
        # Create summary data
        summary_data = {
            'Metric': ['Turns', 'Words', 'Nonverbal', 'Questions', 'Disfluencies'],
            'Caregiver': [
                df_total_view['Caregiver Turns'].sum(),
                df_total_view['Caregiver Words'].sum(),
                df_total_view['Caregiver Nonverbal'].sum(),
                df_total_view['Caregiver Questions'].sum(),
                df_total_view['Caregiver Disfluencies'].sum()
            ],
            'PLWD': [
                df_total_view['PLWD Turns'].sum(),
                df_total_view['PLWD Words'].sum(),
                df_total_view['PLWD Nonverbal'].sum(),
                df_total_view['PLWD Questions'].sum(),
                df_total_view['PLWD Disfluencies'].sum()
            ]
        }
        
        # Add total pain/comfort metrics
        st.write(f"**Total Pain Mentions:** {df_total_view['Pain Mentions'].sum()}")
        st.write(f"**Total Comfort Mentions:** {df_total_view['Comfort Mentions'].sum()}")
        
        df_summary = pd.DataFrame(summary_data)
        
        # Create a grouped bar chart
        fig = px.bar(
            df_summary, 
            x='Metric', 
            y=['Caregiver', 'PLWD'],
            barmode='group',
            title='Caregiver vs PLWD Metrics',
            labels={'value': 'Count', 'variable': 'Speaker'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[1]:
        # Metrics by Week
        st.subheader("Metrics by Week")
        
        # Create line charts for each metric by week
        metrics = ['Turns', 'Words', 'Nonverbal', 'Questions', 'Disfluencies']
        
        # Show pain/comfort mentions by week
        fig_pain_comfort = px.line(
            df_week_summary, 
            x='Week', 
            y=['Pain Mentions', 'Comfort Mentions'],
            markers=True,
            title='Pain and Comfort Mentions by Week',
            labels={'value': 'Count', 'variable': 'Mention Type'}
        )
        st.plotly_chart(fig_pain_comfort, use_container_width=True)
        
        for metric in metrics:
            caregiver_col = f'Caregiver {metric}'
            plwd_col = f'PLWD {metric}'
            
            # Create a line chart
            fig = px.line(
                df_week_summary, 
                x='Week', 
                y=[caregiver_col, plwd_col],
                markers=True,
                title=f'{metric} by Week',
                labels={'value': 'Count', 'variable': 'Speaker'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[2]:
        # Metrics by Condition
        st.subheader("Metrics by Condition")
        
        # Show pain/comfort mentions by condition
        fig_pain_comfort_condition = px.bar(
            df_condition_summary, 
            x='Condition', 
            y=['Pain Mentions', 'Comfort Mentions'],
            barmode='group',
            title='Pain and Comfort Mentions by Condition',
            labels={'value': 'Count', 'variable': 'Mention Type'}
        )
        st.plotly_chart(fig_pain_comfort_condition, use_container_width=True)
        
        # Create bar charts for each metric by condition
        for metric in metrics:
            caregiver_col = f'Caregiver {metric}'
            plwd_col = f'PLWD {metric}'
            
            # Create a grouped bar chart
            fig = px.bar(
                df_condition_summary, 
                x='Condition', 
                y=[caregiver_col, plwd_col],
                barmode='group',
                title=f'{metric} by Condition',
                labels={'value': 'Count', 'variable': 'Speaker'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[3]:
        # Metrics by Session Type
        st.subheader("Metrics by Session Type")
        
        # Show pain/comfort mentions by session type
        fig_pain_comfort_session = px.bar(
            df_session_summary, 
            x='Session Type', 
            y=['Pain Mentions', 'Comfort Mentions'],
            barmode='group',
            title='Pain and Comfort Mentions by Session Type',
            labels={'value': 'Count', 'variable': 'Mention Type'}
        )
        st.plotly_chart(fig_pain_comfort_session, use_container_width=True)
        
        # Create bar charts for each metric by session type
        for metric in metrics:
            caregiver_col = f'Caregiver {metric}'
            plwd_col = f'PLWD {metric}'
            
            # Create a grouped bar chart
            fig = px.bar(
                df_session_summary, 
                x='Session Type', 
                y=[caregiver_col, plwd_col],
                barmode='group',
                title=f'{metric} by Session Type',
                labels={'value': 'Count', 'variable': 'Speaker'}
            )
            
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
