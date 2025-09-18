import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENRICHED_PATH = "transcript_insights_updated.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_engagement_data(selected_patients, selected_sessions, selected_conditions):
    # Load data
    classified = load_json(CLASSIFIED_PATH)
    enriched = load_json(ENRICHED_PATH)
    
    # Initialize data structures
    engagement_rows = []
    overlapping_examples = []
    
    # Process each file in classified data
    for file in classified:
        # Skip Final Interview files
        if file.get("final_interview", False) or file.get("session_type", "") == "Final Interview":
            continue
            
        patient_id = file.get("patient_id")
        session_type = file.get("session_type")
        # Normalize condition_value by stripping whitespace
        condition_value = file.get("condition_value", "").strip()
        week = file.get("week")
        filename = file.get("filename")
        
        # Apply filters
        if (selected_patients and patient_id not in selected_patients) or \
           (selected_sessions and session_type not in selected_sessions) or \
           (selected_conditions and condition_value not in selected_conditions):
            continue
            
        # Find basic statistics in enriched dataset
        stats_data = None
        if patient_id in enriched:
            # Check each session type category
            for session_category, files in enriched[patient_id].items():
                if filename in files and "basic_statistics" in files[filename]:
                    stats_data = files[filename]["basic_statistics"]
                    break
                    
        # Skip if no statistics data found
        if not stats_data:
            continue
            
        # Extract engagement metrics
        caregiver_turns = stats_data.get("caregiver_turns", 0)
        plwd_turns = stats_data.get("plwd_turns", 0)
        caregiver_words = stats_data.get("caregiver_words", 0)
        plwd_words = stats_data.get("plwd_words", 0)
        overlapping_speech = stats_data.get("overlapping_speech", 0)
        
        # Ensure numeric values
        try:
            caregiver_turns = int(caregiver_turns)
        except (ValueError, TypeError):
            caregiver_turns = 0
            
        try:
            plwd_turns = int(plwd_turns)
        except (ValueError, TypeError):
            plwd_turns = 0
            
        try:
            caregiver_words = int(caregiver_words)
        except (ValueError, TypeError):
            caregiver_words = 0
            
        try:
            plwd_words = int(plwd_words)
        except (ValueError, TypeError):
            plwd_words = 0
            
        try:
            overlapping_speech = int(overlapping_speech)
        except (ValueError, TypeError):
            overlapping_speech = 0
        
        # Compute helper columns
        turn_diff = caregiver_turns - plwd_turns
        word_diff = caregiver_words - plwd_words
        # Calculate dominance ratio with proper handling of zero PLWD turns
        if plwd_turns == 0:
            dominance_ratio = float('inf') if caregiver_turns > 0 else 1.0
        else:
            dominance_ratio = caregiver_turns / plwd_turns
        
        # Create row for dataframe
        engagement_rows.append({
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Condition": condition_value,
            "Week": week,
            "Filename": filename,
            "Caregiver Turns": caregiver_turns,
            "PLWD Turns": plwd_turns,
            "Caregiver Words": caregiver_words,
            "PLWD Words": plwd_words,
            "Overlapping Speech": overlapping_speech,
            "Turn Difference": turn_diff,
            "Word Difference": word_diff,
            "Dominance Ratio": dominance_ratio
        })
        
        # Collect overlapping speech examples
        if overlapping_speech > 0:
            overlapping_examples.append({
                "Patient ID": patient_id,
                "Week": week,
                "Filename": filename,
                "Overlapping Speech Count": overlapping_speech
            })
    
    # Create DataFrame
    engagement_df = pd.DataFrame(engagement_rows)
    overlapping_df = pd.DataFrame(overlapping_examples)
    
    return engagement_df, overlapping_df

