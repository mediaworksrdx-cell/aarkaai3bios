import re

def _is_list_header(text, pos):
    # pos is the index of '.'
    i = pos - 1
    while i >= 0 and text[i].isdigit():
        i -= 1
    if i < pos - 1:
        # Digits found. Check if preceded by a newline (possibly with space) or start of text
        prefix = text[:i + 1]
        if not prefix.strip():
            return True
        # Check if the prefix ends with a newline character, possibly followed by spaces
        stripped_len = len(prefix) - len(prefix.rstrip(' '))
        if stripped_len > 0:
            prefix = prefix[:-stripped_len]
        if prefix and prefix[-1] == '\n':
            return True
    return False

def _clean_response(text):
    if not text:
        return text
    
    # Strip out hallucinated markers
    text = text.replace("[end of web search results]", "").strip()
    text = text.replace("[End of web search results]", "").strip()

    # Do not truncate if text contains code blocks to avoid corrupting code syntax.
    if "```" in text:
        # If the code block is unclosed, close it cleanly
        if text.count("```") % 2 != 0:
            return text + "\n```"
        return text

    # Remove trailing unfinished list headers or newlines (e.g. \n\n7. or \n-)
    text = re.sub(r'\n+\s*(?:-|\*|\d+\.)\s*$', '', text)
        
    # If it naturally ends in a punctuation mark (and isn't a dangling list number like "5."), leave it alone!
    if text[-1] in ".!?" and not (text[-1] == "." and len(text) > 1 and text[-2].isdigit()):
        return text

    # Otherwise, find the latest complete sentence ending in the second half of the text
    best_pos = -1
    for end_char in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
        pos = text.rfind(end_char)
        while pos > best_pos:
            # If the period is part of a list header, ignore it and search backwards
            if end_char in [". ", ".\n"] and _is_list_header(text, pos):
                pos = text.rfind(end_char, 0, pos)
                continue
            best_pos = pos
            break
            
    if best_pos > len(text) * 0.5:
        return text[:best_pos + 1]
            
    return text + "."

# Test Case 1: Ends with unfinished list header "7."
text_1 = "ult in stock losses for individual companies, including those with lower-than-expected earnings.\n\n7."
print("TC1:", repr(_clean_response(text_1)))

# Test Case 2: Ends with unfinished list header "7. " (with space)
text_2 = "ult in stock losses for individual companies, including those with lower-than-expected earnings.\n\n7. "
print("TC2:", repr(_clean_response(text_2)))

# Test Case 3: Ends with partial sentence in point 7
text_3 = "5. Price.\n\n6. Market conditions: Factors such as rising interest rates, including those with lower-than-expected earnings.\n\n7. Analysts expectations: If the"
print("TC3:", repr(_clean_response(text_3)))

# Test Case 4: Ends with a number at the end of a sentence
text_4 = "The stock rose in 2026. This was because it did well."
print("TC4:", repr(_clean_response(text_4)))
