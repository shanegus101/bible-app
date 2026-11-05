import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
import re
from groq import Groq

# --- PAGE SETUP ---
st.set_page_config(page_title="Heirloom Bible Study", page_icon="📜", layout="centered")

# --- CUSTOM VINTAGE / HEIRLOOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #FAF6F0;
    color: #2C221E;
}

h1, h2, h3, h4 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    color: #2C221E !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
    margin-top: 0.6rem !important;
}

p, li, div {
    font-family: 'Inter', sans-serif;
    color: #3D3228;
    line-height: 1.68;
    font-size: 0.97rem;
}

strong {
    color: #231A14;
    font-weight: 600;
}

/* Fix mobile dropdown text truncation so verse numbers & titles are always readable */
div[data-baseweb="select"] span,
ul[data-testid="stSelectboxVirtualDropdown"] li {
    white-space: normal !important;
    word-wrap: break-word !important;
    line-height: 1.35 !important;
    padding-top: 4px !important;
    padding-bottom: 4px !important;
}

.vintage-card {
    background: linear-gradient(135deg, #FBF6E9 0%, #F5DEC0 55%, #F2CFAA 100%);
    border-radius: 22px;
    padding: 30px 26px;
    margin: 22px 0 14px 0;
    border: 1px solid #E6D2B5;
    box-shadow: 0 8px 24px rgba(139, 98, 59, 0.08);
}

.vintage-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #8C735B;
    margin-bottom: 6px;
    font-weight: 600;
}

.vintage-subheader {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.65rem;
    font-weight: 700;
    color: #2C221E;
    margin-top: 0;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(140, 115, 91, 0.25);
    padding-bottom: 8px;
}

.vintage-verse-text {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.45rem;
    line-height: 1.55;
    color: #2C221E;
    margin-bottom: 18px;
    font-weight: 500;
}

.vintage-verse-num {
    font-size: 0.85rem;
    color: #9C7A54;
    vertical-align: super;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    margin-right: 4px;
}

.vintage-ref {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8C735B;
    font-weight: 600;
}

.insight-card {
    background-color: #FFFDF9;
    border-radius: 18px;
    padding: 26px 26px;
    margin-bottom: 30px;
    border: 1px solid #EFE6D8;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
}

