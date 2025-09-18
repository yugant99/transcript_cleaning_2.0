import streamlit as st
import pandas as pd
import json
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENRICHED_PATH = "transcript_insights_updated.json"
ENHANCED_ANALYSIS_PATH = "enhanced_analysis.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def build_sentiment_dataframe(selected_patients, selected_sessions, selected_conditions):
    # Load data
    classified = load_json(CLASSIFIED_PATH)
    enriched = load_json(ENRICHED_PATH)
    
    # Initialize data structures
    sentiment_rows = []
    examples_by_week = {}
    
    # Process each file
    for file in classified:
        # Skip Final Interview files
        if file.get("final_interview", False) or file.get("session_type", "") == "Final Interview":
            continue
            
        patient_id = file.get("patient_id")
        session_type = file.get("session_type")
        week = file.get("week")
        filename = file.get("filename")
        condition_value = file.get("condition_value", "").strip()  # Get condition value
        
        # Apply filters
        if (selected_patients and patient_id not in selected_patients) or \
           (selected_sessions and session_type not in selected_sessions) or \
           (selected_conditions and condition_value not in selected_conditions):
            continue
            
        # Find sentiment data in enriched dataset
        sentiment_data = None
        if patient_id in enriched:
            # Check each session type category
            for session_category, files in enriched[patient_id].items():
                if filename in files and "Sentiment Analysis" in files[filename]:
                    sentiment_data = files[filename]["Sentiment Analysis"]
                    break
                    
        # Skip if no sentiment data found
        if not sentiment_data:
            continue
            
        # Extract sentiment counts
        sentiment_counts = sentiment_data.get("sentiment_counts", {})
        positive_ct = sentiment_counts.get("positive", 0)
        negative_ct = sentiment_counts.get("negative", 0)
        neutral_ct = sentiment_counts.get("neutral", 0)
        
        # Handle case where counts are not numeric
        if not isinstance(positive_ct, (int, float)):
            try:
                positive_ct = int(positive_ct)
            except (ValueError, TypeError):
                positive_ct = 0
                
        if not isinstance(negative_ct, (int, float)):
            try:
                negative_ct = int(negative_ct)
            except (ValueError, TypeError):
                negative_ct = 0
                
        if not isinstance(neutral_ct, (int, float)):
            try:
                neutral_ct = int(neutral_ct)
            except (ValueError, TypeError):
                neutral_ct = 0
        
        # Create row for dataframe
        sentiment_rows.append({
            "Patient ID": patient_id,
            "Session Type": session_type,
            "Week": week,
            "Positive": positive_ct,
            "Negative": negative_ct,
            "Neutral": neutral_ct,
            "Total": positive_ct + negative_ct + neutral_ct,
            "Net Score": positive_ct - negative_ct,
            "Filename": filename,
            "Condition": condition_value  # Add condition value
        })

        # Collect examples for this week
        if week not in examples_by_week:
            examples_by_week[week] = []
            
        # Get examples and handle different data types
        examples_list = sentiment_data.get("examples", [])
        if not isinstance(examples_list, list):
            # If examples is not a list, try to convert it to one
            if examples_list:
                examples_list = [examples_list]
            else:
                examples_list = []
                
        for ex in examples_list:
            example_text = ""
            # Extract text based on the format of the example
            if isinstance(ex, str):
                example_text = ex
            elif isinstance(ex, dict):
                if 'text' in ex and isinstance(ex['text'], str):
                    example_text = ex['text']
                elif 'context' in ex and isinstance(ex['context'], str):
                    example_text = ex['context']
            
            # Add to examples collection if we found text
            if example_text:
                examples_by_week[week].append(example_text)
    
    # Create DataFrame
    df = pd.DataFrame(sentiment_rows)
    return df, examples_by_week

