import streamlit as st
import requests
import json
import os
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
    margin-bottom: 16px;
    font-weight: 600;
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

# --- APP HEADER ---
st.markdown("<div style='text-align: center; padding-top: 10px;'>", unsafe_allow_html=True)
st.markdown("<div class='vintage-label' style='margin-bottom: 4px;'>HEIRLOOM EDITION</div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 2.5rem; margin-top: 0; padding-top: 0;'>Scripture & Study</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- LOAD BIBLE DATA ---
BIBLE_FILE = "bible_data.json"

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

bible_data = load_bible()

raw_key = st.secrets.get("shanesapi", None)
api_key = raw_key.strip() if raw_key else None

# --- PASSAGE SELECTOR ---
with st.expander("📖 Select Book & Chapter", expanded=False):
    if not api_key:
        input_key = st.text_input("Enter Groq API Key:", type="password")
        if input_key:
            api_key = input_key.strip()
            
    book_names = [book['name'] for book in bible_data]
    selected_book_name = st.selectbox("Book", book_names, index=39)
    
    selected_book = next(b for b in bible_data if b['name'] == selected_book_name)
    num_chapters = len(selected_book['chapters'])
    selected_chapter_num = st.selectbox("Chapter", range(1, num_chapters + 1), index=7)
    
    chunk_size = st.slider("Verses per reading card", min_value=3, max_value=10, value=5)
    
    if st.button("Begin / Reset Chapter", use_container_width=True):
        st.session_state.current_chunk = 0
        st.session_state.history = []
        st.session_state.chapter_summary = None
        st.session_state.prayer_generated = False
        st.rerun()

if "current_chunk" not in st.session_state:
    st.session_state.current_chunk = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "chapter_summary" not in st.session_state:
    st.session_state.chapter_summary = None
if "prayer_generated" not in st.session_state:
    st.session_state.prayer_generated = False
if "working_model" not in st.session_state:
    st.session_state.working_model = None

verses = selected_book['chapters'][selected_chapter_num - 1]
chunks = [verses[i:i + chunk_size] for i in range(0, len(verses), chunk_size)]
total_chunks = len(chunks)

# --- STRICT DEVOTIONAL PROMPTS ---
SYSTEM_PROMPT = """You are an insightful, warm, and clear Bible study teacher writing a clean devotional guide.
CRITICAL RULES:
1. NEVER include conversational filler like "Sure, let's break down...", "Here is the analysis", or "In this request". Start IMMEDIATELY with the first heading.
2. Quote or reference the NASB (New American Standard Bible) wording when discussing the text.
3. Keep explanations minimalistic, grounded in historical/cultural context, and deeply practical. Do not hallucinate events from other chapters."""

# Automatically cycles through every model on your Groq account until one succeeds!
def call_groq_safely(prompt):
    client = Groq(api_key=api_key)
    
    # 1. Fetch all real model IDs currently active on your Groq account
    try:
        live_models = [m.id for m in client.models.list().data]
    except Exception:
        live_models = []
        
    # Sort so Llama and chat models are tried first, and audio/guard models last
    llama_first = [m for m in live_models if "llama" in m.lower() and "guard" not in m.lower()]
    other_chat = [m for m in live_models if m not in llama_first and not any(x in m.lower() for x in ["whisper", "orpheus", "tts", "guard", "embed", "playai"])]
    everything_else = [m for m in live_models if m not in llama_first and m not in other_chat]
    
    candidate_models = llama_first + other_chat + everything_else
    
    # If we already found a working model earlier in this session, try it first!
    if st.session_state.working_model:
        candidate_models = [st.session_state.working_model] + [m for m in candidate_models if m != st.session_state.working_model]
        
    errors = []
    for model_id in candidate_models:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            content = completion.choices[0].message.content
            # If the model uses <think> tags (like Qwen/DeepSeek), strip them out cleanly
            if "<think>" in content and "</think>" in content:
                content = content.split("</think>")[-1].strip()
            st.session_state.working_model = model_id
            return content
        except Exception as e:
            errors.append(f"{model_id}: {str(e)}")
            continue
            
    st.error("None of the models on your Groq account responded. Models tried: " + " | ".join(errors))
    st.stop()

def get_llama_insight(book, chapter, verse_range, text, previous_context):
    prompt = f"""
Passage: {book} {chapter}:{verse_range}
Text: "{text}"
Previous context in this chapter: {previous_context if previous_context else "This is the opening section of the chapter."}

Write a clean, theme-driven devotional breakdown of ONLY {book} {chapter}:{verse_range} using this EXACT Markdown template:

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

# --- CHAPTER SUBHEADER ---
st.markdown(f"<h2 style='text-align: center; margin-top: 15px; margin-bottom: 20px; font-style: italic;'>{selected_book_name} · Chapter {selected_chapter_num}</h2>", unsafe_allow_html=True)

if not api_key:
    st.warning("👆 Tap 'Select Book & Chapter' above to enter your Groq API Key.")
    st.stop()

# --- DISPLAY VINTAGE CARDS & STUDY NOTES ---
for item in st.session_state.history:
    st.markdown(f"""
    <div class="vintage-card">
        <div class="vintage-label">SCRIPTURE READING</div>
        <div class="vintage-verse-text">{item['html_text']}</div>
        <div class="vintage-ref">{selected_book_name.upper()} {selected_chapter_num}:{item['range']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="insight-card">
        <div class="vintage-label" style="margin-bottom: 6px;">STUDY NOTES & INSIGHTS</div>
    """, unsafe_allow_html=True)
    st.markdown(item['insight'])
    st.markdown("</div>", unsafe_allow_html=True)

# --- NEXT SECTION BUTTON ---
if st.session_state.current_chunk < total_chunks:
    idx = st.session_state.current_chunk
    current_verses = chunks[idx]
    start_v = (idx * chunk_size) + 1
    end_v = start_v + len(current_verses) - 1
    v_range = f"{start_v}–{end_v}"
    
    plain_text = " ".join([f"({start_v + i}) {v}" for i, v in enumerate(current_verses)])
    html_text = " ".join([f"<span class='vintage-verse-num'>{start_v + i}</span>{v}" for i, v in enumerate(current_verses)])
    
    if st.button(f"Read Verses {v_range}  →", use_container_width=True):
        with st.spinner("Unpacking the themes of this passage..."):
            prev_summary = " | ".join([f"Verses {h['range']}: {h.get('plain_text', '')}" for h in st.session_state.history[-2:]])
            insight = get_llama_insight(selected_book_name, selected_chapter_num, v_range, plain_text, prev_summary)
            
            st.session_state.history.append({
                "range": v_range,
                "plain_text": plain_text,
                "html_text": html_text,
                "insight": insight
            })
            st.session_state.current_chunk += 1
            st.rerun()

# --- END OF CHAPTER: BIG PICTURE SUMMARY + PRAYER & APPLICATION ---
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
