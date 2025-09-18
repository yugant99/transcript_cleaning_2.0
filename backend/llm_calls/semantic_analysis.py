#!/usr/bin/env python3
import json
import os
import pickle
import numpy as np
import faiss
from datetime import datetime
from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# No need for API keys anymore!

class SemanticAnalyzer:
    def __init__(self):
        # Initialize medical/psychology lexicons
        self.init_lexicons()
        
        # Load existing data
        self.load_processed_data()
        self.load_metrics_data()
    
    def init_lexicons(self):
        """Initialize comprehensive medical/psychology lexicons"""
        
        # Physical Pain Terms
        self.physical_pain_terms = {
            # Direct pain words
            "pain", "painful", "hurts", "hurt", "hurting", "ache", "aching", "aches",
            "sore", "soreness", "tender", "tenderness", "stiff", "stiffness", 
            "cramping", "cramps", "throbbing", "pounding", "stabbing", "sharp",
            "burning", "tingling", "numb", "numbness", "swollen", "swelling",
            
            # Body parts + discomfort
            "back pain", "neck pain", "headache", "migraine", "joint pain",
            "knee pain", "hip pain", "shoulder pain", "chest pain", "stomach ache",
            
            # Intensity descriptors
            "agony", "excruciating", "severe", "intense", "unbearable", "terrible",
            "awful", "killing me", "torture", "misery", "suffering",
            
            # Physical discomfort
            "uncomfortable", "discomfort", "bothers", "bothering", "irritating",
            "annoying", "unpleasant", "difficulty", "trouble", "struggle",
            "can't move", "can't sit", "can't stand", "can't walk",
            
            # Fatigue and weakness
            "tired", "exhausted", "fatigued", "weak", "weakness", "drained",
            "worn out", "beat", "wiped out", "no energy", "can't do",
            
            # VR/Technology specific
            "dizzy", "dizziness", "nauseous", "nausea", "motion sick",
            "headache from", "eye strain", "blurry", "too bright", "overwhelming"
        }
        
        # Emotional/Psychological Pain Terms
        self.emotional_pain_terms = {
            # Direct emotional pain
            "upset", "frustrated", "frustration", "angry", "mad", "irritated",
            "annoyed", "worried", "anxious", "anxiety", "nervous", "scared",
            "afraid", "fear", "fearful", "panicked", "stressed", "stress",
            
            # Sadness and depression
            "sad", "sadness", "depressed", "depression", "down", "low",
            "blue", "crying", "tears", "weeping", "sobbing", "heartbroken",
            "hopeless", "helpless", "worthless", "useless",
            
            # Confusion and cognitive distress
            "confused", "confusion", "lost", "don't understand", "can't think",
            "forgetful", "memory problems", "can't remember", "blank",
            "overwhelmed", "too much", "can't handle", "give up",
            
            # Social/emotional isolation
            "lonely", "alone", "isolated", "abandoned", "rejected", "ignored",
            "embarrassed", "ashamed", "humiliated", "stupid", "foolish",
            
            # Behavioral indicators
            "can't cope", "falling apart", "breaking down", "losing it",
            "had enough", "fed up", "sick of", "hate this", "want to quit"
        }
        
        # Comfort/Wellbeing Terms
        self.comfort_terms = {
            # Physical comfort
            "comfortable", "comfort", "feels good", "feeling good", "better",
            "improved", "relief", "relieved", "relaxed", "relaxing", "calm",
            "peaceful", "soothing", "gentle", "soft", "smooth", "easy",
            "pleasant", "nice", "wonderful", "great", "excellent", "perfect",
            
            # Physical wellbeing
            "strong", "stronger", "energetic", "refreshed", "rested",
            "no pain", "pain free", "painless", "healing", "recovered",
            "mobile", "flexible", "steady", "balanced", "stable",
            
            # Emotional wellbeing
            "happy", "happiness", "joy", "joyful", "cheerful", "pleased",
            "content", "satisfied", "proud", "accomplished", "successful",
            "confident", "secure", "safe", "protected", "supported",
            
            # Engagement and enjoyment
            "fun", "enjoyable", "enjoying", "love", "like", "appreciate",
            "amazing", "fantastic", "awesome", "brilliant", "fascinating",
            "interesting", "engaging", "exciting", "thrilling", "delightful",
            
            # Cognitive comfort
            "clear", "focused", "sharp", "alert", "aware", "understand",
            "makes sense", "easy to use", "simple", "straightforward",
            "manageable", "doable", "achievable", "possible",
            
            # VR/Technology specific comfort
            "immersive", "realistic", "smooth", "responsive", "intuitive",
            "user friendly", "helpful", "beneficial", "therapeutic",
            "calming", "soothing", "distracting", "engaging"
        }
        
        # Compile all terms for efficient searching
        self.all_pain_terms = self.physical_pain_terms | self.emotional_pain_terms
        self.all_comfort_terms = self.comfort_terms
        
        print(f"✅ Loaded {len(self.all_pain_terms)} pain terms and {len(self.all_comfort_terms)} comfort terms")
    
    def load_processed_data(self):
        """Load embeddings and chunk data"""
        try:
            with open('../../processed_data/master_transcripts.pkl', 'rb') as f:
                self.transcript_data = pickle.load(f)
            
            self.embeddings = self.transcript_data['embeddings']
            self.chunk_metadata = self.transcript_data['chunk_metadata']
            
            # Load FAISS index
            self.index = faiss.read_index('../../processed_data/faiss_index.bin')
            print(f"✅ Loaded {len(self.chunk_metadata)} chunks with embeddings")
            
        except Exception as e:
            print(f"❌ Error loading processed data: {e}")
            raise
    
    def load_metrics_data(self):
        """Load existing metrics to match format"""
        try:
            with open('../outputfile/metrics_output.json', 'r') as f:
                self.metrics_data = json.load(f)
            print(f"✅ Loaded {len(self.metrics_data)} metric records")
        except Exception as e:
            print(f"❌ Error loading metrics data: {e}")
            raise
    
    def lexicon_based_search(self, text, term_set):
        """Search for lexicon terms in text with context scoring"""
        text_lower = text.lower()
        
        # Clean text for better matching
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        
        matches = []
        total_score = 0
        
        for term in term_set:
            # Exact phrase matching
            if term in text_lower:
                # Context scoring - give higher weight to complete phrases
                phrase_count = text_lower.count(term)
                word_count = len(term.split())
                
                # Multi-word phrases get higher scores
                score = phrase_count * (word_count ** 1.5)
                total_score += score
                
                matches.append({
                    'term': term,
                    'count': phrase_count,
                    'score': score
                })
        
        return {
            'matches': matches,
            'total_score': total_score,
            'match_count': len(matches)
        }
    
    def analyze_chunk_sentiment(self, chunk_text):
        """Analyze a chunk for pain/comfort using lexicons"""
        pain_analysis = self.lexicon_based_search(chunk_text, self.all_pain_terms)
        comfort_analysis = self.lexicon_based_search(chunk_text, self.all_comfort_terms)
        
        return {
            'pain_score': pain_analysis['total_score'],
            'comfort_score': comfort_analysis['total_score'],
            'pain_matches': pain_analysis['matches'],
            'comfort_matches': comfort_analysis['matches'],
            'pain_count': pain_analysis['match_count'],
            'comfort_count': comfort_analysis['match_count']
        }
    
    def extract_topics_clustering(self, chunks, n_topics=5):
        """Extract topics using TF-IDF + K-means clustering"""
        if not chunks or len(chunks) < 3:
            return []
        
        # Combine all chunk texts
        texts = [chunk.get('text', '') for chunk in chunks if chunk.get('text', '').strip()]
        
        if not texts:
            return []
        
        try:
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                min_df=2,  # Ignore terms that appear in less than 2 documents
                max_df=0.8  # Ignore terms that appear in more than 80% of documents
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Perform clustering
            n_clusters = min(n_topics, len(texts), tfidf_matrix.shape[1])
            if n_clusters < 2:
                return []
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Extract top terms for each cluster
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(n_clusters):
                # Get cluster center
                cluster_center = kmeans.cluster_centers_[i]
                
                # Get top terms for this cluster
                top_indices = cluster_center.argsort()[-3:][::-1]  # Top 3 terms
                top_terms = [feature_names[idx] for idx in top_indices]
                
                # Create topic label
                topic_label = ' '.join(top_terms)
                if topic_label.strip():
                    topics.append(topic_label)
            
            return topics[:5]  # Return top 5 topics
            
        except Exception as e:
            print(f"❌ Error in topic extraction: {e}")
            return []
    
    def analyze_file_pain_comfort(self, chunks):
        """Analyze file chunks for pain and comfort using lexicons"""
        if not chunks:
            return {"pain_mentions": 0, "comfort_mentions": 0, "pain_details": [], "comfort_details": []}
        
        total_pain_score = 0
        total_comfort_score = 0
        pain_details = []
        comfort_details = []
        
        for chunk in chunks:
            chunk_text = chunk.get('text', '')
            analysis = self.analyze_chunk_sentiment(chunk_text)
            
            total_pain_score += analysis['pain_score']
            total_comfort_score += analysis['comfort_score']
            
            # Collect detailed matches for validation
            if analysis['pain_matches']:
                pain_details.extend([
                    {
                        'term': match['term'],
                        'count': match['count'],
                        'context': chunk_text[:100] + '...' if len(chunk_text) > 100 else chunk_text
                    }
                    for match in analysis['pain_matches']
                ])
            
            if analysis['comfort_matches']:
                comfort_details.extend([
                    {
                        'term': match['term'],
                        'count': match['count'],
                        'context': chunk_text[:100] + '...' if len(chunk_text) > 100 else chunk_text
                    }
                    for match in analysis['comfort_matches']
                ])
        
        # Convert scores to mention counts (normalize by score thresholds)
        pain_mentions = min(int(total_pain_score / 2), len(pain_details))  # Normalize score
        comfort_mentions = min(int(total_comfort_score / 2), len(comfort_details))
        
        return {
            "pain_mentions": pain_mentions,
            "comfort_mentions": comfort_mentions,
            "pain_details": pain_details[:10],  # Limit for output size
            "comfort_details": comfort_details[:10]
        }
    
    # Removed - using clustering instead!
    
    def process_all_files(self):
        """Process all files for semantic analysis"""
        results = []
        
        # Group chunks by file
        file_chunks = {}
        for chunk_meta in self.chunk_metadata:
            file_info = chunk_meta.get('file_metadata', {})
            filename = file_info.get('filename', 'unknown')
            
            if filename not in file_chunks:
                file_chunks[filename] = {
                    'chunks': [],
                    'file_metadata': file_info
                }
            
            file_chunks[filename]['chunks'].append({
                'text': chunk_meta.get('chunk_text', ''),
                'chunk_index': chunk_meta.get('chunk_index', 0)
            })
        
        print(f"🔄 Processing {len(file_chunks)} files for semantic analysis...")
        
        for filename, file_data in file_chunks.items():
            print(f"📄 Processing: {filename}")
            
            # Find matching metrics record
            metrics_record = None
            for record in self.metrics_data:
                if record.get('filename') == filename:
                    metrics_record = record
                    break
            
            if not metrics_record:
                print(f"⚠️  No metrics found for {filename}, skipping...")
                continue
            
            # Analyze pain/comfort mentions using lexicons
            pain_comfort_analysis = self.analyze_file_pain_comfort(file_data['chunks'])
            
            # Extract topics using clustering
            topics = self.extract_topics_clustering(file_data['chunks'])
            
            # Create result record matching metrics format
            result = {
                "patient_id": metrics_record.get("patient_id"),
                "week_label": metrics_record.get("week_label"),
                "session_type": metrics_record.get("session_type"),
                "condition": metrics_record.get("condition"),
                "filename": filename,
                "pain_mentions": pain_comfort_analysis["pain_mentions"],
                "comfort_mentions": pain_comfort_analysis["comfort_mentions"],
                "pain_details": pain_comfort_analysis["pain_details"],
                "comfort_details": pain_comfort_analysis["comfort_details"],
                "topics_discussed": topics,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
        
        return results
    
    def save_results(self, results):
        """Save semantic analysis results"""
        output_dir = "../outputfile"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "semantic_analysis.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Saved {len(results)} semantic analysis records to {output_file}")

def main():
    """Main execution"""
    print("🔄 Starting semantic analysis...")
    
    analyzer = SemanticAnalyzer()
    results = analyzer.process_all_files()
    
    print(f"📊 Analyzed {len(results)} files")
    analyzer.save_results(results)
    print("✅ Semantic analysis complete!")

if __name__ == "__main__":
    main()
