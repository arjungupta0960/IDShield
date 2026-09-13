import streamlit as st
from paddleocr import PaddleOCR


@st.cache_resource
def get_ocr():
    return PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False
    )


@st.cache_data(show_spinner=False)
def extract_text_from_bytes(image_bytes):

    import tempfile
    import os

    ocr = get_ocr()

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as temp_file:

            temp_file.write(image_bytes)
            temp_path = temp_file.name

        result = ocr.predict(temp_path)

        extracted_text = []

        for res in result:

            if not hasattr(res, "json"):
                continue

            data = res.json

            if not isinstance(data, dict):
                continue

            data = data.get("res", data)

            texts = data.get(
                "rec_texts",
                []
            )

            for text in texts:

                if text and text.strip():

                    extracted_text.append(
                        text.strip()
                    )

        return extracted_text

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)