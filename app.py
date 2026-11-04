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

h1, h2, h3 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    color: #2C221E !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

p, li, div {
    font-family: 'Inter', sans-serif;
    color: #4A3F35;
    line-height: 1.65;
}

.vintage-card {
    background: linear-gradient(135deg, #FBF6E9 0%, #F5DEC0 55%, #F2CFAA 100%);
    border-radius: 22px;
    padding: 30px 26px;
    margin: 22px 0 16px 0;
    border: 1px solid #E6D2B5;
    box-shadow: 0 8px 24px rgba(139, 98, 59, 0.08);
}

.vintage-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #8C735B;
    margin-bottom: 18px;
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
    margin-right: 3px;
}

.vintage-ref {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8C735B;
    font-weight: 500;
}

.insight-card {
    background-color: #FFFDF9;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 28px;
    border: 1px solid #EFE6D8;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.02);
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
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    opacity: 0.94 !important;
    transform: translateY(-1px);
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

# Pull API Key (strips any accidental whitespace)
raw_key = st.secrets.get("shanesapi", None)
api_key = raw_key.strip() if raw_key else None

# Auto-detect available Llama models from Groq
@st.cache_data
def get_available_models(_key):
    try:
        client = Groq(api_key=_key)
        models = client.models.list()
        # Filter out audio/whisper/guard models and prioritize Llama models
        chat_models = [
            m.id for m in models.data 
            if not any(x in m.id.lower() for x in ["whisper", "guard", "tts", "vision", "embed"])
        ]
        llama_models = [m for m in chat_models if "llama" in m.lower()]
        other_models = [m for m in chat_models if "llama" not in m.lower()]
        return sorted(llama_models, reverse=True) + sorted(other_models)
    except Exception:
        return ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]

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
    
    if api_key:
        available_models = get_available_models(api_key)
        selected_model = st.selectbox("AI Model", available_models, index=0)
    else:
        selected_model = "llama-3.1-8b-instant"
    
    if st.button("Begin / Reset Chapter", use_container_width=True):
        st.session_state.current_chunk = 0
        st.session_state.history = []
        st.session_state.prayer_generated = False
        st.rerun()

if "current_chunk" not in st.session_state:
    st.session_state.current_chunk = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "prayer_generated" not in st.session_state:
    st.session_state.prayer_generated = False

verses = selected_book['chapters'][selected_chapter_num - 1]
chunks = [verses[i:i + chunk_size] for i in range(0, len(verses), chunk_size)]
total_chunks = len(chunks)

# --- LLAMA (GROQ) HELPER FUNCTIONS ---
def get_llama_insight(book, chapter, verse_range, text, previous_context, model_id):
    client = Groq(api_key=api_key)
    prompt = f"""
    We are doing a step-by-step Bible study of {book} Chapter {chapter}.
    We are currently reading verses {verse_range}:
    "{text}"
    
    Previous sections covered so far: {previous_context if previous_context else "Beginning of the chapter."}
    
    Please provide:
    1. If this isn't the first section, 1 brief sentence tying this to what we just read.
    2. Explain the meaning of these verses in 3-4 short, warm, insightful bullet points (mentioning NASB phrasing/nuance where helpful).
    3. End with a bold 1-sentence 'Takeaway'.
    """
    completion = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are a warm, clear, and insightful Bible study teacher."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def get_prayer_and_application(book, chapter, full_chapter_text, model_id):
    client = Groq(api_key=api_key)
    prompt = f"""
    We just finished studying {book} Chapter {chapter}. 
    Full text: "{full_chapter_text}"
    
    How can I pray over this chapter and integrate it and apply it into my life?
    Break your response down into 3 main themes from the chapter. For each theme provide:
    - **The Heart Check** (A question to ask myself)
    - **How to Apply It** (A practical action for this week)
    - **How to Pray** (A short written prayer)
    
    End with a **Simple 1-Minute Morning Prayer** that ties the whole chapter together.
    """
    completion = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are a wise, practical Christian pastor helping someone apply Scripture to their daily life."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

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
        <div class="vintage-label" style="margin-bottom: 10px;">STUDY NOTES & INSIGHTS</div>
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
        with st.spinner("Reflecting on the passage..."):
            prev_summary = " | ".join([f"v.{h['range']}" for h in st.session_state.history])
            insight = get_llama_insight(selected_book_name, selected_chapter_num, v_range, plain_text, prev_summary, selected_model)
            
            st.session_state.history.append({
                "range": v_range,
                "html_text": html_text,
                "insight": insight
            })
            st.session_state.current_chunk += 1
            st.rerun()

# --- END OF CHAPTER: PRAYER & APPLICATION ---
else:
    st.markdown("<div style='text-align: center; margin: 20px 0; font-family: Cormorant Garamond, serif; font-size: 1.3rem; color: #6E4B2A;'>— Chapter Complete —</div>", unsafe_allow_html=True)
    
    if not st.session_state.prayer_generated:
        if st.button("🙏 Prayer & Life Application", use_container_width=True):
            with st.spinner("Preparing your prayer & application guide..."):
                full_text = " ".join(verses)
                prayer_guide = get_prayer_and_application(selected_book_name, selected_chapter_num, full_text, selected_model)
                st.session_state.prayer_guide = prayer_guide
                st.session_state.prayer_generated = True
                st.rerun()
                
    if st.session_state.prayer_generated:
        st.markdown("""
        <div class="vintage-card">
            <div class="vintage-label">DEVOTIONAL & PRAYER</div>
            <h2 style="margin-top: 0; margin-bottom: 10px;">Integrating the Word</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.prayer_guide)
        st.markdown('</div>', unsafe_allow_html=True)
