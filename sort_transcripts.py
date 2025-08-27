#!/usr/bin/env python3
"""
Transcript File Sorting Script
Sorts transcript files from unsorted_files into organized hierarchical structure:
data/vr###/category/ where category is baseline, EP, ER, or final_interview
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

def parse_filename(filename):
    """
    Parse filename and determine target folder structure and sorting priority.
    Returns: (participant_id, folder_name, session_number, copy_number, original_filename)
    """
    # Remove file extension
    name = filename.replace('.docx', '')
    
    # Extract participant ID (case insensitive)
    participant_match = re.search(r'(?i)vr(\d{3})', name)
    participant_id = participant_match.group(1) if participant_match else None
    
    if not participant_id:
        return None, 'unsorted', 0, 0, filename
    
    # Initialize defaults
    folder_name = 'unsorted'  # Default for unmatched files
    session_number = 0
    
    # Check for baseline files
    if re.search(r'(?i)baseline', name):
        folder_name = 'baseline'
    
    # Check for final interview files
    elif re.search(r'(?i)final.?interview', name) or re.search(r'(?i)final.?interview.?transcribed', name):
        folder_name = 'final_interview'
    
    # Check for picture book (goes to final_interview folder)
    elif re.search(r'(?i)picture.?book', name):
        folder_name = 'final_interview'
    
    # Check for episodes (EP)
    elif re.search(r'(?i)ep(\d)', name):
        folder_name = 'EP'
        ep_match = re.search(r'(?i)ep(\d)', name)
        session_number = int(ep_match.group(1)) if ep_match else 0
    
    # Check for event-related files (ER and ER.i)
    elif re.search(r'(?i)er(\d)', name):
        folder_name = 'ER'
        er_match = re.search(r'(?i)er(\d)', name)
        session_number = int(er_match.group(1)) if er_match else 0
    
    # Handle duplicates (copy, copy 2, etc.)
    copy_number = 0
    copy_match = re.search(r'copy\s*(\d*)', name, re.IGNORECASE)
    if copy_match:
        copy_number = int(copy_match.group(1)) if copy_match.group(1) else 1
    elif re.search(r'\(\d+\)', name):
        paren_match = re.search(r'\((\d+)\)', name)
        copy_number = int(paren_match.group(1)) if paren_match else 0
    
    return participant_id, folder_name, session_number, copy_number, filename

def create_participant_folders(base_path, participant_id):
    """Create the hierarchical folder structure for a participant."""
    participant_folder = os.path.join(base_path, 'data', f'vr{participant_id}')
    categories = ['baseline', 'EP', 'ER', 'final_interview']
    
    created_folders = []
    for category in categories:
        category_path = os.path.join(participant_folder, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path, exist_ok=True)
            created_folders.append(f'vr{participant_id}/{category}')
    
    return created_folders

def file_exists_in_target(target_path, filename):
    """Check if file already exists in target location."""
    return os.path.exists(os.path.join(target_path, filename))

def sort_files(source_dir, target_base_dir):
    """
    Sort files from source directory to hierarchical participant folders.
    Returns: (sorted_count, skipped_count, unsorted_files, sorting_report)
    """
    if not os.path.exists(source_dir):
        return 0, 0, [], {}
    
    # Get all .docx files
    files = [f for f in os.listdir(source_dir) if f.endswith('.docx')]
    
    # Sort files by parsing results for organized processing
    file_data = []
    for filename in files:
        participant_id, folder, session_num, copy_num, orig_name = parse_filename(filename)
        if participant_id:  # Only process files with valid participant IDs
            file_data.append((participant_id, folder, session_num, copy_num, orig_name))
    
    # Sort by participant ID, then folder, then session number, then copy number
    file_data.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    
    # Track results
    sorted_count = 0
    skipped_count = 0
    unsorted_files = []
    sorting_report = defaultdict(lambda: defaultdict(list))
    created_participants = set()
    
    # Process files
    for participant_id, folder, session_num, copy_num, filename in file_data:
        source_path = os.path.join(source_dir, filename)
        
        if folder == 'unsorted':
            unsorted_files.append(filename)
            continue
        
        # Create participant folder structure if not exists
        if participant_id not in created_participants:
            created_folders = create_participant_folders(target_base_dir, participant_id)
            if created_folders:
                print(f"Created folder structure for VR{participant_id}")
            created_participants.add(participant_id)
        
        # Define target path
        target_folder = os.path.join(target_base_dir, 'data', f'vr{participant_id}', folder)
        target_path = os.path.join(target_folder, filename)
        
        # Check if file already exists (skip duplicates)
        if file_exists_in_target(target_folder, filename):
            print(f"  Skipping duplicate: {filename} (already exists in vr{participant_id}/{folder})")
            skipped_count += 1
            continue
        
        try:
            shutil.move(source_path, target_path)
            sorted_count += 1
            sorting_report[f'vr{participant_id}'][folder].append(filename)
            print(f"  Moved: {filename} → vr{participant_id}/{folder}/")
        except Exception as e:
            print(f"Error moving {filename}: {e}")
            unsorted_files.append(filename)
    
    # Handle files without valid participant IDs
    remaining_files = [f for f in os.listdir(source_dir) if f.endswith('.docx')]
    for filename in remaining_files:
        participant_id, folder, _, _, _ = parse_filename(filename)
        if not participant_id:
            unsorted_files.append(filename)
    
    return sorted_count, skipped_count, unsorted_files, dict(sorting_report)

def generate_report(sorted_count, skipped_count, unsorted_files, sorting_report, total_files):
    """Generate a detailed report of the sorting operation."""
    print("\n" + "="*60)
    print("TRANSCRIPT SORTING REPORT")
    print("="*60)
    
    print(f"\nTotal files processed: {total_files}")
    print(f"Successfully sorted: {sorted_count}")
    print(f"Skipped (duplicates): {skipped_count}")
    print(f"Left unsorted: {len(unsorted_files)}")
    
    if total_files > 0:
        print(f"Success rate: {(sorted_count/total_files)*100:.1f}%")
        print(f"Processing rate: {((sorted_count + skipped_count)/total_files)*100:.1f}%")
    
    print(f"\nFiles sorted by participant:")
    for participant, categories in sorting_report.items():
        total_participant_files = sum(len(files) for files in categories.values())
        print(f"  {participant}: {total_participant_files} files")
        for category, files in categories.items():
            print(f"    {category}: {len(files)} files")
            # Show first few files as examples
            for i, file in enumerate(files[:2]):
                print(f"      - {file}")
            if len(files) > 2:
                print(f"      ... and {len(files) - 2} more")
    
    if unsorted_files:
        print(f"\nUnsorted files ({len(unsorted_files)}):")
        for file in unsorted_files[:10]:  # Show first 10
            print(f"  - {file}")
        if len(unsorted_files) > 10:
            print(f"  ... and {len(unsorted_files) - 10} more")
    
    print("\n" + "="*60)

def main():
    """Main function to run the sorting process."""
    # Set up paths
    script_dir = Path(__file__).parent
    source_dir = script_dir / "unsorted_files"
    target_base_dir = script_dir
    
    print("Transcript File Sorting Script")
    print("="*40)
    print(f"Source directory: {source_dir}")
    print(f"Target structure: {target_base_dir}/data/vr###/category/")
    
    # Check if source directory exists
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist!")
        return
    
    # Get initial file count
    all_files = [f for f in os.listdir(source_dir) if f.endswith('.docx')]
    total_files = len(all_files)
    
    if total_files == 0:
        print("No .docx files found in the source directory.")
        return
    
    print(f"Found {total_files} .docx files to process...")
    
    # Sort files
    sorted_count, skipped_count, unsorted_files, sorting_report = sort_files(str(source_dir), str(target_base_dir))
    
    # Generate report
    generate_report(sorted_count, skipped_count, unsorted_files, sorting_report, total_files)
    
    # Save report to file
    report_file = target_base_dir / "sorting_report.txt"
    with open(report_file, 'w') as f:
        f.write("TRANSCRIPT SORTING REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Total files processed: {total_files}\n")
        f.write(f"Successfully sorted: {sorted_count}\n")
        f.write(f"Skipped (duplicates): {skipped_count}\n")
        f.write(f"Left unsorted: {len(unsorted_files)}\n")
        
        if total_files > 0:
            f.write(f"Success rate: {(sorted_count/total_files)*100:.1f}%\n")
            f.write(f"Processing rate: {((sorted_count + skipped_count)/total_files)*100:.1f}%\n")
        
        f.write(f"\nFiles sorted by participant:\n")
        for participant, categories in sorting_report.items():
            total_participant_files = sum(len(files) for files in categories.values())
            f.write(f"  {participant}: {total_participant_files} files\n")
            for category, files in categories.items():
                f.write(f"    {category}: {len(files)} files\n")
                for file in files:
                    f.write(f"      - {file}\n")
        
        if unsorted_files:
            f.write(f"\nUnsorted files ({len(unsorted_files)}):\n")
            for file in unsorted_files:
                f.write(f"  - {file}\n")
    
    print(f"\nDetailed report saved to: {report_file}")
    print("\nTo add new files in the future:")
    print("1. Place new .docx files in the 'unsorted_files' folder")
    print("2. Run: python3 sort_transcripts.py")
    print("3. The script will automatically skip duplicates and sort new files")

if __name__ == "__main__":
    main()
