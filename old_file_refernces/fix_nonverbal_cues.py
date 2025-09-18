import json
import re
from collections import defaultdict

def normalize_nonverbal_cue(cue):
    """Normalize a non-verbal cue to a standard format."""
    if not cue or not isinstance(cue, str):
        return None
    
    # Convert to lowercase for processing
    cue_lower = cue.lower().strip()
    
    # Remove brackets for standardization
    cue_clean = re.sub(r'^\[|\]$', '', cue_lower)
    
    # Normalize common variations
    normalizations = {
        # Inaudible variations
        r'^inaudible.*': 'inaudible',
        
        # Pause variations  
        r'^(long\s+)?pause.*': 'pause',
        
        # Laughter variations
        r'^(laugh|laughter|laughing|laughs|chuckle|chuckles|chuckling|giggle|giggles|giggling).*': 'laughter',
        
        # Coughing variations
        r'^(cough|coughs|coughing).*': 'coughing',
        
        # Sighing variations
        r'^(sigh|sighs|sighing).*': 'sighing',
        
        # Nodding variations
        r'^(nod|nods|nodding).*': 'nodding',
        
        # Head shaking variations
        r'^(shake|shakes|shaking)\s+(head|heads).*': 'shaking_head',
        
        # Humming variations
        r'^(hum|hums|humming).*': 'humming',
        
        # Singing variations
        r'^(sing|sings|singing).*': 'singing',
        
        # Mumbling variations
        r'^(mumble|mumbles|mumbling).*': 'mumbling',
        
        # Yawning variations
        r'^(yawn|yawns|yawning).*': 'yawning',
        
        # Gesturing variations
        r'^(gesture|gestures|gesturing).*': 'gesturing',
        
        # Pointing variations
        r'^(point|points|pointing).*': 'pointing',
        
        # Clapping variations
        r'^(clap|claps|clapping).*': 'clapping',
        
        # Smiling variations (but not camera-related)
        r'^(smile|smiles|smiling)(?!.*camera).*': 'smiling',
        
        # Dancing variations
        r'^(dance|dances|dancing).*': 'dancing',
        
        # Various dash representations
        r'^(-{1,3}|–{1,3}|—{1,3})$': 'interruption',
        
        # Ellipsis
        r'^(\.{3,}|…+)$': 'trailing_off',
    }
    
    # Apply normalizations
    for pattern, replacement in normalizations.items():
        if re.match(pattern, cue_clean):
            return replacement
    
    # Return None for cues that should be excluded
    exclusion_patterns = [
        r'speaking.*\{.*\}',  # Language-specific speaking
        r'speaking.*(spanish|portuguese|russian|mandarin|english)',
        r'translat(e|ing)',
        r'researcher',
        r'research coordinator',
        r'coordinator',
        r'camera',
        r'video',
        r'screen',
        r'recording',
        r'vr\d+_[cp]',  # Participant IDs
        r'name$',  # Just "name"
        r'friend$',  # Just "friend" 
        r'day program leader',
        r'if participant',
        r'for example',
        r'reads (on|sign)',
        r'.{50,}',  # Very long descriptions (50+ chars)
    ]
    
    for pattern in exclusion_patterns:
        if re.search(pattern, cue_clean):
            return None
    
    # If no normalization applied, return the cleaned version
    return cue_clean

def fix_nonverbal_cues():
    """Fix and normalize non-verbal cues in the enhanced analysis data."""
    
    # Load the data
    try:
        with open('enhanced_transcript_analysis.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("enhanced_transcript_analysis.json not found")
        return
    
    stats = {
        'files_processed': 0,
        'turns_processed': 0,
        'cues_before': 0,
        'cues_after': 0,
        'cues_excluded': 0,
        'cues_normalized': 0
    }
    
    normalization_map = defaultdict(int)
    excluded_cues = defaultdict(int)
    
    # Process each file
    for filename, file_data in data.get("by_file", {}).items():
        stats['files_processed'] += 1
        
        # Fix stats-level nonverbal cues
        if "stats" in file_data and "nonverbal_cues" in file_data["stats"]:
            old_stats = file_data["stats"]["nonverbal_cues"].copy()
            new_stats = defaultdict(int)
            
            for cue_type, count in old_stats.items():
                stats['cues_before'] += count
                normalized = normalize_nonverbal_cue(cue_type)
                
                if normalized is None:
                    stats['cues_excluded'] += count
                    excluded_cues[cue_type] += count
                else:
                    new_stats[normalized] += count
                    stats['cues_after'] += count
                    if normalized != cue_type.lower().strip():
                        stats['cues_normalized'] += count
                        normalization_map[f"{cue_type} -> {normalized}"] += count
            
            # Update the stats
            file_data["stats"]["nonverbal_cues"] = dict(new_stats)
        
        # Fix turn-level nonverbal cues
        if "turns" in file_data:
            for turn in file_data["turns"]:
                stats['turns_processed'] += 1
                
                if "nonverbal_cues" in turn:
                    old_cues = turn["nonverbal_cues"].copy()
                    new_cues = []
                    
                    for cue in old_cues:
                        stats['cues_before'] += 1
                        normalized = normalize_nonverbal_cue(cue)
                        
                        if normalized is None:
                            stats['cues_excluded'] += 1
                            excluded_cues[cue] += 1
                        else:
                            new_cues.append(normalized)
                            stats['cues_after'] += 1
                            if normalized != cue.lower().strip():
                                stats['cues_normalized'] += 1
                                normalization_map[f"{cue} -> {normalized}"] += 1
                    
                    # Update the cues
                    turn["nonverbal_cues"] = new_cues
    
    # Save the fixed data
    with open('enhanced_transcript_analysis_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("=== NON-VERBAL CUE NORMALIZATION COMPLETE ===\n")
    print(f"Files processed: {stats['files_processed']}")
    print(f"Turns processed: {stats['turns_processed']}")
    print(f"Cues before: {stats['cues_before']}")
    print(f"Cues after: {stats['cues_after']}")
    print(f"Cues excluded: {stats['cues_excluded']}")
    print(f"Cues normalized: {stats['cues_normalized']}")
    
    print(f"\nReduction: {stats['cues_excluded']} cues ({stats['cues_excluded']/stats['cues_before']*100:.1f}%)")
    
    if excluded_cues:
        print(f"\n=== TOP EXCLUDED CUES ===")
        for cue, count in sorted(excluded_cues.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {cue}: {count}")
    
    if normalization_map:
        print(f"\n=== TOP NORMALIZATIONS ===")
        for mapping, count in sorted(normalization_map.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {mapping}: {count}")
    
    print(f"\nFixed data saved to: enhanced_transcript_analysis_fixed.json")

if __name__ == "__main__":
    fix_nonverbal_cues() 