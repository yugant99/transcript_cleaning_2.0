import streamlit as st
import pandas as pd
import json
import plotly.express as px
from collections import Counter
import numpy as np

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENRICHED_PATH = "transcript_insights_updated.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# Function to calculate proxy lexical diversity metrics from available statistics
def calculate_proxy_lexical_metrics(stats, caregiver_questions=0, plwd_questions=0):
    """
    Calculates proxy metrics for lexical diversity using available statistics:
    - Word Ratio: Ratio of PLWD words to total words (measure of conversational balance)
    - Vocabulary Density: Words per turn (higher values may indicate more complex speech)
    - Question Ratio: Questions to total words (measure of interactive engagement)
    """
    caregiver_words = stats.get('caregiver_words', 0)
    plwd_words = stats.get('plwd_words', 0)
    caregiver_turns = stats.get('caregiver_turns', 0)
    plwd_turns = stats.get('plwd_turns', 0)
    
    total_words = caregiver_words + plwd_words
    total_turns = caregiver_turns + plwd_turns
    total_questions = caregiver_questions + plwd_questions
    
    # Avoid division by zero
    word_ratio = plwd_words / total_words if total_words > 0 else 0.0
    
    # Words per turn (vocabulary density)
    caregiver_density = caregiver_words / caregiver_turns if caregiver_turns > 0 else 0.0
    plwd_density = plwd_words / plwd_turns if plwd_turns > 0 else 0.0
    
    # Question to word ratio (engagement measure)
    question_word_ratio = total_questions / total_words if total_words > 0 else 0.0
    
    return {
        "word_ratio": word_ratio,
        "caregiver_density": caregiver_density,
        "plwd_density": plwd_density,
        "question_word_ratio": question_word_ratio
    }

