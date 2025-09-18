#!/usr/bin/env python3
"""
Data Explorer - Examine transcript content to validate calculation methods
"""
import os
import re
from docx import Document

def read_docx(file_path):
    """Read content from a Word document"""
    try:
        doc = Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            content.append(paragraph.text)
        return '\n'.join(content)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def extract_participant_id(text):
    """Extract participant ID from transcript"""
    match = re.search(r'vr(?:x)?\d+', text, re.IGNORECASE)
    return match.group(0).lower() if match else None

def analyze_transcript_sample(file_path):
    """Analyze a single transcript file"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    content = read_docx(file_path)
    if not content:
        print("❌ Could not read file content")
        return
    
    # Extract participant ID
    participant_id = extract_participant_id(content)
    print(f"📋 Participant ID: {participant_id}")
    
    # Show first 500 characters
    print(f"\n📄 CONTENT PREVIEW (first 500 chars):")
    print("-" * 50)
    print(content[:500])
    print("-" * 50)
    
    if participant_id:
        # Check for speaker patterns
        caregiver_pattern = f"{participant_id}_c:"
        plwd_pattern = f"{participant_id}_p:"
        
        caregiver_matches = re.findall(caregiver_pattern, content, re.IGNORECASE)
        plwd_matches = re.findall(plwd_pattern, content, re.IGNORECASE)
        
        print(f"\n🗣️  SPEAKER PATTERNS:")
        print(f"   Caregiver turns ({caregiver_pattern}): {len(caregiver_matches)}")
        print(f"   PLWD turns ({plwd_pattern}): {len(plwd_matches)}")
        
        # Check for overlapping speech
        overlap_count = content.count('/')
        print(f"   Overlapping speech ('/'): {overlap_count}")
        
        # Check for nonverbal cues
        nonverbal_matches = re.findall(r'\[(.*?)\]', content)
        print(f"   Nonverbal cues [brackets]: {len(nonverbal_matches)}")
        if nonverbal_matches:
            print(f"   Sample nonverbals: {nonverbal_matches[:5]}")
        
        # Check for questions
        question_count = content.count('?')
        print(f"   Question marks: {question_count}")
        
        # Check for disfluencies
        disfluency_pattern = r'\b(um|umm|uh|uhh|er|ah|hmm|mhm)\b'
        disfluency_matches = re.findall(disfluency_pattern, content, re.IGNORECASE)
        print(f"   Disfluencies: {len(disfluency_matches)}")
        
        # Sample speaker segments
        print(f"\n💬 SAMPLE SPEAKER SEGMENTS:")
        caregiver_segments = re.findall(f"{caregiver_pattern}(.*?)(?={participant_id}_[cp]:|$)", content, re.DOTALL | re.IGNORECASE)
        plwd_segments = re.findall(f"{plwd_pattern}(.*?)(?={participant_id}_[cp]:|$)", content, re.DOTALL | re.IGNORECASE)
        
        if caregiver_segments:
            print(f"   Caregiver sample: {caregiver_segments[0][:100]}...")
        if plwd_segments:
            print(f"   PLWD sample: {plwd_segments[0][:100]}...")
        
        # Test sentence counting
        if caregiver_segments:
            sample_text = caregiver_segments[0]
            sentences = re.split(r'[.!?]+', sample_text.strip())
            sentence_count = len([s for s in sentences if s.strip()])
            print(f"\n📝 SENTENCE COUNTING TEST:")
            print(f"   Sample text: {sample_text[:150]}...")
            print(f"   Detected sentences: {sentence_count}")
            print(f"   Sentence splits: {[s.strip()[:30] for s in sentences if s.strip()]}")

def main():
    """Explore data directory and analyze sample files"""
    data_dir = "data"
    
    print("🔍 TRANSCRIPT DATA EXPLORER")
    print("=" * 60)
    
    # Find sample files from different participants
    sample_files = []
    
    for participant_dir in os.listdir(data_dir):
        participant_path = os.path.join(data_dir, participant_dir)
        if os.path.isdir(participant_path):
            # Look for files in subdirectories
            for session_type in os.listdir(participant_path):
                session_path = os.path.join(participant_path, session_type)
                if os.path.isdir(session_path):
                    for file_name in os.listdir(session_path):
                        if file_name.endswith('.docx'):
                            sample_files.append(os.path.join(session_path, file_name))
                            break  # Just one file per session type
                    if len(sample_files) >= 3:  # Limit to 3 samples
                        break
            if len(sample_files) >= 3:
                break
    
    print(f"📁 Found {len(sample_files)} sample files to analyze")
    
    # Analyze each sample file
    for file_path in sample_files:
        analyze_transcript_sample(file_path)
    
    print(f"\n{'='*60}")
    print("✅ ANALYSIS COMPLETE")
    print("📊 Use this data to validate calculation methods")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
