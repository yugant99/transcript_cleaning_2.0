#!/usr/bin/env python3
import json
import pickle
import os
from pathlib import Path
from textblob import TextBlob
from collections import defaultdict
import re

class SentimentAnalyzer:
    def __init__(self, processed_data_dir="processed_data"):
        self.processed_data_dir = Path(processed_data_dir)
        self.master_file = self.processed_data_dir / "master_transcripts.pkl"
        self.load_chunk_data()
    
    def load_chunk_data(self):
        """Load existing chunk data with embeddings"""
        if self.master_file.exists():
            with open(self.master_file, 'rb') as f:
                self.master_data = pickle.load(f)
            print(f"✅ Loaded {len(self.master_data.get('chunk_metadata', []))} chunks")
        else:
            print("❌ No processed data found. Run incremental processor first.")
            self.master_data = {'chunk_metadata': []}
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using TextBlob"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Classify sentiment
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "polarity": round(polarity, 3),
            "subjectivity": round(subjectivity, 3),
            "confidence": round(abs(polarity), 3)
        }
    
    def extract_metadata_from_filename(self, filename):
        """Extract metadata from filename"""
        # Remove file extension
        base_filename = os.path.splitext(filename)[0]
        
        # Extract participant ID
        participant_match = re.search(r'(VR\d+)', base_filename, re.IGNORECASE)
        participant_id = participant_match.group(1).upper() if participant_match else "Unknown"
        
        # Extract session type and week
        if 'EP' in base_filename:
            session_type = 'Exposure on Own'
            week_match = re.search(r'EP(\d+)', base_filename)
            week_label = f"Week {week_match.group(1)}" if week_match else "Unknown"
        elif 'ER' in base_filename:
            session_type = 'Exposure with Researcher'
            week_match = re.search(r'ER(\d+)', base_filename)
            week_label = f"Week {week_match.group(1)}" if week_match else "Unknown"
        elif 'baseline' in base_filename.lower():
            session_type = 'Baseline'
            week_label = "Baseline"
        elif 'final' in base_filename.lower():
            session_type = 'Final Interview'
            week_label = "Final"
        else:
            session_type = 'Unknown'
            week_label = "Unknown"
        
        # Condition (simplified logic)
        condition = "VR" if 'EP' in base_filename else "Tablet"
        
        return {
            'patient_id': participant_id,
            'session_type': session_type,
            'week_label': week_label,
            'condition': condition,
            'filename': filename
        }
    
    def process_all_chunks(self):
        """Process all chunks for sentiment analysis"""
        sentiment_results = []
        chunk_examples = defaultdict(list)
        
        for chunk_meta in self.master_data.get('chunk_metadata', []):
            # Get text content
            text = chunk_meta.get('chunk_text', '')
            if not text.strip():
                continue
            
            # Get file metadata
            file_metadata = chunk_meta.get('file_metadata', {})
            file_path = file_metadata.get('file_path', '')
            filename = file_metadata.get('filename', os.path.basename(file_path) if file_path else 'unknown.docx')
            
            # Extract metadata from filename
            metadata = self.extract_metadata_from_filename(filename)
            
            # Analyze sentiment
            sentiment_analysis = self.analyze_sentiment(text)
            
            # Create record
            record = {
                **metadata,
                'chunk_index': chunk_meta.get('chunk_index', 0),
                'text': text,
                'speaker': 'Unknown',  # Speaker info not in chunk metadata
                **sentiment_analysis
            }
            
            sentiment_results.append(record)
            
            # Collect examples by sentiment type
            if sentiment_analysis['confidence'] > 0.3:  # Only confident examples
                chunk_examples[sentiment_analysis['sentiment']].append({
                    'text': text[:200] + "..." if len(text) > 200 else text,
                    'confidence': sentiment_analysis['confidence'],
                    'speaker': 'Unknown',
                    'filename': filename,
                    'patient_id': metadata['patient_id']
                })
        
        return sentiment_results, dict(chunk_examples)
    
    def aggregate_by_file(self, sentiment_results):
        """Aggregate sentiment results by file"""
        file_aggregates = defaultdict(lambda: {
            'positive': 0, 'negative': 0, 'neutral': 0,
            'total_chunks': 0, 'avg_polarity': 0.0, 'avg_confidence': 0.0,
            'metadata': {}
        })
        
        for record in sentiment_results:
            key = record['filename']
            sentiment = record['sentiment']
            
            file_aggregates[key][sentiment] += 1
            file_aggregates[key]['total_chunks'] += 1
            file_aggregates[key]['avg_polarity'] += record['polarity']
            file_aggregates[key]['avg_confidence'] += record['confidence']
            
            # Store metadata (same for all chunks in file)
            if not file_aggregates[key]['metadata']:
                file_aggregates[key]['metadata'] = {
                    'patient_id': record['patient_id'],
                    'session_type': record['session_type'],
                    'week_label': record['week_label'],
                    'condition': record['condition'],
                    'filename': record['filename']
                }
        
        # Calculate averages
        for key, data in file_aggregates.items():
            if data['total_chunks'] > 0:
                data['avg_polarity'] = round(data['avg_polarity'] / data['total_chunks'], 3)
                data['avg_confidence'] = round(data['avg_confidence'] / data['total_chunks'], 3)
                data['positive_pct'] = round((data['positive'] / data['total_chunks']) * 100, 1)
                data['negative_pct'] = round((data['negative'] / data['total_chunks']) * 100, 1)
                data['neutral_pct'] = round((data['neutral'] / data['total_chunks']) * 100, 1)
                data['net_sentiment'] = data['positive'] - data['negative']
        
        return dict(file_aggregates)

def main():
    """Process sentiment analysis and save results"""
    analyzer = SentimentAnalyzer()
    
    print("🔄 Processing sentiment analysis...")
    sentiment_results, examples = analyzer.process_all_chunks()
    
    print("🔄 Aggregating by file...")
    file_aggregates = analyzer.aggregate_by_file(sentiment_results)
    
    # Save results
    output_dir = Path("backend/outputfile")
    output_dir.mkdir(exist_ok=True)
    
    output_data = {
        'file_sentiment_summary': file_aggregates,
        'sentiment_examples': examples,
        'processing_stats': {
            'total_chunks_processed': len(sentiment_results),
            'total_files': len(file_aggregates),
            'positive_examples': len(examples.get('positive', [])),
            'negative_examples': len(examples.get('negative', [])),
            'neutral_examples': len(examples.get('neutral', []))
        }
    }
    
    with open(output_dir / "sentiment_analysis.json", 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Sentiment analysis complete!")
    print(f"   📊 {len(sentiment_results)} chunks processed")
    print(f"   📁 {len(file_aggregates)} files analyzed")
    print(f"   💾 Results saved to backend/outputfile/sentiment_analysis.json")

if __name__ == "__main__":
    main()
