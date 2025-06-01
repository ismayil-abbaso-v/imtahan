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

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Özünü imtahan et"):
            st.session_state.page = "exam"
            st.experimental_rerun()
    with col2:
        if st.button("🎲 Sualları Qarışdır"):
            st.session_state.page = "shuffle"
            st.experimental_rerun()
    with col3:
        if st.button("🎫 Bilet İmtahanı"):
            st.session_state.page = "ticket"
            st.experimental_rerun()

# 📋 Əsas menyu (sidebar)
elif st.session_state.page != "home":
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.experimental_rerun()

    if st.sidebar.button("🎲 Sualları Qarışdır"):
        st.session_state.page = "shuffle"
        st.experimental_rerun()

    if st.sidebar.button("📝 Özünü İmtahan Et"):
        st.session_state.page = "exam"
        st.experimental_rerun()

    if st.sidebar.button("🎫 Bilet İmtahanı"):
        st.session_state.page = "ticket"
        st.experimental_rerun()

# 🎲 Sualları qarışdır
if st.session_state.page == "shuffle":
    st.title("🎲 Test Suallarını Qarışdır və Cavab Açarı Yarat")
    uploaded_file = st.file_uploader("📤 Word (.docx) sənədini seçin", type="docx")
    mode = st.radio("💡 Sualların sayı:", ["🔹 50 təsadüfi sual", "🔸 Bütün suallar"], index=0)

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if len(questions) < 5:
            st.error("❗ Faylda kifayət qədər uyğun sual tapılmadı.")
        else:
            selected = random.sample(questions, min(50, len(questions))) if "50" in mode else questions
            new_doc, answer_key = create_shuffled_docx_and_answers(selected)

            output_docx = BytesIO()
            new_doc.save(output_docx)
            output_docx.seek(0)

            output_answers = BytesIO()
            output_answers.write('\n'.join(answer_key).encode('utf-8'))
            output_answers.seek(0)

            st.success("✅ Qarışdırılmış sənədlər hazırdır!")
            st.download_button("📥 Qarışdırılmış Suallar (.docx)", output_docx, "qarisdirilmis_suallar.docx")
            st.download_button("📥 Cavab Açarı (.txt)", output_answers, "cavab_acari.txt")

# 📝 Özünü imtahan et
elif st.session_state.page == "exam":
    st.title("📝 Özünü Sına: İmtahan Rejimi")
    uploaded_file = st.file_uploader("📤 Test sualları üçün Word (.docx) faylı seçin", type="docx")
    
    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if len(questions) < 5:
            st.error("❗ Faylda kifayət qədər sual tapılmadı.")
        else:
            num_questions = st.slider("Neçə sual cavablandırmaq istəyirsiniz?", 5, min(50, len(questions)), 10)
            selected_questions = random.sample(questions, num_questions)
            score = 0

            st.write("Suallara cavab verin:")
            user_answers = []
            for i, (question, options) in enumerate(selected_questions, 1):
                st.markdown(f"**{i}) {question}**")
                choices = options.copy()
                random.shuffle(choices)
                ans = st.radio(f"Cavab {i}:", choices, key=f"exam_q_{i}")
                user_answers.append((question, options, ans))

            if st.button("Nəticəni Yoxla"):
                score = 0
                for q, opts, user_ans in user_answers:
                    correct_ans = opts[0]
                    if user_ans.strip() == correct_ans.strip():
                        score += 1
                st.success(f"📝 Sənin nəticən: {score} / {num_questions}")

# 🎫 Bilet İmtahanı (Açıq suallar)
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
