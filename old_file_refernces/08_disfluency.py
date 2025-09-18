import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"
TRANSCRIPT_INSIGHTS_PATH = "transcript_insights_updated.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_disfluency_data(selected_patients, selected_sessions, selected_conditions):
    # Load data from all sources
    classified_data = load_json(CLASSIFIED_PATH)
    enhanced_data = load_json(ENHANCED_ANALYSIS_PATH)
    transcript_insights = load_json(TRANSCRIPT_INSIGHTS_PATH)
    
    # Create a mapping of filenames to metadata from classified_data
    filename_to_metadata = {f['filename']: f for f in classified_data}
    
    # Process data for analysis
    disfluency_rows = []
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
        
        # Get statistics
        stats = file_data.get("stats", {})
        
        # Get transcript insights data for turn and word counts
        turn_word_data = {}
        if patient_id in transcript_insights:
            for session_category in transcript_insights[patient_id].values():
                if filename in session_category and "basic_statistics" in session_category[filename]:
                    turn_word_data = session_category[filename]["basic_statistics"]
                    break
        
        # Extract disfluency counts from turn-level data (consistent with other pages)
        caregiver_disfluencies = 0
        plwd_disfluencies = 0
        disfluency_types = {}
        
        # Count disfluencies from turns (matching summary.py, total_view.py, weekly_analysis.py approach)
        for turn in file_data.get("turns", []):
            speaker = turn.get('speaker', '').lower()
            disfluencies = turn.get('disfluencies', [])
            
            # Count disfluencies by speaker
            if disfluencies and len(disfluencies) > 0:
                if speaker == 'caregiver':
                    caregiver_disfluencies += len(disfluencies)
                elif speaker == 'plwd':
                    plwd_disfluencies += len(disfluencies)
                
                # Count disfluency types
                for disfluency in disfluencies:
                    d_type = disfluency.get("type", "unknown")
                    disfluency_types[d_type] = disfluency_types.get(d_type, 0) + 1
        
        # Create entry for the table
        entry = {
            "Patient ID": patient_id,
            "Filename": filename,
            "Session Type": session_type,
            "Condition": condition_value,
            "Week": week,
            "Caregiver Disfluencies": caregiver_disfluencies,
            "PLWD Disfluencies": plwd_disfluencies,
            "Total Disfluencies": caregiver_disfluencies + plwd_disfluencies,
            "Caregiver Turns": turn_word_data.get("caregiver_turns", 0),
            "PLWD Turns": turn_word_data.get("plwd_turns", 0),
            "Caregiver Words": turn_word_data.get("caregiver_words", 0),
            "PLWD Words": turn_word_data.get("plwd_words", 0)
        }
        
        # Add disfluency type counts
        for d_type, count in disfluency_types.items():
            entry[f"{d_type.replace('_', ' ').title()}"] = count
        
        disfluency_rows.append(entry)
        
        # Collect examples
        for turn in file_data.get("turns", []):
            if turn.get("disfluencies"):
                for disfluency in turn.get("disfluencies", []):
                    example = {
                        "patient_id": patient_id,
                        "filename": filename,
                        "week": week,
                        "session_type": session_type,
                        "condition": condition_value,
                        "speaker": turn.get("speaker", "unknown"),
                        "text": turn.get("text", ""),
                        "disfluency_type": disfluency.get("type", "unknown"),
                        "disfluency_text": disfluency.get("text", "")
                    }
                    example_data[week].append(example)
    
    # Convert to DataFrame for display
    df_disfluency = pd.DataFrame(disfluency_rows) if disfluency_rows else pd.DataFrame()
    
    return df_disfluency, example_data