def main():
    st.title("Turn-Taking and Engagement Analysis")

    # Load data
    classified = load_json(CLASSIFIED_PATH)
    
    # Filter out Final Interview files from filter options
    non_final_classified = [f for f in classified if not f.get("final_interview", False) 
                           and f.get("session_type", "") != "Final Interview"]
    
    # Get filter options
    all_patients = sorted(set(f["patient_id"] for f in non_final_classified if f.get("patient_id")))
    all_sessions = sorted(set(f["session_type"] for f in non_final_classified if f.get("session_type")))
    all_conditions = sorted(list(set(f.get("condition_value", "").strip() for f in non_final_classified if f.get("condition_value"))))
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_patients = st.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    with col2:
        selected_sessions = st.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    with col3:
        selected_conditions = st.multiselect("Select Condition(s)", 
                                             options=all_conditions, 
                                             default=all_conditions)
    
    # Extract engagement data
    engagement_df, overlapping_df = extract_engagement_data(selected_patients, selected_sessions, selected_conditions)
    
    if engagement_df.empty:
        st.warning("No engagement data available for selected filters.")
        return
    
    # Display filter selection
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    st.markdown(f"### Showing Engagement Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # --- Data Preparation ---
    
    # Convert Week to numeric for proper sorting and grouping
    engagement_df["Week"] = pd.to_numeric(engagement_df["Week"], errors="coerce")
    
    # Create week label for display purposes
    engagement_df["Week Label"] = engagement_df["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}"
    )
    
    # --- Summary Tables ---
    
    # Display detailed file-level table first
    st.subheader("Detailed Engagement Statistics by File")
    
    # Select columns for detailed view
    detail_cols = ["Week Label", "Patient ID", "Session Type", "Condition", "Filename",
                 "Caregiver Turns", "PLWD Turns", "Overlapping Speech", "Dominance Ratio"]
    
    # Sort by Week, Patient ID, and Session Type
    sorted_df = engagement_df.sort_values(["Week", "Patient ID", "Session Type"])
    
    # Custom formatter for dominance ratio to handle infinity values
    def format_dominance_ratio(val):
        if val == float('inf'):
            return "∞"
        elif val == float('-inf'):
            return "-∞"
        else:
            return f"{val:.2f}"
    
    # Display the detailed table with custom formatting
    styled_df = sorted_df[detail_cols].copy()
    styled_df["Dominance Ratio"] = styled_df["Dominance Ratio"].apply(format_dominance_ratio)
    st.dataframe(styled_df.style.set_properties(**{'background-color': '#f0f8ff', 'color': '#333'}), use_container_width=True)
    
    # --- Weekly Aggregated Summary ---
    
    st.subheader("Weekly Aggregated Engagement Summary")
    
    # Group by week and calculate statistics
    summary_df = engagement_df.groupby("Week Label").agg({
        "Caregiver Turns": "sum",
        "PLWD Turns": "sum",
        "Caregiver Words": "sum",
        "PLWD Words": "sum",
        "Overlapping Speech": "sum",
        "Patient ID": "nunique",
        "Filename": "count"
    }).reset_index()
    
    # Rename columns for clarity
    summary_df = summary_df.rename(columns={
        "Patient ID": "Unique Patients",
        "Filename": "File Count"
    })
    
    # Calculate dominance ratio for the summary with proper handling of zero PLWD turns
    def calculate_dominance_ratio(row):
        caregiver_turns = row["Caregiver Turns"]
        plwd_turns = row["PLWD Turns"]
        if plwd_turns == 0:
            return float('inf') if caregiver_turns > 0 else 1.0
        else:
            return round(caregiver_turns / plwd_turns, 2)
    
    summary_df["Dominance Ratio"] = summary_df.apply(calculate_dominance_ratio, axis=1)
    
    # Format summary table to handle infinity values
    summary_display_df = summary_df.copy()
    summary_display_df["Dominance Ratio"] = summary_display_df["Dominance Ratio"].apply(
        lambda x: "∞" if x == float('inf') else ("-∞" if x == float('-inf') else f"{x:.2f}")
    )
    
    # Display summary table
    st.dataframe(summary_display_df.style.set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}))
    
    # --- VISUAL 1: Motion Scatter ---
    
    st.subheader("Turns per Week (Motion View)")
    
    # Prepare data for motion scatter plot
    motion_df = engagement_df.copy()
    
    # Ensure Week Label is properly ordered for animation
    week_order = sorted([w for w in motion_df["Week Label"].unique() if w != "Final"]) + ["Final"]
    motion_df["Week Label"] = pd.Categorical(motion_df["Week Label"], categories=week_order, ordered=True)
    
    # Create motion scatter plot
    fig1 = px.scatter(
        motion_df,
        x="Caregiver Turns",
        y="PLWD Turns",
        size="Overlapping Speech",
        size_max=20,
        color="Patient ID",
        animation_frame="Week Label",
        hover_name="Patient ID",
        title="Turns per Week (Motion View)",
        labels={
            "Caregiver Turns": "Caregiver Conversation Turns",
            "PLWD Turns": "PLWD Conversation Turns"
        }
    )
    
    # Add diagonal reference line for perfect balance
    max_turns = max(
        motion_df["Caregiver Turns"].max() if not motion_df.empty else 10,
        motion_df["PLWD Turns"].max() if not motion_df.empty else 10
    )
    
    fig1.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max_turns, y1=max_turns,
        line=dict(color="rgba(0,0,0,0.3)", dash="dash")
    )
    
    # Update layout for better readability
    fig1.update_layout(
        xaxis=dict(range=[0, max_turns * 1.1]),
        yaxis=dict(range=[0, max_turns * 1.1])
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # --- NEW VISUAL: Motion Scatter by Condition Type ---
    st.subheader("Turns per Condition Type (Motion View)")
    
    if "Condition" in engagement_df.columns and not engagement_df.empty:
        motion_condition_df = engagement_df.copy()
        motion_condition_df = motion_condition_df.dropna(subset=["Condition", "Caregiver Turns", "PLWD Turns", "Patient ID"])

        # Ensure Condition is treated as a categorical variable for animation frames
        # Order conditions alphabetically or by a defined custom order if needed
        condition_order = sorted(motion_condition_df["Condition"].unique())
        motion_condition_df["Condition"] = pd.Categorical(motion_condition_df["Condition"], categories=condition_order, ordered=True)
        motion_condition_df = motion_condition_df.sort_values("Condition")

        if not motion_condition_df.empty:
            fig_condition_turns = px.scatter(
                motion_condition_df,
                x="Caregiver Turns",
                y="PLWD Turns",
                size="Overlapping Speech", # Optional: size by overlapping speech or another metric
                size_max=20,
                color="Patient ID",
                animation_frame="Condition", # Animate through conditions
                hover_name="Patient ID",
                title="Turns per Condition Type (Motion View)",
                labels={
                    "Caregiver Turns": "Caregiver Conversation Turns",
                    "PLWD Turns": "PLWD Conversation Turns",
                    "Condition": "Condition Type"
                }
            )

            # Determine max turns for axis scaling dynamically
            max_turns_condition = 0
            if not motion_condition_df.empty:
                max_turns_condition = max(
                    motion_condition_df["Caregiver Turns"].max() if "Caregiver Turns" in motion_condition_df else 0,
                    motion_condition_df["PLWD Turns"].max() if "PLWD Turns" in motion_condition_df else 0
                ) 
            max_turns_condition = max(max_turns_condition, 10) # Ensure a minimum range

            fig_condition_turns.add_shape(
                type="line",
                x0=0, y0=0,
                x1=max_turns_condition, y1=max_turns_condition,
                line=dict(color="rgba(0,0,0,0.3)", dash="dash")
            )
            
            fig_condition_turns.update_layout(
                xaxis=dict(range=[0, max_turns_condition * 1.1]),
                yaxis=dict(range=[0, max_turns_condition * 1.1])
            )
            
            st.plotly_chart(fig_condition_turns, use_container_width=True)
        else:
            st.info("No data available for condition-based turns motion view.")
    else:
        st.info("Condition data not available for this visualization.")
    
    # --- VISUAL 2: Ridge "Joy" Chart ---
    
    
    
    # --- VISUAL 3: Interactive Session Type Comparison Rings ---
    
    st.subheader("Engagement Comparison (Interactive Polar Chart)")

    # Radio button to choose grouping
    group_by_choice = st.radio(
        "Group comparison by:",
        ("Session Type", "Condition Type"),
        key="engagement_group_by_selector"
    )

    if group_by_choice == "Session Type":
        st.markdown("#### Comparing by Session Type")
        # Define session type patterns to match (case-insensitively)
        session_patterns = {
            "Baseline": ["baseline"],
            "Final": ["final", "final interview"],
            "ER": ["er", "exposure with researcher", "researcher"],
            "EP": ["ep", "exposure on own", "own"]
        }
        
        # Function to match session types case-insensitively
        def match_session_type(session_type, patterns):
            if session_type is None:
                return False
            session_lower = str(session_type).lower()
            return any(pattern in session_lower for pattern in patterns)

        # Create filtered dataframes for each session type
        temp_dfs = {}
        # Baseline (Week 0)
        baseline_df = engagement_df[engagement_df["Week"] == 0] # Assuming Baseline is always Week 0
        if not baseline_df.empty:
            temp_dfs["Baseline"] = baseline_df
        # Final (Week is None/NaN)
        final_df = engagement_df[engagement_df["Week"].isna()]
        if not final_df.empty:
            temp_dfs["Final"] = final_df
        # ER (Exposure with Researcher)
        er_df = engagement_df[engagement_df["Session Type"].apply(lambda x: match_session_type(x, session_patterns["ER"]))]
        if not er_df.empty:
            temp_dfs["ER"] = er_df
        # EP (Exposure on Own)
        ep_df = engagement_df[engagement_df["Session Type"].apply(lambda x: match_session_type(x, session_patterns["EP"]))]
        if not ep_df.empty:
            temp_dfs["EP"] = ep_df
        
        grouping_options = list(temp_dfs.keys())
        chart_title = "Session Type Engagement Comparison"
        color_discrete_map_key = "Period" # For Session Type
        color_map = {
            "Baseline": "#1E90FF", "Final": "#FF6347", "ER": "#32CD32", "EP": "#FFD700"
        }

    elif group_by_choice == "Condition Type":
        st.markdown("#### Comparing by Condition Type")
        # Use unique conditions from the dataframe
        temp_dfs = {condition: engagement_df[engagement_df["Condition"] == condition] 
                      for condition in engagement_df["Condition"].unique() if condition}
        grouping_options = list(temp_dfs.keys())
        chart_title = "Condition Type Engagement Comparison"
        color_discrete_map_key = "Group" # For Condition Type
        # Define a color map for conditions or use Plotly's default
        # Example:
        unique_conditions_for_map = engagement_df["Condition"].dropna().unique()
        colors = px.colors.qualitative.Plotly
        color_map = {condition: colors[i % len(colors)] for i, condition in enumerate(unique_conditions_for_map)}


    if not grouping_options:
        st.info(f"No data available for comparison by {group_by_choice}.")
    elif len(grouping_options) < 1 : # Requires at least one group for multiselect
        st.info(f"Need at least one {group_by_choice} to display the chart.")
    else:
        selected_groups_for_chart = st.multiselect(
            f"Select {group_by_choice}s to compare:",
            options=grouping_options,
            default=grouping_options[:2] if len(grouping_options) > 1 else grouping_options, # Default to first two or one
            key=f"engagement_{group_by_choice}_selector"
        )
        
        if selected_groups_for_chart:
            polar_data_list = []
            for group_name in selected_groups_for_chart:
                if group_name in temp_dfs:
                    group_data = temp_dfs[group_name]
                    caregiver_turns = group_data["Caregiver Turns"].sum()
                    plwd_turns = group_data["PLWD Turns"].sum()
                    
                    polar_data_list.append({"Speaker": "Caregiver", "Group": group_name, "Turns": caregiver_turns})
                    polar_data_list.append({"Speaker": "PLWD", "Group": group_name, "Turns": plwd_turns})
            
            if polar_data_list:
                polar_df = pd.DataFrame(polar_data_list)
                fig_polar = px.bar_polar(
                    polar_df,
                    r="Turns",
                    theta="Speaker",
                    color="Group", # This will be 'Session Type' or 'Condition Type'
                    barmode="group",
                    title=chart_title,
                    color_discrete_map=color_map
                )
                st.plotly_chart(fig_polar, use_container_width=True)
            else:
                st.info(f"No turn data for selected {group_by_choice}s.")
        else:
            st.info(f"Please select at least one {group_by_choice} to display.")
    
    # --- VISUAL 4: Dominance Heatmap ---
    
    st.subheader("Dominance Heatmap")
    
    # Create pivot table for heatmap
    if len(engagement_df["Patient ID"].unique()) > 1 and len(engagement_df["Week Label"].unique()) > 1:
        heatmap_df = engagement_df.pivot_table(
            index="Patient ID",
            columns="Week Label",
            values="Dominance Ratio",
            aggfunc="mean"
        ).fillna(1.0)  # Fill NaN with 1.0 (equal dominance)
        
        # Create heatmap
        
    
    # --- Overlapping Speech Examples ---
    
    if not overlapping_df.empty:
        st.subheader("Overlapping Speech Examples")
        
        with st.expander("Overlapping Speech Instances"):
            for _, row in overlapping_df.iterrows():
                week_label = "Final" if pd.isna(row["Week"]) else f"Week {int(row['Week'])}"
                st.markdown(f"**Patient {row['Patient ID']} ({week_label})**: {row['Filename']} - {row['Overlapping Speech Count']} instances")
    
if __name__ == "__main__":
    main()
