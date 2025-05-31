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

st.sidebar.title("🔧 Menyu")
menu = st.sidebar.radio("➡️ Rejim seçin:", ["🎲 Sualları Qarışdır", "📝 İmtahan Rejimi"])

if menu == "🎲 Sualları Qarışdır":
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

elif menu == "📝 İmtahan Rejimi":
    st.title("📝 Özünü Sına: İmtahan Rejimi")
    uploaded_file = st.file_uploader("📤 İmtahan üçün Word (.docx) faylını seçin", type="docx")
    mode = st.radio("📌 Sual seçimi:", ["🔹 50 təsadüfi sual", "🔸 Bütün suallar"], index=0)

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if not questions:
            st.error("❗ Heç bir sual tapılmadı.")
        else:
            if "50" in mode:
                questions = random.sample(questions, min(50, len(questions)))

            if "started" not in st.session_state:
                st.session_state.started = False
                st.session_state.questions = questions
                st.session_state.current = 0
                st.session_state.answers = [None] * len(questions) # cavablar None ilə başlanır
                st.session_state.correct_answers = []
                st.session_state.start_time = None
                st.session_state.timer_expired = False

            if not st.session_state.started:
                st.info("📌 60 dəqiqə vaxtınız olacaq. Hazırsınızsa başlayın!")
                if st.button("🚀 Başla"):
                    st.session_state.started = True
                    st.session_state.start_time = datetime.now()
                    st.experimental_rerun()

            elif st.session_state.started:
                now = datetime.now()
                time_left = timedelta(minutes=60) - (now - st.session_state.start_time)
                if time_left.total_seconds() <= 0:
                    st.session_state.timer_expired = True

                if st.session_state.timer_expired:
                    st.warning("⏰ Vaxt bitdi! İmtahan sona çatdı.")
                    st.session_state.current = len(st.session_state.questions)
                else:
                    mins, secs = divmod(int(time_left.total_seconds()), 60)
                    st.info(f"⏳ Qalan vaxt: {mins} dəq {secs} san")

                idx = st.session_state.current
                if idx < len(st.session_state.questions):
                    qtext, options = st.session_state.questions[idx]
                    correct = options[0]
                    if f"shuffled_{idx}" not in st.session_state:
                        shuffled = options[:]
                        random.shuffle(shuffled)
                        st.session_state[f"shuffled_{idx}"] = shuffled
                    else:
                        shuffled = st.session_state[f"shuffled_{idx}"]

                    # Selectbox üçün variantlar: ilk element "Cavab verilməyib"
                    select_options = ["Cavab verilməyib"] + shuffled

                    prev_answer = st.session_state.answers[idx]
                    if prev_answer is None:
                        default_index = 0
                    else:
                        try:
                            default_index = select_options.index(prev_answer)
                        except ValueError:
                            default_index = 0

                    chosen = st.selectbox(f"**{idx+1}) {qtext}**", select_options, index=default_index, key=f"answer_{idx}")

                    # "Cavab verilməyib" seçilsə None kimi saxla
                    if chosen == "Cavab verilməyib":
                        st.session_state.answers[idx] = None
                    else:
                        st.session_state.answers[idx] = chosen

                    st.session_state.correct_answers = [q[1][0] for q in st.session_state.questions]

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("⬅️ Əvvəlki", disabled=idx == 0):
                            st.session_state.current -= 1
                            st.experimental_rerun()
                    with col2:
                        if st.button("🚩 Bitir"):
                            st.session_state.current = len(st.session_state.questions)
                            st.experimental_rerun()
                    with col3:
                        if st.button("➡️ Növbəti"):
                            st.session_state.current += 1
                            st.experimental_rerun()

                else:
                    st.success("🎉 İmtahan tamamlandı!")
                    score = sum(
                        1
                        for user_ans, correct_ans in zip(st.session_state.answers, st.session_state.correct_answers)
                        if user_ans is not None and user_ans == correct_ans
                    )
                    total = len(st.session_state.questions)
                    percent = round((score / total) * 100, 2) if total else 0
                    st.write(f"✅ Düzgün cavablar: {score} / {total}")
                    st.write(f"📊 Doğruluq faizi: {percent}%")