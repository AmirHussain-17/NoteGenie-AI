# note_genie_ai.py
import os, re, json
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

APP_NAME = "NoteGenie AI"
TAGLINE_MD = "*Your study partner, that actually helps* <span style='font-style:normal;'>😉</span>"

st.set_page_config(page_title=APP_NAME, page_icon="📄", layout="centered")
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------- UI Theme --------------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
  background-color: #F7FAF8 !important;
  background-image: url("https://www.transparenttextures.com/patterns/paper-fibers.png") !important;
  background-size: 350px !important;
  background-repeat: repeat !important;
}
.block-container { background-color: rgba(255,255,255,0) !important; }

section[data-testid="stSidebar"] > div {
  background-color: #E9FBF3 !important;
  background-image: url("https://www.transparenttextures.com/patterns/paper.png") !important;
  border-right: 1px solid #C7E9D8 !important;
}

.card {
  background: rgba(255,255,255,0.75);
  border: 2px solid #D5EDE3;
  border-radius: 18px;
  padding: 1.25rem 1.4rem;
  margin: 1rem 0;
  box-shadow: 0px 4px 12px rgba(120,190,165,0.35);
  backdrop-filter: blur(6px);
}

.stButton>button, .stDownloadButton>button {
  background: linear-gradient(90deg, #A9E9D5, #7FDCC0);
  color: #083729 !important;
  border-radius: 12px !important;
  padding: 0.7rem 1.2rem !important;
  font-weight: 700 !important;
  border: none !important;
  box-shadow: 0px 4px 10px rgba(110,190,160,0.5);
  transition: 0.2s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover { scale: 1.05; }

.genie_bubble {
  background: #E5FFF4;
  border: 2px solid #A8E4D0;
  border-radius: 14px;
  padding: 1rem 1.2rem;
  margin-top: .7rem;
  font-size: 1.05rem;
  box-shadow: 0 3px 10px rgba(120,190,160,0.25);
  animation: fadein 0.6s ease;
}

@keyframes fadein {
  from {opacity: 0; transform: translateY(6px);}
  to {opacity: 1; transform: translateY(0);}
}

.user_bubble {
  background: #FFFFFF;
  border: 2px solid #CDEEE0;
  border-radius: 14px;
  padding: 1rem 1.2rem;
  margin-top: .7rem;
  font-size: 1.05rem;
  box-shadow: 0 3px 10px rgba(150,200,180,0.25);
}
            /* Chat Input Box */
[data-testid="stTextInput"] > div > div > input {
  background: #FFFFFF !important;
  border: 2px solid #A8E4D0 !important;
  border-radius: 12px !important;
  padding: 10px !important;
  font-size: 1.05rem !important;
  color: #083729 !important;
  box-shadow: 0px 3px 8px rgba(140, 210, 180, 0.35) !important;
}

[data-testid="stTextInput"] > div > div > input:focus {
  border: 2px solid #6CD6B7 !important;
  outline: none !important;
}

            /* Make chat input background slightly tinted */
[data-testid="stTextInput"] > div > div > input {
  background: #FFFFFF !important;
  border: 2.5px solid #8FDCC9 !important;
  border-radius: 14px !important;
  padding: 12px !important;
  font-size: 1.08rem !important;
  color: #083729 !important;
}


</style>
""", unsafe_allow_html=True)


# -------------------------- Helpers --------------------------
def read_pdf_bytes(file):
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(file.read()))
    return "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()

def call_llm(prompt, temperature=0.25):
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=2800
    )
    return resp.choices[0].message.content.strip()

def call_llm_json(prompt):
    raw = call_llm("Return ONLY JSON. No explanation.\n" + prompt)
    raw = re.sub(r"`+json|`+", "", raw)
    raw = raw[raw.find("{"): raw.rfind("}")+1]
    return json.loads(raw)


# -------------------------- Agents --------------------------
def summarizer_agent(text):
    return call_llm(f"""
Summarize clearly with:
- One-line **TL;DR**
- Bullet points
- Bold key terms
TEXT:
{text}
""")

def qa_quiz_agent_json(text, n):
    return call_llm_json(f"""
Return JSON:
{{"items":[{{"question":"...","answer":"..."}}]}}
Make EXACTLY {n} Q/A.
TEXT:{text}
""")

def mcq_quiz_agent_json(text, n):
    return call_llm_json(f"""
Return JSON:
{{"items":[{{"question":"...", "options":["A","B","C","D"], "answer_index":0}}]}}
Make EXACTLY {n} MCQ.
TEXT:{text}
""")

def explain_answer_agent(answer):
    return call_llm(f"""
Explain this in a soft, gentle, cute tone.

Style guidelines:
- Speak calmly.
- No hard words.
- Be emotionally supportive.
- Use very small sentences.
- Sometimes add a soft comforting emoji like 🌸 or 🍃, but not too many.
- Sound like a kind friend helping.

ANSWER TO EXPLAIN:
{answer}
""")



def make_flashcards(text, n):
    data = qa_quiz_agent_json(text, n)
    return data["items"][:n]


# -------------------------- Header --------------------------
col1, col2 = st.columns([1,6])
with col1:
    st.image("genie.png", width=80)
with col2:
    st.markdown(f"<h1 style='margin-bottom:-10px;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    st.write(TAGLINE_MD, unsafe_allow_html=True)
st.markdown("---")

# ✅ Welcome Notice for Users
st.info(
    """
**Notice**  
This application works best with clean, text-based PDF documents or typed notes.  
If the file contains heavy design elements, scanned pages, or stylized formatting, the output quality may vary.

**For Android Users:**  
Use the menu button (☰) in the top-left corner to switch between features such as Summary, Q/A Quiz, MCQ Quiz, and Chat with Genie.
"""
)




# -------------------------- Sidebar --------------------------
with st.sidebar:
    mode = st.radio("Mode:", ["Summary", "Q/A Quiz", "MCQ Quiz", "Chat with Genie"])

    num_q = st.selectbox("Number of Questions", [5, 10, 15, 20])


uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
pasted_text = st.text_area("Or paste text:", height=150)

generate_clicked = st.button("Generate 🚀")

if generate_clicked:
    st.session_state.text_data = pasted_text.strip() if pasted_text.strip() else read_pdf_bytes(uploaded_pdf)


# -------------------------- Modes --------------------------
if "text_data" not in st.session_state:
    st.stop()  # Wait until user generates


# SUMMARY
if mode == "Summary":
    out = summarizer_agent(st.session_state.text_data)
    st.markdown("### 📝 Summary")
    st.markdown(out)


# Q/A QUIZ WITH EXPLAIN
elif mode == "Q/A Quiz":
    if "qa_quiz" not in st.session_state or generate_clicked:
        st.session_state.qa_quiz = qa_quiz_agent_json(st.session_state.text_data, num_q)["items"]
        st.session_state.explanations = {}

    qa = st.session_state.qa_quiz
    st.markdown("### 🧠 Q/A Quiz")

    for i, qa_item in enumerate(qa, 1):
        st.markdown(f"<div class='card'><h4>Q{i}. {qa_item['question']}</h4><p><b>Answer:</b> {qa_item['answer']}</p></div>", unsafe_allow_html=True)

        if st.button(f"✨ Explain with Genie (Q{i})", key=f"exp_{i}"):
            st.session_state.explanations[i] = explain_answer_agent(qa_item["answer"])

        if i in st.session_state.explanations:
            st.markdown(f"""
            <div class="genie_bubble">
            <strong>🧞‍♂️ Genie:</strong> <span style="opacity:0.85;">(soft & gentle)</span><br><br>
            {st.session_state.explanations[i]} ✨
            </div>
            """, unsafe_allow_html=True)




# MCQ
elif mode == "MCQ Quiz":
    mcq = mcq_quiz_agent_json(st.session_state.text_data, num_q)["items"]
    st.markdown("### 🎯 MCQ Quiz")
    for i, q in enumerate(mcq,1):
        st.markdown(f"<div class='card'><b>Q{i}.</b> {q['question']}<br><br>" +
                    "<br>".join([f"{chr(65+j)}) {opt}" for j,opt in enumerate(q['options'])]) +
                    f"<br><br><b>Correct Answer:</b> {chr(65+q['answer_index'])}) {q['options'][q['answer_index']]}</div>",
                    unsafe_allow_html=True)



# CHAT WITH GENIE (Persistent conversation)
elif mode == "Chat with Genie":
    st.markdown("### 💬 Chat with Your Genie")

    # Initialize chat history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat Input Label (nice & visible)
    st.markdown("<p style='font-size:1.05rem; font-weight:600; color:#0a3d30;'>Type your message 🌿</p>", unsafe_allow_html=True)

    # Chat Input Box
    user_q = st.text_input("", placeholder="Ask anything... ✨")

    # Send Button
    if st.button("Send ✨"):
        if user_q.strip():
            # Add user message
            st.session_state.chat_history.append(("You", user_q))

            # Genie generates soft explanation reply
            reply = explain_answer_agent(user_q)
            st.session_state.chat_history.append(("Genie", reply))

    # Display conversation history
    for sender, msg in st.session_state.chat_history:
        if sender == "You":
            st.markdown(f"""
            <div class="user_bubble">
            <strong>You:</strong> {msg}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="genie_bubble">
            <strong>🧞‍♂️ Genie:</strong> {msg} ✨
            </div>
            """, unsafe_allow_html=True)


# Genie Soft Welcome Message Bar
st.markdown("""
<div style="
    background: #E9FBF3;
    border-radius: 14px;
    border: 1.5px solid #C7E9D8;
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0 1.4rem 0;
    font-size: 1.1rem;
">
🧞‍♂️ <strong>Genie:</strong> Welcome Back!    I'm happy to study with you together. 🍃
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Made with love for students 🍃")
