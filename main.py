import streamlit as st
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import zipfile
import PyPDF2
import docx
import time

# Load environment variables
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("gemini")

st.set_page_config(page_title="AI PortFolio Builder", page_icon="🤖")
st.title(":green[🤖 AI PortFolio Builder]")
st.subheader(":red[Create a website using AI + Resume]")

# Inputs
prompt = st.text_area("Enter your website requirements:")
resume_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])

if st.button("Generate Website"):

    resume_text = ""

    # -------- Resume Text Extraction --------
    if resume_file:
        if resume_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(resume_file)
            for page in reader.pages:
                if page.extract_text():
                    resume_text += page.extract_text()

        elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            document = docx.Document(resume_file)
            for para in document.paragraphs:
                resume_text += para.text + "\n"

    # -------- Prompt --------
    messages = [
        {
            "role": "system",
            "content": """
You are a world-class professional website developer.

Create a  portfolio website using HTML, CSS, and JavaScript.

Use the USER REQUIREMENTS and RESUME CONTENT to build:
- Hero section
- About Me
- Skills
- Education
- Projects
- Contact section
- profile picture 



Return ONLY code in the following STRICT format:

---HTML---
[html code]
---html---

---CSS---
[css code]
---css---

---JS---
[javascript code]
---js---

IMPORTANT:
All tags MUST exist exactly as shown.
Do NOT include explanations or extra text.
            """
        },
        {
            "role": "user",
            "content": f"""
USER REQUIREMENTS:
{prompt}

RESUME CONTENT:
{resume_text}
            """
        }
    ]

    # -------- Model + Retry Logic --------
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

    response = None
    for attempt in range(3):
        try:
            response = model.invoke(messages)
            break
        except Exception as e:
            if "503" in str(e):
                time.sleep(5)
            else:
                raise e

    if response is None:
        st.error("Gemini servers are busy. Please try again later.")
        st.stop()

    output = response.content

    # -------- Extract Code --------
    html_code = output.split("---HTML---")[1].split("---html---")[0].strip()
    css_code = output.split("---CSS---")[1].split("---css---")[0].strip()
    js_code = output.split("---JS---")[1].split("---js---")[0].strip()

    # -------- Save Files --------
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_code)

    with open("style.css", "w", encoding="utf-8") as f:
        f.write(css_code)

    with open("script.js", "w", encoding="utf-8") as f:
        f.write(js_code)

    # -------- ZIP Download --------
    zip_filename = "website_files.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write("index.html")
        zipf.write("style.css")
        zipf.write("script.js")

    st.success("Website generated successfully from resume!")

    st.download_button(
        label="⬇️ Download Zip File",
        data=open(zip_filename, "rb").read(),
        file_name=zip_filename,
        mime="application/zip"
    )
