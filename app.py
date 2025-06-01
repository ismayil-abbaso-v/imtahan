import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="İmtahan Hazırlayıcı", page_icon="📝")

# 🔧 Fayldan test suallarını oxuma funksiyası
def full_text(paragraph):
    return ''.join(run.text for run in paragraph.runs).strip()

def parse_docx(file):
    doc = Document(file)
    question_pattern = re.compile(r"^\s*\d+[.)]\s+")
    option_pattern = re.compile(r"^\s*[A-Ea-e]\)\s+(.*)")

    paragraphs = list(doc.paragraphs)
    i = 0
    question_blocks = []

    while i < len(paragraphs):
        text = full_text(paragraphs[i])
        if question_pattern.match(text):
            question_text = question_pattern.sub('', text)
            i += 1
            options = []
            while i < len(paragraphs):
                text = full_text(paragraphs[i])
                match = option_pattern.match(text)
                if match:
                    options.append(match.group(1).strip())
                    i += 1
                elif text and not question_pattern.match(text) and len(options) < 5:
                    options.append(text)
                    i += 1
                else:
                    break
            if len(options) == 5:
                question_blocks.append((question_text, options))
        else:
            i += 1
    return question_blocks

def create_shuffled_docx_and_answers(questions):
    new_doc = Document()
    answer_key = []

    for idx, (question, options) in enumerate(questions, start=1):
        new_doc.add_paragraph(f"{idx}) {question}")
        correct_answer = options[0]
        random.shuffle(options)

        for j, option in enumerate(options):
            letter = chr(ord('A') + j)
            new_doc.add_paragraph(f"{letter}) {option}")
            if option.strip() == correct_answer.strip():
                answer_key.append(f"{idx}) {letter}")

    return new_doc, answer_key

# 🔧 Açıq sualları oxuma funksiyası
def parse_open_questions(file):
    doc = Document(file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    question_pattern = re.compile(r"^\s*\d+[.)]\s+")

    questions = []
    for p in paragraphs:
        if not question_pattern.match(p):
            questions.append(p)

    return questions

# 🌐 Sessiya idarəsi
if "page" not in st.session_state:
    st.session_state.page = "home"

# 🏠 Ana səhifə
if st.session_state.page == "home":
    st.title("📝 Testləri Qarışdır və Biliklərini Yoxla!")
    st.markdown("Zəhmət olmasa bir rejim seçin:")

    col1 = st.columns(1)
    with col1:
        if st.button("🎫 Bilet İmtahanı"):
            st.session_state.page = "ticket"
            st.rerun()

# 📋 Əsas menyu
else:
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.rerun()

    menu = st.sidebar.radio("➡️ Rejimi dəyiş:", ["🎫 Bilet İmtahanı"],
        index=["ticket"].index(st.session_state.page))
    st.session_state.page = {"🎫 Bilet İmtahanı": "ticket"}[menu]

# 🎫 Bilet İmtahanı (Yenilənmiş)
elif st.session_state.page == "ticket":
    st.title("🎫 Bilet İmtahanı (Açıq suallar)")
    uploaded_file = st.file_uploader("📤 Bilet sualları üçün Word (.docx) faylı seçin", type="docx")

    if uploaded_file:
        questions = parse_open_questions(uploaded_file)
        if len(questions) < 5:
            st.error("❗ Kifayət qədər sual yoxdur (minimum 5 tələb olunur).")
        else:
            if st.button("🆕 Yeni Bilet Yarat"):
                st.session_state.ticket_questions = random.sample(questions, 5)

            if "ticket_questions" not in st.session_state:
                st.session_state.ticket_questions = random.sample(questions, 5)

            st.success("✅ Hazır bilet sualları:")
            for i, q in enumerate(st.session_state.ticket_questions, 1):
                st.markdown(f"### {i}) {q}")

            st.info("📌 Bu suallar bilet formasında təqdim olunur. Cavabları ayrıca yazın.")
