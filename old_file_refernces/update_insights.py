#!/usr/bin/env python3
import json
import os
import sys

def update_transcript_insights():
    """
    Update transcript_insights.json with specific fields from fixed_insights.json
    Only updates the fields for files that exist in fixed_insights.json
    """
    print("Starting update process...")
    
    # Load the fixed insights data
    try:
        with open('fixed_insights.json', 'r', encoding='utf-8') as f:
            fixed_insights = json.load(f)
        print(f"Successfully loaded fixed_insights.json")
    except Exception as e:
        print(f"Error loading fixed_insights.json: {str(e)}")
        return False
    
    # Load the original transcript insights data
    try:
        with open('transcript_insights.json', 'r', encoding='utf-8') as f:
            transcript_insights = json.load(f)
        print(f"Successfully loaded transcript_insights.json")
    except Exception as e:
        print(f"Error loading transcript_insights.json: {str(e)}")
        return False
    
    # Create a backup of the original file
    backup_file = 'transcript_insights_backup.json'
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_insights, f, indent=2)
        print(f"Created backup at {backup_file}")
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False
    
    # Fields to update
    fields_to_update = [
        "caregiver_turns",
        "plwd_turns",
        "caregiver_words",
        "plwd_words"
    ]
    
    # Track statistics
    files_updated = 0
    fields_updated = 0
    
    # Create a flat list of all files in fixed_insights.json
    fixed_files = []
    for patient_id, sessions in fixed_insights.items():
        for session_type, files in sessions.items():
            for file_name in files.keys():
                fixed_files.append({
                    'patient_id': patient_id,
                    'session_type': session_type,
                    'file_name': file_name,
                    'data': files[file_name]
                })
    
    print(f"Found {len(fixed_files)} files to process in fixed_insights.json")
    
    # Process each file in fixed_insights.json
    for fixed_file in fixed_files:
        file_name = fixed_file['file_name']
        print(f"\nProcessing {file_name}...")
        
        # Look for the file in transcript_insights.json
        # First check if it exists directly in the patient's session
        patient_id = fixed_file['patient_id']
        session_type = fixed_file['session_type']
        
        # Check if the patient exists in transcript_insights
        if patient_id in transcript_insights:
            # Check if the session exists for this patient
            if session_type in transcript_insights[patient_id]:
                # Check if the file exists in this session
                if file_name in transcript_insights[patient_id][session_type]:
                    # File found, update the fields
                    print(f"  Found {file_name} in transcript_insights.json")
                    
                    # Get the source data
                    source_data = fixed_file['data']['basic_statistics']
                    
                    # Get the target data
                    target_data = transcript_insights[patient_id][session_type][file_name]
                    
                    # Update each field if it exists in the source
                    for field in fields_to_update:
                        if field in source_data:
                            # Update in basic_statistics if it exists
                            if "basic_statistics" in target_data and field in target_data["basic_statistics"]:
                                target_data["basic_statistics"][field] = source_data[field]
                                print(f"    Updated basic_statistics.{field}: {source_data[field]}")
                                fields_updated += 1
                            
                            # Check if Caregiver-PLWD Interaction section exists
                            if "Caregiver-PLWD Interaction" not in target_data:
                                target_data["Caregiver-PLWD Interaction"] = {}
                            
                            # Update the field in Caregiver-PLWD Interaction
                            target_data["Caregiver-PLWD Interaction"][field] = source_data[field]
                            print(f"    Updated Caregiver-PLWD Interaction.{field}: {source_data[field]}")
                            fields_updated += 1
                    
                    files_updated += 1
                    continue
        
        # If we get here, the file wasn't found in the expected location
        # Try a case-insensitive search through all files
        print(f"  File not found in expected location, searching case-insensitive...")
        found = False
        
        for ti_patient_id, ti_sessions in transcript_insights.items():
            for ti_session_type, ti_files in ti_sessions.items():
                for ti_file_name in ti_files.keys():
                    # Case-insensitive comparison
                    if file_name.lower() == ti_file_name.lower():
                        print(f"  Found {file_name} as {ti_file_name} in transcript_insights.json")
                        
                        # Get the source data
                        source_data = fixed_file['data']['basic_statistics']
                        
                        # Get the target data
                        target_data = transcript_insights[ti_patient_id][ti_session_type][ti_file_name]
                        
                        # Update each field if it exists in the source
                        for field in fields_to_update:
                            if field in source_data:
                                # Update in basic_statistics if it exists
                                if "basic_statistics" in target_data and field in target_data["basic_statistics"]:
                                    target_data["basic_statistics"][field] = source_data[field]
                                    print(f"    Updated basic_statistics.{field}: {source_data[field]}")
                                    fields_updated += 1
                                
                                # Check if Caregiver-PLWD Interaction section exists
                                if "Caregiver-PLWD Interaction" not in target_data:
                                    target_data["Caregiver-PLWD Interaction"] = {}
                                
                                # Update the field in Caregiver-PLWD Interaction
                                target_data["Caregiver-PLWD Interaction"][field] = source_data[field]
                                print(f"    Updated Caregiver-PLWD Interaction.{field}: {source_data[field]}")
                                fields_updated += 1
                        
                        files_updated += 1
                        found = True
                        break
                
                if found:
                    break
            
            if found:
                break
        
        if not found:
            print(f"  WARNING: Could not find {file_name} in transcript_insights.json")
    
    # Save the updated transcript_insights.json
    try:
        with open('transcript_insights_updated.json', 'w', encoding='utf-8') as f:
            json.dump(transcript_insights, f, indent=2)
        print(f"\nSaved updated data to transcript_insights_updated.json")
        print(f"Updated {files_updated} files and {fields_updated} fields")
    except Exception as e:
        print(f"\nError saving updated data: {str(e)}")
        return False
    
    print("\nUpdate process completed successfully!")
    print("To use the updated file, rename transcript_insights_updated.json to transcript_insights.json")
    print("If anything went wrong, you can restore from transcript_insights_backup.json")
    return True

if __name__ == "__main__":
    update_transcript_insights()
