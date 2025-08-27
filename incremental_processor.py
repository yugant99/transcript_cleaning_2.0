#!/usr/bin/env python3
"""
Incremental DOCX Processing Pipeline
Adds new files to existing embeddings without reprocessing everything
"""

import os
import re
import pickle
import json
import numpy as np
import faiss
from pathlib import Path
from docx import Document
from datetime import datetime
from sentence_transformers import SentenceTransformer

class IncrementalProcessor:
    def __init__(self, processed_data_dir="processed_data"):
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(exist_ok=True)
        
        self.master_file = self.processed_data_dir / "master_transcripts.pkl"
        self.faiss_file = self.processed_data_dir / "faiss_index.bin"
        self.processed_files_log = self.processed_data_dir / "processed_files.json"
        
        # Load existing data if available
        self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing processed data or initialize empty structures."""
        if self.master_file.exists():
            print("Loading existing processed data...")
            with open(self.master_file, 'rb') as f:
                self.master_data = pickle.load(f)
            
            # Load FAISS index
            if self.faiss_file.exists():
                self.faiss_index = faiss.read_index(str(self.faiss_file))
            else:
                # Rebuild FAISS index from embeddings
                embeddings = self.master_data['embeddings']
                dimension = embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)
                faiss.normalize_L2(embeddings)
                self.faiss_index.add(embeddings.astype(np.float32))
            
            # Load processed files log
            if self.processed_files_log.exists():
                with open(self.processed_files_log, 'r') as f:
                    self.processed_files = set(json.load(f))
            else:
                # Extract from existing data
                self.processed_files = set()
                for chunk_meta in self.master_data.get('chunk_metadata', []):
                    self.processed_files.add(chunk_meta['file_metadata']['file_path'])
            
            print(f"Loaded {len(self.master_data.get('chunk_metadata', []))} existing chunks from {len(self.processed_files)} files")
        else:
            print("No existing data found. Starting fresh...")
            self.master_data = {
                'embeddings': np.array([]).reshape(0, 384),  # Empty array with correct shape
                'chunk_metadata': [],
                'file_data': [],
                'processing_timestamp': datetime.now().isoformat(),
                'embedding_model': 'all-MiniLM-L6-v2',
                'embedding_dimension': 384
            }
            self.faiss_index = faiss.IndexFlatIP(384)
            self.processed_files = set()
    
    def extract_docx_content(self, file_path):
        """Extract clean text content from DOCX file."""
        try:
            doc = Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    # Clean text
                    text = re.sub(r'\s+', ' ', text).strip()
                    text = re.sub(r'^([a-zA-Z0-9_]+)\s*:\s*', r'\1: ', text)
                    content.append(text)
            
            return content
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def parse_file_metadata(self, file_path):
        """Extract metadata from file path and name."""
        path_obj = Path(file_path)
        filename = path_obj.name
        
        # Extract participant ID
        participant_match = re.search(r'(?i)vr(\d{3})', filename)
        participant_id = f"vr{participant_match.group(1)}" if participant_match else "unknown"
        
        # Extract session type from parent directory
        session_type = path_obj.parent.name
        
        # Extract session number if available
        session_number = None
        if session_type == "EP":
            ep_match = re.search(r'(?i)ep(\d)', filename)
            session_number = int(ep_match.group(1)) if ep_match else None
        elif session_type == "ER":
            er_match = re.search(r'(?i)er(\d)', filename)
            session_number = int(er_match.group(1)) if er_match else None
        
        return {
            'participant_id': participant_id,
            'session_type': session_type,
            'session_number': session_number,
            'filename': filename,
            'file_path': str(file_path)
        }
    
    def find_new_files(self, data_dir):
        """Find files that haven't been processed yet."""
        all_files = []
        new_files = []
        
        for participant_dir in Path(data_dir).iterdir():
            if not participant_dir.is_dir():
                continue
                
            for session_dir in participant_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                    
                for file_path in session_dir.glob("*.docx"):
                    all_files.append(file_path)
                    if str(file_path) not in self.processed_files:
                        new_files.append(file_path)
        
        return all_files, new_files
    
    def process_new_files(self, new_files):
        """Process only new files and add to existing data."""
        if not new_files:
            print("No new files to process!")
            return
        
        print(f"Processing {len(new_files)} new files...")
        
        # Load model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        new_chunks = []
        new_chunk_metadata = []
        new_file_data = []
        
        for file_path in new_files:
            print(f"Processing: {file_path.name}")
            
            # Extract content and metadata
            text_content = self.extract_docx_content(file_path)
            metadata = self.parse_file_metadata(file_path)
            
            if text_content:
                # Store file data
                file_data = {
                    'metadata': metadata,
                    'text_chunks': text_content,
                    'chunk_count': len(text_content)
                }
                new_file_data.append(file_data)
                
                # Prepare chunks for embedding
                for i, chunk in enumerate(text_content):
                    new_chunks.append(chunk)
                    
                    chunk_meta = {
                        'file_metadata': metadata,
                        'chunk_index': i,
                        'chunk_text': chunk
                    }
                    new_chunk_metadata.append(chunk_meta)
                
                # Mark as processed
                self.processed_files.add(str(file_path))
        
        if not new_chunks:
            print("No valid content found in new files!")
            return
        
        print(f"Creating embeddings for {len(new_chunks)} new chunks...")
        
        # Create embeddings for new chunks
        new_embeddings = model.encode(new_chunks, show_progress_bar=True)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(new_embeddings)
        
        # Add to existing data
        if len(self.master_data['embeddings']) == 0:
            # First time - initialize arrays
            self.master_data['embeddings'] = new_embeddings
        else:
            # Append to existing embeddings
            self.master_data['embeddings'] = np.vstack([
                self.master_data['embeddings'], 
                new_embeddings
            ])
        
        # Add to FAISS index
        self.faiss_index.add(new_embeddings.astype(np.float32))
        
        # Update metadata
        self.master_data['chunk_metadata'].extend(new_chunk_metadata)
        self.master_data['file_data'].extend(new_file_data)
        self.master_data['total_files'] = len(self.master_data['file_data'])
        self.master_data['total_chunks'] = len(self.master_data['chunk_metadata'])
        self.master_data['last_update'] = datetime.now().isoformat()
        
        print(f"Added {len(new_chunks)} chunks from {len(new_files)} files")
    
    def save_data(self):
        """Save updated data to files."""
        print("Saving updated data...")
        
        # Save master data
        with open(self.master_file, 'wb') as f:
            pickle.dump(self.master_data, f)
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, str(self.faiss_file))
        
        # Save processed files log
        with open(self.processed_files_log, 'w') as f:
            json.dump(list(self.processed_files), f, indent=2)
        
        # Save summary
        summary = {
            'total_files': self.master_data.get('total_files', 0),
            'total_chunks': self.master_data.get('total_chunks', 0),
            'participants': list(set(fd['metadata']['participant_id'] 
                                   for fd in self.master_data['file_data'])),
            'session_types': list(set(fd['metadata']['session_type'] 
                                    for fd in self.master_data['file_data'])),
            'last_update': self.master_data.get('last_update', 'unknown')
        }
        
        summary_file = self.processed_data_dir / "processing_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Data saved. Total: {summary['total_files']} files, {summary['total_chunks']} chunks")
    
    def process_data_directory(self, data_dir="data"):
        """Main method to process data directory incrementally."""
        print("🔄 Starting Incremental Processing")
        print("=" * 50)
        
        if not Path(data_dir).exists():
            print(f"Error: Data directory '{data_dir}' not found!")
            return
        
        start_time = datetime.now()
        
        # Find new files
        all_files, new_files = self.find_new_files(data_dir)
        
        print(f"Found {len(all_files)} total files")
        print(f"Already processed: {len(self.processed_files)} files")
        print(f"New files to process: {len(new_files)} files")
        
        if new_files:
            # Process new files
            self.process_new_files(new_files)
            
            # Save updated data
            self.save_data()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 50)
            print("✅ INCREMENTAL PROCESSING COMPLETE!")
            print("=" * 50)
            print(f"New files processed: {len(new_files)}")
            print(f"Total files in system: {self.master_data.get('total_files', 0)}")
            print(f"Total chunks: {self.master_data.get('total_chunks', 0)}")
            print(f"Processing time: {duration}")
        else:
            print("\n✅ No new files to process. System is up to date!")

def main():
    """Main function."""
    processor = IncrementalProcessor()
    processor.process_data_directory("data")

if __name__ == "__main__":
    main()