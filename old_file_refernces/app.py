import streamlit as st
from streamlit.components.v1 import html
from theme import apply_theme, create_breadcrumb, card_container
import json
import os

# --- Helper functions for consistent filtering across pages ---
@st.cache_data
def load_json_data(path):
    """Load JSON data with caching for better performance"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data from {path}: {e}")
        return None

def get_filter_options():
    """Get common filter options used across pages - excludes Final Interview files"""
    classified_data = load_json_data("classified_output_1.json")
    if not classified_data:
        return [], [], []
    
    # Filter out Final Interview files
    filtered_data = [f for f in classified_data if not f.get("final_interview", False) 
                    and f.get("session_type", "") != "Final Interview"]
        
    all_patients = sorted(set(f.get("patient_id", "") for f in filtered_data if f.get("patient_id")))
    all_sessions = sorted(set(f.get("session_type", "") for f in filtered_data if f.get("session_type")))
    all_conditions = sorted(set(f.get("condition_value", "") for f in filtered_data if f.get("condition_value")))
    
    return all_patients, all_sessions, all_conditions

# Set page configuration for a wide, spacious layout
st.set_page_config(
    page_title="Transcript Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Apply consistent theme across all pages
apply_theme()
    
# --- Main Page Content ---
st.title("📊 Transcript Analysis Dashboard")

# Add explanation about data sources and calculations
with st.expander("📖 **About Data Sources & Calculations**", expanded=False):
    st.markdown("""
    ### 🔍 **Core Data Processing Pipeline:**
    
    **1. transcript_insight.py** → Extracts basic statistics:
    - Turn counting: Identifies speaker segments by `participant_id_c:` and `participant_id_p:` patterns
    - Basic word counting: Simple word splits (later refined by word_count_updater.py)
    - Question counting: Simple question mark counting (later improved by enhanced analysis)
    
    **2. word_count_updater.py** → Cleans word counts:
    - Extracts speaker segments: Uses regex patterns `{participant_id}_c:` and `{participant_id}_p:` to identify speaker turns
    - Removes bracketed content: Uses `re.sub(r'\[.*?\]', '', segment)` to exclude `[pause]`, `[laughter]`, etc.
    - Tokenizes by whitespace: Splits segments using `segment.strip().split()`
    - Removes disfluencies: Filters out predefined set including "um", "umm", "uh", "uhh", "uhhh", "er", "err", "erm", "ah", "ahh", "hm", "hmm", "mhm", "mm", "mmm", "eh", "ehm", "em"
    - Updates `transcript_insights_updated.json` with cleaned caregiver_words and plwd_words counts
    
    **3. disfluency_ques.py** → Enhanced turn-level analysis:
    - Question detection: Context-aware identification using turn patterns
    - Disfluency detection: Precise regex patterns for filled pauses
    - Response tracking: Links questions to responses
    - Generates `enhanced_transcript_analysis.json`
    
    **4. fix_nonverbal_cues.py** → Normalizes non-verbal cues:
    - Standardizes variations: "laugh", "laughter" → "laughter"
    - Excludes problematic cues: Language annotations, technical metadata
    - Generates `enhanced_transcript_analysis_fixed.json`
    
    ### 📊 **Metric Consistency Across Views:**
    - **Word Counts**: All views use cleaned counts from `word_count_updater.py`
    - **Question Counts**: All views use turn-level detection from `enhanced_transcript_analysis.json`
    - **Disfluency Counts**: All views use turn-level counts from `enhanced_transcript_analysis.json`
    - **Turn Counts**: All views use speaker segment patterns from `transcript_insight.py`
    """)

# Custom CSS for better spacing and readability
st.markdown("""
    <style>
    .main-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .category-header {
        color: #1f77b4;
        margin-bottom: 15px;
    }
    .page-description {
        color: #495057;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Create category containers with detailed descriptions
def create_category_section(title, pages_info):
    st.markdown(f'<div class="main-card">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="category-header">{title}</h2>', unsafe_allow_html=True)
    
    for page_name, info in pages_info.items():
        col1, col2 = st.columns([1, 5])
        with col1:
            st.page_link(info["path"], label="Open", icon="➡️")
        with col2:
            with st.expander(f"📊 {page_name}", expanded=False):
                st.markdown(f'**Purpose**: {info["description"]}')
                
                if "calculations" in info:
                    st.markdown("**📈 Key Calculations:**")
                    for calc_name, calc_desc in info["calculations"].items():
                        st.markdown(f"- **{calc_name}**: {calc_desc}")
                
                if "data_sources" in info:
                    st.markdown("**📁 Data Sources:**")
                    for source_name, source_desc in info["data_sources"].items():
                        st.markdown(f"- **{source_name}**: {source_desc}")
                
                if "metrics" in info:
                    st.markdown("**📊 Metrics Displayed:**")
                    for metric in info["metrics"]:
                        st.markdown(f"- {metric}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Define page categories and their descriptions
interaction_pages = {
    "Caregiver-PLWD Interaction": {
        "path": "pages/01_caregiver_plwd_interaction.py",
        "description": "Provides three different views of interaction patterns: Turn Analysis, Word Usage, and Interaction Summaries.",
        "calculations": {
            "Turn Analysis": "Counts speaker segments identified by participant_id_c: and participant_id_p: patterns",
            "Word Usage": "Uses cleaned word counts from word_count_updater.py (excludes disfluencies and [bracketed content])",
            "Turn Balance": "Caregiver turns / PLWD turns ratio"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Turn counts, word counts, and basic statistics",
            "classified_output_1.json": "Session metadata and condition information"
        },
        "metrics": [
            "Caregiver/PLWD turn counts", "Word counts per speaker", "Turn-taking balance ratios"
        ]
    },
    "Nonverbal Communication": {
        "path": "pages/non_verb.py",
        "description": "Analyzes normalized non-verbal cues (laughter, sighs, pauses) with cleaned data from fix_nonverbal_cues.py.",
        "calculations": {
            "Nonverbal Rate": "Total nonverbal cues / total words × 100",
            "Cue Normalization": "Uses fix_nonverbal_cues.py to standardize variations (e.g., 'laugh', 'laughter' → 'laughter')",
            "Weekly Aggregation": "Sums nonverbal cues by week across all sessions"
        },
        "data_sources": {
            "enhanced_transcript_analysis_fixed.json": "Normalized nonverbal cues from turn-level analysis",
            "transcript_insights_updated.json": "Word counts for rate calculations",
            "classified_output_1.json": "Session and week metadata"
        },
        "metrics": [
            "Nonverbal cue counts by type", "Nonverbal rates per speaker", "Weekly progression trends"
        ]
    },
    "Turn Taking Ratio": {
        "path": "pages/turn_taking_ratio.py",
        "description": "Analyzes conversation balance and turn-taking patterns between caregivers and PLWD.",
        "calculations": {
            "Overlapping Speech": "Counts instances marked by '/' in transcripts (from transcript_insight.py)",
            "Dominance Ratio": "caregiver_turns / (plwd_turns + 1e-9) to avoid division by zero",
            "Turn Difference": "caregiver_turns - plwd_turns"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Turn counts and overlapping speech statistics",
            "classified_output_1.json": "Session metadata and filtering options"
        },
        "metrics": [
            "Turn counts per speaker", "Overlapping speech instances", "Dominance ratios", "Motion views by week/condition"
        ]
    }
}

language_pages = {
    "Lexical Diversity": {
        "path": "pages/lexical_diversity.py",
        "description": "Comprehensive language analysis measuring conversation interactivity and speech complexity.",
        "calculations": {
            "Question Word Ratio": "(total_questions / total_words) - uses enhanced_transcript_analysis.json for accurate question counts",
            "Speech Density": "total_words / total_turns for each speaker - indicates speech complexity and elaboration (higher values = more words per conversational turn)",
            "Caregiver Density": "caregiver_words / caregiver_turns - measures caregiver speech elaboration",
            "PLWD Density": "plwd_words / plwd_turns - measures PLWD speech elaboration",
            "Word Counts": "From word_count_updater.py: excludes disfluencies and [bracketed content]"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn statistics",
            "enhanced_transcript_analysis.json": "Turn-level question identification (is_question flags)",
            "classified_output_1.json": "Session metadata and condition information"
        },
        "metrics": [
            "Speech density (words per turn) by speaker", "Question-to-word ratios", "Speech complexity measures", "Condition-based comparisons"
        ]
    },
    "Disfluency Analysis": {
        "path": "pages/disfluency.py",
        "description": "Analysis of speech disfluencies and filled pauses using pattern matching from disfluency_ques.py.",
        "calculations": {
            "Disfluency Rate": "(disfluency_count / total_words) × 100 for each speaker - disfluencies per 100 words",
            "Disfluency Detection": "Turn-level detection using regex patterns for 'um', 'uh', 'er', 'ah', 'hmm', etc. from disfluency_ques.py",
            "Disfluency Counting": "Counts individual disfluency instances from turn-level data in enhanced_transcript_analysis.json",
            "Rate Calculation": "Divides disfluency counts by word counts (not turn counts) to get meaningful percentages"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level disfluency detection, individual disfluency instances, and disfluency type classification",
            "transcript_insights_updated.json": "Cleaned word counts (denominator for rate calculations) and turn counts",
            "classified_output_1.json": "Session type, condition, week, and participant metadata"
        },
        "metrics": [
            "Disfluency rates per speaker", "Disfluency type breakdowns", "Weekly progression", "Polar charts by condition"
        ]
    },
    "Sentiment Analysis": {
        "path": "pages/sentiment_analysis.py",
        "description": "Sentiment analysis using local Mistral-7B model for context-aware classification.",
        "calculations": {
            "Sentiment Classification": "Local Mistral-7B model analyzes utterances as positive/negative/neutral",
            "Sentiment Counts": "Aggregates sentiment classifications by week and session type",
            "Temporal Trends": "Line charts showing sentiment progression over study weeks"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level sentiment classifications",
            "classified_output_1.json": "Session type and week metadata"
        },
        "metrics": [
            "Sentiment distribution percentages", "Weekly sentiment trends", "Session type comparisons", "Example utterances"
        ]
    },
    "Custom Mistral Query": {
        "path": "pages/custom_mistral_query.py",
        "description": "Interactive search and query tool using local Mistral-7B model.",
        "calculations": {
            "Keyword Search": "Exact text matching in transcript content",
            "Semantic Search": "Vector-based similarity search for contextual relevance",
            "LLM Analysis": "Local Mistral-7B processes found contexts to answer questions"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Full transcript text and turn-level data",
            "classified_output_1.json": "File metadata for search context"
        },
        "metrics": [
            "Search result relevance scores", "Context snippets", "LLM-generated insights"
        ]
    },
    "Word Repeat Analysis": {
        "path": "pages/word_repeats.py",
        "description": "Detects and analyzes immediate word repetitions using NLP techniques to identify disfluency patterns.",
        "calculations": {
            "Word Repeat Detection": "NLTK tokenization and immediate repetition detection (back-to-back identical words)",
            "Repeat Rate": "(word_repeats / total_words) × 100 for each speaker - repetitions per 100 words",
            "Context Highlighting": "Shows repeated words in context with surrounding text for analysis",
            "Filtering": "Excludes disfluency markers (um, uh, er) but includes meaningful repeated words"
        },
        "data_sources": {
            "enriched_turns.csv": "Individual turn text data for real-time word repeat analysis",
            "classified_output_1.json": "Session metadata and condition information for filtering"
        },
        "metrics": [
            "Word repeat counts by speaker", "Word repeat rates per 100 words", "Weekly progression trends", "Example contexts with highlighted repetitions"
        ]
    }
}

analysis_pages = {
    "Memory Analysis": {
        "path": "pages/07_memory.py",
        "description": "Uses local Mistral-7B model to identify and analyze memory-related references in conversations.",
        "calculations": {
            "Memory Detection": "Local Mistral-7B model identifies references to past events, memories, and recollections",
            "Memory Classification": "Categorizes memory types (episodic, semantic, procedural)",
            "Temporal Analysis": "Tracks memory references across study weeks"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Full transcript text for memory analysis",
            "classified_output_1.json": "Session and participant metadata"
        },
        "metrics": [
            "Memory reference counts", "Memory type distributions", "Weekly memory trends", "Example memory mentions"
        ]
    },

    "Questions & Answers": {
        "path": "pages/questions_answers.py",
        "description": "Comprehensive analysis of question-asking patterns and conversational engagement.",
        "calculations": {
            "Question Rates": "(questions / words) × 100 for each speaker - more accurate than per-turn rates",
            "Question Balance": "A score from 0.1 to 0.9 showing how evenly questions are shared between caregiver and person with dementia (0.5 = perfectly balanced)",
            "Engagement Index": "A measure of how actively the person with dementia participates in conversations - higher scores mean more questions and better engagement",
            "Question Detection": "Turn-level analysis from enhanced_transcript_analysis.json using is_question flags"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level question identification and response tracking",
            "transcript_insights_updated.json": "Word counts for rate calculations",
            "classified_output_1.json": "Session metadata and filtering options"
        },
        "metrics": [
            "Question rates per 100 words", "Question balance ratios", "Engagement indices", "Baseline vs final comparisons"
        ]
    }
}

overview_pages = {
    "Total View": {
        "path": "pages/total_view.py",
        "description": "Comprehensive aggregation and analysis of all key conversation metrics across multiple views.",
        "calculations": {
            "Turn Counting": "Speaker segments identified by participant_id_c: and participant_id_p: patterns",
            "Word Counting": "From word_count_updater.py: excludes disfluencies and [bracketed content]",
            "Question Detection": "Turn-level analysis using is_question flags from enhanced_transcript_analysis.json",
            "Disfluency Counting": "Turn-level disfluency instances from enhanced_transcript_analysis.json"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn statistics",
            "enhanced_transcript_analysis.json": "Turn-level question and disfluency data",
            "classified_output_1.json": "Session and condition metadata"
        },
        "metrics": [
            "File-level detailed statistics", "Week-wise aggregations", "Condition-based comparisons", "Session type breakdowns"
        ]
    },
    
    "Summary": {
        "path": "pages/summary.py",
        "description": "Patient-by-patient breakdown showing all key conversation metrics in expandable sections.",
        "calculations": {
            "Patient Grouping": "Organizes all metrics by participant ID",
            "Turn Counting": "From transcript_insight.py: participant_id_c: and participant_id_p: patterns",
            "Word Counting": "From word_count_updater.py: excludes disfluencies and [bracketed content]",
            "Question/Disfluency Counting": "From enhanced_transcript_analysis.json turn-level data"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn data",
            "enhanced_transcript_analysis.json": "Turn-level question and disfluency counts",
            "classified_output_1.json": "Session and condition metadata"
        },
        "metrics": [
            "Per-patient session statistics", "Week-by-week progression", "Condition and session type breakdowns"
        ]
    }
}

# Create ordered page structure as requested
ordered_pages = {
    "Caregiver-PLWD Interaction": {
        "path": "pages/01_caregiver_plwd_interaction.py",
        "description": "Provides three different views of interaction patterns: Turn Analysis, Word Usage, and Interaction Summaries.",
        "calculations": {
            "Turn Analysis": "Counts speaker segments identified by participant_id_c: and participant_id_p: patterns",
            "Word Usage": "Uses cleaned word counts from word_count_updater.py (excludes disfluencies and [bracketed content])",
            "Turn Balance": "Caregiver turns / PLWD turns ratio"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Turn counts, word counts, and basic statistics",
            "classified_output_1.json": "Session metadata and condition information"
        },
        "metrics": [
            "Caregiver/PLWD turn counts", "Word counts per speaker", "Turn-taking balance ratios"
        ]
    },
    "Summary": {
        "path": "pages/02_summary.py",
        "description": "Patient-by-patient breakdown showing all key conversation metrics in expandable sections.",
        "calculations": {
            "Patient Grouping": "Organizes all metrics by participant ID",
            "Turn Counting": "From transcript_insight.py: participant_id_c: and participant_id_p: patterns",
            "Word Counting": "From word_count_updater.py: excludes disfluencies and [bracketed content]",
            "Question/Disfluency Counting": "From enhanced_transcript_analysis.json turn-level data"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn data",
            "enhanced_transcript_analysis.json": "Turn-level question and disfluency counts",
            "classified_output_1.json": "Session and condition metadata"
        },
        "metrics": [
            "Per-patient session statistics", "Week-by-week progression", "Condition and session type breakdowns"
        ]
    },
    "Sentiment Analysis": {
        "path": "pages/03_sentiment_analysis.py",
        "description": "Sentiment analysis using local Mistral-7B model for context-aware classification.",
        "calculations": {
            "Sentiment Classification": "Local Mistral-7B model analyzes utterances as positive/negative/neutral",
            "Sentiment Counts": "Aggregates sentiment classifications by week and session type",
            "Temporal Trends": "Line charts showing sentiment progression over study weeks"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level sentiment classifications",
            "classified_output_1.json": "Session type and week metadata"
        },
        "metrics": [
            "Sentiment distribution percentages", "Weekly sentiment trends", "Session type comparisons", "Example utterances"
        ]
    },
    "Lexical Diversity": {
        "path": "pages/04_lexical_diversity.py",
        "description": "Comprehensive language analysis measuring conversation interactivity and speech complexity.",
        "calculations": {
            "Question Word Ratio": "(total_questions / total_words) - uses enhanced_transcript_analysis.json for accurate question counts",
            "Speech Density": "total_words / total_turns for each speaker - indicates speech complexity and elaboration (higher values = more words per conversational turn)",
            "Caregiver Density": "caregiver_words / caregiver_turns - measures caregiver speech elaboration",
            "PLWD Density": "plwd_words / plwd_turns - measures PLWD speech elaboration",
            "Word Counts": "From word_count_updater.py: excludes disfluencies and [bracketed content]"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn statistics",
            "enhanced_transcript_analysis.json": "Turn-level question identification (is_question flags)",
            "classified_output_1.json": "Session metadata and condition information"
        },
        "metrics": [
            "Speech density (words per turn) by speaker", "Question-to-word ratios", "Speech complexity measures", "Condition-based comparisons"
        ]
    },

    "Questions & Answers": {
        "path": "pages/05_questions_answers.py",
        "description": "Comprehensive analysis of question-asking patterns and conversational engagement.",
        "calculations": {
            "Question Rates": "(questions / words) × 100 for each speaker - more accurate than per-turn rates",
            "Question Balance": "A score from 0.1 to 0.9 showing how evenly questions are shared between caregiver and person with dementia (0.5 = perfectly balanced)",
            "Engagement Index": "A measure of how actively the person with dementia participates in conversations - higher scores mean more questions and better engagement",
            "Question Detection": "Turn-level analysis from enhanced_transcript_analysis.json using is_question flags"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level question identification and response tracking",
            "transcript_insights_updated.json": "Word counts for rate calculations",
            "classified_output_1.json": "Session metadata and filtering options"
        },
        "metrics": [
            "Question rates per 100 words", "Question balance ratios", "Engagement indices", "Baseline vs final comparisons"
        ]
    },
    "Nonverbal Communication": {
        "path": "pages/06_non_verb.py",
        "description": "Analyzes normalized non-verbal cues (laughter, sighs, pauses) with cleaned data from fix_nonverbal_cues.py.",
        "calculations": {
            "Nonverbal Rate": "Total nonverbal cues / total words × 100",
            "Cue Normalization": "Uses fix_nonverbal_cues.py to standardize variations (e.g., 'laugh', 'laughter' → 'laughter')",
            "Weekly Aggregation": "Sums nonverbal cues by week across all sessions"
        },
        "data_sources": {
            "enhanced_transcript_analysis_fixed.json": "Normalized nonverbal cues from turn-level analysis",
            "transcript_insights_updated.json": "Word counts for rate calculations",
            "classified_output_1.json": "Session and week metadata"
        },
        "metrics": [
            "Nonverbal cue counts by type", "Nonverbal rates per speaker", "Weekly progression trends"
        ]
    },
    "Memory Analysis": {
        "path": "pages/07_memory.py",
        "description": "Uses local Mistral-7B model to identify and analyze memory-related references in conversations.",
        "calculations": {
            "Memory Detection": "Local Mistral-7B model identifies references to past events, memories, and recollections",
            "Memory Classification": "Categorizes memory types (episodic, semantic, procedural)",
            "Temporal Analysis": "Tracks memory references across study weeks"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Full transcript text for memory analysis",
            "classified_output_1.json": "Session and participant metadata"
        },
        "metrics": [
            "Memory reference counts", "Memory type distributions", "Weekly memory trends", "Example memory mentions"
        ]
    }
}

# Additional pages that come after the main ordered ones
additional_pages = {
    "Turn Taking Ratio": {
        "path": "pages/09_turn_taking_ratio.py",
        "description": "Analyzes conversation balance and turn-taking patterns between caregivers and PLWD.",
        "calculations": {
            "Overlapping Speech": "Counts instances marked by '/' in transcripts (from transcript_insight.py)",
            "Dominance Ratio": "caregiver_turns / (plwd_turns + 1e-9) to avoid division by zero",
            "Turn Difference": "caregiver_turns - plwd_turns"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Turn counts and overlapping speech statistics",
            "classified_output_1.json": "Session metadata and filtering options"
        },
        "metrics": [
            "Turn counts per speaker", "Overlapping speech instances", "Dominance ratios", "Motion views by week/condition"
        ]
    },
    "Disfluency Analysis": {
        "path": "pages/08_disfluency.py",
        "description": "Analysis of speech disfluencies and filled pauses using pattern matching from disfluency_ques.py.",
        "calculations": {
            "Disfluency Rate": "(disfluency_count / total_words) × 100 for each speaker - disfluencies per 100 words",
            "Disfluency Detection": "Turn-level detection using regex patterns for 'um', 'uh', 'er', 'ah', 'hmm', etc. from disfluency_ques.py",
            "Disfluency Counting": "Counts individual disfluency instances from turn-level data in enhanced_transcript_analysis.json",
            "Rate Calculation": "Divides disfluency counts by word counts (not turn counts) to get meaningful percentages"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Turn-level disfluency detection, individual disfluency instances, and disfluency type classification",
            "transcript_insights_updated.json": "Cleaned word counts (denominator for rate calculations) and turn counts",
            "classified_output_1.json": "Session type, condition, week, and participant metadata"
        },
        "metrics": [
            "Disfluency rates per speaker", "Disfluency type breakdowns", "Weekly progression", "Polar charts by condition"
        ]
    },
    "Word Repeat Analysis": {
        "path": "pages/10_word_repeats.py",
        "description": "Detects and analyzes immediate word repetitions using NLP techniques to identify disfluency patterns.",
        "calculations": {
            "Word Repeat Detection": "NLTK tokenization and immediate repetition detection (back-to-back identical words)",
            "Repeat Rate": "(word_repeats / total_words) × 100 for each speaker - repetitions per 100 words",
            "Context Highlighting": "Shows repeated words in context with surrounding text for analysis",
            "Filtering": "Excludes disfluency markers (um, uh, er) but includes meaningful repeated words"
        },
        "data_sources": {
            "enriched_turns.csv": "Individual turn text data for real-time word repeat analysis",
            "classified_output_1.json": "Session metadata and condition information for filtering"
        },
        "metrics": [
            "Word repeat counts by speaker", "Word repeat rates per 100 words", "Weekly progression trends", "Example contexts with highlighted repetitions"
        ]
    },
    "Custom Mistral Query": {
        "path": "pages/11_custom_mistral_query.py",
        "description": "Interactive search and query tool using local Mistral-7B model.",
        "calculations": {
            "Keyword Search": "Exact text matching in transcript content",
            "Semantic Search": "Vector-based similarity search for contextual relevance",
            "LLM Analysis": "Local Mistral-7B processes found contexts to answer questions"
        },
        "data_sources": {
            "enhanced_transcript_analysis.json": "Full transcript text and turn-level data",
            "classified_output_1.json": "File metadata for search context"
        },
        "metrics": [
            "Search result relevance scores", "Context snippets", "LLM-generated insights"
        ]
    },
    "Total View": {
        "path": "pages/12_total_view.py",
        "description": "Comprehensive aggregation and analysis of all key conversation metrics across multiple views.",
        "calculations": {
            "Turn Counting": "Speaker segments identified by participant_id_c: and participant_id_p: patterns",
            "Word Counting": "From word_count_updater.py: excludes disfluencies and [bracketed content]",
            "Question Detection": "Turn-level analysis using is_question flags from enhanced_transcript_analysis.json",
            "Disfluency Counting": "Turn-level disfluency instances from enhanced_transcript_analysis.json"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Cleaned word counts and turn statistics",
            "enhanced_transcript_analysis.json": "Turn-level question and disfluency data",
            "classified_output_1.json": "Session and condition metadata"
        },
        "metrics": [
            "File-level detailed statistics", "Week-wise aggregations", "Condition-based comparisons", "Session type breakdowns"
        ]
    },
    "VR Experiences": {
        "path": "pages/13_vr_experiences.py",
        "description": "Analysis of VR-related experiences and interactions within the conversation data.",
        "calculations": {
            "VR Content Detection": "Identifies VR-related content and experiences mentioned in conversations",
            "Experience Analysis": "Analyzes patterns in VR experience discussions"
        },
        "data_sources": {
            "transcript_insights_updated.json": "Conversation content and structure",
            "classified_output_1.json": "Session and condition metadata"
        },
        "metrics": [
            "VR experience mentions", "VR-related conversation patterns"
        ]
    }
}

# Display pages in the requested order
st.markdown("### 📊 **Main Analysis Pages**")
create_category_section("", ordered_pages)

st.markdown("### 🔧 **Additional Analysis Tools**")
create_category_section("", additional_pages)

# Add helpful tips at the bottom
with st.expander("💡 Tips for Using the Dashboard"):
    st.markdown("""
    - Each page provides specific insights into different aspects of caregiver-PLWD interactions
    - Use the filters at the top of each page to focus on specific participants or sessions
    - Look for the "?" icons throughout the dashboard for additional explanations
    - The Directory page provides a quick overview of all available analyses
    """)

if __name__ == "__main__":
    pass  # Streamlit runs the app automatically
