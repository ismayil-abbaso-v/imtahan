import streamlit as st
import re
import random
from docx import Document
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="İmtahan Hazırlayıcı", page_icon="📝")


def full_text(paragraph):
    """
    Docx paragraph obyektinin içindəki bütün run-ların mətni birləşdirilir.
    """
    return ''.join(run.text for run in paragraph.runs).strip()


def parse_docx(file):
    """
    .docx faylını oxuyub, içərisindəki “sual + 5 variant” bloklarını çıxarır.
    Gözləntilər:
      - Hər sual sətiri “1. Sualın mətni…” və ya “1) Sualın mətni…” formatında başlayır.
      - Ardınca ən az 5 variant gəlir: “A) variant mətni”, “B) variant mətni”, …, “E) variant mətni”.
    Return:
      [(question_text:str, options: List[str])] formasında siyahı qaytarır.
      Burada `options[0]` mütləq doğru cavab olmalıdır. (Faylınızda beli bir logic varsa,
      doğru cavab həmişə birinci yazılıbsa, bu yanaşma işləyəcək.)
    """
    doc = Document(file)
    paragraphs = list(doc.paragraphs)

    question_pattern = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)") # 1. və ya 1) şəklində
    option_pattern = re.compile(r"^\s*([A-Ea-e])[\.\)]?\s+(.*)") # A) və ya A. …

    questions = []
    i = 0
    while i < len(paragraphs):
        raw = full_text(paragraphs[i])
        m_q = question_pattern.match(raw)
        if m_q:
            # tapılan sual nömrəsi və sual mətni
            # question_no = m_q.group(1)
            question_text = m_q.group(2).strip()
            i += 1

            # İndi variantları toplayırıq
            options = []
            while i < len(paragraphs) and len(options) < 5:
                raw_opt = full_text(paragraphs[i])
                m_opt = option_pattern.match(raw_opt)
                if m_opt:
                    # variant mətni (məsələn, "Variant mətni")
                    opt_text = m_opt.group(2).strip()
                    options.append(opt_text)
                    i += 1
                else:
                    # Bəzən variant mətni sətirə tam oturmaya bilər, yəni variant mətni
                    # bir neçə paragrapha bölünə bilər. O halda, sonuncu variant varsa,
                    # onu birləşdiririk.
                    if options and raw_opt:
                        # Son variantı son sətirə əlavə edək (məsələn, çoxsətirli variant)
                        options[-1] += " " + raw_opt
                        i += 1
                    else:
                        # Varianta uyğun gəlməyən başqa bir paragrafsa, çıxırıq
                        break

            # yalnız əgər 5 variant tam toplanıbsa, sualı siyahıya əlavə edirik
            if len(options) == 5:
                questions.append((question_text, options))
            # yoxsa, bu blok sual-blok deyil, növbəti paragrafa keç
        else:
            i += 1

    return questions


def create_shuffled_docx_and_answers(questions):
    """
    Verilən sual + variant siyahısını qarışdırır, yeni .docx yaradır, 
    eyni zamanda cavab açarını (A, B, C, D, E) qaytarır.
    Gözlənti: questions = [(question:str, options:[str, str, str, str, str]), ...]
      Burada hər question-un options[0] = doğru cavab olaraq nəzərdə tutulur.
    """
    new_doc = Document()
    answer_key = []

    for idx, (question, options) in enumerate(questions, start=1):
        # Yeni sual paragrafı
        new_doc.add_paragraph(f"{idx}) {question}")

        # Doğru cavabı “options[0]” kimi götürürük
        correct_answer_text = options[0].strip()

        # Variant siyahısını qarışdırırıq
        shuffled_opts = options[:] # surəti al
        random.shuffle(shuffled_opts)

        # Qarışdırılmış variantları yazırıq və doğru cavaba hansı hərf düşdüsə əlavə edirik
        for j, opt in enumerate(shuffled_opts):
            letter = chr(ord('A') + j) # A, B, C, D, E
            new_doc.add_paragraph(f"{letter}) {opt}")
            # Boşluq və kiçik-böyük hərf nə fərq etməsin deyə strip() + lower()
            if opt.strip().lower() == correct_answer_text.lower():
                answer_key.append(f"{idx}) {letter}")

    return new_doc, answer_key


