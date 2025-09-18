import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENRICHED_PATH = "transcript_insights_updated.json"
ENHANCED_ANALYSIS_PATH = "enhanced_transcript_analysis.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_qa_data(selected_patients, selected_sessions, selected_conditions):
    # Load data
    classified = load_json(CLASSIFIED_PATH)
    enriched = load_json(ENRICHED_PATH)
    enhanced = load_json(ENHANCED_ANALYSIS_PATH)
    
    # Create a mapping of filenames to metadata from classified_data
    filename_to_metadata = {f['filename']: f for f in classified}
    
    # Initialize data structures
    qa_rows = []
    examples_by_week = defaultdict(list)
    
    # Process enhanced transcript analysis data for questions and answers
    for filename, file_data in enhanced.get("by_file", {}).items():
        # Get metadata from classified data or from the file data itself
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
        
        # Get statistics from file data
        stats = file_data.get("stats", {})
        
        # Get turn counts and word counts from transcript_insights_updated.json
        turn_word_data = {}
        if patient_id in enriched:
            for session_category in enriched[patient_id].values():
                if filename in session_category and "basic_statistics" in session_category[filename]:
                    turn_word_data = session_category[filename]["basic_statistics"]
                    break
        
        # Extract questions counts
        caregiver_questions = 0
        plwd_questions = 0
        question_examples = []
        
        # Extract questions and examples from turns data
        for turn in file_data.get("turns", []):
            speaker = turn.get("speaker", "unknown")
            is_question = turn.get("is_question", False)
            is_response = turn.get("is_response", False)
            
            if is_question:
                if speaker == "caregiver":
                    caregiver_questions += 1
                elif speaker == "plwd":
                    plwd_questions += 1
                
                # Store this as a question example
                question_example = {
                    "patient_id": patient_id,
                    "filename": filename,
                    "week": week,
                    "session_type": session_type,
                    "condition": condition_value,
                    "speaker": speaker,
                    "text": turn.get("text", ""),
                    "type": "question"
                }
                question_examples.append(question_example)
                examples_by_week[week].append(question_example)
            
            # Also track responses separately
            if is_response:
                # Store this as a response example
                response_example = {
                    "patient_id": patient_id,
                    "filename": filename,
                    "week": week,
                    "session_type": session_type,
                    "condition": condition_value,
                    "speaker": speaker,
                    "text": turn.get("text", ""),
                    "type": "response"
                }
                examples_by_week[week].append(response_example)
        
        # Calculate total questions and question balance metrics
        total_questions = caregiver_questions + plwd_questions
        
        # Calculate a question balance metric that works well with zeros
        if caregiver_questions == 0 and plwd_questions == 0:
            # If both are zero, balance is neutral (0.5)
            answer_ratio = 0.5
        elif caregiver_questions == 0:
            # If only caregiver questions is zero, balance is high (0.9)
            answer_ratio = 0.9
        elif plwd_questions == 0:
            # If only PLWD questions is zero, balance is low (0.1)
            answer_ratio = 0.1
        else:
            # Otherwise, normalize to a 0.1-0.9 range
            raw_ratio = plwd_questions / (caregiver_questions + plwd_questions)
            answer_ratio = 0.1 + (raw_ratio * 0.8)  # Scale to 0.1-0.9 range
        
        # Create row for dataframe
        qa_rows.append({
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Week": week,
            "Filename": filename,
            "Condition": condition_value,
            "Caregiver Questions": caregiver_questions,
            "PLWD Questions": plwd_questions,
            "Total Questions": total_questions,
            "Answer Ratio": answer_ratio,
            "Caregiver Turns": turn_word_data.get("caregiver_turns", 0),
            "PLWD Turns": turn_word_data.get("plwd_turns", 0),
            "Caregiver Words": turn_word_data.get("caregiver_words", 0),
            "PLWD Words": turn_word_data.get("plwd_words", 0)
        })
    
    # Create DataFrame
    qa_df = pd.DataFrame(qa_rows)
    
    return qa_df, examples_by_week

