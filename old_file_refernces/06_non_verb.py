import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
from collections import defaultdict

# --- Loaders ---

def load_classified_data(classified_json_path):
    with open(classified_json_path, 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    return classified_data


def load_enriched_data(enriched_json_path):
    with open(enriched_json_path, 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)
    return enriched_data

def load_enhanced_analysis(enhanced_analysis_path):
    with open(enhanced_analysis_path, 'r', encoding='utf-8') as f:
        enhanced_data = json.load(f)
    return enhanced_data

# --- Paths to your JSON files ---
CLASSIFIED_JSON_PATH = "classified_output_1.json"
ENRICHED_JSON_PATH = "transcript_insights_updated.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis_fixed.json"  # Using cleaned/normalized data

# --- Main Streamlit App for Non-verbal Analysis ---

def main():
    st.title("Nonverbal Communication Analysis")
    
    # Display data quality note
    st.info("📊 **Data Quality Improvements**: Non-verbal cues have been cleaned and normalized. "
            "Language annotations (e.g., 'speaking Portuguese'), technical metadata, and variations "
            "like '[inaudible]' vs 'inaudible' have been standardized for consistent analysis.")

    classified_data = load_classified_data(CLASSIFIED_JSON_PATH)
    enriched_data = load_enriched_data(ENRICHED_JSON_PATH)
    enhanced_data = load_enhanced_analysis(ENHANCED_ANALYSIS_PATH)

    if not classified_data or not enriched_data or not enhanced_data:
        st.warning("One or more required data files could not be loaded.")
        return

    # Filter out Final Interview files
    classified_data = [f for f in classified_data if not f.get("final_interview", False) 
                      and f.get("session_type", "") != "Final Interview"]

    # Filters - kept on the main page (not in sidebar)
    all_patients = sorted(set(f['patient_id'] for f in classified_data if f.get('patient_id')))
    all_sessions = sorted(set(f['session_type'] for f in classified_data if f.get('session_type')))
    # Normalize conditions for the filter options by stripping whitespace
    all_conditions = sorted(list(set(f.get("condition_value", "").strip() for f in classified_data if f.get("condition_value"))))

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_patients = st.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    with col2:
        selected_sessions = st.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    with col3:
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)

    # Create a filename to metadata mapping for quick lookups
    filename_to_metadata = {f['filename']: f for f in classified_data}

    # Define categories for separation
    EXTRA_CUES = {'inaudible', 'pause', 'interruption'}  # These will go to "Extra" section
    
    # Prepare nonverbal analysis data
    nonverbal_rows = []
    extra_rows = []  # New section for inaudible, pause, interruption
    example_data = defaultdict(list)
    extra_example_data = defaultdict(list)

    # Process enhanced transcript analysis data for nonverbal cues
    for filename, file_data in enhanced_data.get("by_file", {}).items():
        # Get metadata from classified data or from the file data itself
        metadata = file_data.get("metadata", {})
        if not metadata:
            metadata = filename_to_metadata.get(filename, {})
            
        patient_id = metadata.get('patient_id', 'Unknown')
        session_type = metadata.get('session_type', 'Unknown')
        condition_value = metadata.get('condition_value', '').strip()
        week = metadata.get('week', 'Unknown')

        # Apply filters
        if selected_patients and patient_id not in selected_patients:
            continue
        if selected_sessions and session_type not in selected_sessions:
            continue
        if selected_conditions and condition_value not in selected_conditions:
            continue

        # Get statistics from file data
        stats = file_data.get("stats", {})
        nonverbal_cue_counts = stats.get("nonverbal_cues", {})

        # Initialize counters for nonverbal cues by speaker (excluding extras)
        caregiver_nonverbal = 0
        plwd_nonverbal = 0
        
        # Initialize counters for extra cues by speaker
        caregiver_extra = 0
        plwd_extra = 0
        
        # Get turn counts and word counts from transcript_insights_updated.json
        turn_word_data = {}
        if patient_id in enriched_data:
            for session_category in enriched_data[patient_id].values():
                if filename in session_category and "basic_statistics" in session_category[filename]:
                    turn_word_data = session_category[filename]["basic_statistics"]
                    break
        
        # Extract examples and count nonverbal cues by speaker, separating extras
        for turn in file_data.get("turns", []):
            nonverbal_cues = turn.get("nonverbal_cues", [])
            speaker = turn.get("speaker", "unknown")
            
            if nonverbal_cues:
                # Separate nonverbal cues from extra cues
                regular_cues = [cue for cue in nonverbal_cues if cue.lower() not in EXTRA_CUES]
                extra_cues = [cue for cue in nonverbal_cues if cue.lower() in EXTRA_CUES]
                
                # Count regular nonverbal cues by speaker
                if speaker == "caregiver":
                    caregiver_nonverbal += len(regular_cues)
                    caregiver_extra += len(extra_cues)
                elif speaker == "plwd":
                    plwd_nonverbal += len(regular_cues)
                    plwd_extra += len(extra_cues)
                
                # Store examples for regular nonverbal cues
                for cue in regular_cues:
                    example = {
                        "patient_id": patient_id,
                        "filename": filename,
                        "week": week,
                        "session_type": session_type,
                        "condition": condition_value,
                        "speaker": speaker,
                        "text": turn.get("text", ""),
                        "nonverbal_cue": cue
                    }
                    example_data[week].append(example)
                
                # Store examples for extra cues
                for cue in extra_cues:
                    example = {
                        "patient_id": patient_id,
                        "filename": filename,
                        "week": week,
                        "session_type": session_type,
                        "condition": condition_value,
                        "speaker": speaker,
                        "text": turn.get("text", ""),
                        "extra_cue": cue
                    }
                    extra_example_data[week].append(example)

        # Create entry for the nonverbal analysis table
        entry = {
            "Week": week,
            "Filename": filename,
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Condition": condition_value,
            "Caregiver Nonverbal": caregiver_nonverbal,
            "PLWD Nonverbal": plwd_nonverbal,
            "Total Nonverbal Cues": caregiver_nonverbal + plwd_nonverbal,
            "Caregiver Turns": turn_word_data.get("caregiver_turns", 0),
            "PLWD Turns": turn_word_data.get("plwd_turns", 0),
            "Caregiver Words": turn_word_data.get("caregiver_words", 0),
            "PLWD Words": turn_word_data.get("plwd_words", 0)
        }
        
        # Add counts for specific nonverbal cue types (excluding extras)
        for cue_type, count in nonverbal_cue_counts.items():
            if cue_type.lower() not in EXTRA_CUES:
                entry[f"{cue_type.replace('_', ' ').title()}"] = count
        
        nonverbal_rows.append(entry)
        
        # Create entry for the extra analysis table
        extra_entry = {
            "Week": week,
            "Filename": filename,
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Condition": condition_value,
            "Caregiver Extra": caregiver_extra,
            "PLWD Extra": plwd_extra,
            "Total Extra Cues": caregiver_extra + plwd_extra,
            "Caregiver Turns": turn_word_data.get("caregiver_turns", 0),
            "PLWD Turns": turn_word_data.get("plwd_turns", 0),
            "Caregiver Words": turn_word_data.get("caregiver_words", 0),
            "PLWD Words": turn_word_data.get("plwd_words", 0)
        }
        
        # Add counts for specific extra cue types
        for cue_type, count in nonverbal_cue_counts.items():
            if cue_type.lower() in EXTRA_CUES:
                extra_entry[f"{cue_type.replace('_', ' ').title()}"] = count
        
        extra_rows.append(extra_entry)

    df_nonverbal = pd.DataFrame(nonverbal_rows)
    df_extra = pd.DataFrame(extra_rows)

    if df_nonverbal.empty and df_extra.empty:
        st.info("No nonverbal communication or extra data available for selected filters.")
        return

    # --- Dynamic Header ---
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    st.markdown(f"### Showing Nonverbal Communication Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")

    # --- Grouping by Week for Nonverbal Data ---
    if not df_nonverbal.empty:
        df_nonverbal['Week'] = pd.to_numeric(df_nonverbal['Week'], errors='coerce')
        
        # Create week label for display
        df_nonverbal["Week Label"] = df_nonverbal["Week"].apply(
            lambda w: "Final" if pd.isna(w) else f"Week {int(w)}" if not pd.isna(w) else "Unknown"
        )
        
        # Calculate rates for analysis
        df_nonverbal['Caregiver Nonverbal Rate'] = (df_nonverbal['Caregiver Nonverbal'] / df_nonverbal['Caregiver Words'] * 100).round(2)
        df_nonverbal['PLWD Nonverbal Rate'] = (df_nonverbal['PLWD Nonverbal'] / df_nonverbal['PLWD Words'] * 100).round(2)
        df_nonverbal['Overall Nonverbal Rate'] = ((df_nonverbal['Caregiver Nonverbal'] + df_nonverbal['PLWD Nonverbal']) / 
                                                (df_nonverbal['Caregiver Words'] + df_nonverbal['PLWD Words']) * 100).round(2)
    
    # --- Grouping by Week for Extra Data ---
    if not df_extra.empty:
        df_extra['Week'] = pd.to_numeric(df_extra['Week'], errors='coerce')
        
        # Create week label for display
        df_extra["Week Label"] = df_extra["Week"].apply(
            lambda w: "Final" if pd.isna(w) else f"Week {int(w)}" if not pd.isna(w) else "Unknown"
        )
        
        # Calculate rates for analysis
        df_extra['Caregiver Extra Rate'] = (df_extra['Caregiver Extra'] / df_extra['Caregiver Words'] * 100).round(2)
        df_extra['PLWD Extra Rate'] = (df_extra['PLWD Extra'] / df_extra['PLWD Words'] * 100).round(2)
        df_extra['Overall Extra Rate'] = ((df_extra['Caregiver Extra'] + df_extra['PLWD Extra']) / 
                                         (df_extra['Caregiver Words'] + df_extra['PLWD Words']) * 100).round(2)
    
    # Display detailed table with filenames
    if not df_nonverbal.empty:
        st.subheader("Detailed Nonverbal Communication Data by File")
        
        # Define columns for display
        display_columns = [
            'Week Label', 'Patient ID', 'Session Type', 'Condition', 'Filename',
            'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
            'Caregiver Nonverbal', 'PLWD Nonverbal', 'Total Nonverbal Cues',
            'Caregiver Nonverbal Rate', 'PLWD Nonverbal Rate', 'Overall Nonverbal Rate'
        ]
        
        nonverbal_type_columns = [col for col in df_nonverbal.columns if col not in display_columns 
                                and col not in ['Week']]
        
        # Sort by Week and Patient ID for better readability
        df_sorted = df_nonverbal.sort_values(['Week', 'Patient ID']).fillna(0)
        
        # Format the table with styling
        st.dataframe(
            df_sorted[display_columns].style
            .format({
                'Caregiver Nonverbal Rate': '{:.2f}%',
                'PLWD Nonverbal Rate': '{:.2f}%',
                'Overall Nonverbal Rate': '{:.2f}%'
            })
            .set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
            use_container_width=True
        )
    else:
        st.info("No nonverbal communication data available for selected filters.")
    
    # --- NEW EXTRA SECTION ---
    st.markdown("---")  # Visual separator
    st.header("Extra Communication Elements")
    st.info("📝 **Extra Elements**: This section includes 'inaudible', 'pause', and 'interruption' - "
            "elements that provide context but are not traditional nonverbal communication cues.")
    
    if not df_extra.empty:
        st.subheader("Detailed Extra Communication Data by File")
        
        # Define columns for display
        extra_display_columns = [
            'Week Label', 'Patient ID', 'Session Type', 'Condition', 'Filename',
            'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
            'Caregiver Extra', 'PLWD Extra', 'Total Extra Cues',
            'Caregiver Extra Rate', 'PLWD Extra Rate', 'Overall Extra Rate'
        ]
        
        extra_type_columns = [col for col in df_extra.columns if col not in extra_display_columns 
                            and col not in ['Week']]
        
        # Sort by Week and Patient ID for better readability
        df_extra_sorted = df_extra.sort_values(['Week', 'Patient ID']).fillna(0)
        
        # Format the table with styling
        st.dataframe(
            df_extra_sorted[extra_display_columns].style
            .format({
                'Caregiver Extra Rate': '{:.2f}%',
                'PLWD Extra Rate': '{:.2f}%',
                'Overall Extra Rate': '{:.2f}%'
            })
            .set_properties(**{'background-color': '#fff3cd', 'color': '#333'}),  # Different color for distinction
            use_container_width=True
        )
    else:
        st.info("No extra communication elements available for selected filters.")
    
    # --- Weekly Extra Summary ---
    if not df_extra.empty:
        st.subheader("Weekly Extra Communication Summary")
        
        # Group by week and calculate statistics
        extra_summary_df = df_extra.groupby("Week Label").agg({
            "Caregiver Extra": "sum",
            "PLWD Extra": "sum",
            "Caregiver Turns": "sum",
            "PLWD Turns": "sum",
            "Total Extra Cues": "sum",
            "Patient ID": "nunique",
            "Filename": "count"
        }).reset_index()
        
        # Rename columns for clarity
        extra_summary_df = extra_summary_df.rename(columns={
            "Patient ID": "Unique Patients",
            "Filename": "File Count"
        })
        
        # Calculate rates for the summary
        extra_summary_df["Caregiver Extra Rate"] = (extra_summary_df["Caregiver Extra"] / extra_summary_df["Caregiver Turns"] * 100).round(2)
        extra_summary_df["PLWD Extra Rate"] = (extra_summary_df["PLWD Extra"] / extra_summary_df["PLWD Turns"] * 100).round(2)
        extra_summary_df["Overall Extra Rate"] = ((extra_summary_df["Caregiver Extra"] + extra_summary_df["PLWD Extra"]) / 
                                               (extra_summary_df["Caregiver Turns"] + extra_summary_df["PLWD Turns"]) * 100).round(2)
        
        # Display summary table
        st.dataframe(
            extra_summary_df.style
            .format({
                'Caregiver Extra Rate': '{:.2f}%',
                'PLWD Extra Rate': '{:.2f}%',
                'Overall Extra Rate': '{:.2f}%'
            })
            .set_properties(**{'background-color': '#fff3cd', 'color': '#333'}),
            use_container_width=True
        )

    # --- Add New Plots Here ---
    st.subheader("Analysis of Specific Nonverbal Cues")

    if not df_nonverbal.empty and nonverbal_type_columns:
        # Plot 1: Dynamic Horizontal Bar Chart for Top N Cues
        st.markdown("#### Top Nonverbal Cues")
        
        # Create dataframe with counts
        overall_counts = df_sorted[nonverbal_type_columns].sum().reset_index()
        overall_counts.columns = ['Nonverbal Cue Type', 'Total Count']
        
        if not overall_counts.empty:
            # Sort by count in descending order
            overall_counts = overall_counts.sort_values('Total Count', ascending=False)
            
            # Add Top N selector
            total_cues = len(overall_counts)
            max_cues = min(20, total_cues)  # Cap at 20 for usability
            default_n = min(10, total_cues)  # Default to 10 or fewer if less available
            
            col1, col2 = st.columns([3, 1])
            with col2:
                top_n = st.slider("Show Top N Cues", min_value=3, max_value=max_cues, value=default_n, step=1)
            
            # Filter to top N cues
            filtered_counts = overall_counts.head(top_n)
            
            # Calculate dynamic y-axis range based on data
            max_count = filtered_counts['Total Count'].max()
            y_max = max_count * 1.1  # Add 10% padding
            
            # Create horizontal bar chart
            with col1:
                st.markdown(f"<h5>Showing top {top_n} of {total_cues} nonverbal cue types</h5>", unsafe_allow_html=True)
            
            fig_overall = px.bar(
                filtered_counts, 
                y='Nonverbal Cue Type', 
                x='Total Count',
                orientation='h',  # Horizontal orientation
                title='Top Nonverbal Cues by Frequency',
                labels={
                    'Total Count': 'Occurrences',
                    'Nonverbal Cue Type': 'Cue Type'
                },
                height=max(300, 40 * top_n)  # Dynamic height based on number of bars
            )
            
            # Customize layout
            fig_overall.update_layout(
                xaxis_range=[0, y_max],
                yaxis=dict(
                    categoryorder='total ascending'  # Order bars by value
                ),
                margin=dict(l=20, r=20, t=40, b=20),
                hoverlabel=dict(bgcolor="white", font_size=12)
            )
            
            # Add value labels on bars
            fig_overall.update_traces(
                texttemplate='%{x:,}',  # Format with commas
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
            )
            
            st.plotly_chart(fig_overall, use_container_width=True)
        else:
            st.info("No data available for nonverbal cues visualization.")

        # Plot 2: Grouped Counts
      

    # --- Weekly Aggregated Summary ---
    if not df_nonverbal.empty:
        st.subheader("Weekly Nonverbal Communication Summary")
        
        # Group by week and calculate statistics
        summary_df = df_nonverbal.groupby("Week Label").agg({
            "Caregiver Nonverbal": "sum",
            "PLWD Nonverbal": "sum",
            "Caregiver Turns": "sum",
            "PLWD Turns": "sum",
            "Total Nonverbal Cues": "sum",
            "Patient ID": "nunique",
            "Filename": "count"
        }).reset_index()
        
        # Rename columns for clarity
        summary_df = summary_df.rename(columns={
            "Patient ID": "Unique Patients",
            "Filename": "File Count"
        })
        
        # Calculate rates for the summary
        summary_df["Caregiver Nonverbal Rate"] = (summary_df["Caregiver Nonverbal"] / summary_df["Caregiver Turns"] * 100).round(2)
        summary_df["PLWD Nonverbal Rate"] = (summary_df["PLWD Nonverbal"] / summary_df["PLWD Turns"] * 100).round(2)
        summary_df["Overall Nonverbal Rate"] = ((summary_df["Caregiver Nonverbal"] + summary_df["PLWD Nonverbal"]) / 
                                             (summary_df["Caregiver Turns"] + summary_df["PLWD Turns"]) * 100).round(2)
        
        # Display summary table
        st.dataframe(
            summary_df.style
            .format({
                'Caregiver Nonverbal Rate': '{:.2f}%',
                'PLWD Nonverbal Rate': '{:.2f}%',
                'Overall Nonverbal Rate': '{:.2f}%'
            })
            .set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
            use_container_width=True
        )

    # --- Visualization ---
    st.subheader("Communication Trends")

    # Line chart for nonverbal trends over weeks
    if not df_nonverbal.empty and 'Week' in df_nonverbal.columns:
        st.markdown("#### Nonverbal Communication Trends")
        
        # Group by Week for the trend analysis
        week_df = df_nonverbal.groupby('Week').agg({
            'Caregiver Nonverbal': 'sum',
            'PLWD Nonverbal': 'sum',
            'Caregiver Turns': 'sum',
            'PLWD Turns': 'sum'
        }).reset_index()
        
        # Calculate rates
        week_df['Caregiver Rate'] = (week_df['Caregiver Nonverbal'] / week_df['Caregiver Turns'] * 100).round(2)
        week_df['PLWD Rate'] = (week_df['PLWD Nonverbal'] / week_df['PLWD Turns'] * 100).round(2)
        
        # Create line chart
        fig = px.line(
            week_df,
            x='Week',
            y=['Caregiver Rate', 'PLWD Rate'],
            title="Nonverbal Communication Rate Over Weeks",
            labels={'value': 'Nonverbal Rate (%)', 'variable': 'Speaker'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Line chart for extra trends over weeks
    if not df_extra.empty and 'Week' in df_extra.columns:
        st.markdown("#### Extra Communication Elements Trends")
        
        # Group by Week for the trend analysis
        week_extra_df = df_extra.groupby('Week').agg({
            'Caregiver Extra': 'sum',
            'PLWD Extra': 'sum',
            'Caregiver Turns': 'sum',
            'PLWD Turns': 'sum'
        }).reset_index()
        
        # Calculate rates
        week_extra_df['Caregiver Rate'] = (week_extra_df['Caregiver Extra'] / week_extra_df['Caregiver Turns'] * 100).round(2)
        week_extra_df['PLWD Rate'] = (week_extra_df['PLWD Extra'] / week_extra_df['PLWD Turns'] * 100).round(2)
        
        # Create line chart
        fig_extra = px.line(
            week_extra_df,
            x='Week',
            y=['Caregiver Rate', 'PLWD Rate'],
            title="Extra Communication Elements Rate Over Weeks",
            labels={'value': 'Extra Elements Rate (%)', 'variable': 'Speaker'},
            markers=True,
            color_discrete_map={'Caregiver Rate': '#ffa500', 'PLWD Rate': '#ff6347'}  # Different colors
        )
        st.plotly_chart(fig_extra, use_container_width=True)

    # --- Interactive Treemap for Nonverbal Cues by Condition ---
    st.subheader("Nonverbal Communication by Condition Type (Interactive Treemap)")
    st.markdown("<p style='color:#666;font-size:0.9em;margin-bottom:1em'>Click on any block to zoom in and explore subcategories. Click in the center to zoom out.</p>", unsafe_allow_html=True)
    
    if not df_nonverbal.empty and 'Condition' in df_nonverbal.columns and nonverbal_type_columns:
        # Create a list to hold all treemap data
        treemap_data = []
        
        # Process data for each condition
        for condition in df_nonverbal['Condition'].unique():
            condition_data = df_nonverbal[df_nonverbal['Condition'] == condition]
            
            # Get caregiver nonverbal cues
            for cue_type in nonverbal_type_columns:
                caregiver_count = condition_data[cue_type].sum() * (condition_data['Caregiver Nonverbal'].sum() / 
                                                                  (condition_data['Caregiver Nonverbal'].sum() + 
                                                                   condition_data['PLWD Nonverbal'].sum() + 0.0001))
                if caregiver_count > 0:
                    treemap_data.append({
                        'Condition': condition,
                        'Speaker': 'Caregiver',
                        'Cue Type': cue_type,
                        'Count': int(caregiver_count)
                    })
                
                # Get PLWD nonverbal cues
                plwd_count = condition_data[cue_type].sum() * (condition_data['PLWD Nonverbal'].sum() / 
                                                            (condition_data['Caregiver Nonverbal'].sum() + 
                                                             condition_data['PLWD Nonverbal'].sum() + 0.0001))
                if plwd_count > 0:
                    treemap_data.append({
                        'Condition': condition,
                        'Speaker': 'PLWD',
                        'Cue Type': cue_type,
                        'Count': int(plwd_count)
                    })
        
        # Create DataFrame from the collected data
        treemap_df = pd.DataFrame(treemap_data)
        
        if not treemap_df.empty:
            # Create path for treemap hierarchy
            treemap_df['path'] = treemap_df.apply(
                lambda x: f"{x['Condition']}/{x['Speaker']}/{x['Cue Type']}", axis=1
            )
            
            # Create the treemap
            fig_treemap = px.treemap(
                treemap_df,
                path=['Condition', 'Speaker', 'Cue Type'],
                values='Count',
                color='Speaker',
                color_discrete_map={'Caregiver': '#4e79a7', 'PLWD': '#f28e2b'},
                title="Nonverbal Cue Distribution by Condition and Speaker",
                hover_data=['Count']
            )
            
            # Customize treemap appearance
            fig_treemap.update_traces(
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Path: %{id}<extra></extra>',
                texttemplate='<b>%{label}</b><br>%{value}',
                marker_line=dict(width=1, color='white')
            )
            
            fig_treemap.update_layout(
                margin=dict(t=50, l=25, r=25, b=25),
                height=600
            )
            
            st.plotly_chart(fig_treemap, use_container_width=True)
        else:
            st.info("No data available to display nonverbal communication treemap.")
    else:
        st.info("Condition data or nonverbal cue types not available for treemap visualization.")

    # --- Example Section ---
    st.subheader("Communication Examples")

    # Sort weeks for consistent display (handling text vs numeric weeks)
    all_weeks = set(list(example_data.keys()) + list(extra_example_data.keys()))
    try:
        sorted_weeks = sorted([w for w in all_weeks if w is not None], 
                             key=lambda x: float(x) if x and x != 'Unknown' else float('inf'))
    except ValueError:
        sorted_weeks = sorted([w for w in all_weeks if w is not None])
    
    if 'Unknown' in all_weeks:
        sorted_weeks.append('Unknown')
    
    # Display examples by week
    for week in sorted_weeks:
        nonverbal_examples = example_data.get(week, [])
        extra_examples = extra_example_data.get(week, [])
        week_label = "Final" if week is None or pd.isna(week) else f"Week {week}"
        
        total_examples = len(nonverbal_examples) + len(extra_examples)
        
        if total_examples > 0:
            with st.expander(f"{week_label} Examples ({total_examples} total: {len(nonverbal_examples)} nonverbal, {len(extra_examples)} extra)"):
                
                # Display nonverbal examples
                if nonverbal_examples:
                    st.markdown("**Nonverbal Communication Examples:**")
                    for idx, example in enumerate(nonverbal_examples[:15]):  # Limit to 15 per type
                        speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                        nonverbal_highlighted = f"{example['text']} **[{example['nonverbal_cue']}]**"
                        
                        st.markdown(f"{idx+1}. {speaker_bold}: {nonverbal_highlighted}")
                        st.markdown(f"   - Session: {example['session_type']}, Condition: {example['condition']}")
                        st.divider()
                    
                    if len(nonverbal_examples) > 15:
                        st.info(f"{len(nonverbal_examples) - 15} more nonverbal examples not shown")
                
                # Display extra examples
                if extra_examples:
                    st.markdown("**Extra Communication Elements Examples:**")
                    for idx, example in enumerate(extra_examples[:15]):  # Limit to 15 per type
                        speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                        extra_highlighted = f"{example['text']} **[{example['extra_cue']}]**"
                        
                        st.markdown(f"{idx+1}. {speaker_bold}: {extra_highlighted}")
                        st.markdown(f"   - Session: {example['session_type']}, Condition: {example['condition']}")
                        st.divider()
                    
                    if len(extra_examples) > 15:
                        st.info(f"{len(extra_examples) - 15} more extra examples not shown")
        else:
            with st.expander(f"{week_label} Examples"):
                st.info("No examples available for the selected filters.")
    
    # --- Summary statistics ---
    st.subheader("Summary Statistics")
    
    # Create tabs for nonverbal and extra statistics
    tab1, tab2 = st.tabs(["Nonverbal Statistics", "Extra Elements Statistics"])
    
    with tab1:
        if not df_nonverbal.empty:
            # Group by speaker type for overall statistics
            total_caregiver_nonverbal = df_nonverbal['Caregiver Nonverbal'].sum()
            total_plwd_nonverbal = df_nonverbal['PLWD Nonverbal'].sum()
            total_caregiver_turns = df_nonverbal['Caregiver Turns'].sum()
            total_plwd_turns = df_nonverbal['PLWD Turns'].sum()
            
            # Calculate average rates safely (avoid division by zero)
            if total_caregiver_turns > 0:
                avg_caregiver_rate = (total_caregiver_nonverbal / total_caregiver_turns * 100)
            else:
                avg_caregiver_rate = 0
                
            if total_plwd_turns > 0:
                avg_plwd_rate = (total_plwd_nonverbal / total_plwd_turns * 100)
            else:
                avg_plwd_rate = 0
            
            summary_data = {
                "Total Caregiver Nonverbal Cues": total_caregiver_nonverbal,
                "Total PLWD Nonverbal Cues": total_plwd_nonverbal,
                "Total Caregiver Turns": total_caregiver_turns,
                "Total PLWD Turns": total_plwd_turns,
                "Average Caregiver Nonverbal Rate": avg_caregiver_rate,
                "Average PLWD Nonverbal Rate": avg_plwd_rate,
            }
            
            summary_df_overall = pd.DataFrame([summary_data])
            
            # Add nonverbal cue type totals if available
            if 'nonverbal_type_columns' in locals():
                for col in nonverbal_type_columns:
                    summary_df_overall[f"Total {col}"] = df_nonverbal[col].sum() if col in df_nonverbal.columns else 0
            
            # Display summary
            summary_transposed = summary_df_overall.T.rename(columns={0: 'Value'})
            
            # Create a safe formatter function that handles potential errors
            def safe_format(x, name):
                try:
                    if "Rate" in name:
                        if pd.notna(x) and not pd.isna(x) and not np.isinf(x) and x != float('inf'):
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
        else:
            st.info("No nonverbal communication data available.")
    
    with tab2:
        if not df_extra.empty:
            # Group by speaker type for overall statistics
            total_caregiver_extra = df_extra['Caregiver Extra'].sum()
            total_plwd_extra = df_extra['PLWD Extra'].sum()
            total_caregiver_turns_extra = df_extra['Caregiver Turns'].sum()
            total_plwd_turns_extra = df_extra['PLWD Turns'].sum()
            
            # Calculate average rates safely (avoid division by zero)
            if total_caregiver_turns_extra > 0:
                avg_caregiver_extra_rate = (total_caregiver_extra / total_caregiver_turns_extra * 100)
            else:
                avg_caregiver_extra_rate = 0
                
            if total_plwd_turns_extra > 0:
                avg_plwd_extra_rate = (total_plwd_extra / total_plwd_turns_extra * 100)
            else:
                avg_plwd_extra_rate = 0
            
            extra_summary_data = {
                "Total Caregiver Extra Cues": total_caregiver_extra,
                "Total PLWD Extra Cues": total_plwd_extra,
                "Total Caregiver Turns": total_caregiver_turns_extra,
                "Total PLWD Turns": total_plwd_turns_extra,
                "Average Caregiver Extra Rate": avg_caregiver_extra_rate,
                "Average PLWD Extra Rate": avg_plwd_extra_rate,
            }
            
            extra_summary_df_overall = pd.DataFrame([extra_summary_data])
            
            # Add extra cue type totals if available
            if 'extra_type_columns' in locals():
                for col in extra_type_columns:
                    extra_summary_df_overall[f"Total {col}"] = df_extra[col].sum() if col in df_extra.columns else 0
            
            # Display summary
            extra_summary_transposed = extra_summary_df_overall.T.rename(columns={0: 'Value'})
            
            # Apply formatting with error handling
            extra_formatted_df = pd.DataFrame()
            extra_formatted_df['Value'] = [safe_format(x, name) for name, x in zip(extra_summary_transposed.index, extra_summary_transposed['Value'])]
            extra_formatted_df.index = extra_summary_transposed.index
            
            # Display the formatted dataframe
            st.dataframe(extra_formatted_df, use_container_width=True)
        else:
            st.info("No extra communication elements data available.")

if __name__ == "__main__":
    main()
