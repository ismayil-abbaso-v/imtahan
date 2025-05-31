
import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Test Qarışdırıcı və İmtahan Rejimi", page_icon="📄")

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

menu = st.sidebar.radio("Seçim et:", ["📤 Variantları Qarışdır", "📝 İmtahan Rejimi"])

if menu == "📝 İmtahan Rejimi":
    st.title("📝 Öz İmtahanını Yoxla")
    uploaded_file = st.file_uploader("📤 Word (.docx) faylını yüklə", type="docx")
    mode = st.radio("📌 Rejim seç:", ["50 random sual", "Bütün suallar"], index=0)

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if not questions:
            st.error("Sual tapılmadı.")
        else:
            if mode == "50 random sual":
                questions = random.sample(questions, min(50, len(questions)))
            else:
                toplam = len(questions)
                col1, col2 = st.columns(2)
                with col1:
                    start = st.number_input("İlk sual №", 1, toplam, value=1, step=1)
                with col2:
                    end = st.number_input("Son sual №", start, toplam, value=min(start+49, toplam), step=1)
                questions = questions[start-1:end]  # ardıcıl aralıq

            if "started" not in st.session_state:
                st.session_state.started = False
                st.session_state.questions = questions
                st.session_state.current = 0
                st.session_state.answers = []
                st.session_state.correct_answers = []
                st.session_state.start_time = None
                st.session_state.timer_expired = False

            if not st.session_state.started:
                if st.button("🚀 İmtahana Başla"):
                    st.session_state.started = True
                    st.session_state.start_time = datetime.now()
                    st.rerun()

            elif st.session_state.started:
                now = datetime.now()
                time_left = timedelta(minutes=60) - (now - st.session_state.start_time)
                if time_left.total_seconds() <= 0:
                    st.session_state.timer_expired = True

                if st.session_state.timer_expired:
                    st.warning("⏰ Vaxt bitdi! İmtahan başa çatdı.")
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

                    st.markdown(f"**{idx+1}) {qtext}**")
                    selected = st.radio("Variant seç:", shuffled, key=f"answer_{idx}")

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
                    st.success("✅ İmtahan bitdi!")
                    score = sum(1 for a, b in zip(st.session_state.answers, st.session_state.correct_answers) if a == b)
                    st.markdown(f"### Nəticə: {score}/{len(st.session_state.questions)} doğru cavab ✅")

                    with st.expander("📋 Detallı nəticə"):
                        for i, (ua, ca, q) in enumerate(zip(st.session_state.answers, st.session_state.correct_answers, st.session_state.questions)):
                            status = "✅ Düzgün" if ua == ca else "❌ Səhv"
                            st.markdown(f"**{i+1}) {q[0]}**\nSənin cavabın: `{ua}` — Doğru: `{ca}` → {status}")

                    if st.button("🔁 Yenidən başla"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
