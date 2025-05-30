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

def create_shuffled_docx_and_answers(suallar):
    yeni_doc = Document()
    cavablar = []

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

menu = st.sidebar.radio("Seçim et:", ["📤 Variantları Qarışdır", "📝 İmtahan Hazırla"])

if menu == "📤 Variantları Qarışdır":
    st.title("📤 Sual Variantlarını Qarışdır")
    uploaded_file = st.file_uploader("Word (.docx) sənədini seç", type="docx")
    mode = st.radio("Rejim:", ["50 sual", "Bütün suallar"], index=0)

    if uploaded_file:
        suallar = parse_docx(uploaded_file)
        if len(suallar) < 5:
            st.error("Faylda kifayət qədər uyğun sual tapılmadı.")
        else:
            secilmis = random.sample(suallar, min(50, len(suallar))) if mode == "50 sual" else suallar
            yeni_doc, cavablar = create_shuffled_docx_and_answers(secilmis)

            output_docx = BytesIO()
            yeni_doc.save(output_docx)
            output_docx.seek(0)

            output_answers = BytesIO()
            output_answers.write('\n'.join(cavablar).encode('utf-8'))
            output_answers.seek(0)

            st.success("✅ Sənədlər hazırdır!")
            st.download_button("📥 Qarışdırılmış suallar (.docx)", output_docx, "qarisdirilmis_suallar.docx")
            st.download_button("📥 Cavab açarı (.txt)", output_answers, "cavablar.txt")

elif menu == "📝 İmtahan Hazırla":
    st.title("📝 Öz İmtahanını Yarat")

    uploaded_file = st.file_uploader("📤 Word (.docx) faylını yüklə", type="docx")

    if uploaded_file:
        questions = parse_docx(uploaded_file)

        if not questions:
            st.error("Sual tapılmadı.")
        else:
            # Başlanğıc və son sual nömrəsini seçmək üçün slider
            sual_sayi = len(questions)
            start_q = st.number_input("Başlanğıc sual №", min_value=1, max_value=sual_sayi, value=1)
            end_q = st.number_input("Son sual №", min_value=start_q, max_value=sual_sayi, value=sual_sayi)

            selected_questions = questions[start_q-1:end_q]

            if st.button("📄 İmtahan sənədini hazırla"):
                yeni_doc, cavablar = create_shuffled_docx_and_answers(selected_questions)

                output_docx = BytesIO()
                yeni_doc.save(output_docx)
                output_docx.seek(0)

                output_answers = BytesIO()
                output_answers.write('\n'.join(cavablar).encode('utf-8'))
                output_answers.seek(0)

                st.success(f"✅ {start_q}-dən {end_q}-ə qədər olan suallarla imtahan hazırlandı!")
                st.download_button("📥 İmtahan sualları (.docx)", output_docx, "imtahan_suallari.docx")
                st.download_button("📥 Cavab açarı (.txt)", output_answers, "cavablar.txt")