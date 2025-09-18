import re
import string
from collections import defaultdict

# Try to import NLTK, fallback to basic string methods if not available
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    
    # Download required NLTK data if not present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        
except ImportError:
    NLTK_AVAILABLE = False

class WordRepeatDetector:
    """Detects immediate word repetitions in text using NLP techniques"""
    
    def __init__(self):
        self.disfluency_markers = {
            'um', 'uh', 'er', 'ah', 'you know', 'i mean', 
            'sort of', 'kind of', 'well', 'so', 'basically'
        }
        
        # Get English stopwords if NLTK is available
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        else:
            self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    def clean_text(self, text):
        """Clean text by removing non-verbal cues and special characters"""
        if not text:
            return ""
        
        # Remove content in brackets/parentheses (non-verbal cues)
        text = re.sub(r'\[.*?\]', ' ', text)
        text = re.sub(r'\(.*?\)', ' ', text)
        
        # Remove multiple spaces and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def tokenize_words(self, text):
        """Tokenize text into words using NLTK if available, otherwise basic split"""
        if not text:
            return []
        
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text.lower())
                # Filter out punctuation and empty strings
                words = [token for token in tokens if token not in string.punctuation and token.strip()]
                return words
            except:
                # Fallback to basic tokenization
                pass
        
        # Basic tokenization fallback
        words = text.lower().split()
        words = [word.strip(string.punctuation) for word in words if word.strip()]
        return [word for word in words if word and word not in string.punctuation]
    
    def detect_immediate_repeats(self, words):
        """Detect immediate word repetitions (back-to-back identical words)"""
        if len(words) < 2:
            return []
        
        repeats = []
        i = 0
        
        while i < len(words) - 1:
            current_word = words[i]
            
            # Skip only if it's a disfluency marker (allow all other words including single letters)
            if current_word in self.disfluency_markers:
                i += 1
                continue
            
            # Check for immediate repetition
            if current_word == words[i + 1]:
                # Count consecutive repetitions
                repeat_count = 1
                j = i + 1
                while j < len(words) and words[j] == current_word:
                    repeat_count += 1
                    j += 1
                
                # Create context (5 words before and after)
                start_idx = max(0, i - 5)
                end_idx = min(len(words), j + 5)
                context_words = words[start_idx:end_idx]
                
                # Highlight the repeated word in context
                highlighted_context = []
                for idx, word in enumerate(context_words):
                    actual_idx = start_idx + idx
                    if i <= actual_idx < j:  # This is a repeated word
                        highlighted_context.append(f"**{word}**")
                    else:
                        highlighted_context.append(word)
                
                repeats.append({
                    'word': current_word,
                    'count': repeat_count,
                    'position': i,
                    'context': ' '.join(highlighted_context)
                })
                
                i = j  # Skip past all repetitions
            else:
                i += 1
        
        return repeats
    
    def analyze_text(self, text):
        """Main analysis function that returns word repeat statistics"""
        if not text or not text.strip():
            return {
                'total_repeats': 0,
                'unique_repeated_words': 0,
                'examples': [],
                'repeat_rate': 0.0
            }
        
        # Clean and tokenize the text
        cleaned_text = self.clean_text(text)
        words = self.tokenize_words(cleaned_text)
        
        if len(words) < 2:
            return {
                'total_repeats': 0,
                'unique_repeated_words': 0,
                'examples': [],
                'repeat_rate': 0.0
            }
        
        # Detect repeats
        repeats = self.detect_immediate_repeats(words)
        
        # Calculate statistics
        total_repeats = sum(repeat['count'] - 1 for repeat in repeats)  # -1 because we count extra repetitions
        unique_repeated_words = len(repeats)
        repeat_rate = (total_repeats / len(words)) * 100 if words else 0.0
        
        return {
            'total_repeats': total_repeats,
            'unique_repeated_words': unique_repeated_words,
            'examples': repeats,
            'repeat_rate': round(repeat_rate, 2)
        }

# Convenience functions for easy usage
def detect_word_repeats(text):
    """Convenience function to detect word repeats in a text"""
    detector = WordRepeatDetector()
    return detector.analyze_text(text)

def analyze_turn_for_word_repeats(text):
    """Analyze a single turn for word repeats - returns count and examples"""
    analysis = detect_word_repeats(text)
    return {
        'count': analysis['total_repeats'],
        'examples': analysis['examples']
    }

# Test function
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "I think think we should go",
        "The weather is is really nice today",
        "We need to to to finish this project",
        "Hello how are you doing today",
        "Um, I I really like like this approach"
    ]
    
    detector = WordRepeatDetector()
    
    for text in test_texts:
        print(f"\nText: '{text}'")
        result = detector.analyze_text(text)
        print(f"Repeats: {result['total_repeats']}")
        print(f"Examples: {[ex['word'] for ex in result['examples']]}") 