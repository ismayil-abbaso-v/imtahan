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

# ✅ Bilet üçün açıq sualları oxuma funksiyası (sənədin ilk nömrəli sətrindən başlayır)
def parse_open_questions(file):
    doc = Document(file)
    open_questions = []
    found_start = False
    number_like = re.compile(r"^\s*\d+[\.\)]?\s*")

    for para in doc.paragraphs:
        text = full_text(para).strip()
        if not text:
            continue
        if not found_start and number_like.match(text):
            found_start = True
        if found_start:
            open_questions.append(text)
    return open_questions

# Sessiya vəziyyəti
if "page" not in st.session_state:
    st.session_state.page = "home"

# Ana səhifə
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

# Yan menyu və səhifə keçidi
else:
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.rerun()

    menu = st.sidebar.radio("➡️ Rejimi dəyiş:", ["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et", "🎫 Bilet İmtahanı"])
    selected_page = {
        "🎲 Sualları Qarışdır": "shuffle",
        "📝 Özünü İmtahan Et": "exam",
        "🎫 Bilet İmtahanı": "ticket"
    }[menu]

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

    # 1️⃣ Sualları qarışdır
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

    # 2️⃣ İmtahan rejimi
    elif st.session_state.page == "exam":
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
                    st.session_state.answers = []
                    st.session_state.correct_answers = []
                    st.session_state.start_time = None
                    st.session_state.timer_expired = False

                if not st.session_state.started:
                    st.info("📌 60 dəqiqə vaxtınız olacaq. Hazırsınızsa başlayın!")
                    if st.button("🚀 Başla"):
                        st.session_state.started = True
                        st.session_state.start_time = datetime.now()
                        st.rerun()

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
                    total = len(st.session_state.questions)
                    if idx < total:
                        qtext, options = st.session_state.questions[idx]
                        correct = options[0]
                        if f"shuffled_{idx}" not in st.session_state:
                            shuffled = options[:]
                            random.shuffle(shuffled)
                            st.session_state[f"shuffled_{idx}"] = shuffled
                        else:
                            shuffled = st.session_state[f"shuffled_{idx}"]

                        st.progress((idx / total))
                        st.markdown(f"**{idx+1}) {qtext}**")
                        selected = st.radio("📌 Cavab seçin:", shuffled, key=f"answer_{idx}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("⬅️ Əvvəlki", disabled=idx == 0):
                                st.session_state.current -= 1
                                st.rerun()
                        with col2:
                            if st.button("🚩 Bitir"):
                                st.session_state.current = len(st.session_state.questions)
                                st.rerun()
                        with col3:
                            if st.button("➡️ Növbəti", disabled=(selected is None)):
                                if len(st.session_state.answers) <= idx:
                                    st.session_state.answers.append(selected)
                                    st.session_state.correct_answers.append(correct)
                                else:
                                    st.session_state.answers[idx] = selected
                                    st.session_state.correct_answers[idx] = correct
                                st.session_state.current += 1
                                st.rerun()
                    else:
                        st.success("🎉 İmtahan tamamlandı!")
                        score = sum(1 for a, b in zip(st.session_state.answers, st.session_state.correct_answers) if a == b)
                        percent = (score / total) * 100
                        st.markdown(f"### ✅ Nəticə: {score} düzgün cavab / {total} sual")
                        st.markdown(f"<p style='font-size:16px;'>📈 Doğruluq faizi: <strong>{percent:.2f}%</strong></p>", unsafe_allow_html=True)
                        st.progress(score / total)

                        with st.expander("📊 Detallı nəticələr"):
                            for i, (ua, ca, q) in enumerate(zip(st.session_state.answers, st.session_state.correct_answers, st.session_state.questions)):
                                status = "✅ Düzgün" if ua == ca else "❌ Səhv"
                                st.markdown(f"**{i+1}) {q[0]}**\n• Sənin cavabın: `{ua}`\n• Doğru cavab: `{ca}` → {status}")

                        if st.button("🔁 Yenidən Başla"):
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.session_state.page = "home"
                            st.rerun()

    # 3️⃣ 🎫 Bilet İmtahanı
    elif st.session_state.page == "ticket":
        st.title("🎫 Bilet İmtahanı Rejimi")
        uploaded_file = st.file_uploader("📤 Word (.docx) bilet suallarını yüklə", type="docx")
        if uploaded_file:
            questions = parse_open_questions(uploaded_file)
            if len(questions) < 5:
                st.error("❗ Kifayət qədər uyğun sual tapılmadı.")
            else:
                if "ticket_questions" not in st.session_state or st.button("🔄 Bileti Dəyiş"):
                    st.session_state.ticket_questions = random.sample(questions, 5)
                    st.session_state.show_ticket = False
                if st.button("🎫 Bileti Seç"):
                    st.session_state.show_ticket = True
                if st.session_state.get("show_ticket", False):
                    st.subheader("📋 Sizin Bilet:")
                    for i, q in enumerate(st.session_state.ticket_questions, start=1):
                        st.markdown(f"**{i}) {q}**")