.stButton > button {
    background: linear-gradient(135deg, #8C6239 0%, #6E4B2A 100%) !important;
    color: #FAF6F0 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 24px !important;
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 4px 12px rgba(110, 75, 42, 0.2) !important;
}

.stButton > button p {
    color: #FAF6F0 !important;
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 1.2rem !important;
}

div[data-testid="stExpander"] {
    background-color: #FFFDF9;
    border-radius: 14px;
    border: 1px solid #E6D7C3;
}
</style>
""", unsafe_allow_html=True)

# --- TOP ANCHOR FOR MOBILE AUTO-SCROLL ---
st.markdown("<div id='top-anchor'></div>", unsafe_allow_html=True)

# --- APP HEADER ---
st.markdown("<div style='text-align: center; padding-top: 10px;'>", unsafe_allow_html=True)
st.markdown("<div class='vintage-label' style='margin-bottom: 4px;'>HEIRLOOM EDITION</div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 2.5rem; margin-top: 0; padding-top: 0;'>Scripture & Study</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- LOAD BIBLE DATA & PERSISTENT SECTION CACHE ---
BIBLE_FILE = "bible_data.json"
SECTIONS_CACHE_FILE = "sections_cache.json"

@st.cache_data
def load_bible():
    if not os.path.exists(BIBLE_FILE):
        url = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_bbe.json"
        response = requests.get(url)
        data = json.loads(response.content.decode('utf-8-sig'))
        with open(BIBLE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    else:
        with open(BIBLE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def load_persistent_sections():
    if os.path.exists(SECTIONS_CACHE_FILE):
        try:
            with open(SECTIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_persistent_sections(cache_dict):
    try:
        with open(SECTIONS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_dict, f)
    except Exception:
        pass

bible_data = load_bible()
book_names = [book['name'] for book in bible_data]

# --- API KEY HANDLING (Supports primary 'shanesapi' + optional backup 'shanesapi2') ---
api_keys = []
for secret_name in ["shanesapi", "shanesapi2", "backup_api"]:
    val = st.secrets.get(secret_name, None)
    if val and val.strip():
        api_keys.append(val.strip())

if not api_keys and st.session_state.get("user_api_key"):
    api_keys.append(st.session_state.get("user_api_key"))

has_api_key = len(api_keys) > 0

# --- INITIALIZE SESSION STATE & MEMORY ---
if "working_model" not in st.session_state:
    st.session_state.working_model = None
if "sections_cache" not in st.session_state:
    st.session_state.sections_cache = load_persistent_sections()
if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False

query_book = st.query_params.get("book", None)
query_chapter = st.query_params.get("chapter", None)

if "study_started" not in st.session_state:
    if query_book in book_names and query_chapter and query_chapter.isdigit():
        b_obj = next(b for b in bible_data if b['name'] == query_book)
        c_num = max(1, min(int(query_chapter), len(b_obj['chapters'])))
        st.session_state.selected_book_name = query_book
        st.session_state.selected_chapter_num = c_num
        st.session_state.study_started = True
    else:
        st.session_state.selected_book_name = "Matthew"
        st.session_state.selected_chapter_num = 1
        st.session_state.study_started = False

        components.html("""
        <script>
        const savedBook = localStorage.getItem('heirloom_book');
        const savedChap = localStorage.getItem('heirloom_chapter');
        const urlParams = new URLSearchParams(window.parent.location.search);
        if (savedBook && savedChap && !urlParams.get('book')) {
            urlParams.set('book', savedBook);
            urlParams.set('chapter', savedChap);
            window.parent.location.search = urlParams.toString();
        }
        </script>
        """, height=0)

if "current_chunk" not in st.session_state:
    st.session_state.current_chunk = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "chapter_summary" not in st.session_state:
    st.session_state.chapter_summary = None
if "prayer_generated" not in st.session_state:
    st.session_state.prayer_generated = False

if st.session_state.scroll_to_top:
    components.html("""
        <script>
            window.parent.document.getElementById('top-anchor').scrollIntoView({behavior: 'smooth'});
            window.parent.scrollTo({top: 0, behavior: 'smooth'});
        </script>
    """, height=0)
    st.session_state.scroll_to_top = False

def save_reading_progress(book, chapter, start_section_idx=0):
    st.session_state.selected_book_name = book
    st.session_state.selected_chapter_num = chapter
    st.session_state.current_chunk = start_section_idx
    st.session_state.history = []
    st.session_state.chapter_summary = None
    st.session_state.prayer_generated = False
    st.session_state.study_started = True
    st.session_state.scroll_to_top = True
    st.query_params["book"] = book
    st.query_params["chapter"] = str(chapter)
    components.html(f"""
        <script>
            localStorage.setItem('heirloom_book', "{book}");
            localStorage.setItem('heirloom_chapter', "{chapter}");
        </script>
    """, height=0)

# --- STRICT DEVOTIONAL PROMPTS ---
SYSTEM_PROMPT = """You are an insightful, warm, and clear Bible study teacher writing a clean devotional guide.
CRITICAL RULES:
1. NEVER include conversational filler like "Sure, let's break down...", "Here is the analysis", or "In this request". Start IMMEDIATELY with the first heading.
2. Quote or reference the NASB (New American Standard Bible) wording when discussing the text.
3. Keep explanations minimalistic, grounded in historical/cultural context, and deeply practical. Do not hallucinate events from other chapters."""

# Cycles through all API keys and models automatically so you never hit a wall
def call_groq_safely(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.4):
    errors = []
    for key_idx, current_key in enumerate(api_keys):
        client = Groq(api_key=current_key)
        try:
            live_models = [m.id for m in client.models.list().data]
        except Exception:
            live_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            
        llama_first = [m for m in live_models if "llama" in m.lower() and "guard" not in m.lower()]
        other_chat = [m for m in live_models if m not in llama_first and not any(x in m.lower() for x in ["whisper", "orpheus", "tts", "guard", "embed", "playai"])]
        everything_else = [m for m in live_models if m not in llama_first and m not in other_chat]
        
        candidate_models = llama_first + other_chat + everything_else
        if st.session_state.working_model:
            candidate_models = [st.session_state.working_model] + [m for m in candidate_models if m != st.session_state.working_model]
            
        for model_id in candidate_models:
            try:
                completion = client.chat.completions.create(
                    model=model_id,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                content = completion.choices[0].message.content
                if "<think>" in content and "</think>" in content:
                    content = content.split("</think>")[-1].strip()
                st.session_state.working_model = model_id
                return content
            except Exception as e:
                errors.append(f"Key{key_idx+1}/{model_id}: {str(e)}")
                continue
                
    st.error("All models/keys exhausted. Details: " + " | ".join(errors[:5]))
    st.stop()

# --- THEMATIC SUBHEADER GENERATOR (PERICOPES) ---
def build_fallback_sections(total_verses, max_v=15):
    sections = []
    for s in range(1, total_verses + 1, max_v):
        e = min(s + max_v - 1, total_verses)
        sections.append({"title": f"Verses {s}–{e}", "start": s, "end": e})
    return sections

def enforce_max_chunk_size(sections, max_verses=18):
    final_sections = []
    for sec in sections:
        start = sec["start"]
        end = sec["end"]
        title = sec["title"]
        length = end - start + 1
        if length <= max_verses:
            final_sections.append(sec)
        else:
            num_parts = (length + max_verses - 1) // max_verses
            part_size = (length + num_parts - 1) // num_parts
            for p in range(num_parts):
                p_start = start + p * part_size
                p_end = min(start + (p + 1) * part_size - 1, end)
                if p_start <= p_end:
                    final_sections.append({
                        "title": f"{title} (Pt. {p + 1})",
                        "start": p_start,
                        "end": p_end
                    })
    return final_sections

def get_chapter_sections(book, chapter, verses_list):
    cache_key = f"{book}_{chapter}"
    if cache_key in st.session_state.sections_cache:
        return st.session_state.sections_cache[cache_key]

    total_verses = len(verses_list)
    if not has_api_key:
        return build_fallback_sections(total_verses)

    numbered_text = "\n".join([f"{i+1}. {v}" for i, v in enumerate(verses_list)])
    prompt = f"""Divide {book} Chapter {chapter} ({total_verses} verses total, 1 to {total_verses}) into its natural biblical thematic subheaders (pericopes), similar to an NASB Study Bible.

CRITICAL RULES:
1. Cover every verse from 1 to {total_verses} in sequential order with NO gaps and NO overlaps.
2. Keep each "title" VERY SHORT and punchy (2 to 5 words maximum, e.g., "John's Questions", "Jesus' Tribute to John", "The Parable of the Sower").
3. MAXIMUM 18 verses per section. If a section is longer than 18 verses, split it into consecutive parts (e.g., "Sermon on the Mount (Pt. 1)").
4. Return ONLY a valid JSON array of objects with keys "title" (string), "start" (integer), and "end" (integer).

Chapter Text:
{numbered_text}"""

    try:
        raw_resp = call_groq_safely(
            prompt,
            system_prompt="You are a biblical scholar and precise JSON generator. Output ONLY a valid JSON array.",
            temperature=0.1
        )
        match = re.search(r'\[.*\]', raw_resp, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            validated = []
            expected_start = 1
            for item in parsed:
                t = str(item.get("title", "Scripture Reading")).strip()
                e = int(item.get("end", expected_start))
                if e < expected_start:
                    continue
                if e > total_verses:
                    e = total_verses
                validated.append({"title": t, "start": expected_start, "end": e})
                expected_start = e + 1
                if expected_start > total_verses:
                    break
            if expected_start <= total_verses:
                validated.append({
                    "title": "Concluding Verses",
                    "start": expected_start,
                    "end": total_verses
                })
            final_sections = enforce_max_chunk_size(validated, max_verses=18)
            st.session_state.sections_cache[cache_key] = final_sections
            save_persistent_sections(st.session_state.sections_cache)
            return final_sections
    except Exception:
        pass

    fallback = build_fallback_sections(total_verses)
    st.session_state.sections_cache[cache_key] = fallback
    return fallback

def format_dropdown_label(sec):
    v_str = f"v. {sec['start']}–{sec['end']}" if sec['start'] != sec['end'] else f"v. {sec['start']}"
    return f"{v_str} · {sec['title']}"

# --- DEVOTIONAL ANALYSIS GENERATORS ---
def get_llama_insight(book, chapter, section_title, verse_range, text, previous_context):
    prompt = f"""
Passage: {book} {chapter}:{verse_range} ({section_title})
Text: "{text}"
Previous context in this chapter: {previous_context if previous_context else "This is the opening section of the chapter."}

Write a clean, theme-driven devotional breakdown of ONLY {book} {chapter}:{verse_range} using this EXACT Markdown template (if the passage is under 5 verses, you may use 1 Sub-Theme section; otherwise use 2 Sub-Theme sections):

### The Big Picture: [Create a Short, Compelling Theme Title]
[2-3 clear sentences setting the scene. If this is not the first section, smoothly connect it to what happened right before this. Explain the main tension or big idea of these verses.]

### [1. Short Sub-Theme Title (Verses X–Y)]
* **The Context:** [1-2 sentences explaining who is involved or important cultural/historical background.]
* **What Happens:** [1-2 sentences explaining the action or dialogue, quoting key NASB phrases.]
* **The Meaning:** [2-3 sentences unpacking the deeper spiritual truth and why Jesus/the author says or does this.]

### [2. Second Short Sub-Theme Title (Verses Y–Z)]
* **The Context:** [1-2 sentences of background or setup.]
* **What Happens:** [1-2 sentences on the action/response.]
* **The Meaning:** [2-3 sentences unpacking the heart of the lesson.]

### Summary
* **[Key Contrast or Point 1]:** [1 punchy sentence]
* **[Key Contrast or Point 2]:** [1 punchy sentence]

**Ultimately:** [1 final, memorable sentence summarizing what {book} {chapter}:{verse_range} teaches us about following God.]
"""
    return call_groq_safely(prompt)

def get_chapter_summary(book, chapter, full_chapter_text):
    prompt = f"""
We just finished reading all of {book} Chapter {chapter}.
Full chapter text: "{full_chapter_text}"

Provide a clean, minimalistic "Big Picture Chapter Summary" using this EXACT Markdown structure (no intro chatter):

### The Big Picture of {book} {chapter}
[2-3 sentences explaining the overarching message and flow of the entire chapter from start to finish.]

### Major Themes We Saw
* **1. [Theme 1]:** [1-2 clear sentences tying back to specific moments in the chapter.]
* **2. [Theme 2]:** [1-2 clear sentences.]
* **3. [Theme 3]:** [1-2 clear sentences.]

**The Ultimate Takeaway:** [1 powerful closing sentence that captures the heart of {book} {chapter}.]
"""
    return call_groq_safely(prompt)

def get_prayer_and_application(book, chapter, full_chapter_text):
    prompt = f"""
Passage: {book} Chapter {chapter}
Full text: "{full_chapter_text}"

Write a personal, practical guide on how to pray over this chapter and integrate it into daily life. Use this EXACT Markdown template (no intro chatter):

### 1. [Practical Theme 1 Title]
* **The Heart Check:** [1-2 piercing, honest questions to ask myself based on this chapter.]
* **How to Apply It:** [1 specific, concrete action I can take this week.]
* **How to Pray:** > *"[A sincere, 2-3 sentence first-person prayer]"*

### 2. [Practical Theme 2 Title]
* **The Heart Check:** [1-2 honest questions to ask myself.]
* **How to Apply It:** [1 specific, concrete action for this week.]
* **How to Pray:** > *"[A sincere, 2-3 sentence first-person prayer]"*

### 3. [Practical Theme 3 Title]
* **The Heart Check:** [1-2 honest questions to ask myself.]
* **How to Apply It:** [1 specific, concrete action for this week.]
* **How to Pray:** > *"[A sincere, 2-3 sentence first-person prayer]"*

---
### A Simple 1-Minute Prayer to Start Your Day
> **"[A unified, powerful 4-sentence daily prayer weaving all three themes of {book} {chapter} together. Amen.]"**
"""
    return call_groq_safely(prompt)

# --- VIEW 1: WELCOME / LANDING SCREEN ---
if not st.session_state.study_started:
    st.markdown("""
    <div class="vintage-card" style="text-align: center;">
        <div class="vintage-label">WELCOME TO YOUR DEVOTIONAL</div>
        <h2 style="margin-top: 4px; margin-bottom: 10px;">Select Your Reading Place</h2>
        <p style="margin-bottom: 0;">Choose a Book and Chapter below. Your place will be automatically remembered as you read.</p>
    </div>
    """, unsafe_allow_html=True)

    if not has_api_key:
        input_key = st.text_input("Enter Groq API Key to Begin:", type="password")
        if input_key:
            st.session_state.user_api_key = input_key.strip()
            st.rerun()
        st.stop()

    default_book_idx = book_names.index(st.session_state.selected_book_name) if st.session_state.selected_book_name in book_names else 39
    chosen_book_name = st.selectbox("Book", book_names, index=default_book_idx)
    chosen_book_obj = next(b for b in bible_data if b['name'] == chosen_book_name)
    num_chaps = len(chosen_book_obj['chapters'])
    
    default_chap_idx = min(st.session_state.selected_chapter_num - 1, num_chaps - 1)
    chosen_chap_num = st.selectbox("Chapter", range(1, num_chaps + 1), index=max(0, default_chap_idx))

    chap_verses = chosen_book_obj['chapters'][chosen_chap_num - 1]
    with st.spinner(f"Loading sections for {chosen_book_name} {chosen_chap_num}..."):
        preview_sections = get_chapter_sections(chosen_book_name, chosen_chap_num, chap_verses)

    # Verse numbers placed FIRST so they never cut off on mobile screens
    section_labels = [format_dropdown_label(s) for s in preview_sections]
    chosen_sec_label = st.selectbox("Starting Section", section_labels, index=0)
    chosen_sec_idx = section_labels.index(chosen_sec_label)

    if st.button("Open Scripture  →", use_container_width=True):
        save_reading_progress(chosen_book_name, chosen_chap_num, chosen_sec_idx)
        st.rerun()
    st.stop()

# --- VIEW 2: ACTIVE READING VIEW ---
selected_book_name = st.session_state.selected_book_name
selected_chapter_num = st.session_state.selected_chapter_num
selected_book = next(b for b in bible_data if b['name'] == selected_book_name)
verses = selected_book['chapters'][selected_chapter_num - 1]

if not has_api_key:
    with st.expander("🔑 Enter Groq API Key", expanded=True):
        input_key = st.text_input("Groq API Key:", type="password")
        if input_key:
            st.session_state.user_api_key = input_key.strip()
            st.rerun()
    st.stop()

with st.spinner(f"Preparing thematic sections for {selected_book_name} {selected_chapter_num}..."):
    sections = get_chapter_sections(selected_book_name, selected_chapter_num, verses)
total_chunks = len(sections)

# --- TOP PASSAGE & SECTION SELECTOR ---
with st.expander("📖 Select Book, Chapter & Starting Section", expanded=False):
    b_idx = book_names.index(selected_book_name)
    new_book_name = st.selectbox("Book", book_names, index=b_idx, key="nav_book")
    new_book_obj = next(b for b in bible_data if b['name'] == new_book_name)
    new_num_chapters = len(new_book_obj['chapters'])
    
    c_idx = selected_chapter_num - 1 if new_book_name == selected_book_name else 0
    c_idx = min(max(0, c_idx), new_num_chapters - 1)
    new_chapter_num = st.selectbox("Chapter", range(1, new_num_chapters + 1), index=c_idx, key="nav_chap")
    
    nav_verses = new_book_obj['chapters'][new_chapter_num - 1]
    nav_sections = get_chapter_sections(new_book_name, new_chapter_num, nav_verses)
    nav_section_labels = [format_dropdown_label(s) for s in nav_sections]
    selected_nav_sec = st.selectbox("Start at Section", nav_section_labels, index=0, key="nav_sec")
    selected_nav_sec_idx = nav_section_labels.index(selected_nav_sec)
    
    if st.button("Begin / Jump to Section", use_container_width=True):
        save_reading_progress(new_book_name, new_chapter_num, selected_nav_sec_idx)
        st.rerun()

# --- CHAPTER SUBHEADER ---
st.markdown(f"<h2 style='text-align: center; margin-top: 15px; margin-bottom: 20px; font-style: italic;'>{selected_book_name} · Chapter {selected_chapter_num}</h2>", unsafe_allow_html=True)

# --- DISPLAY VINTAGE CARDS & STUDY NOTES ---
for item in st.session_state.history:
    st.markdown(f"""
    <div class="vintage-card">
        <div class="vintage-label">SCRIPTURE READING</div>
        <div class="vintage-subheader">{item['title']}</div>
        <div class="vintage-verse-text">{item['html_text']}</div>
        <div class="vintage-ref">{selected_book_name.upper()} {selected_chapter_num}:{item['range']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight-card">
        <div class="vintage-label" style="margin-bottom: 6px;">STUDY NOTES & INSIGHTS</div>
    """, unsafe_allow_html=True)
    st.markdown(item['insight'])
    st.markdown("</div>", unsafe_allow_html=True)

# --- NEXT THEMATIC SECTION BUTTON ---
if st.session_state.current_chunk < total_chunks:
    idx = st.session_state.current_chunk
    current_sec = sections[idx]
    sec_title = current_sec['title']
    start_v = current_sec['start']
    end_v = current_sec['end']
    v_range = f"{start_v}–{end_v}" if start_v != end_v else f"{start_v}"
    
    current_verses = verses[start_v - 1 : end_v]
    plain_text = " ".join([f"({start_v + i}) {v}" for i, v in enumerate(current_verses)])
    html_text = " ".join([f"<span class='vintage-verse-num'>{start_v + i}</span>{v}" for i, v in enumerate(current_verses)])
    
    if st.button(f"Read v. {v_range} · {sec_title}  →", use_container_width=True):
        with st.spinner(f"Unpacking '{sec_title}' (Verses {v_range})..."):
            if st.session_state.history:
                prev_summary = " | ".join([f"{h['title']} (v. {h['range']}): {h.get('plain_text', '')}" for h in st.session_state.history[-2:]])
            elif start_v > 1:
                earlier_v = verses[:start_v - 1]
                prev_summary = "Earlier in this chapter: " + " ".join([f"({i+1}) {v}" for i, v in enumerate(earlier_v[-10:])])
            else:
                prev_summary = ""
                
            insight = get_llama_insight(selected_book_name, selected_chapter_num, sec_title, v_range, plain_text, prev_summary)
            
            st.session_state.history.append({
                "title": sec_title,
                "range": v_range,
                "plain_text": plain_text,
                "html_text": html_text,
                "insight": insight
            })
            st.session_state.current_chunk += 1
            st.rerun()

# --- END OF CHAPTER: BIG PICTURE SUMMARY + PRAYER & BOTTOM NAVIGATION ---
else:
    st.markdown("<div style='text-align: center; margin: 24px 0 12px 0; font-family: Cormorant Garamond, serif; font-size: 1.4rem; color: #6E4B2A;'>— Chapter Complete —</div>", unsafe_allow_html=True)
    
    if not st.session_state.chapter_summary:
        with st.spinner("Synthesizing the Big Picture of the chapter..."):
            full_text = " ".join(verses)
            st.session_state.chapter_summary = get_chapter_summary(selected_book_name, selected_chapter_num, full_text)
            st.rerun()
            
    if st.session_state.chapter_summary:
        st.markdown("""
        <div class="vintage-card">
            <div class="vintage-label">CHAPTER OVERVIEW</div>
            <h2 style="margin-top: 0; margin-bottom: 4px;">The Big Picture Summary</h2>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.chapter_summary)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.prayer_generated:
        if st.button("🙏 How can I pray over & apply this chapter?", use_container_width=True):
            with st.spinner("Preparing your personal prayer & application guide..."):
                full_text = " ".join(verses)
                prayer_guide = get_prayer_and_application(selected_book_name, selected_chapter_num, full_text)
                st.session_state.prayer_guide = prayer_guide
                st.session_state.prayer_generated = True
                st.rerun()
                
    if st.session_state.prayer_generated:
        st.markdown("""
        <div class="vintage-card">
            <div class="vintage-label">DEVOTIONAL & APPLICATION</div>
            <h2 style="margin-top: 0; margin-bottom: 4px;">Integrating the Word</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.prayer_guide)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BOTTOM CHAPTER ADVANCE & RESET CONTROLS (FOR MOBILE) ---
    st.markdown("<hr style='border: none; border-top: 1px solid #E6D2B5; margin: 28px 0 18px 0;'>", unsafe_allow_html=True)
    
    num_chapters_in_book = len(selected_book['chapters'])
    current_book_idx = book_names.index(selected_book_name)
    
    if selected_chapter_num < num_chapters_in_book:
        next_book_name = selected_book_name
        next_chap_num = selected_chapter_num + 1
    elif current_book_idx + 1 < len(book_names):
        next_book_name = book_names[current_book_idx + 1]
        next_chap_num = 1
    else:
        next_book_name = None
        next_chap_num = None

    if next_book_name:
        if st.button(f"Continue to {next_book_name} Chapter {next_chap_num}  →", use_container_width=True):
            save_reading_progress(next_book_name, next_chap_num, 0)
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("↺ Restart This Chapter", use_container_width=True):
            save_reading_progress(selected_book_name, selected_chapter_num, 0)
            st.rerun()
    with col2:
        if st.button("📖 Choose Another Passage", use_container_width=True):
            st.session_state.study_started = False
            st.session_state.scroll_to_top = True
            st.query_params.clear()
            st.rerun()
