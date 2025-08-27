# Transcript Processing and Analysis Dashboard

A Python-based system for processing, analyzing, and visualizing transcript data. This project includes tools for organizing transcripts, creating embeddings for semantic search, and analyzing various aspects of communication patterns.

## Features

- **Transcript Organization**: Automatically sort and organize transcript files into a structured hierarchy
- **Incremental Processing**: Process new transcripts and add them to existing embeddings without reprocessing everything
- **Semantic Search**: Create and search through embeddings of transcript content
- **Analysis Dashboard**: Visualize and analyze various aspects of communication including:
  - Caregiver-PLWD Interaction Analysis
  - Sentiment Analysis
  - Lexical Diversity Analysis
  - Questions & Answers Analysis
  - Nonverbal Communication Analysis
  - Memory Analysis
  - Disfluency Analysis
  - Turn-Taking and Engagement Analysis
  - Word Repeats Analysis
  - Topic Explorer

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yugant99/transcript_cleaning_2.0.git
cd transcript_cleaning_2.0
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create required directories:
```bash
mkdir data processed_data unsorted_files
```

## Usage

### Sorting Transcripts

1. Place unsorted transcript files in the `unsorted_files` directory
2. Run the sorting script:
```bash
python sort_transcripts.py
```

The script will:
- Organize files into a structured hierarchy
- Skip duplicates
- Generate a sorting report

### Processing Transcripts

1. Ensure transcripts are organized in the `data` directory
2. Run the incremental processor:
```bash
python incremental_processor.py
```

The processor will:
- Process only new files
- Create embeddings for semantic search
- Update the master data store
- Generate a processing summary

## Project Structure

```
transcript_dashboard_new/
├── data/                    # Organized transcript files (not in repo)
├── processed_data/          # Generated embeddings and metadata (not in repo)
├── unsorted_files/         # Directory for files to be sorted (not in repo)
├── docs/                   # Project documentation
├── incremental_processor.py # Script for processing transcripts
├── sort_transcripts.py     # Script for organizing files
└── requirements.txt        # Python dependencies
```

## Dependencies

- Python 3.8+
- sentence-transformers
- faiss-cpu
- python-docx
- numpy
- See requirements.txt for complete list

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
