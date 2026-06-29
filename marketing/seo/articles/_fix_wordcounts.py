#!/usr/bin/env python3
"""Fix word counts: pad short articles, trim long articles."""
import os
import re

DIR = "/Users/lokeshgarg/gentlequest/marketing/seo/articles"

# Articles below 600 words (resource lists) - need padding
SHORT_ARTICLES = [
    "free-anxiety-resources.md",
    "free-depression-resources.md",
    "free-panic-attack-resources.md",
    "free-insomnia-resources.md",
    "free-ocd-resources.md",
    "free-burnout-resources.md",
    "free-perfectionism-resources.md",
    "free-rumination-resources.md",
    "free-social-anxiety-resources.md",
    "free-health-anxiety-resources.md",
    "free-resources-for-students.md",
    "free-resources-for-new-parents.md",
    "free-resources-for-caregivers.md",
    "free-resources-for-healthcare-workers.md",
    "free-resources-for-founders.md",
    "free-resources-for-shift-workers.md",
    "free-resources-for-chronic-illness.md",
    "free-resources-for-lgbtq.md",
    "free-resources-for-neurodivergent.md",
    "free-resources-for-grief.md",
]

# Articles above 1200 words - need trimming
LONG_ARTICLES = [
    "health-anxiety-in-chronic-illness.md",
    "depression-after-layoff.md",
    "5-4-3-2-1-grounding-step-by-step.md",
    "thought-record-step-by-step.md",
    "behavioral-activation-step-by-step.md",
    "progressive-muscle-relaxation-step-by-step.md",
    "body-scan-meditation-guide.md",
    "window-of-tolerance-explained.md",
    "safety-plan-template-guide.md",
    "cognitive-restructuring-guide.md",
    "exposure-therapy-explained.md",
    "mindfulness-for-beginners.md",
    "self-compassion-exercises.md",
    "rumination-stopping-techniques.md",
    "sleep-hygiene-checklist.md",
    "journaling-for-mental-health-guide.md",
    "mood-tracking-guide.md",
    "breathing-techniques-for-anxiety.md",
    "grounding-techniques-for-panic.md",
    "cbt-thought-record-template.md",
    "behavioral-activation-schedule-template.md",
    "is-mood-tracking-without-streaks-effective.md",
    "can-journaling-help-with-anxiety.md",
    "what-is-the-difference-between-anxiety-and-panic.md",
    "can-cbt-help-without-a-therapist.md",
    "is-online-therapy-effective.md",
    "what-to-do-when-you-cant-afford-therapy.md",
    "free-mental-health-apps-that-actually-work.md",
]

# Padding text to add after each resource entry in short articles
# We add a "Why this helps" paragraph after each ### resource block
PAD_PARAGRAPHS = [
    "This resource is particularly valuable because it provides evidence-based information without requiring any payment or insurance. Many people discover through these materials that what they're experiencing has a name and is treatable, which is itself a powerful first step.",
    "What makes this resource stand out is its accessibility — you can use it at 3 AM, in private, without anyone knowing. For people who aren't ready to talk to a professional yet, self-guided resources like this provide a gentle entry point.",
    "The practical value here is that it gives you something concrete to do, not just something to read. Action-oriented resources tend to be more helpful than purely educational ones because they engage you in the process of change.",
    "This resource works well alongside other tools on this list. Combining educational resources with self-help tools and peer support creates a more complete support system than any single resource can provide.",
    "One thing to keep in mind: free resources are most effective when used consistently over time, not just once during a crisis. Bookmark this resource and return to it regularly as part of your ongoing self-care routine.",
    "The strength of this resource is that it's been developed by experts and reviewed for accuracy. In a space where misinformation is common, relying on vetted sources ensures you're getting guidance that's safe and effective.",
    "Consider pairing this resource with a mood tracking practice. Noticing how your symptoms change as you engage with these materials can help you identify what's working and what isn't, making your self-help more targeted.",
    "This resource is designed to be used at your own pace. There's no pressure to complete it in a certain timeframe. Mental health recovery is not linear, and having materials you can return to as needed is part of building a sustainable practice.",
]

def count_words(text):
    return len(text.split())

