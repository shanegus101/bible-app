import streamlit as st
import requests
import json
import os
from groq import Groq

st.set_page_config(page_title="Llama Bible Study", page_icon="🦙", layout="centered")
st.title("🦙📖 Bible Study")

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

# Automatically pulls your key named 'shanesapi' from Streamlit Secrets
api_key = st.secrets.get("shanesapi", None)

with st.expander("⚙️ Choose Book & Chapter", expanded=False):
    if not api_key:
        api_key = st.text_input("Enter Groq API Key:", type="password")
        
    book_names = [book['name'] for book in bible_data]
    selected_book_name = st.selectbox("Select Book", book_names, index=39)
    
    selected_book = next(b for b in bible_data if b['name'] == selected_book_name)
    num_chapters = len(selected_book['chapters'])
    selected_chapter_num = st.selectbox("Select Chapter", range(1, num_chapters + 1), index=7)
    
    chunk_size = st.slider("Verses per section", min_value=3, max_value=10, value=5)
    
    if st.button("🔄 Start / Reset Chapter", use_container_width=True):
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

def get_llama_insight(book, chapter, verse_range, text, previous_context):
    client = Groq(api_key=api_key)
    prompt = f"""
    We are doing a step-by-step Bible study of {book} Chapter {chapter}.
    We are currently reading verses {verse_range}:
    "{text}"
    
    Previous sections covered so far: {previous_context if previous_context else "Beginning of the chapter."}
    
    Please provide:
    1. If this isn't the first section, 1 sentence tying this to what we just read.
    2. Explain the meaning of these verses in 3-4 short, punchy bullet points (include NASB phrasing/nuance where helpful).
    3. A 1-sentence 'Takeaway' at the end.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a warm, clear, and insightful Bible study teacher."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def get_prayer_and_application(book, chapter, full_chapter_text):
    client = Groq(api_key=api_key)
    prompt = f"""
    We just finished studying {book} Chapter {chapter}. 
    Full text: "{full_chapter_text}"
    
    How can I pray over this chapter and integrate it and apply it into my life?
    Break your response down into 3 main themes from the chapter. For each theme provide:
    - **The Heart Check** (A question to ask myself)
    - **How to Apply It** (A practical action for this week)
    - **How to Pray** (A short written prayer)
    
    End with a **Simple 1-Minute Prayer to Start Your Day** that ties the whole chapter together.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a wise, practical Christian pastor helping someone apply Scripture to their daily life."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

st.subheader(f"📍 {selected_book_name} {selected_chapter_num}")

if not api_key:
    st.warning("👆 Tap 'Choose Book & Chapter' above to enter your Groq API Key.")
    st.stop()

for item in st.session_state.history:
    with st.container():
        st.markdown(f"### 📜 Verses {item['range']}")
        st.info(item['text'])
        st.markdown(item['insight'])
        st.divider()

if st.session_state.current_chunk < total_chunks:
    idx = st.session_state.current_chunk
    current_verses = chunks[idx]
    start_v = (idx * chunk_size) + 1
    end_v = start_v + len(current_verses) - 1
    v_range = f"{start_v}–{end_v}"
    
    formatted_text = " ".join([f"**({start_v + i})** {v}" for i, v in enumerate(current_verses)])
    
    if st.button(f"Read Verses {v_range} ➡️", type="primary", use_container_width=True):
        with st.spinner("Llama is studying the text..."):
            prev_summary = " | ".join([f"v.{h['range']}" for h in st.session_state.history])
            insight = get_llama_insight(selected_book_name, selected_chapter_num, v_range, formatted_text, prev_summary)
            
            st.session_state.history.append({
                "range": v_range,
                "text": formatted_text,
                "insight": insight
            })
            st.session_state.current_chunk += 1
            st.rerun()

else:
    st.success("🎉 Chapter Complete!")
    if not st.session_state.prayer_generated:
        if st.button("🙏 How can I pray & apply this?", type="primary", use_container_width=True):
            with st.spinner("Writing your prayer & application guide..."):
                full_text = " ".join(verses)
                prayer_guide = get_prayer_and_application(selected_book_name, selected_chapter_num, full_text)
                st.session_state.prayer_guide = prayer_guide
                st.session_state.prayer_generated = True
                st.rerun()
                
    if st.session_state.prayer_generated:
        st.markdown("## 🌱 Prayer & Life Application")
        st.markdown(st.session_state.prayer_guide)