def main():
    st.title("Disfluency Analysis")
    
    # Load classified data for filters
    classified = load_json(CLASSIFIED_PATH)
    
    # Filter out Final Interview files from filter options
    non_final_classified = [f for f in classified if not f.get("final_interview", False) 
                           and f.get("session_type", "") != "Final Interview"]
    
    # Get filter options
    all_patients = sorted(set(f["patient_id"] for f in non_final_classified if f.get("patient_id")))
    all_sessions = sorted(set(f["session_type"] for f in non_final_classified if f.get("session_type")))
    all_conditions = sorted(list(set(f.get("condition_value", "").strip() for f in non_final_classified if f.get("condition_value"))))
    
    # Create filters - at the top of the page, not in sidebar
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_patients = st.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    with col2:
        selected_sessions = st.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    with col3:
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Extract disfluency data based on filters
    df_disfluency, example_data = extract_disfluency_data(selected_patients, selected_sessions, selected_conditions)
    
    if df_disfluency.empty:
        st.warning("No disfluency data available for selected filters.")
        return
    
    # --- Display the dynamic header with filter information ---
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    
    st.markdown(f"### Showing Disfluency Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # Convert 'Week' to numeric for proper sorting and calculations
    if 'Week' in df_disfluency.columns:
        df_disfluency['Week'] = pd.to_numeric(df_disfluency['Week'], errors='coerce')
    
    # Create week label for display purposes
    df_disfluency["Week Label"] = df_disfluency["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}" if not pd.isna(w) else "Unknown"
    )
    
    # Calculate rate metrics: disfluencies per 100 words (not per turn)
    # Note: Disfluency counts come from turn-level analysis, but rates use word counts for meaningful percentages
    if not df_disfluency.empty:
        df_disfluency['Caregiver Disfluency Rate'] = (df_disfluency['Caregiver Disfluencies'] / df_disfluency['Caregiver Words'] * 100).round(2)
        df_disfluency['PLWD Disfluency Rate'] = (df_disfluency['PLWD Disfluencies'] / df_disfluency['PLWD Words'] * 100).round(2)
        df_disfluency['Overall Disfluency Rate'] = ((df_disfluency['Caregiver Disfluencies'] + df_disfluency['PLWD Disfluencies']) / 
                                                  (df_disfluency['Caregiver Words'] + df_disfluency['PLWD Words']) * 100).round(2)
    
    # --- Display detailed table ---
    st.subheader("Detailed Disfluency Statistics by File")
    
    # Define columns for detailed view
    display_columns = [
        'Week Label', 'Patient ID', 'Session Type', 'Condition', 'Filename',
        'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
        'Caregiver Disfluencies', 'PLWD Disfluencies', 'Total Disfluencies',
        'Caregiver Disfluency Rate', 'PLWD Disfluency Rate', 'Overall Disfluency Rate'
    ]
    
    # Add any disfluency type columns that exist
    disfluency_type_columns = [col for col in df_disfluency.columns if col not in display_columns 
                             and col not in ['Week']]
    
    if disfluency_type_columns:
        display_columns.extend(disfluency_type_columns)
    
    # Sort by Week and Patient ID for better readability
    df_sorted = df_disfluency.sort_values(['Week', 'Patient ID']).fillna(0)
    
    # Format numeric columns
    st.dataframe(
        df_sorted[display_columns].style
        .format({
            'Caregiver Disfluency Rate': '{:.2f}%',
            'PLWD Disfluency Rate': '{:.2f}%',
            'Overall Disfluency Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f0f8ff', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- Weekly Aggregated Summary ---
    st.subheader("Weekly Aggregated Disfluency Summary")
    
    # Group by week and calculate statistics
    summary_df = df_disfluency.groupby("Week Label").agg({
        "Caregiver Disfluencies": "sum",
        "PLWD Disfluencies": "sum",
        "Caregiver Words": "sum",
        "PLWD Words": "sum",
        "Total Disfluencies": "sum",
        "Patient ID": "nunique",
        "Filename": "count"
    }).reset_index()
    
    # Rename columns for clarity
    summary_df = summary_df.rename(columns={
        "Patient ID": "Unique Patients",
        "Filename": "File Count"
    })
    
    # Calculate rates for the summary
    summary_df["Caregiver Disfluency Rate"] = (summary_df["Caregiver Disfluencies"] / summary_df["Caregiver Words"] * 100).round(2)
    summary_df["PLWD Disfluency Rate"] = (summary_df["PLWD Disfluencies"] / summary_df["PLWD Words"] * 100).round(2)
    summary_df["Overall Disfluency Rate"] = ((summary_df["Caregiver Disfluencies"] + summary_df["PLWD Disfluencies"]) / 
                                           (summary_df["Caregiver Words"] + summary_df["PLWD Words"]) * 100).round(2)
    
    # Display summary table
    st.dataframe(
        summary_df.style
        .format({
            'Caregiver Disfluency Rate': '{:.2f}%',
            'PLWD Disfluency Rate': '{:.2f}%',
            'Overall Disfluency Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- Visualizations ---
    st.subheader("Disfluency Visualizations")
    
    # Tab-based visualization layout
    tab1, tab2, tab3 = st.tabs(["By Speaker", "By Week", "By Condition"])
    
    with tab1:
        st.subheader("Disfluency by Speaker")
        
        # Group by patient_id and calculate average disfluency rates
        speaker_df = df_disfluency.groupby('Patient ID').agg({
            'Caregiver Disfluency Rate': 'mean',
            'PLWD Disfluency Rate': 'mean'
        }).reset_index()
        
        # Create a bar chart comparing caregiver vs PLWD disfluency rates by patient
        speaker_df_melted = pd.melt(
            speaker_df, 
            id_vars=['Patient ID'],
            value_vars=['Caregiver Disfluency Rate', 'PLWD Disfluency Rate'],
            var_name='Speaker',
            value_name='Disfluency Rate (%)'
        )
        
        fig_speaker = px.bar(
            speaker_df_melted,
            x='Patient ID',
            y='Disfluency Rate (%)',
            color='Speaker',
            barmode='group',
            title="Average Disfluency Rate by Speaker and Participant",
            labels={'value': 'Disfluency Rate (%)'},
        )
        
        st.plotly_chart(fig_speaker, use_container_width=True)
        
    with tab2:
        st.subheader("Disfluency Trends Over Time")
        
        # Group by Week and calculate aggregated metrics
        week_df = df_disfluency.groupby('Week').agg({
            'Caregiver Disfluencies': 'sum',
            'PLWD Disfluencies': 'sum',
            'Caregiver Words': 'sum',
            'PLWD Words': 'sum'
        }).reset_index()
        
        # Calculate rates: disfluencies per 100 words (aggregated by week)
        week_df['Caregiver Rate'] = (week_df['Caregiver Disfluencies'] / week_df['Caregiver Words'] * 100).round(2)
        week_df['PLWD Rate'] = (week_df['PLWD Disfluencies'] / week_df['PLWD Words'] * 100).round(2)
        
        # Create line chart for trends
        fig_week = px.line(
            week_df,
            x='Week',
            y=['Caregiver Rate', 'PLWD Rate'],
            title="Disfluency Rate Trends Over Study Weeks",
            labels={'value': 'Disfluency Rate (%)', 'variable': 'Speaker'},
            markers=True
        )
        
        st.plotly_chart(fig_week, use_container_width=True)
        
        # Scatter plot of disfluencies per week (motion view)
        if not df_disfluency.empty and 'Week' in df_disfluency.columns:
            motion_df = df_disfluency.copy()
            
            fig_motion = px.scatter(
                motion_df,
                x="Caregiver Disfluencies",
                y="PLWD Disfluencies",
                size="Total Disfluencies",
                size_max=20,
                color="Patient ID",
                animation_frame="Week Label",
                hover_name="Patient ID",
                title="Disfluencies by Week (Motion View)",
                labels={
                    "Caregiver Disfluencies": "Caregiver Disfluencies",
                    "PLWD Disfluencies": "PLWD Disfluencies"
                }
            )
            
            # Add diagonal reference line for perfect balance
            max_disfluencies = max(
                motion_df["Caregiver Disfluencies"].max() if not motion_df.empty else 10,
                motion_df["PLWD Disfluencies"].max() if not motion_df.empty else 10
            )
            
            fig_motion.add_shape(
                type="line",
                x0=0, y0=0,
                x1=max_disfluencies, y1=max_disfluencies,
                line=dict(color="rgba(0,0,0,0.3)", dash="dash")
            )
            
            # Update layout for better readability
            fig_motion.update_layout(
                xaxis=dict(range=[0, max_disfluencies * 1.1]),
                yaxis=dict(range=[0, max_disfluencies * 1.1])
            )
            
            st.plotly_chart(fig_motion, use_container_width=True)
        
    with tab3:
        st.subheader("Disfluency by Condition")
        
        # Group by Condition
        condition_df = df_disfluency.groupby('Condition').agg({
            'Caregiver Disfluencies': 'sum',
            'PLWD Disfluencies': 'sum',
            'Caregiver Words': 'sum',
            'PLWD Words': 'sum'
        }).reset_index()
        
        # Calculate rates: disfluencies per 100 words (aggregated by condition)
        condition_df['Caregiver Rate'] = (condition_df['Caregiver Disfluencies'] / condition_df['Caregiver Words'] * 100).round(2)
        condition_df['PLWD Rate'] = (condition_df['PLWD Disfluencies'] / condition_df['PLWD Words'] * 100).round(2)
        
        # Create stacked bar chart by condition
        condition_df_melted = pd.melt(
            condition_df,
            id_vars=['Condition'],
            value_vars=['Caregiver Rate', 'PLWD Rate'],
            var_name='Speaker',
            value_name='Disfluency Rate (%)'
        )
        
        fig_condition = px.bar(
            condition_df_melted,
            x='Condition', 
            y='Disfluency Rate (%)',
            color='Speaker',
            barmode='group',
            title="Disfluency Rates by Condition Type and Speaker",
        )
        
        st.plotly_chart(fig_condition, use_container_width=True)
        
        # Polar chart for condition comparison
        st.subheader("Disfluency Comparison (Interactive Polar Chart)")
        
        # Get unique conditions for comparison
        all_available_conditions = sorted(condition_df['Condition'].unique())
        
        if len(all_available_conditions) > 1:
            selected_condition_groups = st.multiselect(
                "Select Conditions to compare:",
                options=all_available_conditions,
                default=all_available_conditions[:min(3, len(all_available_conditions))]
            )
            
            if selected_condition_groups:
                filtered_condition_df = condition_df[condition_df['Condition'].isin(selected_condition_groups)]
                
                polar_data_list = []
                for _, row in filtered_condition_df.iterrows():
                    polar_data_list.append({
                        "Speaker": "Caregiver", 
                        "Condition": row['Condition'], 
                        "Disfluency Rate": row['Caregiver Rate']
                    })
                    polar_data_list.append({
                        "Speaker": "PLWD", 
                        "Condition": row['Condition'], 
                        "Disfluency Rate": row['PLWD Rate']
                    })
                
                polar_df = pd.DataFrame(polar_data_list)
                
                fig_polar = px.bar_polar(
                    polar_df,
                    r="Disfluency Rate",
                    theta="Speaker",
                    color="Condition", 
                    barmode="group",
                    title="Condition Type Disfluency Rate Comparison"
                )
                
                st.plotly_chart(fig_polar, use_container_width=True)
            else:
                st.info("Please select conditions to compare")
        else:
            st.info("Not enough condition types for comparison")
    
    # --- Disfluency Examples Section ---
    st.subheader("Disfluency Examples by Week")
    
    # Sort weeks for consistent display (handling text vs numeric weeks)
    try:
        sorted_weeks = sorted([w for w in example_data.keys() if w is not None], 
                            key=lambda x: float(x) if x and x != 'Unknown' else float('inf'))
    except ValueError:
        sorted_weeks = sorted([w for w in example_data.keys() if w is not None])
    
    if 'Unknown' in example_data:
        sorted_weeks.append('Unknown')
    
    for week in sorted_weeks:
        examples = example_data[week]
        
        if examples:
            with st.expander(f"Week {week} Examples ({len(examples)} examples)"):
                for idx, example in enumerate(examples[:30]):  # Limit to 30 examples per week to prevent UI overload
                    speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                    disfluency_highlighted = example['text'].replace(
                        example['disfluency_text'], 
                        f"**[{example['disfluency_text']}]**"
                    ) if example['disfluency_text'] in example['text'] else example['text']
                    
                    st.markdown(f"{idx+1}. {speaker_bold}: {disfluency_highlighted}")
                    st.markdown(f"   - Disfluency Type: {example['disfluency_type']}, Session: {example['session_type']}, Condition: {example['condition']}")
                    st.divider()
                
                if len(examples) > 30:
                    st.info(f"{len(examples) - 30} more examples not shown")
        else:
            with st.expander(f"Week {week} Examples"):
                st.info("No examples available for the selected filters.")
    
    # --- Summary statistics ---
    st.subheader("Summary Statistics")
    
    # Group by speaker type for overall statistics
    total_caregiver_disfluencies = df_disfluency['Caregiver Disfluencies'].sum()
    total_plwd_disfluencies = df_disfluency['PLWD Disfluencies'].sum()
    total_caregiver_words = df_disfluency['Caregiver Words'].sum()
    total_plwd_words = df_disfluency['PLWD Words'].sum()
    
    # Calculate average rates safely (avoid division by zero): disfluencies per 100 words
    if total_caregiver_words > 0:
        avg_caregiver_rate = (total_caregiver_disfluencies / total_caregiver_words * 100)
    else:
        avg_caregiver_rate = 0
        
    if total_plwd_words > 0:
        avg_plwd_rate = (total_plwd_disfluencies / total_plwd_words * 100)
    else:
        avg_plwd_rate = 0
    
    summary_data = {
        "Total Caregiver Disfluencies": total_caregiver_disfluencies,
        "Total PLWD Disfluencies": total_plwd_disfluencies,
        "Total Caregiver Words": total_caregiver_words,
        "Total PLWD Words": total_plwd_words,
        "Average Caregiver Disfluency Rate": avg_caregiver_rate,
        "Average PLWD Disfluency Rate": avg_plwd_rate,
    }
    
    summary_df = pd.DataFrame([summary_data])
    
    # Add disfluency type totals
    for col in disfluency_type_columns:
        summary_df[f"Total {col}"] = df_disfluency[col].sum()
    
    # Display summary
    summary_transposed = summary_df.T.rename(columns={0: 'Value'})
    
    # Create a safe formatter function that handles potential errors
    def safe_format(x, name):
        try:
            if "Rate" in name:
                if pd.notna(x) and not np.isinf(x) and not np.isneginf(x):
                    return f"{x:.2f}%"
                else:
                    return "0.00%"
            else:
                return f"{int(x):,}" if pd.notna(x) and not pd.isna(x) else "0"
        except (ValueError, TypeError):
            return str(x)
    
    # Apply formatting with error handling
    formatted_df = pd.DataFrame()
    formatted_df['Value'] = [safe_format(x, name) for name, x in zip(summary_transposed.index, summary_transposed['Value'])]
    formatted_df.index = summary_transposed.index
    
    # Display the formatted dataframe
    st.dataframe(formatted_df, use_container_width=True)

if __name__ == "__main__":
    main() 