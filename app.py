elif menu == "📝 İmtahan Rejimi":
    st.title("📝 Öz İmtahanını Yoxla")
    uploaded_file = st.file_uploader("📤 Word (.docx) faylını yüklə", type="docx")

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        total_questions = len(questions)

        if not questions:
            st.error("Sual tapılmadı.")
        else:
            st.markdown(f"*Fayldakı ümumi sual sayı:* {total_questions}")

            start_idx = st.number_input("Başlanğıc sual nömrəsi:", min_value=1, max_value=total_questions, value=1)
            end_idx = st.number_input("Sonuncu sual nömrəsi:", min_value=start_idx, max_value=total_questions, value=min(start_idx+49, total_questions))

            selected_questions = questions[start_idx-1:end_idx]

            if "started" not in st.session_state:
                st.session_state.started = False
                st.session_state.questions = selected_questions
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

                    st.markdown(f"{idx+1}) {qtext}")
                    selected = st.radio("Variant seç:", shuffled, key=f"answer_{idx}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("⬅ Əvvəlki", disabled=idx == 0):
                            st.session_state.current -= 1
                            st.rerun()
                    with col2:
                        if st.button("🚩 Bitir"):
                            st.session_state.current = len(st.session_state.questions)
                            st.rerun()
                    with col3:
                        if st.button("➡ Növbəti", disabled=(selected is None)):
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
                            st.markdown(f"{i+1}) {q[0]}\nSənin cavabın: {ua} — Doğru: {ca} → {status}")

                    if st.button("🔁 Yenidən başla"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()