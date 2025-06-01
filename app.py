import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="İmtahan Hazırlayıcı", page_icon="📝")

def full_text(paragraph):
    return ''.join(run.text for run in paragraph.runs).strip()

def parse_docx(file):
    doc = Document(file)
    question_pattern = re.compile(r"^\s*\d+[.)]\s+")
    option_pattern = re.compile(r"^\s*[A-Ea-e])\s+(.*)")
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

# ✅ Yeni: Sadə açıq sualları oxumaq üçün funksiya
def parse_open_questions(file):
    doc = Document(file)
    open_questions = []
    question_pattern = re.compile(r"^\s*\d+[.)]?\s+(.*)")
    for para in doc.paragraphs:
        text = full_text(para)
        match = question_pattern.match(text)
        if match:
            question_text = match.group(1).strip()
            open_questions.append(question_text)
    return open_questions

# Sessiya idarəetməsi
if "page" not in st.session_state:
    st.session_state.page = "home"

# 🏠 Ana səhifə
if st.session_state.page == "home":
    st.title("📝 Testləri Qarışdır və Biliklərini Yoxla!")
    st.markdown("Zəhmət olmasa bir rejim seçin:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Özünü imtahan et "):
            st.session_state.page = "exam"
            st.rerun()
    with col2:
        if st.button("🎲 Sualları Qarışdır"):
            st.session_state.page = "shuffle"
            st.rerun()
    with col3:
        if st.button("🎫 Bilet İmtahanı"):
            st.session_state.page = "ticket"
            st.rerun()

# Sol menyu və funksional səhifələr
else:
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.rerun()

    menu = st.sidebar.radio("➡️ Rejimi dəyiş:", ["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et", "🎫 Bilet İmtahanı"],
                            index=["shuffle", "exam", "ticket"].index(st.session_state.page))

    st.session_state.page = ["shuffle", "exam", "ticket"][["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et", "🎫 Bilet İmtahanı"].index(menu)]

    # Mövcud funksiyalar (qarışdır və imtahan) burda qalır...

    # ✅ 3️⃣ Bilet İmtahanı
    if st.session_state.page == "ticket":
        st.title("🎫 Bilet İmtahanı Rejimi")
        uploaded_file = st.file_uploader("📤 Word (.docx) bilet suallarını yüklə", type="docx")
        if uploaded_file:
            questions = parse_open_questions(uploaded_file)
            if len(questions) < 5:
                st.error("❗ Kifayət qədər uyğun sual tapılmadı.")
            else:
                if "ticket_questions" not in st.session_state or st.button("🔄 Bileti Dəyiş"):
                    st.session_state.ticket_questions = random.sample(questions, 5)

                if st.button("🎫 Bileti Seç"):
                    st.session_state.show_ticket = True

                if st.session_state.get("show_ticket", False):
                    st.subheader("📋 Sizin Bilet:")
                    for i, q in enumerate(st.session_state.ticket_questions, start=1):
                        st.markdown(f"**{i}) {q}**")