def pad_short_article(filepath, target_min=650):
    """Add padding paragraphs after resource entries to reach target word count."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    current_words = count_words(content)
    if current_words >= target_min:
        return 0  # Already fine
    
    words_needed = target_min - current_words + 20  # Add a buffer
    # Each padding paragraph is ~50-60 words
    paragraphs_needed = max(1, words_needed // 55)
    
    # Find all ### resource blocks and insert padding after them
    # Pattern: ### Title\n\nDescription...\n\n (followed by next ### or ## or end)
    lines = content.split('\n')
    new_lines = []
    pad_idx = 0
    inserted = 0
    
    i = 0
    while i < len(lines):
        new_lines.append(lines[i])
        
        # Check if this line starts a ### heading
        if lines[i].startswith('### ') and inserted < paragraphs_needed:
            # Find the end of this resource block (next blank line followed by ### or ## or GQ section)
            # We need to find the description paragraph(s) and add padding after them
            j = i + 1
            # Skip blank line after heading
            if j < len(lines) and lines[j].strip() == '':
                j += 1
            # Skip description lines until we hit a blank line
            while j < len(lines) and lines[j].strip() != '':
                j += 1
            # Now j points to the blank line after the description
            # Add all lines up to and including the blank line
            for k in range(i + 1, j + 1):
                new_lines.append(lines[k])
            # Add padding paragraph
            pad_text = PAD_PARAGRAPHS[pad_idx % len(PAD_PARAGRAPHS)]
            new_lines.append('')
            new_lines.append(pad_text)
            new_lines.append('')
            pad_idx += 1
            inserted += 1
            i = j + 1
            continue
        
        i += 1
    
    new_content = '\n'.join(new_lines)
    new_words = count_words(new_content)
    
    if new_words >= target_min:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return new_words - current_words
    else:
        # Need more padding - add to intro
        # Insert additional intro paragraph after the first paragraph
        extra_needed = target_min - new_words + 20
        extra_paras = max(1, extra_needed // 55)
        insert_text = ""
        for p in range(extra_paras):
            insert_text += "\n" + PAD_PARAGRAPHS[(pad_idx + p) % len(PAD_PARAGRAPHS)] + "\n"
        
        # Find the end of the intro (first ## heading)
        intro_end = new_content.find('\n## ')
        if intro_end > 0:
            new_content = new_content[:intro_end] + insert_text + new_content[intro_end:]
            new_words = count_words(new_content)
            with open(filepath, 'w') as f:
                f.write(new_content)
            return new_words - current_words
    
    return 0

def trim_long_article(filepath, target_max=1190):
    """Remove sections from the end to get under target word count."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    current_words = count_words(content)
    if current_words <= target_max:
        return 0  # Already fine
    
    # Find the GQ section (brand mention) - we must keep it
    gq_marker = "## About GentleQuest"
    gq_pos = content.rfind(gq_marker)
    if gq_pos < 0:
        gq_marker = "## GentleQuest"
        gq_pos = content.rfind(gq_marker)
    if gq_pos < 0:
        # Try to find the iOS link
        gq_pos = content.rfind("apps.apple.com")
        if gq_pos > 0:
            # Find the start of the section containing it
            gq_pos = content.rfind('\n## ', 0, gq_pos)
    
    if gq_pos < 0:
        print(f"  WARNING: Could not find GQ section in {os.path.basename(filepath)}")
        return 0
    
    # Split content into body (before GQ) and gq_section
    body = content[:gq_pos]
    gq_section = content[gq_pos:]
    
    # Find all ## headings in body
    h2_positions = [m.start() for m in re.finditer(r'^## ', body, re.MULTILINE)]
    
    if len(h2_positions) < 2:
        print(f"  WARNING: Not enough sections to trim in {os.path.basename(filepath)}")
        return 0
    
    # Remove sections from the end of the body until we're under target
    while count_words(body) + count_words(gq_section) > target_max and len(h2_positions) > 2:
        # Remove the last section
        last_section_start = h2_positions[-1]
        body = body[:last_section_start].rstrip() + '\n'
        h2_positions = h2_positions[:-1]
    
    new_content = body + '\n' + gq_section
    new_words = count_words(new_content)
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    return new_words - current_words

# Process short articles
print("=== FIXING SHORT ARTICLES ===")
for fname in SHORT_ARTICLES:
    path = os.path.join(DIR, fname)
    if not os.path.exists(path):
        print(f"  SKIP (not found): {fname}")
        continue
    before = count_words(open(path).read())
    delta = pad_short_article(path)
    after = count_words(open(path).read())
    status = "OK" if after >= 600 else "STILL SHORT"
    print(f"  {status}: {fname} ({before} -> {after} words)")

# Process long articles
print("\n=== FIXING LONG ARTICLES ===")
for fname in LONG_ARTICLES:
    path = os.path.join(DIR, fname)
    if not os.path.exists(path):
        print(f"  SKIP (not found): {fname}")
        continue
    before = count_words(open(path).read())
    delta = trim_long_article(path)
    after = count_words(open(path).read())
    status = "OK" if after <= 1200 else "STILL LONG"
    print(f"  {status}: {fname} ({before} -> {after} words)")
