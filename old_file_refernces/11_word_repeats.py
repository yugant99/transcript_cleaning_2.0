import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict

# Import word repeat detector
try:
    from word_repeat_detector import analyze_turn_for_word_repeats, WordRepeatDetector
    WORD_REPEAT_AVAILABLE = True
except ImportError:
    st.warning("⚠️ Word repeat detection not available. Install nltk: pip install nltk")
    WORD_REPEAT_AVAILABLE = False
    def analyze_turn_for_word_repeats(text):
        return {'count': 0, 'examples': []}

# --- Paths to your data files ---
ENRICHED_TURNS_CSV = "enriched_turns.csv"
CLASSIFIED_PATH = "classified_output_1.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"
TRANSCRIPT_INSIGHTS_PATH = "transcript_insights.json"

@st.cache_data
def load_enriched_turns_data():
    """Load the enriched turns CSV data"""
    try:
        df = pd.read_csv(ENRICHED_TURNS_CSV)
        return df
    except Exception as e:
        st.error(f"Error loading enriched turns data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return {}

def extract_word_repeat_data(selected_patients, selected_sessions, selected_conditions):
    """Extract word repeat data from enriched_turns.csv"""
    
    # Load the enriched turns data
    turns_df = load_enriched_turns_data()
    if turns_df.empty:
        return pd.DataFrame(), defaultdict(list)
    
    # Load classified data for condition mapping
    classified_data = load_json(CLASSIFIED_PATH)
    filename_to_condition = {f['filename']: f.get('condition_value', '').strip() for f in classified_data}
    turns_df['condition'] = turns_df['file_name'].map(filename_to_condition).fillna('')
    
    # Load data from all sources
    classified_data = load_json(CLASSIFIED_PATH)
    enhanced_data = load_json(ENHANCED_ANALYSIS_PATH)
    transcript_insights = load_json(TRANSCRIPT_INSIGHTS_PATH)
    
    # Create a mapping of filenames to metadata from classified_data
    filename_to_metadata = {f['filename']: f for f in classified_data}
    
    # Process data for analysis
    word_repeat_rows = []
    example_data = defaultdict(list)
    
    # Process enhanced_transcript_analysis.json data
    for filename, file_data in enhanced_data.get("by_file", {}).items():
        # Get metadata from classified_data
        metadata = file_data.get("metadata", {})
        if not metadata:
            metadata = filename_to_metadata.get(filename, {})
            
        # Skip Final Interview files
        if metadata.get("final_interview", False) or metadata.get("session_type", "") == "Final Interview":
            continue
            
        patient_id = metadata.get('patient_id', 'Unknown')
        session_type = metadata.get('session_type', 'Unknown')
        condition_value = metadata.get('condition_value', '').strip()
        week = metadata.get('week', 'Unknown')
        
        # Apply filters
        if (selected_patients and patient_id not in selected_patients) or \
           (selected_sessions and session_type not in selected_sessions) or \
           (selected_conditions and condition_value not in selected_conditions):
            continue
        
        # Initialize counters
        caregiver_word_repeats = 0
        plwd_word_repeats = 0
        caregiver_turns = 0
        plwd_turns = 0
        caregiver_words = 0
        plwd_words = 0
        
        # Process each turn in the file
        for _, turn_row in turns_df[turns_df['file_name'] == filename].iterrows():
            speaker = turn_row['speaker']
            turn_text = str(turn_row['turn_text']) if pd.notna(turn_row['turn_text']) else ''
            word_count = turn_row['word_count'] if pd.notna(turn_row['word_count']) else len(turn_text.split())
            
            # Count turns and words by speaker
            if speaker == 'caregiver':
                caregiver_turns += 1
                caregiver_words += word_count
            elif speaker == 'plwd':
                plwd_turns += 1
                plwd_words += word_count
            
            # Analyze word repeats for this turn
            if WORD_REPEAT_AVAILABLE and turn_text.strip():
                word_repeat_analysis = analyze_turn_for_word_repeats(turn_text)
                repeat_count = word_repeat_analysis['count']
                
                if repeat_count > 0:
                    if speaker == 'caregiver':
                        caregiver_word_repeats += repeat_count
                    elif speaker == 'plwd':
                        plwd_word_repeats += repeat_count
                    
                    # Store examples for later display
                    for example in word_repeat_analysis['examples']:
                        example_data[week].append({
                            'participant_id': patient_id,
                            'file_name': filename,
                            'session_type': session_type,
                            'condition': condition_value,
                            'speaker': speaker,
                            'word': example['word'],
                            'context': example['context'],
                            'count': example['count'],
                            'turn_text': turn_text[:200] + '...' if len(turn_text) > 200 else turn_text
                        })
        
        # Create file summary
        word_repeat_rows.append({
            "Patient ID": patient_id,
            "Filename": filename,
            "Session Type": session_type,
            "Condition": condition_value,
            "Week": week,
            "Caregiver Word Repeats": caregiver_word_repeats,
            "PLWD Word Repeats": plwd_word_repeats,
            "Total Word Repeats": caregiver_word_repeats + plwd_word_repeats,
            "Caregiver Turns": caregiver_turns,
            "PLWD Turns": plwd_turns,
            "Caregiver Words": caregiver_words,
            "PLWD Words": plwd_words
        })
    
    # Convert to DataFrame
    df_word_repeats = pd.DataFrame(word_repeat_rows) if word_repeat_rows else pd.DataFrame()
    
    return df_word_repeats, example_data

def main():
    st.title("Word Repeats Analysis")
    st.markdown("*Analyzing immediate word repetitions in transcript data using NLP techniques*")
    
    # Show word repeat availability status
    if WORD_REPEAT_AVAILABLE:
        st.success("✅ Word Repeat Detection Available (Using NLTK)")
    else:
        st.warning("⚠️ Word Repeat Detection Disabled - Install nltk for full functionality")
        st.info("Run: `pip install nltk` to enable word repeat detection")
        return
    
    # Load enriched turns data to get filter options
    turns_df = load_enriched_turns_data()
    if turns_df.empty:
        st.error("Could not load enriched turns data. Please check that enriched_turns.csv exists.")
        return
    
    # Load classified data for filters
    classified_data = load_json(CLASSIFIED_PATH)
    
    # Filter out Final Interview files from filter options
    non_final_classified = [f for f in classified_data if not f.get("final_interview", False) 
                           and f.get("session_type", "") != "Final Interview"]
    
    # Get filter options
    all_patients = sorted(set(f["patient_id"] for f in non_final_classified if f.get("patient_id")))
    all_sessions = sorted(set(f["session_type"] for f in non_final_classified if f.get("session_type")))
    all_conditions = sorted(list(set(f.get("condition_value", "").strip() for f in non_final_classified if f.get("condition_value"))))
    
    # Display data info
    st.info(f"Loaded {len(turns_df):,} turns from {turns_df['file_name'].nunique()} files across {turns_df['participant_id'].nunique()} participants")
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_patients = st.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    with col2:
        selected_sessions = st.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    with col3:
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Extract word repeat data based on filters
    df_word_repeats, example_data = extract_word_repeat_data(
        selected_patients, selected_sessions, selected_conditions
    )
    
    if df_word_repeats.empty:
        st.warning("No data available for selected filters.")
        return
    
    # Display filter information
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    
    st.markdown(f"### Showing Word Repeat Analysis for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # Convert 'Week' to numeric for proper sorting and calculations
    if 'Week' in df_word_repeats.columns:
        df_word_repeats['Week'] = pd.to_numeric(df_word_repeats['Week'], errors='coerce')
    
    # Create week label for display purposes
    df_word_repeats["Week Label"] = df_word_repeats["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}" if not pd.isna(w) else "Unknown"
    )
    
    # Calculate word repeat rates: word repeats per 100 words
    if not df_word_repeats.empty:
        # Avoid division by zero
        df_word_repeats['Caregiver Words'] = df_word_repeats['Caregiver Words'].replace(0, 1)
        df_word_repeats['PLWD Words'] = df_word_repeats['PLWD Words'].replace(0, 1)
        
        df_word_repeats['Caregiver Word Repeat Rate'] = (df_word_repeats['Caregiver Word Repeats'] / df_word_repeats['Caregiver Words'] * 100).round(2)
        df_word_repeats['PLWD Word Repeat Rate'] = (df_word_repeats['PLWD Word Repeats'] / df_word_repeats['PLWD Words'] * 100).round(2)
        df_word_repeats['Overall Word Repeat Rate'] = ((df_word_repeats['Caregiver Word Repeats'] + df_word_repeats['PLWD Word Repeats']) / 
                                                   (df_word_repeats['Caregiver Words'] + df_word_repeats['PLWD Words']) * 100).round(2)
    
    # --- Display detailed table ---
    st.subheader("Detailed Word Repeat Statistics by File")
    
    # Define columns for detailed view
    display_columns = [
        'Week Label', 'Patient ID', 'Session Type', 'Condition', 'Filename',
        'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
        'Caregiver Word Repeats', 'PLWD Word Repeats', 'Total Word Repeats',
        'Caregiver Word Repeat Rate', 'PLWD Word Repeat Rate', 'Overall Word Repeat Rate'
    ]
    
    # Sort by Week and Patient ID for better readability
    df_sorted = df_word_repeats.sort_values(['Week', 'Patient ID']).fillna(0)
    
    # Format numeric columns
    st.dataframe(
        df_sorted[display_columns].style
        .format({
            'Caregiver Word Repeat Rate': '{:.2f}%',
            'PLWD Word Repeat Rate': '{:.2f}%',
            'Overall Word Repeat Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f0f8ff', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- Weekly Aggregated Summary ---
    st.subheader("Weekly Aggregated Word Repeat Summary")
    
    # Group by week and calculate statistics
    summary_df = df_word_repeats.groupby("Week Label").agg({
        "Caregiver Word Repeats": "sum",
        "PLWD Word Repeats": "sum",
        "Caregiver Words": "sum",
        "PLWD Words": "sum",
        "Total Word Repeats": "sum",
        "Patient ID": "nunique",
        "Filename": "count"
    }).reset_index()
    
    # Rename columns for clarity
    summary_df = summary_df.rename(columns={
        "Patient ID": "Unique Patients",
        "Filename": "File Count"
    })
    
    # Calculate word repeat rates for the summary
    summary_df["Caregiver Word Repeat Rate"] = (summary_df["Caregiver Word Repeats"] / summary_df["Caregiver Words"] * 100).round(2)
    summary_df["PLWD Word Repeat Rate"] = (summary_df["PLWD Word Repeats"] / summary_df["PLWD Words"] * 100).round(2)
    summary_df["Overall Word Repeat Rate"] = ((summary_df["Caregiver Word Repeats"] + summary_df["PLWD Word Repeats"]) / 
                                           (summary_df["Caregiver Words"] + summary_df["PLWD Words"]) * 100).round(2)
    
    # Display summary table
    st.dataframe(
        summary_df.style
        .format({
            'Caregiver Word Repeat Rate': '{:.2f}%',
            'PLWD Word Repeat Rate': '{:.2f}%',
            'Overall Word Repeat Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- Visualizations ---
    st.subheader("Word Repeat Visualizations")
    
    # Tab-based visualization layout
    tab1, tab2, tab3, tab4 = st.tabs(["By Speaker", "Trends Over Time", "By Condition", "Detailed Analysis"])
    
    with tab1:
        st.subheader("Word Repeat Rate by Speaker")
        
        # Word repeat rates by speaker
        repeat_speaker_df = df_word_repeats.groupby('Patient ID').agg({
            'Caregiver Word Repeat Rate': 'mean',
            'PLWD Word Repeat Rate': 'mean'
        }).reset_index()
        
        repeat_speaker_melted = pd.melt(
            repeat_speaker_df,
            id_vars=['Patient ID'],
            value_vars=['Caregiver Word Repeat Rate', 'PLWD Word Repeat Rate'],
            var_name='Speaker',
            value_name='Word Repeat Rate (%)'
        )
        
        fig_repeat_speaker = px.bar(
            repeat_speaker_melted,
            x='Patient ID',
            y='Word Repeat Rate (%)',
            color='Speaker',
            barmode='group',
            title="Average Word Repeat Rate by Speaker and Participant",
            color_discrete_map={'Caregiver Word Repeat Rate': '#FF6B6B', 'PLWD Word Repeat Rate': '#4ECDC4'}
        )
        
        st.plotly_chart(fig_repeat_speaker, use_container_width=True)
    
    with tab2:
        st.subheader("Word Repeat Trends Over Time")
        
        # Word repeat trends over time
        repeat_week_df = df_word_repeats.groupby('Week').agg({
            'Caregiver Word Repeats': 'sum',
            'PLWD Word Repeats': 'sum',
            'Caregiver Words': 'sum',
            'PLWD Words': 'sum'
        }).reset_index()
        
        repeat_week_df['Caregiver Repeat Rate'] = (repeat_week_df['Caregiver Word Repeats'] / repeat_week_df['Caregiver Words'] * 100).round(2)
        repeat_week_df['PLWD Repeat Rate'] = (repeat_week_df['PLWD Word Repeats'] / repeat_week_df['PLWD Words'] * 100).round(2)
        
        fig_repeat_week = px.line(
            repeat_week_df,
            x='Week',
            y=['Caregiver Repeat Rate', 'PLWD Repeat Rate'],
            title="Word Repeat Rate Trends Over Study Weeks",
            labels={'value': 'Word Repeat Rate (%)', 'variable': 'Speaker'},
            markers=True,
            color_discrete_map={'Caregiver Repeat Rate': '#FF6B6B', 'PLWD Repeat Rate': '#4ECDC4'}
        )
        
        st.plotly_chart(fig_repeat_week, use_container_width=True)
        
        # Scatter plot animation over time
        if not df_word_repeats.empty and 'Week' in df_word_repeats.columns:
            motion_df = df_word_repeats.copy()
            
            fig_motion = px.scatter(
                motion_df,
                x="Caregiver Word Repeats",
                y="PLWD Word Repeats",
                size="Total Word Repeats",
                size_max=20,
                color="Patient ID",
                animation_frame="Week Label",
                hover_name="Patient ID",
                title="Word Repeats by Week (Motion View)",
                labels={
                    "Caregiver Word Repeats": "Caregiver Word Repeats",
                    "PLWD Word Repeats": "PLWD Word Repeats"
                }
            )
            
            # Add diagonal reference line
            max_repeats = max(
                motion_df["Caregiver Word Repeats"].max() if not motion_df.empty else 10,
                motion_df["PLWD Word Repeats"].max() if not motion_df.empty else 10
            )
            
            fig_motion.add_shape(
                type="line",
                x0=0, y0=0,
                x1=max_repeats, y1=max_repeats,
                line=dict(color="rgba(0,0,0,0.3)", dash="dash")
            )
            
            fig_motion.update_layout(
                xaxis=dict(range=[0, max_repeats * 1.1]),
                yaxis=dict(range=[0, max_repeats * 1.1])
            )
            
            st.plotly_chart(fig_motion, use_container_width=True)
    
    with tab3:
        st.subheader("Word Repeats by Condition")
        
        # Group by Condition
        condition_df = df_word_repeats.groupby('Condition').agg({
            'Caregiver Word Repeats': 'sum',
            'PLWD Word Repeats': 'sum',
            'Caregiver Words': 'sum',
            'PLWD Words': 'sum'
        }).reset_index()
        
        # Calculate rates
        condition_df['Caregiver Rate'] = (condition_df['Caregiver Word Repeats'] / condition_df['Caregiver Words'] * 100).round(2)
        condition_df['PLWD Rate'] = (condition_df['PLWD Word Repeats'] / condition_df['PLWD Words'] * 100).round(2)
        
        condition_df_melted = pd.melt(
            condition_df,
            id_vars=['Condition'],
            value_vars=['Caregiver Rate', 'PLWD Rate'],
            var_name='Speaker',
            value_name='Word Repeat Rate (%)'
        )
        
        fig_condition = px.bar(
            condition_df_melted,
            x='Condition', 
            y='Word Repeat Rate (%)',
            color='Speaker',
            barmode='group',
            title="Word Repeat Rates by Condition Type and Speaker",
            color_discrete_map={'Caregiver Rate': '#FF6B6B', 'PLWD Rate': '#4ECDC4'}
        )
        
        st.plotly_chart(fig_condition, use_container_width=True)
    
    with tab4:
        st.subheader("Detailed Analysis")
        
        # Bubble chart: Word repeats by file
        fig_bubble = px.scatter(
            df_word_repeats,
            x="Caregiver Word Repeats",
            y="PLWD Word Repeats",
            size="Total Word Repeats",
            color="Condition", 
            hover_name="Patient ID",
            title="Word Repeats Distribution by File",
            labels={
                "Caregiver Word Repeats": "Caregiver Word Repeats",
                "PLWD Word Repeats": "PLWD Word Repeats"
            }
        )
        
        st.plotly_chart(fig_bubble, use_container_width=True)
        
        # Correlation analysis
        if len(df_word_repeats) > 1:
            st.subheader("Correlation Analysis")
            
            correlation_data = df_word_repeats[['Caregiver Word Repeat Rate', 'PLWD Word Repeat Rate', 
                                             'Caregiver Words', 'PLWD Words']].corr()
            
            fig_corr = px.imshow(
                correlation_data,
                title="Correlation Matrix: Word Repeat Rates and Word Counts",
                color_continuous_scale="RdBu",
                color_continuous_midpoint=0,
                text_auto=True
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
    
    # --- Word Repeat Examples Section ---
    if example_data:
        st.subheader("Word Repeat Examples by Week")
        
        # Sort weeks for consistent display
        try:
            sorted_weeks = sorted([w for w in example_data.keys() if w is not None], 
                                key=lambda x: float(x) if str(x).replace('.','').isdigit() else float('inf'))
        except ValueError:
            sorted_weeks = sorted([w for w in example_data.keys() if w is not None])
        
        if 'Unknown' in example_data:
            sorted_weeks.append('Unknown')
        
        for week in sorted_weeks:
            examples = example_data[week]
            
            if examples:
                with st.expander(f"Week {week} Word Repeat Examples ({len(examples)} examples)"):
                    for idx, example in enumerate(examples[:20]):  # Limit to 20 examples per week
                        speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                        st.markdown(f"{idx+1}. {speaker_bold}: {example['context']}")
                        st.markdown(f"   - Repeated Word: **{example['word']}** (repeated {example['count']} times), Session: {example['session_type']}, Condition: {example['condition']}")
                        st.caption(f"From: {example['file_name']}")
                        st.divider()
                    
                    if len(examples) > 20:
                        st.info(f"{len(examples) - 20} more examples not shown")
            else:
                with st.expander(f"Week {week} Word Repeat Examples"):
                    st.info("No word repeat examples available for the selected filters.")
    
    # --- Summary statistics ---
    st.subheader("Summary Statistics")
    
    # Calculate summary statistics
    total_caregiver_word_repeats = df_word_repeats['Caregiver Word Repeats'].sum()
    total_plwd_word_repeats = df_word_repeats['PLWD Word Repeats'].sum()
    total_caregiver_words = df_word_repeats['Caregiver Words'].sum()
    total_plwd_words = df_word_repeats['PLWD Words'].sum()
    
    # Calculate average rates safely
    avg_caregiver_repeat_rate = (total_caregiver_word_repeats / total_caregiver_words * 100) if total_caregiver_words > 0 else 0
    avg_plwd_repeat_rate = (total_plwd_word_repeats / total_plwd_words * 100) if total_plwd_words > 0 else 0
    
    summary_data = {
        "Total Caregiver Word Repeats": total_caregiver_word_repeats,
        "Total PLWD Word Repeats": total_plwd_word_repeats,
        "Total Caregiver Words": total_caregiver_words,
        "Total PLWD Words": total_plwd_words,
        "Average Caregiver Word Repeat Rate": avg_caregiver_repeat_rate,
        "Average PLWD Word Repeat Rate": avg_plwd_repeat_rate,
        "Total Files Analyzed": len(df_word_repeats),
        "Total Participants": df_word_repeats['Patient ID'].nunique()
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_transposed = summary_df.T.rename(columns={0: 'Value'})
    
    # Format the summary
    def safe_format(x, name):
        try:
            if "Rate" in name:
                return f"{x:.2f}%" if pd.notna(x) and not np.isinf(x) else "0.00%"
            else:
                return f"{int(x):,}" if pd.notna(x) else "0"
        except (ValueError, TypeError):
            return str(x)
    
    formatted_df = pd.DataFrame()
    formatted_df['Value'] = [safe_format(x, name) for name, x in zip(summary_transposed.index, summary_transposed['Value'])]
    formatted_df.index = summary_transposed.index
    
    st.dataframe(formatted_df, use_container_width=True)

if __name__ == "__main__":
    main() 