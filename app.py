# 2️⃣ İmtahan rejimi (Hamısı bir səhifədə + qarışıq variantlar + vaxtölçən + aralıq seçimi)
elif st.session_state.page == "exam":
    st.title("📝 Özünü Sına: İmtahan Rejimi")

    uploaded_file = st.file_uploader("📤 İmtahan üçün Word (.docx) faylını seçin", type="docx")
    mode = st.radio("📌 Sual seçimi:", ["🔹 50 təsadüfi sual", "🔸 Sual aralığı seç"], index=0)

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if not questions:
            st.error("❗ Heç bir sual tapılmadı.")
        else:
            total_questions = len(questions)

            if "exam_started" not in st.session_state:
                st.session_state.exam_started = False
            if "exam_submitted" not in st.session_state:
                st.session_state.exam_submitted = False
            if "exam_start_time" not in st.session_state:
                st.session_state.exam_start_time = None

            if "50" in mode:
                st.info("📌 60 dəqiqə vaxtınız olacaq.")
                if not st.session_state.exam_started:
                    if st.button("🚀 İmtahana Başla"):
                        selected = random.sample(questions, min(50, total_questions))
                        shuffled_questions = []
                        for q_text, opts in selected:
                            correct = opts[0]
                            shuffled = opts[:]
                            random.shuffle(shuffled)
                            shuffled_questions.append((q_text, shuffled, correct))

                        st.session_state.exam_questions = shuffled_questions
                        st.session_state.exam_answers = [""] * len(shuffled_questions)
                        st.session_state.exam_start_time = datetime.now()
                        st.session_state.exam_started = True
                        st.rerun()
            else:
                st.info("📌 Vaxt limiti yoxdur. İstədiyiniz aralığı seçin.")
                start_q = st.number_input("🔢 Başlanğıc sual nömrəsi", min_value=1, max_value=total_questions, value=1)
                end_q = st.number_input("🔢 Sonuncu sual nömrəsi", min_value=start_q, max_value=total_questions, value=min(start_q + 49, total_questions))

                if not st.session_state.exam_started:
                    if st.button("🚀 Aralıq İmtahana Başla"):
                        selected = questions[start_q - 1:end_q]
                        shuffled_questions = []
                        for q_text, opts in selected:
                            correct = opts[0]
                            shuffled = opts[:]
                            random.shuffle(shuffled)
                            shuffled_questions.append((q_text, shuffled, correct))

                        st.session_state.exam_questions = shuffled_questions
                        st.session_state.exam_answers = [""] * len(shuffled_questions)
                        st.session_state.exam_started = True
                        st.rerun()

            if st.session_state.exam_started and not st.session_state.exam_submitted:
                if "50" in mode:
                    elapsed = datetime.now() - st.session_state.exam_start_time
                    remaining = timedelta(minutes=60) - elapsed
                    seconds_left = int(remaining.total_seconds())
                    if seconds_left <= 0:
                        st.warning("⏰ Vaxt bitdi! İmtahan tamamlandı.")
                        st.session_state.exam_submitted = True
                        st.rerun()
                    else:
                        mins, secs = divmod(seconds_left, 60)
                        st.info(f"⏳ Qalan vaxt: {mins} dəq {secs} san")

                for i, (qtext, options, _) in enumerate(st.session_state.exam_questions):
                    st.markdown(f"**{i+1}) {qtext}**")
                    st.session_state.exam_answers[i] = st.radio(
                        label="", options=options, key=f"q_{i}", label_visibility="collapsed"
                    )

                if st.button("📤 İmtahanı Bitir"):
                    st.session_state.exam_submitted = True
                    st.rerun()

            elif st.session_state.exam_submitted:
                st.success("🎉 İmtahan tamamlandı!")
                correct_list = [correct for _, _, correct in st.session_state.exam_questions]
                score = sum(1 for a, b in zip(st.session_state.exam_answers, correct_list) if a == b)
                total = len(correct_list)
                percent = (score / total) * 100

                st.markdown(f"### ✅ Nəticə: {score} düzgün cavab / {total} sual")
                st.markdown(f"<p style='font-size:16px;'>📈 Doğruluq faizi: <strong>{percent:.2f}%</strong></p>", unsafe_allow_html=True)
                st.progress(score / total)

                with st.expander("📊 Detallı nəticələr"):
                    for i, (ua, ca, (qtext, _, _)) in enumerate(zip(st.session_state.exam_answers, correct_list, st.session_state.exam_questions)):
                        status = "✅ Düzgün" if ua == ca else "❌ Səhv"
                        st.markdown(f"**{i+1}) {qtext}**\n• Sənin cavabın: `{ua}`\n• Doğru cavab: `{ca}` → {status}")

                if st.button("🔁 Yenidən Başla"):
                    for key in ["exam_questions", "exam_answers", "exam_started", "exam_submitted", "exam_start_time"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
