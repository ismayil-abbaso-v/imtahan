import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="İmtahan Hazırlayıcı", page_icon="📝")

# Fayldan sualları oxuma funksiyası
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
            # Əsas düzgünlük: sualın cavab variantları 5 olmalıdır (1 doğru + 4 yanlış)
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
        shuffled_options = options[:]
        random.shuffle(shuffled_options)

        for j, option in enumerate(shuffled_options):
            letter = chr(ord('A') + j)
            new_doc.add_paragraph(f"{letter}) {option}")
            if option.strip() == correct_answer.strip():
                answer_key.append(f"{idx}) {letter}")
    return new_doc, answer_key

# Sessiya üçün default dəyərlər
if "page" not in st.session_state:
    st.session_state.page = "home"

# Ana səhifə
if st.session_state.page == "home":
    st.title("📝 Testləri Qarışdır və Biliklərini Yoxla!")
    st.markdown("Zəhmət olmasa bir rejim seçin:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Özünü imtahan et"):
            st.session_state.page = "exam"
            st.experimental_rerun()
    with col2:
        if st.button("🎲 Sualları Qarışdır"):
            st.session_state.page = "shuffle"
            st.experimental_rerun()

else:
    # Sidebar Menyu
    st.sidebar.title("🔧 Menyu")
    if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "home"
        st.experimental_rerun()

    menu = st.sidebar.radio(
        "➡️ Rejimi dəyiş:",
        ["🎲 Sualları Qarışdır", "📝 Özünü İmtahan Et"],
        index=0 if st.session_state.page == "shuffle" else 1
    )
    st.session_state.page = "shuffle" if menu == "🎲 Sualları Qarışdır" else "exam"

    # Sualları Qarışdır rejimi
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

    # İmtahan rejimi
    elif st.session_state.page == "exam":
        st.title("📝 Özünü Sına: İmtahan Rejimi")
        uploaded_file = st.file_uploader("📤 İmtahan üçün Word (.docx) faylını seçin", type="docx")
        mode = st.radio("📌 Sual seçimi:", ["🔹 50 təsadüfi sual", "🔸 Bütün suallar"], index=0)

        if uploaded_file:
            questions = parse_docx(uploaded_file)
            if not questions:
                st.error("❗ Heç bir sual tapılmadı.")
            else:
                questions = random.sample(questions, min(50, len(questions))) if "50" in mode else questions

                # İmtahan sessiyasını ilk dəfə yaradanda
                if "started" not in st.session_state:
                    st.session_state.started = False
                    st.session_state.questions = questions
                    st.session_state.current = 0
                    st.session_state.answers = [None] * len(questions)  # Cavablar üçün None-dan ibarət siyahı
                    st.session_state.correct_answers = [opts[0] for _, opts in questions]
                    st.session_state.start_time = None
                    st.session_state.timer_expired = False

                if not st.session_state.started:
                    st.info("📌 60 dəqiqə vaxtınız olacaq. Hazırsınızsa başlayın!")
                    if st.button("🚀 Başla"):
                        st.session_state.started = True
                        st.session_state.start_time = datetime.now()
                        st.experimental_rerun()

                else:
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

                        # Variantları qarışdır və yadda saxla
                        if f"shuffled_{idx}" not in st.session_state:
                            shuffled = options[:]
                            random.shuffle(shuffled)
                            st.session_state[f"shuffled_{idx}"] = shuffled
                        else:
                            shuffled = st.session_state[f"shuffled_{idx}"]

                        st.progress((idx + 1) / total)
                        st.markdown(f"**{idx + 1}) {qtext}**")

                        # İstifadəçinin əvvəl seçdiyi cavabı əks etdir
                        default_answer = st.session_state.answers[idx]
                        selected = st.radio("📌 Cavab seçin:", shuffled, index=shuffled.index(default_answer) if default_answer in shuffled else 0, key=f"answer_{idx}")

                        # Cavabı yadda saxla
                        st.session_state.answers[idx] = selected

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("⬅️ Əvvəlki", disabled=idx == 0):
                                st.session_state.current -= 1
                                st.experimental_rerun()
                        with col2:
                            if st.button("🚩 Bitir"):
                                st.session_state.current = total
                                st.experimental_rerun()
                        with col3:
                            if st.button("➡️ Növbəti", disabled=selected is None):
                                if idx < total - 1:
                                    st.session_state.current += 1
                                else:
                                    st.session_state.current = total
                                st.experimental_rerun()

                    else:
                        # İmtahan tamamlanıb
                        score = sum(1 for ua, ca in zip(st.session_state.answers, st.session_state.correct_answers) if ua == ca)
                        total = len(st.session_state.questions)
                        percent = (score / total) * 100

                        st.success("🎉 İmtahan tamamlandı!")
                        st.markdown(f"### ✅ Nəticə: {score} düzgün cavab / {total} sual")
                        st.markdown(f"<p style='font-size:16px;'>📈 Doğruluq faizi: <strong>{percent:.2f}%</strong></p>", unsafe_allow_html=True)
                        st.progress(score / total)

                        with st.expander("📊 Detallı nəticələr"):
                            for i, (ua, ca, (qtext, _)) in enumerate(zip(st.session_state.answers, st.session_state.correct_answers, st.session_state.questions)):
                                status = "✅ Düzgün" if ua == ca else "❌ Səhv"
                                st.markdown(f"**{i + 1}) {qtext}**\n• Sənin cavabın: `{ua}`\n• Doğru cavab: `{ca}` → {status}")

                        if st.button("🔁 Yenidən Başla"):
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.session_state.page = "home"
                            st.experimental_rerun()
