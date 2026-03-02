import csv
from bs4 import BeautifulSoup
import unicodedata

# function to help ignore the unicode changes like ’ v.s. ' (hard to notice)
def normalize(text):
    return text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')

def extract_text_dict(hocr_filepath):
    """Extracts words into a dictionary mapping ID to the actual value"""
    text_dict = {}
    try:
        with open(hocr_filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            for span in soup.find_all('span', class_='ocrx_word'):
                word_id = span.get('id')
                word_text = span.get_text().strip()
                if word_id:
                    text_dict[word_id] = word_text
        return text_dict
    except Exception as e:
        print(f"Error: {e}")
        return {}

def calculate_metrics_by_id(orig_dict, manual_dict, ai_dict):
    stats = {
        "Total Errors to Fix": 0,
        "AI Correct Fixes": 0,
        "AI Missed (Unchanged)": 0,
        "AI Wrong Fixes": 0,
        "AI False Positives": 0
    }
    detailed_results = []

    # use the the manual hocr as source of truth (because that is what we expect)
    for word_id, manual_text in manual_dict.items():
        manual_text = normalize(manual_text)
        orig_text = normalize(orig_dict.get(word_id, ""))
        ai_text = normalize(ai_dict.get(word_id, ""))

        # skip if there was a word insertion in manual
        if (manual_text != "" and orig_text == "") or (manual_text != "" and ai_text == ""):
            continue

        # change was made between original and human corected
        if orig_text != manual_text:
            stats["Total Errors to Fix"] += 1
            if ai_text == manual_text:
                status = "CORRECT_FIX"
                stats["AI Correct Fixes"] += 1
            elif ai_text == orig_text:
                status = "MISSED_FIX"
                stats["AI Missed (Unchanged)"] += 1
            else:
                status = "WRONG_FIX"
                stats["AI Wrong Fixes"] += 1
            
            detailed_results.append({
                "ID": word_id, "Original": orig_text, 
                "Manual": manual_text, "AI": ai_text, "Status": status
            })

        # ai changed the word that was already corrected
        elif ai_text != orig_text: # and orig_text == manual_text due to elif
            stats["AI False Positives"] += 1
            detailed_results.append({
                "ID": word_id, "Original": orig_text, 
                "Manual": manual_text, "AI": ai_text, "Status": "FALSE_POSITIVE"
            })

    # calculate percentage
    total = stats["Total Errors to Fix"]
    stats["Accuracy on Errors %"] = round((stats["AI Correct Fixes"] / total * 100), 2) if total > 0 else 100
    
    return stats, detailed_results

def run_evaluation(orig_path, manual_path, ai_path, output_csv="id_based_evaluation.csv"):
    print(f"--- 📂 Loading HOCR Files ---")
    orig_dict = extract_text_dict(orig_path)
    manual_dict = extract_text_dict(manual_path)
    ai_dict = extract_text_dict(ai_path)
    
    print(f"Words loaded - Orig: {len(orig_dict)}, Manual: {len(manual_dict)}, AI: {len(ai_dict)}")

    # safety check
    if not orig_dict or not manual_dict or not ai_dict:
        print("❌ Error: One or more files could not be parsed. Check your file paths.")
        return

    # get the details and print the stats
    stats, detailed_results = calculate_metrics_by_id(orig_dict, manual_dict, ai_dict)
    
    print("\n--- 📊 PERFORMANCE SUMMARY (ID-BASED) ---")
    print(f"Total OCR Errors found by Human: {stats['Total Errors to Fix']}")
    print(f"✅ AI Correctly Fixed:           {stats['AI Correct Fixes']}")
    print(f"❌ AI Missed (No change):        {stats['AI Missed (Unchanged)']}")
    print(f"⚠️ AI Wrong Fix (Hallucinated):  {stats['AI Wrong Fixes']}")
    print(f"🚫 AI False Positives:           {stats['AI False Positives']}")
    print(f"------------------------------------------")
    print(f"🚀 SUCCESS RATE ON ERRORS:      {stats['Accuracy on Errors %']}")
    print(f"------------------------------------------")
        
    # saving to csv file
    if detailed_results:
        keys = detailed_results[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(detailed_results)
        print(f"\n✅ Detailed log saved to: {output_csv}")
    else:
        print("\nℹ️ No changes or errors detected to log.")


if __name__ == "__main__":
    ORIGINAL_HOCR = "comparisons-v2/approach-1d/hocr_original/005_01_2.hocr"
    MANUAL_HOCR = "comparisons-v2/approach-1d/hocr_manually_corrected/005_01_2_Corrected_OCR.hocr"
    AI_HOCR = "comparisons-v2/approach-1d/hocr_gemini_corrected/005_01_2/2.5_flash_dynamic_AI_corrected.hocr"

    run_evaluation(ORIGINAL_HOCR, MANUAL_HOCR, AI_HOCR)
