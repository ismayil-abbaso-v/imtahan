import streamlit as st import re import random from docx import Document from io import BytesIO from datetime import datetime, timedelta

st.set_page_config(page_title="Test Qarışdırıcı və İmtahan Rejimi", page_icon="📄")

--- Fayldan sualları oxuma funksiyası ---

def parse_docx(file): doc = Document(file) question_pattern = re.compile(r"^\s*\d+[.)]\s+") option_pattern = re.compile(r"^\s*[A-Ea-e])\s+(.*)")

paragraphs = list(doc.paragraphs)
i = 0
question_blocks = []

while i < len(paragraphs):
    text = paragraphs[i].text.strip()
    if question_pattern.match(text):
        question_text = question_pattern.sub('', text)
        i += 1
        options = []
        while i < len(paragraphs):
            text = paragraphs[i].text.strip()
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

--- Qarışdırılmış sənəd və cavab siyahısı hazırlayan funksiyası ---

def create_shuffled_docx_and_answers(suallar): yeni_doc = Document() cavablar = []

for idx, (sual_metni, variantlar) in enumerate(suallar, start=1):
    yeni_doc.add_paragraph(f"{idx}) {sual_metni}")

    dogru_cavab_mətni = variantlar[0]
    random.shuffle(variantlar)

    for j, variant in enumerate(variantlar):
        herf = chr(ord('A') + j)
        yeni_doc.add_paragraph(f"{herf}) {variant}")
        if variant.strip() == dogru_cavab_mətni.strip():
            cavablar.append(f"{idx}) {herf}")

return yeni_doc, cavablar

--- Web App interfeysi ---

if menu == "📤 Sənəddən suallar çıxart (qarışdır + cavab)": st.title("📤 Sual Variantlarını Qarışdır") elif menu == "📝 Özünü imtahanda yoxla": st.title("📝 Öz İmtahanını Yoxla")

menu = st.sidebar.radio("Seçim et:", ["📤 Sənəddən suallar çıxart (qarışdır + cavab)", "📝 Özünü imtahanda yoxla"])

if menu == "📤 Sənəddən suallar çıxart (qarışdır + cavab)": uploaded_file = st.file_uploader("Word (.docx) sənədini seç", type="docx") mode = st.radio("Rejim seç:", ["50 sual", "Bütün suallar"], index=0)

if uploaded_file:
    suallar = parse_docx(uploaded_file)
    if len(suallar) < 5:
        st.error("Faylda kifayət qədər uyğun sual tapılmadı.")
    else:
        if mode == "50 sual":
            secilmis = random.sample(suallar, min(50, len(suallar)))
        else:
            secilmis = suallar

        yeni_doc, cavablar = create_shuffled_docx_and_answers(secilmis)

        output_docx = BytesIO()
        yeni_doc.save(output_docx)
        output_docx.seek(0)

        output_answers = BytesIO()
        output_answers.write('\n'.join(cavablar).encode('utf-8'))
        output_answers.seek(0)

        st.success("✅ Sənədlər hazırdır!")
        st.download_button("📥 Qarışdırılmış suallar (.docx)", data=output_docx, file_name="qarisdirilmis_suallar.docx")
        st.download_button("📥 Cavab açarı (.txt)", data=output_answers, file_name="cavablar.txt")

elif menu == "📝 Özünü imtahanda yoxla": uploaded_file = st.file_uploader("📤 Word (.docx) faylını yüklə", type="docx") mode = st.radio("📌 Rejim seç:", ["50 random sual", "Bütün suallar"], index=0)

if uploaded_file:
    questions = parse_docx(uploaded_file)
    if not questions:
        st.error("Sual tapılmadı. Fayl formatını yoxla.")
    else:
        if mode == "50 random sual":
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
            if st.button("🚀 İmtahana Başla"):
                st.session_state.started = True
                st.session_state.start_time = datetime.now()
                st.rerun()

        elif st.session_state.started:
            now = datetime.now()
            time_left = timedelta(hours=1) - (now - st.session_state.start_time)

            if time_left.total_seconds() <= 0:
                st.session_state.timer_expired = True

            if st.session_state.timer_expired:
                st.warning("⏰ Vaxt bitdi! İmtahan başa çatdı.")
                st.session_state.current = len(st.session_state.questions)

            else:
                minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                st.info(f"⏳ Qalan vaxt: {minutes} dəq {seconds} san")

            idx = st.session_state.current
            if idx < len(st.session_state.questions):
                question_text, options = st.session_state.questions[idx]
                correct_answer = options[0]
                if f"shuffled_{idx}" not in st.session_state:
                    shuffled = options[:]
                    random.shuffle(shuffled)
                    st.session_state[f"shuffled_{idx}"] = shuffled
                else:
                    shuffled = st.session_state[f"shuffled_{idx}"]

                st.markdown(f"**{idx+1}) {question_text}**")
                selected = st.radio("Variantı seç:", shuffled, key=f"answer_{idx}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("⬅️ Əvvəlki", disabled=idx == 0):
                        st.session_state.current -= 1
                        st.rerun()

                with col2:
                    if st.button("🚩 İmtahanı Bitir"):
                        st.session_state.current = len(st.session_state.questions)
                        st.rerun()

                with col3:
                    if st.button("➡️ Növbəti sual", disabled=(selected is None)):
                        if len(st.session_state.answers) <= idx:
                            st.session_state.answers.append(selected)
                            st.session_state.correct_answers.append(correct_answer)
                        else:
                            st.session_state.answers[idx] = selected
                            st.session_state.correct_answers[idx] = correct_answer
                        st.session_state.current += 1
                        st.rerun()
            else:
                st.success("✅ İmtahan bitdi!")
                correct_count = sum(1 for a, b in zip(st.session_state.answers, st.session_state.correct_answers) if a == b)
                st.markdown(f"### Nəticə: {correct_count}/{len(st.session_state.questions)} doğru cavab ✅")

                with st.expander("📋 Sual-sual nəticələr"):
                    for i, (user_ans, correct_ans, q) in enumerate(zip(
                        st.session_state.answers,
                        st.session_state.correct_answers,
                        st.session_state.questions
                    )):
                        question_text = q[0]
                        status = "✅ Düzgün" if user_ans == correct_ans else "❌ Səhv"
                        st.markdown(f"**{i+1}) {question_text}**\n\nSənin cavabın: `{user_ans}` — Doğru cavab: `{correct_ans}` → {status}")

                if st.button("🔁 Yenidən başla"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()