def parse_open_questions(file):
    """
    Bilet imtahanı üçün (açıq suallar) bütün paragraph-ları sual kimi qəbul edirik.
    Yəni fayldakı hər paragrafı “1) Sual mətni” şəklində sayırıq.
    """
    doc = Document(file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    questions = []
    for idx, p in enumerate(paragraphs, start=1):
        # Əgər sətir rəqəmlə başlayırsa, onu silib saxlayaq
        q = re.sub(r"^\s*\d+\s*[\.\)]?\s*", "", p).strip()
        if q:
            questions.append(q)
    return questions


# ------------------------------------------------------------------------
# S T R E A M L I T Q A Y I D A L A R I
# ------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------------------------------------
# Ana səhifə
# -----------------------------------------------------
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

    st.stop()


# -----------------------------------------------------
# Sidebar menyusu (Ana səhifədən başqa səhifələr üçün)
# -----------------------------------------------------
st.sidebar.title("🔧 Menyu")
if st.sidebar.button("🏠 Ana Səhifəyə Qayıt"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.page = "home"
    st.experimental_rerun()

menu = st.sidebar.radio(
    "➡️ Rejimi dəyiş:",
    ["📝 Özünü İmtahan Et", "🎲 Sualları Qarışdır", "🎫 Bilet İmtahanı"],
    index=["exam", "shuffle", "ticket"].index(st.session_state.page),
)
mapping = {
    "📝 Özünü İmtahan Et": "exam",
    "🎲 Sualları Qarışdır": "shuffle",
    "🎫 Bilet İmtahanı": "ticket"
}
st.session_state.page = mapping[menu]


# -----------------------------------------------------
# 1) ÖZÜNÜ İMTAHAN ET (exam)
# -----------------------------------------------------
if st.session_state.page == "exam":
    st.title("📝 Özünü Sına: İmtahan Rejimi")
    uploaded_file = st.file_uploader("📤 İmtahan üçün Word (.docx) faylını seçin", type="docx")

    mode = st.radio("📌 Sual seçimi:", ["🔹 50 təsadüfi sual", "🔸 Bütün suallar"], index=0)

    if uploaded_file:
        # Sual-paragrafları parse edirik
        questions = parse_docx(uploaded_file)
        if not questions:
            st.error("❗ Heç bir sual tapılmadı. Faylınızı yoxlayın: suallar düzgün nömrələnməyib və ya variantlar səhv formatlanıb.")
            st.stop()

        # Sessiya dəyişənlərini init edək
        if "exam_started" not in st.session_state:
            st.session_state.exam_started = False
        if "exam_submitted" not in st.session_state:
            st.session_state.exam_submitted = False
        if "exam_start_time" not in st.session_state:
            st.session_state.exam_start_time = None
        if "use_timer" not in st.session_state:
            st.session_state.use_timer = False

        # Hələ imtahan başlamayıbsa, “İmtahana Başla” düyməsini göstər
        if not st.session_state.exam_started:
            if st.button("🚀 İmtahana Başla"):
                # Seçilən sual sayını təyin edək
                if "50" in mode:
                    selected = random.sample(questions, min(50, len(questions)))
                    st.session_state.use_timer = True
                else:
                    selected = questions
                    st.session_state.use_timer = False

                # Sualların hər biri üçün variantları qarışdırırıq və doğru cavabı saxlayırıq
                shuffled_questions = []
                for q_text, opts in selected:
                    correct = opts[0].strip()
                    shuffled = opts[:] # nüsxə götür
                    random.shuffle(shuffled)
                    shuffled_questions.append((q_text, shuffled, correct))

                st.session_state.exam_questions = shuffled_questions
                st.session_state.exam_answers = [""] * len(shuffled_questions)
                st.session_state.exam_start_time = datetime.now()
                st.session_state.exam_started = True
                st.experimental_rerun()

            st.stop()

        # İmtahan başlayıb, amma nəticə göstərilməyib
        if st.session_state.exam_started and not st.session_state.exam_submitted:
            # Əgər timer istifadə olunacaqsa
            if st.session_state.use_timer:
                elapsed = datetime.now() - st.session_state.exam_start_time
                remaining = timedelta(minutes=60) - elapsed
                seconds_left = int(remaining.total_seconds())
                if seconds_left <= 0:
                    st.warning("⏰ Vaxt bitdi! İmtahan avtomatik tamamlandı.")
                    st.session_state.exam_submitted = True
                    st.experimental_rerun()
                else:
                    mins, secs = divmod(seconds_left, 60)
                    st.info(f"⏳ Qalan vaxt: {mins} dəq {secs} san")
            else:
                st.info("ℹ️ Bu rejimdə zaman məhdudiyyəti yoxdur.")

            # Sualları bir-bir göstər, radio düyməsi ilə variant seçimi et
            for i, (qtext, options, _) in enumerate(st.session_state.exam_questions):
                st.markdown(f"**{i+1}) {qtext}**")
                # cavabları saxla
                st.session_state.exam_answers[i] = st.radio(
                    label="",
                    options=options,
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )

            # “İmtahanı Bitir” düyməsi
            if st.button("📤 İmtahanı Bitir"):
                st.session_state.exam_submitted = True
                st.experimental_rerun()
            st.stop()

        # İmtahan tamamlanıb, resultları göstər
        if st.session_state.exam_submitted:
            st.success("🎉 İmtahan tamamlandı!")
            correct_list = [correct for _, _, correct in st.session_state.exam_questions]
            # Cavablar müqayisə edilir
            score = sum(
                1 for user_ans, true_ans in zip(st.session_state.exam_answers, correct_list)
                if user_ans.strip().lower() == true_ans.strip().lower()
            )
            total = len(correct_list)
            percent = (score / total) * 100
            st.markdown(f"### ✅ Nəticə: {score} düzgün cavab / {total} sual")
            st.markdown(
                f"<p style='font-size:16px;'>📈 Doğruluq faizi: <strong>{percent:.2f}%</strong></p>",
                unsafe_allow_html=True
            )
            st.progress(score / total)

            with st.expander("📊 Detallı nəticələr"):
                for i, (user_ans, true_ans, (qtext, _, _)) in enumerate(
                        zip(st.session_state.exam_answers, correct_list, st.session_state.exam_questions), 1):
                    status = "✅ Düzgün" if user_ans.strip().lower() == true_ans.strip().lower() else "❌ Səhv"
                    st.markdown(
                        f"**{i}) {qtext}**\n"
                        f"• Sənin cavabın: `{user_ans}`\n"
                        f"• Doğru cavab: `{true_ans}` → {status}"
                    )

            if st.button("🔁 Yenidən Başla"):
                for key in ["exam_questions", "exam_answers", "exam_started", "exam_submitted", "exam_start_time", "use_timer"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.experimental_rerun()

            st.stop()


# -----------------------------------------------------
# 2) SUALLARI QARIŞDIR (shuffle)
# -----------------------------------------------------
elif st.session_state.page == "shuffle":
    st.title("🎲 Test Suallarını Qarışdır və Cavab Açarı Yarat")
    uploaded_file = st.file_uploader("📤 Word (.docx) sənədini seçin", type="docx")
    mode = st.radio("💡 Sualların sayı:", ["🔹 50 təsadüfi sual", "🔸 Bütün suallar"], index=0)

    if uploaded_file:
        questions = parse_docx(uploaded_file)
        if len(questions) < 5:
            st.error("❗ Faylda kifayət qədər uyğun sual tapılmadı (minimum 5).")
            st.stop()

        # Sualların çatışan sayı
        if "50" in mode:
            selected = random.sample(questions, min(50, len(questions)))
        else:
            selected = questions

        new_doc, answer_key = create_shuffled_docx_and_answers(selected)

        # Yaranan .docx faylını istifadəçiyə verir
        output_docx = BytesIO()
        new_doc.save(output_docx)
        output_docx.seek(0)

        # Cavab açarını .txt şəklində verir
        output_answers = BytesIO()
        output_answers.write('\n'.join(answer_key).encode('utf-8'))
        output_answers.seek(0)

        st.success("✅ Qarışdırılmış sənədlər hazırdır!")
        st.download_button("📥 Qarışdırılmış Suallar (.docx)", output_docx, "qarisdirilmis_suallar.docx")
        st.download_button("📥 Cavab Açarı (.txt)", output_answers, "cavab_acari.txt")
        st.stop()


# -----------------------------------------------------
# 3) BİLET İMTAHAN (ticket)
# -----------------------------------------------------
elif st.session_state.page == "ticket":
    st.title("🎫 Bilet İmtahanı (Açıq suallar)")
    uploaded_file = st.file_uploader("📤 Bilet sualları üçün Word (.docx) faylı seçin", type="docx")

    if uploaded_file:
        questions = parse_open_questions(uploaded_file)
        if len(questions) < 5:
            st.error("❗ Kifayət qədər sual yoxdur (minimum 5 tələb olunur).")
            st.stop()

        if "ticket_started" not in st.session_state:
            st.session_state.ticket_started = False
            st.session_state.ticket_questions = []

        if not st.session_state.ticket_started:
            if st.button("🎟️ Bilet Çək"):
                st.session_state.ticket_questions = random.sample(questions, 5)
                st.session_state.ticket_started = True
            st.stop()

        if st.session_state.ticket_started:
            st.success("✅ Hazır bilet sualları:")
            for i, q in enumerate(st.session_state.ticket_questions, start=1):
                st.markdown(f"<p style='font-size:16px;'><strong>{i})</strong> {q}</p>", unsafe_allow_html=True)
            st.markdown("---")
            if st.button("🔁 Yenidən Bilet Çək"):
                st.session_state.ticket_questions = random.sample(questions, 5)
            st.stop()