def main():
    st.title("Sentiment Analysis")

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
        selected_conditions = st.multiselect("Select Condition(s)", options=all_conditions, default=all_conditions)
    
    # Build dataframe with sentiment data
    df, examples_bank = build_sentiment_dataframe(selected_patients, selected_sessions, selected_conditions)
    
    if df.empty:
        st.warning("No sentiment data available for selected filters.")
        return
    
    # Display filter selection
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    st.markdown(f"### Showing Sentiment Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # --- Data Preparation ---
    
    # Convert Week to numeric for proper sorting and grouping
    df["Week"] = pd.to_numeric(df["Week"], errors="coerce")
    
    # Create week label for display purposes
    df["Week Label"] = df["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}"
    )
    
    # Split data into numeric weeks and final weeks
    numeric_df = df[df["Week"].notna()]   # baseline + numbered weeks
    final_df = df[df["Week"].isna()]      # final-interview rows
    
    # --- Summary Table ---
    
    # Group by week and calculate statistics
    df_grouped = df.groupby("Week Label").agg({
        "Positive": "sum",
        "Negative": "sum",
        "Neutral": "sum",
        "Total": "sum",
        "Patient ID": "nunique",
        "Filename": "count"
    }).reset_index()
    
    # Rename columns for clarity
    df_grouped = df_grouped.rename(columns={
        "Patient ID": "Unique Patients",
        "Filename": "File Count"
    })
    
    # Calculate percentages
    df_grouped["Positive %"] = (df_grouped["Positive"] / df_grouped["Total"] * 100).round(1)
    df_grouped["Negative %"] = (df_grouped["Negative"] / df_grouped["Total"] * 100).round(1)
    df_grouped["Neutral %"] = (df_grouped["Neutral"] / df_grouped["Total"] * 100).round(1)
    
    # Display statistics table
    st.subheader("Sentiment Statistics by Week")
    st.dataframe(df_grouped.style.set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}))
    
    # --- VISUAL 1: Simple Line Chart ---
    
    st.subheader("Sentiment Trends Over Time")
    
    if not numeric_df.empty:
        # Group by week and sum sentiment counts
        week_summary = numeric_df.groupby("Week").agg({
            "Positive": "sum",
            "Negative": "sum", 
            "Neutral": "sum"
        }).reset_index()
        
        # Create simple line chart
        fig1 = px.line(
            week_summary,
            x="Week",
            y=["Positive", "Negative", "Neutral"],
            title="Sentiment Counts Over Time",
            labels={"Week": "Week Number", "value": "Count", "variable": "Sentiment"},
            color_discrete_map={"Positive": "#2E8B57", "Negative": "#CD5C5C", "Neutral": "#6495ED"},
            markers=True
        )
        
        # Add final interview data if available
        if not final_df.empty:
            final_counts = {
                "Positive": final_df["Positive"].sum(),
                "Negative": final_df["Negative"].sum(),
                "Neutral": final_df["Neutral"].sum()
            }
            
            last_week = week_summary["Week"].max()
            final_week = last_week + 1
            
            # Add final data points
            for sentiment, count in final_counts.items():
                color = {"Positive": "#2E8B57", "Negative": "#CD5C5C", "Neutral": "#6495ED"}[sentiment]
                fig1.add_trace(
                    go.Scatter(
                        x=[final_week],
                        y=[count],
                        mode="markers",
                        marker=dict(size=10, color=color),
                        name=f"Final {sentiment}",
                        showlegend=False
                    )
                )
            
            # Update x-axis to show "Final" label
            tick_vals = list(week_summary["Week"]) + [final_week]
            tick_text = [str(int(w)) for w in week_summary["Week"]] + ["Final"]
            fig1.update_xaxes(tickvals=tick_vals, ticktext=tick_text)
        
        fig1.update_layout(
            xaxis_title="Week",
            yaxis_title="Sentiment Count",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Not enough data to generate the sentiment trends visualization.")
    
    # --- VISUAL 2: Diverging Heatmap ---
    
    st.subheader("Sentiment Polarity by Participant and Week")
    
    if not df.empty and len(df["Patient ID"].unique()) > 0:
        # Create pivot table for heatmap
        heatmap_df = df.pivot_table(
            index="Patient ID",
            columns="Week Label",
            values="Net Score",
            aggfunc="sum"
        ).fillna(0)
        
        # Create heatmap
        fig2 = px.imshow(
            heatmap_df,
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            title="Positive-Minus-Negative Sentiment Heatmap",
            labels={"color": "Net Score"}
        )
        
        # Show values in cells
        fig2.update_traces(text=heatmap_df, texttemplate="%{z}")
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data to generate the heatmap visualization.")
    
    # --- VISUAL 2.5: Detailed Sentiment Statistics Table ---
    st.subheader("Detailed Sentiment Statistics by Session Type")
    
    # Create a detailed table with session type, week, and filename
    detail_cols = ["Patient ID", "Session Type", "Week", "Filename", "Condition", "Positive", "Negative", "Neutral", "Net Score"]
    detail_df = df[detail_cols].copy()
    
    # Format the Week column for display
    detail_df["Week"] = detail_df["Week"].apply(lambda w: "Final" if pd.isna(w) else f"Week {int(w)}" if isinstance(w, (int, float)) else w)
    
    # Sort by Session Type, Patient ID, and Week
    detail_df = detail_df.sort_values(["Session Type", "Patient ID", "Week"])
    
    # Display the table with a filter
    st.dataframe(detail_df, use_container_width=True)
    
    # --- VISUAL 3: Polar "Rose" Comparison ---
    
    st.subheader("Session Type Sentiment Comparison (Interactive)")

    # Map session types to labels
    session_type_map = {
        0: "Baseline",
        None: "Final",
        "Exposure with Researcher": "ER",
        "Exposure on Own": "EP"
    }

    # Debug: Print unique session types in the dataset
    st.write("Available session types in data:", df["Session Type"].unique())
    
    # Collect all available session types
    available_types = {}
    
    # Baseline (Week 0)
    baseline_df = df[df["Week"] == 0]
    if not baseline_df.empty:
        available_types["Baseline"] = baseline_df
    else:
        # Create empty dataframe with the same structure
        available_types["Baseline"] = pd.DataFrame(columns=df.columns)
        available_types["Baseline"]["Positive"] = [0]
        available_types["Baseline"]["Negative"] = [0]
        available_types["Baseline"]["Neutral"] = [0]
    
    # Final (Week is None)
    final_df = df[df["Week"].isna()]
    if not final_df.empty:
        available_types["Final"] = final_df
    else:
        # Create empty dataframe with the same structure
        available_types["Final"] = pd.DataFrame(columns=df.columns)
        available_types["Final"]["Positive"] = [0]
        available_types["Final"]["Negative"] = [0]
        available_types["Final"]["Neutral"] = [0]
    
    # ER - Always include even if empty
    # Match "Exposure with Researcher"
    er_df = df[df["Session Type"] == "Exposure with Researcher"]
    if not er_df.empty:
        available_types["ER"] = er_df
        # Debug: Show ER data
        st.write("ER Data Found:", len(er_df), "rows")
    else:
        # Create empty dataframe with the same structure
        available_types["ER"] = pd.DataFrame(columns=df.columns)
        available_types["ER"]["Positive"] = [0]
        available_types["ER"]["Negative"] = [0]
        available_types["ER"]["Neutral"] = [0]
        # Debug: No ER data found
        st.write("No ER data found in the filtered dataset")
    
    # EP - Always include even if empty
    # Match "Exposure on Own"
    ep_df = df[df["Session Type"] == "Exposure on Own"]
    if not ep_df.empty:
        available_types["EP"] = ep_df
        # Debug: Show EP data
        st.write("EP Data Found:", len(ep_df), "rows")
    else:
        # Create empty dataframe with the same structure
        available_types["EP"] = pd.DataFrame(columns=df.columns)
        available_types["EP"]["Positive"] = [0]
        available_types["EP"]["Negative"] = [0]
        available_types["EP"]["Neutral"] = [0]
        # Debug: No EP data found
        st.write("No EP data found in the filtered dataset")

    sentiment_types = list(available_types.keys())
    sentiment_names = ["Positive", "Negative", "Neutral"]
    color_map = {"Baseline": "#1E90FF", "Final": "#FF6347", "ER": "#32CD32", "EP": "#FFD700"}

    # Create a trace for each session type
    traces = []
    for period in sentiment_types:
        period_counts = [available_types[period][sent].sum() for sent in sentiment_names]
        traces.append(go.Scatterpolar(
            r=period_counts + [period_counts[0]],
            theta=sentiment_names + [sentiment_names[0]],
            name=period,
            line=dict(color=color_map.get(period, None)),
            visible=True  # All visible by default
        ))

    fig3 = go.Figure(data=traces)
    
    # Configure the layout for better legend interactivity
    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Session Type Sentiment Comparison (Click legend items to toggle)",
        legend=dict(
            title="Session Types",
            itemclick="toggle",      # Toggle single trace
            itemdoubleclick="toggleothers",  # Toggle all others
            orientation="h",        # Horizontal legend
            yanchor="bottom",       # Position at bottom
            y=1.02,                # Slightly above the chart
            xanchor="right",        # Right-aligned
            x=1                    # At the right edge
        )
    )
    
    # Add annotation explaining how to use the legend
    fig3.add_annotation(
        text="Click legend items to show/hide • Double-click to isolate",
        xref="paper", yref="paper",
        x=0.5, y=-0.1,
        showarrow=False,
        font=dict(size=10, color="gray")
    )
    
    st.plotly_chart(fig3, use_container_width=True)

    # --- NEW VISUAL: Condition Type Sentiment Comparison ---
    
    st.subheader("Condition Type Sentiment Comparison (Interactive)")
    
    # Get unique conditions
    unique_conditions = df["Condition"].dropna().unique()
    
    # Collect all available condition types
    condition_types = {}
    
    # Create a dataframe for each condition type
    for condition in unique_conditions:
        condition_df = df[df["Condition"] == condition]
        if not condition_df.empty:
            condition_types[condition] = condition_df
            # Debug: Show condition data
            st.write(f"{condition} Data Found:", len(condition_df), "rows")
        else:
            # Create empty dataframe with the same structure
            condition_types[condition] = pd.DataFrame(columns=df.columns)
            condition_types[condition]["Positive"] = [0]
            condition_types[condition]["Negative"] = [0]
            condition_types[condition]["Neutral"] = [0]
    
    condition_names = list(condition_types.keys())
    # Use Plotly's qualitative color schemes for condition type comparison
    condition_colors = px.colors.qualitative.Plotly
    condition_color_map = {condition: condition_colors[i % len(condition_colors)] 
                           for i, condition in enumerate(condition_names)}
    
    # Create a trace for each condition type
    condition_traces = []
    for condition in condition_names:
        condition_counts = [condition_types[condition][sent].sum() for sent in sentiment_names]
        condition_traces.append(go.Scatterpolar(
            r=condition_counts + [condition_counts[0]],
            theta=sentiment_names + [sentiment_names[0]],
            name=condition,
            line=dict(color=condition_color_map.get(condition, None)),
            visible=True  # All visible by default
        ))
    
    fig_conditions = go.Figure(data=condition_traces)
    
    # Configure the layout for better legend interactivity
    fig_conditions.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Condition Type Sentiment Comparison (Click legend items to toggle)",
        legend=dict(
            title="Condition Types",
            itemclick="toggle",      # Toggle single trace
            itemdoubleclick="toggleothers",  # Toggle all others
            orientation="h",        # Horizontal legend
            yanchor="bottom",       # Position at bottom
            y=1.02,                # Slightly above the chart
            xanchor="right",        # Right-aligned
            x=1                    # At the right edge
        )
    )
    
    # Add annotation explaining how to use the legend
    fig_conditions.add_annotation(
        text="Click legend items to show/hide • Double-click to isolate",
        xref="paper", yref="paper",
        x=0.5, y=-0.1,
        showarrow=False,
        font=dict(size=10, color="gray")
    )
    
    st.plotly_chart(fig_conditions, use_container_width=True)
    
    # --- Examples by Week Section ---
    
    st.subheader("Sentiment Examples by Week")
    
    # Define safe sorting function for weeks
    def safe_sort_key(item):
        if item is None:
            return float('inf')  # Place None values at the end
        try:
            return float(item)  # Try to convert to numeric for proper sorting
        except (ValueError, TypeError):
            return str(item)  # Fall back to string comparison
    
    # Create expanders for each week
    for week in sorted(examples_bank.keys(), key=safe_sort_key):
        week_label = "Final" if week is None or pd.isna(week) else f"Week {week}"
        with st.expander(f"{week_label} Examples"):
            if examples_bank[week]:
                for example in examples_bank[week]:
                    st.markdown(f"- {example}")
            else:
                st.info("No examples available for this week.")

if __name__ == "__main__":
    main()
