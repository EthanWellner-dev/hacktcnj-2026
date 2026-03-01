"""Content filter for harmful, unkind, and neurodivergent-hurtful words."""

# Common unkind and hurtful words
UNKIND_WORDS = [
    'stupid', 'dumb', 'idiot', 'moron', 'imbecile', 'loser', 'trash', 'garbage',
    'worthless', 'useless', 'pathetic', 'lame', 'uncool', 'disgusting', 'gross',
    'ugly', 'fat', 'skinny', 'weak', 'coward', 'fake', 'poser', 'jerk', 'asshole',
    'bastard', 'bitch', 'slut', 'whore', 'creep', 'pervert', 'weirdo', 'freak'
]

# Words that are hurtful to neurodivergent community
NEURODIVERGENT_HURTFUL_WORDS = [
    'crazy', 'insane', 'psycho', 'schizo', 'retard', 'retarded', 'tard',
    'autistic', 'aspie',  # often used as insults
    'adhd', 'add',  # used derogatorily
    'nuts', 'nutty', 'unhinged', 'broken', 'damaged',  # relating to mental state
    'mental', 'mentally ill',  # used as insult
    'high functioning', 'not really autistic', 'look autistic',
    'too smart to be autistic', 'everyone a little autistic',
    'functioning labels', 'aspergers', 'asperger',
    'cure', 'recover from autism', 'vaccine caused',
    'special interest',  # when used mockingly
    'stimming', 'flapping'  # when used mockingly
]

# Combine all filters
ALL_FILTER_WORDS = set(UNKIND_WORDS + NEURODIVERGENT_HURTFUL_WORDS)

def contains_harmful_content(text):
    """
    Check if text contains any harmful words.
    Returns (bool, list) - (contains_harmful, list_of_found_words)
    """
    if not text:
        return False, []
    
    text_lower = text.lower()
    found_words = []
    
    for word in ALL_FILTER_WORDS:
        # Check for whole word matches to avoid false positives
        # (e.g., "smart" shouldn't catch "smartass")
        if f' {word} ' in f' {text_lower} ' or text_lower.startswith(word + ' ') or text_lower.endswith(f' {word}'):
            found_words.append(word)
        elif word in text_lower:
            # Additional check for word boundaries
            import re
            if re.search(rf'\b{re.escape(word)}\b', text_lower):
                found_words.append(word)
    
    return len(found_words) > 0, list(set(found_words))


def filter_message(text):
    """
    Filter a message and return a cleaned version with flagged words replaced.
    Returns cleaned text with harmful words replaced with ***.
    """
    if not text:
        return text
    
    text_lower = text.lower()
    filtered_text = text
    
    for word in ALL_FILTER_WORDS:
        import re
        pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
        filtered_text = pattern.sub('***', filtered_text)
    
    return filtered_text
