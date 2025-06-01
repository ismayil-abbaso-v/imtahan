import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="İmtahan Hazırlayıcı", page_icon="📝")

# 🔧 Paragraphdan tam mətn çək
def full_text(paragraph):
    return ''.join(run.text for run in paragraph.runs).strip()

# 🔧 Test suallarını oxu
def parse_docx(file):
    doc = Document(file)
    question_pattern = re.compile(r"^\s*\d+[\.\)]\s+")
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

# 🔧 Yazılı açıq sualları oxu
def extract_open_questions(docx_file):
    doc = Document(docx_file)
    pattern = re.compile(r"^\s*\d+[\.\)]\s+(.*)")
    questions = []
    for para in doc.paragraphs:
        match = pattern.match(para.text.strip())
        if match:
            questions.append(match.group(1).strip())
    return questions

# 🔧 Sualları qarışdır və cavab açarı yarat
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

# 📍 Sessiya idarəsi
if "page" not in st.session_state:
    st.session_state.page = "home"

# 🏠 Ana səhifə
if st.session_state.page == "home":
    st.title("📝 Testləri Qarışdır və Bilet İmtahanı Et")
    st.markdown("Rejim seçin:")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎲 Sualları Qarışdır"):
            st.session_state.page = "shuffle"
            st.experimental_rerun()
    with col2:
        if st.button("📝 Özünü İmtahan Et"):
            st.session_state.page = "exam"
            st.experimental_rerun()
    with col3:
        if st.button("🎫 Bilet İmtahanı"):
            st.session_state.page = "ticket"
            st.experimental_rerun()

# 🔙 Yan menyu
else:
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifə"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.experimental_rerun()

    menu = st.sidebar.radio("Rejimi dəyiş:", ["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et", "🎫 Bilet İmtahanı"],
                            index=["shuffle", "exam", "ticket"].index(st.session_state.page))
    st.session_state.page = ["shuffle", "exam", "ticket"][["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et", "🎫 Bilet İmtahanı"].index(menu)]

    # 1️⃣ Qarışdır rejimi
    if st.session_state.page == "shuffle":
        st.title("🎲 Test Suallarını Qarışdır")
        uploaded_file = st.file_uploader("📤 Word (.docx) sənədini yüklə", type="docx")
        mode = st.radio("💡 Sual sayı:", ["🔹 50 təsadüfi", "🔸 Hamısı"], index=0)

        if uploaded_file:
            questions = parse_docx(uploaded_file)
            if len(questions) < 5:
                st.error("❗ Uyğun sual tapılmadı.")
            else:
                selected = random.sample(questions, min(50, len(questions))) if "50" in mode else questions
                new_doc, answer_key = create_shuffled_docx_and_answers(selected)

                output_docx = BytesIO()
                new_doc.save(output_docx)
                output_docx.seek(0)

                output_answers = BytesIO()
                output_answers.write('\n'.join(answer_key).encode('utf-8'))
                output_answers.seek(0)

                st.success("✅ Sənədlər hazırdır!")
                st.download_button("📥 Qarışdırılmış Suallar", output_docx, "qarisdirilmis_suallar.docx")
                st.download_button("📥 Cavab Açarı", output_answers, "cavab_acari.txt")

    # 2️⃣ Test İmtahanı
    elif st.session_state.page == "exam":
        st.title("📝 Özünü İmtahan Et")
        # Buraya test imtahan hissəsi əlavə edilə bilər

    # 3️⃣ Bilet İmtahanı
    elif st.session_state.page == "ticket":
        st.title("🎫 Bilet İmtahanı (Açıq Suallar)")
        uploaded_file = st.file_uploader("📤 Word (.docx) faylını yüklə", type="docx")

        if uploaded_file:
            all_questions = extract_open_questions(uploaded_file)

            if len(all_questions) < 5:
                st.error("❗ Kifayət qədər sual yoxdur.")
            else:
                if "ticket_questions" not in st.session_state:
                    st.session_state.ticket_questions = random.sample(all_questions, 5)

                st.markdown("### 📄 Sizin Bilet:")
                for i, q in enumerate(st.session_state.ticket_questions, start=1):
                    st.markdown(f"**{i}) {q}**")

                if st.button("🔁 Yeni Bilet"):
                    del st.session_state["ticket_questions"]
                    st.experimental_rerun()