def main():
    st.title("Questions & Answers Analysis")

    # Load data
    classified = load_json(CLASSIFIED_PATH)
    
    # Filter out Final Interview files from filter options
    non_final_classified = [f for f in classified if not f.get("final_interview", False) 
                           and f.get("session_type", "") != "Final Interview"]
    
    # Get filter options
    all_patients = sorted(set(f["patient_id"] for f in non_final_classified if f.get("patient_id")))
    all_sessions = sorted(set(f["session_type"] for f in non_final_classified if f.get("session_type")))
    all_conditions = sorted(list(set(f.get("condition_value", "").strip() for f in non_final_classified if f.get("condition_value"))))
    
    # Create filters - keep them on the main page, not in sidebar
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_patients = st.multiselect("Select Participant(s)", options=all_patients, default=all_patients)
    with col2:
        selected_sessions = st.multiselect("Select Session Type(s)", options=all_sessions, default=all_sessions)
    with col3:
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Extract questions and answers data
    qa_df, examples_by_week = extract_qa_data(selected_patients, selected_sessions, selected_conditions)
    
    if qa_df.empty:
        st.warning("No questions and answers data available for selected filters.")
        return
    
    # Display filter selection
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    st.markdown(f"### Showing Questions & Answers Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # --- Data Preparation ---
    
    # Convert Week to numeric for proper sorting and grouping
    qa_df["Week"] = pd.to_numeric(qa_df["Week"], errors="coerce")
    
    # Create week label for display purposes
    qa_df["Week Label"] = qa_df["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}"
    )
    
    # Calculate question rates (questions per 100 words)
    if not qa_df.empty:
        qa_df['Caregiver Question Rate'] = (qa_df['Caregiver Questions'] / (qa_df['Caregiver Words'] + 1e-9) * 100).round(2)
        qa_df['PLWD Question Rate'] = (qa_df['PLWD Questions'] / (qa_df['PLWD Words'] + 1e-9) * 100).round(2)
        qa_df['Overall Question Rate'] = ((qa_df['Caregiver Questions'] + qa_df['PLWD Questions']) / 
                                         (qa_df['Caregiver Words'] + qa_df['PLWD Words'] + 1e-9) * 100).round(2)
    
    # --- Display detailed table ---
    st.subheader("Detailed Questions & Answers Statistics by File")
    
    # Define columns for display
    display_columns = [
        'Week Label', 'Patient ID', 'Session Type', 'Condition', 'Filename',
        'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
        'Caregiver Questions', 'PLWD Questions', 'Total Questions',
        'Caregiver Question Rate', 'PLWD Question Rate', 'Overall Question Rate'
    ]
    
    # Sort by Week and Patient ID for better readability
    df_sorted = qa_df.sort_values(['Week', 'Patient ID']).fillna(0)
    
    # Format the table with styling
    st.dataframe(
        df_sorted[display_columns].style
        .format({
            'Caregiver Question Rate': '{:.2f}%',
            'PLWD Question Rate': '{:.2f}%',
            'Overall Question Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f0f8ff', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- Summary Table ---
    st.subheader("Questions & Answers Summary by Week")
    
    # Group by week and calculate statistics with Condition included
    summary_df = qa_df.groupby(["Week Label", "Condition"]).agg({
        "Caregiver Questions": "sum",
        "PLWD Questions": "sum",
        "Total Questions": "sum",
        "Caregiver Words": "sum",
        "PLWD Words": "sum",
        "Patient ID": "nunique",
        "Filename": "count"
    }).reset_index()
    
    # Rename columns for clarity
    summary_df = summary_df.rename(columns={
        "Patient ID": "Unique Patients",
        "Filename": "File Count"
    })
    
    # Calculate percentages and rates (questions per 100 words)
    summary_df["Caregiver %"] = (summary_df["Caregiver Questions"] / (summary_df["Total Questions"] + 1e-9) * 100).round(1)
    summary_df["PLWD %"] = (summary_df["PLWD Questions"] / (summary_df["Total Questions"] + 1e-9) * 100).round(1)
    summary_df["Caregiver Question Rate"] = (summary_df["Caregiver Questions"] / (summary_df["Caregiver Words"] + 1e-9) * 100).round(2)
    summary_df["PLWD Question Rate"] = (summary_df["PLWD Questions"] / (summary_df["PLWD Words"] + 1e-9) * 100).round(2)
    
    # Display summary table
    st.dataframe(
        summary_df.style
        .format({
            'Caregiver %': '{:.1f}%',
            'PLWD %': '{:.1f}%',
            'Caregiver Question Rate': '{:.2f}%',
            'PLWD Question Rate': '{:.2f}%'
        })
        .set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}),
        use_container_width=True
    )
    
    # --- VISUAL 1: Radar Chart for Question Balance ---
    
    st.subheader("Question Balance by Participant")
    
    # Prepare data for radar chart
    radar_df = qa_df.copy()
    
    # Calculate question balance ratio (normalized between 0-1)
    radar_df["Balance Ratio"] = radar_df["PLWD Questions"] / (radar_df["Total Questions"] + 1e-9)
    
    # Group by patient and calculate average balance ratio
    patient_balance = radar_df.groupby("Patient ID")["Balance Ratio"].mean().reset_index()
    
    # Create radar chart
    fig1 = px.line_polar(
        patient_balance,
        r="Balance Ratio",
        theta="Patient ID",
        line_close=True,
        range_r=[0, patient_balance["Balance Ratio"].max() * 1.1 or 0.5],
        title="Question Balance by Participant (Higher = More PLWD Questions)"
    )
    
    # Enhance the radar chart appearance
    fig1.update_traces(fill='toself', opacity=0.6)
    fig1.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, patient_balance["Balance Ratio"].max() * 1.1 or 0.5]
            )
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # --- VISUAL 2: Question Trend Timeline ---
    
    st.subheader("Question Trends Over Time")
    
    # Prepare data for trend visualization
    # Convert Week to numeric for proper sorting
    trend_df = qa_df.copy()
    
    # Group by week and calculate average questions per session
    weekly_avg = trend_df.groupby("Week Label").agg({
        "Caregiver Questions": "mean",
        "PLWD Questions": "mean",
        "Filename": "count"
    }).reset_index()
    weekly_avg.rename(columns={"Filename": "Session Count"}, inplace=True)
    
    # Ensure proper week order
    week_order = sorted([w for w in weekly_avg["Week Label"].unique() if w != "Final"]) + ["Final"]
    weekly_avg["Week Order"] = pd.Categorical(weekly_avg["Week Label"], categories=week_order, ordered=True)
    weekly_avg = weekly_avg.sort_values("Week Order")
    
    # Create a dual-axis chart for questions per session
    fig2 = go.Figure()
    
    # Add caregiver questions line
    fig2.add_trace(go.Scatter(
        x=weekly_avg["Week Label"],
        y=weekly_avg["Caregiver Questions"],
        mode="lines+markers",
        name="Caregiver Questions",
        line=dict(color="#4682B4", width=3),
        marker=dict(size=10)
    ))
    
    # Add PLWD questions line
    fig2.add_trace(go.Scatter(
        x=weekly_avg["Week Label"],
        y=weekly_avg["PLWD Questions"],
        mode="lines+markers",
        name="PLWD Questions",
        line=dict(color="#CD5C5C", width=3),
        marker=dict(size=10)
    ))
    
    # Add session count as bars on secondary y-axis
    fig2.add_trace(go.Bar(
        x=weekly_avg["Week Label"],
        y=weekly_avg["Session Count"],
        name="Number of Sessions",
        marker=dict(color="rgba(180, 180, 180, 0.5)"),
        yaxis="y2",
        opacity=0.7
    ))
    
    # Update layout for dual y-axes
    fig2.update_layout(
        title="Average Questions Per Session Over Time",
        xaxis=dict(title="Week"),
        yaxis=dict(
            title=dict(text="Average Questions Per Session", font=dict(color="#1F77B4")),
            tickfont=dict(color="#1F77B4")
        ),
        yaxis2=dict(
            title=dict(text="Number of Sessions", font=dict(color="#7F7F7F")),
            tickfont=dict(color="#7F7F7F"),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255, 255, 255, 0.5)"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # --- VISUAL 3: Question Type Heatmap ---
    
    st.subheader("Question Pattern Analysis")
    
    # Create a heatmap showing question patterns across participants and weeks
    # Calculate question ratio (PLWD/Caregiver) for each patient and week
    if len(qa_df) > 3:
        # Create pivot table for heatmap
        ratio_pivot = qa_df.pivot_table(
            index="Patient ID",
            columns="Week Label",
            values="Answer Ratio",
            aggfunc="mean"
        ).fillna(0)
        
        # Create annotated heatmap
        fig3 = px.imshow(
            ratio_pivot,
            labels=dict(x="Week", y="Patient ID", color="Question Balance"),
            title="Question Balance Patterns",
            color_continuous_scale=[
                [0, "#053061"],     # Dark blue for caregiver-dominated (0.1)
                [0.25, "#2166AC"],  # Blue for caregiver-leaning
                [0.5, "#F7F7F7"],   # White for balanced
                [0.75, "#B2182B"],  # Red for PLWD-leaning
                [1, "#67001F"]      # Dark red for PLWD-dominated (0.9)
            ],
            zmin=0.1,  # Set minimum value to 0.1
            zmax=0.9,  # Set maximum value to 0.9
            aspect="auto",
            text_auto='.2f'
        )
        
        # Improve layout
        fig3.update_layout(
            xaxis=dict(side="top"),
            coloraxis_colorbar=dict(
                title="Question Balance",
                tickvals=[0.1, 0.3, 0.5, 0.7, 0.9],
                ticktext=["Caregiver Only", "Caregiver Dominant", "Balanced", "PLWD Dominant", "PLWD Only"],
                thicknessmode="pixels", thickness=20,
                lenmode="pixels", len=300,
                yanchor="top", y=1,
                ticks="outside"
            )
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Not enough data for the question pattern heatmap.")
    
    # --- VISUAL 4: Bubble Chart Comparison ---
    
    st.subheader("Baseline vs Final Question Dynamics")
    
    # Filter for baseline and final data
    baseline_df = qa_df[qa_df["Week"] == 0]
    final_df = qa_df[qa_df["Week"].isna()]
    
    if not baseline_df.empty and not final_df.empty:
        # Aggregate data by patient
        baseline_agg = baseline_df.groupby("Patient ID").agg({
            "Caregiver Questions": "sum",
            "PLWD Questions": "sum",
            "Total Questions": "sum"
        }).reset_index()
        baseline_agg["Period"] = "Baseline"
        
        final_agg = final_df.groupby("Patient ID").agg({
            "Caregiver Questions": "sum",
            "PLWD Questions": "sum",
            "Total Questions": "sum"
        }).reset_index()
        final_agg["Period"] = "Final"
        
        # Combine data
        combined = pd.concat([baseline_agg, final_agg])
        
        # Create bubble chart
        fig4 = px.scatter(
            combined,
            x="Caregiver Questions",
            y="PLWD Questions",
            size="Total Questions",
            color="Period",
            facet_col="Period",
            hover_name="Patient ID",
            labels={
                "Caregiver Questions": "Caregiver Questions",
                "PLWD Questions": "PLWD Questions"
            },
            title="Baseline vs Final Question Distribution",
            color_discrete_map={"Baseline": "#1E90FF", "Final": "#FF6347"},
            size_max=40,
            opacity=0.7,
            template="plotly_white"
        )
        
        # Add diagonal reference lines to each facet
        max_val = max(
            combined["Caregiver Questions"].max(),
            combined["PLWD Questions"].max()
        ) * 1.1
        
        fig4.add_shape(
            type="line",
            x0=0, y0=0,
            x1=max_val, y1=max_val,
            line=dict(color="rgba(0,0,0,0.3)", dash="dash"),
            row=1, col=1
        )
        
        fig4.add_shape(
            type="line",
            x0=0, y0=0,
            x1=max_val, y1=max_val,
            line=dict(color="rgba(0,0,0,0.3)", dash="dash"),
            row=1, col=2
        )
        
        # Add annotations explaining the diagonal
        fig4.add_annotation(
            text="Equal Questions",
            x=max_val*0.7, y=max_val*0.7,
            showarrow=False,
            font=dict(size=10, color="rgba(0,0,0,0.5)"),
            textangle=45,
            row=1, col=1
        )
        
        fig4.add_annotation(
            text="Equal Questions",
            x=max_val*0.7, y=max_val*0.7,
            showarrow=False,
            font=dict(size=10, color="rgba(0,0,0,0.5)"),
            textangle=45,
            row=1, col=2
        )
        
        # Update layout
        fig4.update_layout(
            height=500,
            xaxis=dict(range=[0, max_val]),
            xaxis2=dict(range=[0, max_val]),
            yaxis=dict(range=[0, max_val]),
            yaxis2=dict(range=[0, max_val])
        )
        
        # Update facet titles - safely handle annotations without '=' character
        def update_annotation(a):
            if "=" in a.text:
                a.update(text=a.text.split("=")[1])
            return a
            
        fig4.for_each_annotation(update_annotation)
        
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Both baseline and final data are required for the comparison visualization.")
        
    # --- VISUAL 5: Question Engagement Index ---
    
    st.subheader("Question Engagement Index")
    
    # Calculate an engagement index based on question patterns
    if not qa_df.empty:
        # Group by patient
        patient_engagement = qa_df.groupby("Patient ID").agg({
            "Caregiver Questions": "sum",
            "PLWD Questions": "sum",
            "Total Questions": "sum"
        }).reset_index()
        
        # Calculate engagement metrics
        patient_engagement["Engagement Index"] = (
            (patient_engagement["PLWD Questions"] / (patient_engagement["Total Questions"] + 1e-9)) * 
            np.log1p(patient_engagement["Total Questions"])
        ).round(2)
        
        # Sort by engagement index
        patient_engagement = patient_engagement.sort_values("Engagement Index", ascending=False)
        
        # Create horizontal bar chart
        fig5 = px.bar(
            patient_engagement,
            y="Patient ID",
            x="Engagement Index",
            orientation="h",
            color="Engagement Index",
            color_continuous_scale="Viridis",
            title="Question Engagement Index by Participant",
            labels={"Engagement Index": "Engagement Index (higher = more interactive)"},
            text="Engagement Index"
        )
        
        # Add data labels
        fig5.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )
        
        # Improve layout
        fig5.update_layout(
            height=max(300, len(patient_engagement) * 40),
            xaxis=dict(title="Engagement Index"),
            yaxis=dict(title="")
        )
        
        st.plotly_chart(fig5, use_container_width=True)
        
        # Add explanation of the index
        with st.expander("About the Question Engagement Index"):
            st.markdown("""
            The **Question Engagement Index** measures the interactive nature of conversations based on question patterns:
            
            - Higher values indicate more balanced question exchanges (PLWD asking more questions relative to caregiver)
            - The index accounts for both the ratio of questions and the overall volume of questions
            - Formula: (PLWD Questions / Total Questions) × log(1 + Total Questions)
            
            This provides insight into which participants are more actively engaged in two-way conversations versus those in more passive listening roles.
            """)
    else:
        st.info("Not enough data to calculate the engagement index.")
    
    # --- Q&A Examples by Week ---
    
    st.subheader("Question & Answer Examples by Week")
    
    # Define safe sorting function for weeks
    def safe_sort_key(item):
        if item is None:
            return float('inf')  # Place None values at the end
        try:
            return float(item)  # Try to convert to numeric for proper sorting
        except (ValueError, TypeError):
            return str(item)  # Fall back to string comparison
    
    # Create expanders for each week
    for week in sorted(examples_by_week.keys(), key=safe_sort_key):
        week_label = "Final Interview" if week is None or pd.isna(week) else f"Week {int(week)}" if not pd.isna(week) else "Unknown"
        with st.expander(f"{week_label} Examples"):
            if examples_by_week[week]:
                # Group examples by type (question or response)
                questions = [ex for ex in examples_by_week[week] if ex['type'] == 'question']
                responses = [ex for ex in examples_by_week[week] if ex['type'] == 'response']
                
                # Display questions first
                if questions:
                    st.markdown("#### Questions")
                    for idx, example in enumerate(questions[:15]):  # Limit to 15 examples
                        speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                        st.markdown(f"{idx+1}. {speaker_bold}: {example['text']}")
                        st.markdown(f"   - Session: {example['session_type']}, Condition: {example['condition']}")
                        st.divider()
                    
                    if len(questions) > 15:
                        st.info(f"{len(questions) - 15} more question examples not shown")
                
                # Then display responses
                if responses:
                    st.markdown("#### Responses")
                    for idx, example in enumerate(responses[:15]):  # Limit to 15 examples
                        speaker_bold = "**Caregiver**" if example['speaker'] == 'caregiver' else "**PLWD**"
                        st.markdown(f"{idx+1}. {speaker_bold}: {example['text']}")
                        st.markdown(f"   - Session: {example['session_type']}, Condition: {example['condition']}")
                        st.divider()
                    
                    if len(responses) > 15:
                        st.info(f"{len(responses) - 15} more response examples not shown")
            else:
                st.info("No examples available for this week.")

if __name__ == "__main__":
    main()
