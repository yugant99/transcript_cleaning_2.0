import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
import networkx as nx
from collections import Counter

# --- Paths to your JSON files ---
CLASSIFIED_PATH = "classified_output_1.json"
ENRICHED_PATH = "transcript_insights_updated.json"

@st.cache_data
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_topic_data(selected_patients, selected_sessions, selected_conditions, enhanced_data):
    # Load classified data
    classified = load_json(CLASSIFIED_PATH)
    
    # Initialize data
    topic_rows = []
    
    # Process each file in classified data  
    for file in classified:
        # Skip Final Interview files
        if file.get("final_interview", False) or file.get("session_type", "") == "Final Interview":
            continue
            
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
            
        # Find topic data in enriched dataset
        file_topic_data = None
        if patient_id in enhanced_data:
            # Check each session type category
            for session_category, files in enhanced_data[patient_id].items():
                if filename in files and "Topic Modeling" in files[filename]:
                    file_topic_data = files[filename]["Topic Modeling"]
                    break
                    
        # Skip if no topic data found
        if not file_topic_data:
            continue
            
        # Extract main topics
        main_topics = file_topic_data.get("main_topics", [])
        if not isinstance(main_topics, list):
            main_topics = [main_topics] if main_topics else []
        
        # Create rows for topic frequencies (one row per topic)
        for topic in main_topics:
            topic_name = ""
            if isinstance(topic, str):
                topic_name = topic.strip().lower()  # Normalize case and strip whitespace
            elif isinstance(topic, dict) and "topic" in topic:
                topic_name = str(topic["topic"]).strip().lower()  # Normalize case and strip whitespace
            
            # Only add if we have a valid topic name
            if topic_name:
                topic_rows.append({
                    "Patient ID": patient_id,
                    "Session Type": session_type,
                    "Week": week,
                    "Filename": filename,
                    "Condition": condition_value,  # Add condition value
                    "Topic": topic_name.title(),  # Use title case for consistency
                    "Count": 1  # Each topic occurrence counts as 1
                })
        
        # Extract topic switching examples
        topic_switching = file_topic_data.get("topic_switching", [])
        if not isinstance(topic_switching, list):
            topic_switching = [topic_switching] if topic_switching else []
        
        # Parse topic switching examples
        for switch in topic_switching:
            if isinstance(switch, str):
                # Try to extract from_topic and to_topic using regex
                match = re.match(r"From\s+(.+?)\s+to\s+(.+?):\s+'(.+)'", switch)
                if match:
                    from_topic, to_topic, example_text = match.groups()
                    topic_rows.append({
                        "Patient ID": patient_id,
                        "Session Type": session_type,
                        "Week": week,
                        "Filename": filename,
                        "Condition": condition_value,  # Add condition value
                        "From Topic": from_topic.strip().title(),  # Normalize case
                        "To Topic": to_topic.strip().title(),  # Normalize case
                        "Example Text": example_text.strip(),
                        "Original": switch
                    })
                else:
                    # Alternative format handling
                    parts = switch.split(":")
                    if len(parts) >= 2:
                        topic_part = parts[0].strip()
                        example_text = ":".join(parts[1:]).strip()
                        
                        # Try to extract topics from the first part
                        topic_match = re.search(r"from\s+(.+?)\s+to\s+(.+)", topic_part, re.IGNORECASE)
                        if topic_match:
                            from_topic, to_topic = topic_match.groups()
                            topic_rows.append({
                                "Patient ID": patient_id,
                                "Session Type": session_type,
                                "Week": week,
                                "Filename": filename,
                                "Condition": condition_value,  # Add condition value
                                "From Topic": from_topic.strip().title(),  # Normalize case
                                "To Topic": to_topic.strip().title(),  # Normalize case
                                "Example Text": example_text.strip("' "),
                                "Original": switch
                            })
            elif isinstance(switch, dict):
                # Handle dictionary format if present
                from_topic = switch.get("from_topic", "")
                to_topic = switch.get("to_topic", "")
                example = switch.get("example", "")
                
                if from_topic and to_topic:
                    topic_rows.append({
                        "Patient ID": patient_id,
                        "Session Type": session_type,
                        "Week": week,
                        "Filename": filename,
                        "Condition": condition_value,  # Add condition value
                        "From Topic": from_topic.strip().title(),  # Normalize case
                        "To Topic": to_topic.strip().title(),  # Normalize case
                        "Example Text": example,
                        "Original": str(switch)
                    })
    
    # Create DataFrames
    topic_freq_df = pd.DataFrame(topic_rows)
    
    return topic_freq_df