# Main function for Streamlit page
def main():
    st.title("Lexical Diversity Analysis")
    
    # Load data
    classified = load_json(CLASSIFIED_PATH)
    enriched = load_json(ENRICHED_PATH)
    enhanced = load_json(ENHANCED_ANALYSIS_PATH)
    
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
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Extract data for lexical analysis using available metrics
    metrics_data = []
    
    for file in non_final_classified:
        patient_id = file.get("patient_id")
        session_type = file.get("session_type")
        condition_value = file.get("condition_value", "").strip()
        week = file.get("week")
        filename = file.get("filename")
        
        # Apply filters
        if (selected_patients and patient_id not in selected_patients) or \
           (selected_sessions and session_type not in selected_sessions) or \
           (selected_conditions and condition_value not in selected_conditions):
            continue
        
        # Find enriched stats in transcript_insights.json
        enriched_patient_data = None
        if patient_id in enriched:
            # Check each session type category
            for session_category in enriched[patient_id].values():
                if filename in session_category and "basic_statistics" in session_category[filename]:
                    enriched_patient_data = session_category[filename]
                    break
        
        if not enriched_patient_data or "basic_statistics" not in enriched_patient_data:
            continue
            
        # Get basic statistics
        stats = enriched_patient_data["basic_statistics"]
        
        # Get question counts from enhanced_transcript_analysis.json
        caregiver_questions = 0
        plwd_questions = 0
        
        if 'by_file' in enhanced and filename in enhanced['by_file']:
            file_data = enhanced['by_file'][filename]
            
            # Process each turn to count questions
            if 'turns' in file_data:
                for turn in file_data['turns']:
                    speaker = turn.get('speaker', '').lower()
                    is_question = turn.get('is_question', False)
                    
                    # Count questions by speaker
                    if is_question:
                        if speaker == 'caregiver':
                            caregiver_questions += 1
                        elif speaker == 'plwd':
                            plwd_questions += 1
        
        # Calculate proxy lexical metrics from available statistics
        metrics = calculate_proxy_lexical_metrics(stats, caregiver_questions, plwd_questions)
        
        # Add to data collection
        metrics_data.append({
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Week": week,
            "Filename": filename,  # Add filename column
            "Condition": condition_value, # Add Condition column
            "Word Ratio": metrics["word_ratio"],
            "Caregiver Density": metrics["caregiver_density"],
            "PLWD Density": metrics["plwd_density"],
            "Question-Word Ratio": metrics["question_word_ratio"],
            "Total Words": stats.get("caregiver_words", 0) + stats.get("plwd_words", 0)
        })
    
    # Create DataFrame
    df_metrics = pd.DataFrame(metrics_data)
    
    if df_metrics.empty:
        st.warning("No lexical data available for selected filters.")
        return
    
    # Display summary metrics
    st.subheader("Lexical Diversity Metrics Summary")
    # Add "Condition" to the displayed columns (removed Word Ratio)
    display_df_metrics = df_metrics[["Patient ID", "Session Type", "Week", "Condition", "Filename", "Caregiver Density", "PLWD Density", "Question-Word Ratio", "Total Words"]]
    st.dataframe(display_df_metrics.style.format({
        "Caregiver Density": "{:.1f}", 
        "PLWD Density": "{:.1f}",
        "Question-Word Ratio": "{:.3f}",
        "Total Words": "{:,}"
    }))
    
    # Interactive Visualizations with Plotly
    st.subheader("Interactive Visualizations")
    
    # 1. Word Ratio Trend Over Weeks - Radial Spiral Timeline
    if 'Week' in df_metrics.columns and df_metrics['Week'].dtype == 'object':  # Ensure 'Week' is numeric or convertible
        df_metrics['Week'] = pd.to_numeric(df_metrics['Week'], errors='coerce')
        df_metrics = df_metrics.dropna(subset=['Week'])
    
    if not df_metrics.empty:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Create a figure with polar subplot
        fig_spiral = make_subplots(specs=[[{"type": "polar"}]])
        
        # Get unique patients for coloring
        unique_patients = df_metrics["Patient ID"].unique()
        
        # Create color map for patients
        colors = px.colors.qualitative.Plotly
        color_map = {patient: colors[i % len(colors)] for i, patient in enumerate(unique_patients)}
        
        # Add traces for each patient (using PLWD Density instead of Word Ratio)
        for patient in unique_patients:
            patient_data = df_metrics[df_metrics["Patient ID"] == patient].sort_values("Week")
            
            # Add trace for the spiral path
            fig_spiral.add_trace(
                go.Scatterpolar(
                    r=patient_data["PLWD Density"],
                    theta=patient_data["Week"] * 90,  # Scale for better visualization
                    mode="lines+markers",
                    name=patient,
                    line=dict(color=color_map[patient], width=2),
                    marker=dict(size=8, color=color_map[patient]),
                    customdata=np.stack((patient_data["Week"], 
                                        patient_data["PLWD Density"], 
                                        patient_data["Filename"]), axis=-1),
                    hovertemplate="<b>Patient ID:</b> %{fullData.name}<br>" +
                                 "<b>Week:</b> %{customdata[0]}<br>" +
                                 "<b>PLWD Density:</b> %{customdata[1]:.1f}<br>" +
                                 "<b>Filename:</b> %{customdata[2]}<br>"
                )
            )
        
        # Update layout for better visualization
        fig_spiral.update_layout(
            title="PLWD Speech Density - Radial Spiral Timeline",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(df_metrics["PLWD Density"].max() * 1.1, 10)],
                    title="PLWD Density (Words per Turn)",
                    tickfont=dict(size=10),
                ),
                angularaxis=dict(
                    visible=True,
                    tickmode="array",
                    tickvals=[0, 90, 180, 270, 360],
                    ticktext=["Week 0", "Week 1", "Week 2", "Week 3", "Week 4"],
                    direction="clockwise",
                    tickfont=dict(size=10),
                )
            ),
            showlegend=True,
            legend=dict(title="Patient ID"),
            height=600,
            margin=dict(t=100)
        )
        
        # Add animation frames
        frames = []
        for week in sorted(df_metrics["Week"].unique()):
            frame_data = []
            for patient in unique_patients:
                patient_data = df_metrics[(df_metrics["Patient ID"] == patient) & 
                                         (df_metrics["Week"] <= week)].sort_values("Week")
                if not patient_data.empty:
                    frame_data.append(
                        go.Scatterpolar(
                            r=patient_data["PLWD Density"],
                            theta=patient_data["Week"] * 90,
                            mode="lines+markers",
                            line=dict(color=color_map[patient], width=2),
                            marker=dict(size=8, color=color_map[patient])
                        )
                    )
            frames.append(go.Frame(data=frame_data, name=f"Week {week}"))
        
        fig_spiral.frames = frames
        
        # Add animation buttons
        fig_spiral.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=[
                        dict(label="Play",
                             method="animate",
                             args=[None, {"frame": {"duration": 1000, "redraw": True},
                                          "fromcurrent": True,
                                          "transition": {"duration": 500}}]),
                        dict(label="Pause",
                             method="animate",
                             args=[[None], {"frame": {"duration": 0, "redraw": False},
                                           "mode": "immediate",
                                           "transition": {"duration": 0}}])
                    ],
                    direction="left",
                    pad={"r": 10, "t": 10},
                    x=0.1,
                    y=0,
                    xanchor="right",
                    yanchor="top"
                )
            ]
        )
        
        st.plotly_chart(fig_spiral, use_container_width=True)
        
        # 2. Bar Chart for Word Density Comparison
        density_df = df_metrics.melt(
            id_vars=["Patient ID", "Session Type", "Week"],
            value_vars=["Caregiver Density", "PLWD Density"],
            var_name="Speaker", value_name="Words per Turn"
        )
        
        fig_density = px.bar(density_df, x='Patient ID', y='Words per Turn', color='Speaker', barmode='group',
                           title="Speech Complexity: Words per Turn",
                           labels={"Words per Turn": "Average Words per Turn", "Patient ID": "Participant ID"})
        st.plotly_chart(fig_density)
        
        # 3. Scatter Plot for Question-Word Ratio vs PLWD Density
        fig_scatter = px.scatter(df_metrics, x="Question-Word Ratio", y='PLWD Density', color='Patient ID', 
                                 size='Total Words', size_max=50,
                                 title="Engagement vs Speech Complexity",
                                 labels={
                                     "Question-Word Ratio": "Questions / Total Words", 
                                     "PLWD Density": "PLWD Words per Turn"
                                 },
                                 hover_data=["Session Type", "Week", "Condition"])
        st.plotly_chart(fig_scatter)
        
        # 4. Heatmap of Word Ratio by Week and Patient
       
        # --- NEW: Interactive Chart for Lexical Metric by Condition ---
        st.subheader("Lexical Metrics by Condition")
        if not df_metrics.empty and "Condition" in df_metrics.columns:
            # Select a metric to display
            metric_to_plot = st.selectbox(
                "Select metric to compare by condition:",
                options=["PLWD Density", "Caregiver Density", "Question-Word Ratio"],
                index=0,
                key="lexical_metric_condition_selector"
            )

            if metric_to_plot:
                # Group by Condition and calculate mean of the selected metric
                condition_grouped_metric = df_metrics.groupby("Condition")[metric_to_plot].mean().reset_index()
                
                if not condition_grouped_metric.empty:
                    fig_metric_by_condition = px.bar(
                        condition_grouped_metric,
                        x="Condition",
                        y=metric_to_plot,
                        color="Condition",
                        title=f"Average {metric_to_plot} by Condition Type",
                        labels={metric_to_plot: f"Average {metric_to_plot}"}
                    )
                    st.plotly_chart(fig_metric_by_condition, use_container_width=True)
                else:
                    st.info(f"No data to display for {metric_to_plot} by condition.")
        else:
            st.info("No condition data available to generate this chart.")

    
    # Add interpretive text
    st.markdown("""
    ### How to Interpret These Metrics:
    - **Words per Turn (Density)**: Indicates speech complexity and elaboration - calculated as total words divided by total turns for each speaker
    - **Question-Word Ratio**: Measures interactive engagement through questions
    - **Total Words**: Overall conversation volume
    
    These proxy metrics help assess lexical patterns without requiring raw transcript text.
    Hover over or click on data points for more details.
    """)



if __name__ == "__main__":
    main()  # For testing outside Streamlit app