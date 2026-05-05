import csv
import re
import os
import shutil
import glob
import nltk
from nltk.corpus import names
from collections import Counter

# Load NLTK Names (both male and female)
try:
    known_names = set(names.words('male.txt') + names.words('female.txt'))
except LookupError:
    # Fallback if download failed
    known_names = set()
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Load CSV Corrections
csv_corrections = {}
with open('Spelling Corrections.csv', mode='r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) # skip header
    for row in reader:
        if len(row) >= 2:
            error = row[0].strip()
            correct = row[1].strip()
            csv_corrections[error] = correct

# 2. SpellChecker Initialization
spell_en = SpellChecker(language='en')
spell_fr = SpellChecker(language='fr')

def is_modern_valid(w):
    w_lower = w.lower()
    return w_lower in spell_en or w_lower in spell_fr

def is_valid_historical(w):
    w_lower = w.lower()
    
    # Check directly
    if is_modern_valid(w_lower):
        return True
        
    # Check English possessives/apostrophes
    # Strip standard or typographic apostrophe and check strictly against English dictionary
    w_no_apos = w_lower.replace("'", "").replace("’", "").replace("‘", "")
    if w_no_apos != w_lower:
        if w_no_apos in spell_en:
            return True
    
    # Heuristics
    if w_lower.endswith('ck'):
        if is_modern_valid(w_lower[:-1]): # publick -> public
            return True
    if w_lower.endswith('our'):
        if is_modern_valid(w_lower[:-3] + 'or'): # honour -> honor
            return True
    if w_lower.endswith('re'):
        if is_modern_valid(w_lower[:-2] + 'er'): # theatre -> theater
            return True
            
    # Some hardcoded valid historical variants commonly found
    historical_allowlist = {'shew', 'shews', 'chuse', 'connexion', 'compleat', 'to-morrow', 'to-day', 'hath', 'doth', 'thou', 'thee', 'thy', 'thine', 'ye', 'oft'}
    if w_lower in historical_allowlist:
        return True
        
    return False

def is_ignorable(w, is_first_word_in_line=False):
    # Pure numbers
    if w.isdigit():
        return True
    
    # Ordinals (English and French)
    if re.match(r'^\d+(st|nd|rd|th|d|e|eme|ere|ème|er|re)$', w, re.IGNORECASE):
        return True
        
    # Roman Numerals (> 1 char to avoid filtering 'I', 'V', 'C' unnecessarily if they aren't words)
    if len(w) > 1 and re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', w, re.IGNORECASE):
        return True
        
    # Gazetteer: Check if the word is in the standard names database
    # (Checking capitalized version as NLTK names are Title Case)
    if w.capitalize() in known_names:
        return True
        
    # Capitalization Heuristic: If it starts with a capital letter but is NOT the first word 
    # of the line, it is highly likely a proper noun.
    if w and w[0].isupper() and not is_first_word_in_line:
        return True
        
    return False

def split_punctuation(text):
    # Matches prefix punctuation, the word itself, and suffix punctuation
    # We want to keep hyphens attached if they are at the end of the line/word, but let's separate them to check the word, then re-attach.
    match = re.match(r'^(\W*)(.*?)(\W*)$', text)
    if not match:
        return "", text, ""
    
    prefix = match.group(1)
    core = match.group(2)
    suffix = match.group(3)
    
    return prefix, core, suffix

def correct_word_text(original_text, word_id, unresolved_words_list, is_first_word_in_line, hyphen_transform=None):
    if not original_text.strip():
        return original_text, None
        
    # Check if pure numbers/punctuation
    if not any(c.isalpha() for c in original_text):
        return original_text, None

    # Step A: Direct CSV Match
    if original_text in csv_corrections:
        return csv_corrections[original_text], "CSV Dictionary Match"
        
    prefix, core, suffix = split_punctuation(original_text)
    
    if not core:
        return original_text, None
        
    if core in csv_corrections:
        return prefix + csv_corrections[core] + suffix, "CSV Dictionary Match"

    # Step B: Long s unconditional replacement
    core_s = core.replace('ſ', 's')

    # --- HYPHENATION LOOKAHEAD OVERRIDE ---
    if hyphen_transform == 'mark_valid_only':
        return original_text, "Hyphenated Part: Valid Merged Word"
    elif hyphen_transform == 'long_s_only':
        if core_s != core:
            return prefix + core_s + suffix, "Hyphenated Part: Long 's' (\u017f) Replacement"
        return original_text, "Hyphenated Part: Valid Merged Word"
    elif hyphen_transform == 'f2s':
        core_f2s = core_s.replace('f', 's').replace('F', 'S')
        if core_f2s != core:
            return prefix + core_f2s + suffix, "Hyphenated Part: Heuristic 'f' to 's' Replacement"
        return original_text, "Hyphenated Part: Valid Merged Word"
    # --------------------------------------
    
    # Step C: Validity check
    if is_valid_historical(core_s):
        if core_s != core:
            return prefix + core_s + suffix, "Long 's' (\u017f) Replacement"
        return original_text, None
        
    # Step D: Heuristic f -> s
    # Only change 'f' to 's' if the word has an 'f'
    if 'f' in core_s or 'F' in core_s:
        # replace f/F with s/S
        chars = []
        for c in core_s:
            if c == 'f': chars.append('s')
            elif c == 'F': chars.append('S')
            else: chars.append(c)
        core_f2s = "".join(chars)
        
        if is_valid_historical(core_f2s):
            return prefix + core_f2s + suffix, "Heuristic 'f' to 's' Replacement"
            
    # Fallback: if we couldn't make it valid, keep the Long 's' correction but otherwise original
    if not is_valid_historical(core_s):
        # Apply heuristic filtering to avoid logging dates, numbers, roman numerals, and proper nouns
        if not is_ignorable(core_s, is_first_word_in_line):
            unresolved_words_list.append((word_id, core_s))
            
    if core_s != core:
        return prefix + core_s + suffix, "Long 's' (\u017f) Replacement (Unresolved)"
        
    return original_text, None

def process_hocr(file_path):
    print(f"\n--- Processing {file_path} ---")
    backup_path = file_path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml') # using lxml as it's more robust for XML/XHTML
        
    # --- HYPHENATION LOOKAHEAD PRE-PASS ---
    all_words = soup.find_all("span", class_="ocrx_word")
    hyphenated_transformations = {}
    
    for i in range(len(all_words) - 1):
        w1 = all_words[i]
        w2 = all_words[i+1]
        
        t1 = w1.text.strip()
        t2 = w2.text.strip()
        
        if not t1 or not t2: continue
        
        # Check if t1 ends with hyphen or hyphen-like character
        if t1.endswith('-') or t1.endswith('—') or t1.endswith('‐'):
            prefix1, core1, suffix1 = split_punctuation(t1)
            prefix2, core2, suffix2 = split_punctuation(t2)
            
            if not core1 or not core2: continue
            
            comb = core1 + core2
            
            if comb in csv_corrections:
                hyphenated_transformations[w1.get('id')] = 'mark_valid_only'
                hyphenated_transformations[w2.get('id')] = 'mark_valid_only'
                continue
                
            comb_s = comb.replace('ſ', 's')
            if is_valid_historical(comb_s):
                hyphenated_transformations[w1.get('id')] = 'long_s_only'
                hyphenated_transformations[w2.get('id')] = 'long_s_only'
                continue
                
            if 'f' in comb_s or 'F' in comb_s:
                comb_f2s = comb_s.replace('f', 's').replace('F', 'S')
                if is_valid_historical(comb_f2s):
                    hyphenated_transformations[w1.get('id')] = 'f2s'
                    hyphenated_transformations[w2.get('id')] = 'f2s'
                    continue
    # --------------------------------------
        
    lines = soup.find_all(class_="ocr_line")
    changed_count = 0
    unresolved_words = []
    corrections_made = []
    rule_counts = Counter()
    
    for line in lines:
        words = line.find_all("span", class_="ocrx_word")
        
        for idx, word_span in enumerate(words):
            orig_text = word_span.text
            word_id = word_span.get('id', '')
            if not orig_text:
                continue
                
            # Treat the very first word of an ocr_line as the start of a sentence/line
            is_first_word = (idx == 0)
            
            h_trans = hyphenated_transformations.get(word_id)
                
            new_text, rule = correct_word_text(orig_text, word_id, unresolved_words, is_first_word, h_trans)
            if new_text != orig_text and rule:
                # Note: if rule is "Hyphenated Part: Valid Merged Word" and new_text == orig_text, it skips here
                corrections_made.append((word_id, orig_text, new_text, rule))
                word_span.string = new_text
                changed_count += 1
                rule_counts[rule] += 1
            
    print(f"Made {changed_count} corrections in {file_path}:")
    for w_id, orig, new, rule in corrections_made:
        print(f"  [{w_id}] '{orig}' -> '{new}' [{rule}]")
        
    if changed_count > 0:
        print("\n  Categorized by rule:")
        for rule, count in rule_counts.items():
            print(f"    - {rule}: {count}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # Write Corrected Words specifically for this file
    corrected_csv_out = f"{base_name}_Corrected_Words.csv"
    with open(corrected_csv_out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Word ID', 'Original Word', 'Corrected Word', 'Rule Applied'])
        for w_id, orig, new, rule in corrections_made:
            writer.writerow([w_id, orig, new, rule])
    print(f"Logged {len(corrections_made)} corrected words to {corrected_csv_out}")
        
    # Write Unresolved Words specifically for this file
    unresolved_csv_out = f"{base_name}_Unresolved_Words.csv"
    with open(unresolved_csv_out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Word ID', 'Unresolved Word'])
        for w_id, w in unresolved_words:
            writer.writerow([w_id, w])
            
    print(f"Logged {len(unresolved_words)} unresolved words to {unresolved_csv_out}")
    return changed_count

# Clean up old combined unresolved words file if it exists
if os.path.exists('Unresolved_Words_To_Review.csv'):
    os.remove('Unresolved_Words_To_Review.csv')

hocr_files = glob.glob('data/*.hocr')
# Filter out the backup/mock hocr files for the main processing loop to keep it clean
hocr_files = [hf for hf in hocr_files if not hf.endswith('.bak') and '_mock' not in hf and '_llm' not in hf]

total_corrections = 0
for hf in hocr_files:
    total_corrections += process_hocr(hf)

print(f"\n=====================================")
print(f"GRAND TOTAL OF UPDATED WORDS: {total_corrections}")
print(f"=====================================\n")