def main():
    st.title("Topic Explorer")

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
    
    # Extract topic data
    topic_freq_df = extract_topic_data(selected_patients, selected_sessions, selected_conditions, load_json(ENRICHED_PATH))
    
    if topic_freq_df.empty:
        st.warning("No topic data available for selected filters.")
        return
    
    # Display filter selection
    selected_patients_text = ", ".join(selected_patients) if selected_patients else "All"
    selected_sessions_text = ", ".join(selected_sessions) if selected_sessions else "All"
    selected_conditions_text = ", ".join(selected_conditions) if selected_conditions else "All"
    st.markdown(f"### Showing Topic Data for: Participants - **{selected_patients_text}**, Sessions - **{selected_sessions_text}**, Conditions - **{selected_conditions_text}**")
    
    # --- Data Preparation ---
    
    # Convert Week to numeric for proper sorting and grouping
    topic_freq_df["Week"] = pd.to_numeric(topic_freq_df["Week"], errors="coerce")
    
    # Create week label for display purposes
    topic_freq_df["Week Label"] = topic_freq_df["Week"].apply(
        lambda w: "Final" if pd.isna(w) else f"Week {int(w)}"
    )
    
    # --- Data Separation and Aggregation ---
    
    # Separate topic switching data before aggregation (check if Original column exists)
    if "Original" in topic_freq_df.columns:
        switches_df = topic_freq_df[topic_freq_df["Original"].notna()].copy()
        # Filter out topic switching rows for main topic analysis
        main_topics_df = topic_freq_df[topic_freq_df["Original"].isna()].copy()
    else:
        switches_df = pd.DataFrame()  # Empty dataframe if no switching data
        main_topics_df = topic_freq_df.copy()
    
    # Aggregate main topics data to handle duplicates
    if not main_topics_df.empty:
        topic_freq_df = main_topics_df.groupby([
            "Patient ID", "Session Type", "Week", "Week Label", "Filename", "Condition", "Topic"
        ])["Count"].sum().reset_index()
    else:
        topic_freq_df = main_topics_df
    
    # --- Summary Table ---
    
    st.subheader("Topic Frequency Summary")
    
    # Group by topic and count occurrences
    topic_summary = topic_freq_df.groupby("Topic")["Count"].sum().reset_index()
    topic_summary = topic_summary.sort_values("Count", ascending=False)
    
    # Display summary table
    st.dataframe(topic_summary.style.set_properties(**{'background-color': '#f9f9f9', 'color': '#333'}))
    
    # --- VISUAL 1: Sunburst Chart ---
    
    st.subheader("Topic Distribution Sunburst")
    
    # Prepare data for sunburst chart by aggregating at each level but keeping condition info
    sunburst_df = topic_freq_df.groupby(["Patient ID", "Week Label", "Topic", "Condition"])["Count"].sum().reset_index()
    
    # Create a combined path that includes condition info for hover
    sunburst_df["Topic_with_Condition"] = sunburst_df["Topic"] + " (" + sunburst_df["Condition"] + ")"
    
    # Only create sunburst if we have data
    if not sunburst_df.empty:
        # Create sunburst chart with condition info in hover
        fig1 = px.sunburst(
            sunburst_df,
            path=["Patient ID", "Week Label", "Topic_with_Condition"],
            values="Count",
            title="Topic Distribution Hierarchy (Hover to see VR/Tablet condition)",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hover_data={"Condition": True}
        )
        
        # Update hover template to show condition clearly
        fig1.update_traces(
            hovertemplate="<b>%{label}</b><br>" +
                         "Count: %{value}<br>" +
                         "Condition: %{customdata[0]}<br>" +
                         "<extra></extra>",
            customdata=sunburst_df[["Condition"]].values
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available for the sunburst chart.")
    
    # --- VISUAL 2: Sankey Diagram ---
    
    
    # --- VISUAL 3: Network Graph ---
    
    st.subheader("Topic Relationship Network")
    
    # Create a graph to represent topic co-occurrences
    G = nx.Graph()
    
    # Group by filename to find co-occurring topics
    file_topics = topic_freq_df.groupby("Filename")["Topic"].apply(list).reset_index()
    
    # Add nodes for all topics
    all_topics = topic_freq_df["Topic"].unique()
    for topic in all_topics:
        G.add_node(topic)
    
    # Add edges for co-occurring topics
    edge_weights = {}
    
    for _, row in file_topics.iterrows():
        topics = row["Topic"]
        # Create edges between all pairs of topics in the same file
        for i in range(len(topics)):
            for j in range(i + 1, len(topics)):
                edge = tuple(sorted([topics[i], topics[j]]))
                if edge in edge_weights:
                    edge_weights[edge] += 1
                else:
                    edge_weights[edge] = 1
    
    # Add weighted edges to the graph
    for (source, target), weight in edge_weights.items():
        G.add_edge(source, target, weight=weight)
    
    # Calculate node sizes based on degree
    node_degrees = dict(G.degree())
    node_sizes = {node: (degree + 1) * 10 for node, degree in node_degrees.items()}
    
    # Calculate positions using spring layout
    pos = nx.spring_layout(G, seed=42)
    
    # Create network visualization using Plotly
    edge_x = []
    edge_y = []
    edge_weights_list = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights_list.append(edge[2]["weight"])
    
    # Scale edge widths
    max_weight = max(edge_weights_list) if edge_weights_list else 1
    edge_widths = [1 + (w / max_weight) * 5 for w in edge_weights_list]
    
    # Create edges trace with fixed width instead of variable widths
    edges_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='rgba(150, 150, 150, 0.7)'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>Connections: {node_degrees[node]}")
        node_size.append(node_sizes[node])
    
    nodes_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='Turbo',  # Updated to 'Turbo' for greater color variety
            size=node_size,
            color=[node_degrees[node] for node in G.nodes()],
            line=dict(width=2, color='white')
        )
    )
    
    # Create the figure
    fig3 = go.Figure(data=[edges_trace, nodes_trace],
                    layout=go.Layout(
                        title=dict(text='Topic Relationship Network', font=dict(size=16)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # --- Topic Switch Examples ---
    
    if not switches_df.empty:
        st.subheader("Topic Switch Examples")
        
        # Define safe sorting function for weeks
        def safe_sort_key(item):
            if item is None:
                return float('inf')  # Place None values at the end
            try:
                return float(item)  # Try to convert to numeric for proper sorting
            except (ValueError, TypeError):
                return str(item)  # Fall back to string comparison
        
        # Group switches by week
        week_groups = switches_df.groupby("Week Label")
        
        # Create expanders for each week
        for week_label, group in sorted(week_groups, key=lambda x: safe_sort_key(x[0])):
            with st.expander(f"Topic Switches - {week_label}"):
                for _, row in group.iterrows():
                    st.markdown(f"**From '{row['From Topic']}' to '{row['To Topic']}':** {row['Example Text']}")
    else:
        st.info("No topic switch examples available for the selected filters.")

if __name__ == "__main__":
    main()
