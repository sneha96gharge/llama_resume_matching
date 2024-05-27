import streamlit as st # type: ignore
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import requests
# from prompt import prompt_extract_text # type: ignore
from prompt_utils import prompt_extract_text  # type: ignore # Changed to local import
from langchain_community.llms import Ollama # type: ignore
import os
import io
from groq import Groq # type: ignore

client = Groq(
    api_key='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',
)

# openai_api_key = os.getenv("OPENAI_API_KEY")
# llm = Ollama(model='llama3')

def get_resume_pdf_text(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
    
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def generate_text(prompt, text):
    combined_prompt=''

    if len(text) > 0:
       combined_prompt = f"{prompt}\n\n{text}"
    else:
        combined_prompt = prompt

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": combined_prompt,
        }
    ],
    model="llama3-70b-8192",
)
    text = chat_completion.choices[0].message.content
    return text

def generate_match_text(resume_text, job_description):
    prompt = f"""
    Given the following resume and job description, compare them to provide a percentage matching score out of 100. The comparison should focus on skills, experience, years of experience, and education/qualifications.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Please provide a detailed analysis of the match with the following breakdown:
       - Percentage based on skills: 
       - Percentage based on experience: 
       - Percentage based on years of experience: 
       - Percentage based on education/qualifications: 

       Also, provide a final overall percentage score.
    """
    return prompt

def main():
    load_dotenv()

    st.set_page_config(page_title="Resume-JobDescription matcher")
    st.header("Matching percentage: ")

    match_score = None 

    with st.sidebar:
        st.subheader("Your Resume")
        uploaded_file  = st.file_uploader(
            "Upload the Resume here'", accept_multiple_files=False)
        
        if st.button("Upload Resume"):
            if uploaded_file is not None:
                with st.spinner('Uploading Resune'):
                    with open("temp.pdf", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    text_resume = get_resume_pdf_text("temp.pdf")
                    st.session_state['final_text_resume'] = generate_text(prompt_extract_text, text_resume)
                    st.success("Resume successfully uploaded and processed.")

        st.subheader("Job Description")
        uploaded_file_job  = st.file_uploader(
            "Upload the Job Description here", accept_multiple_files=False)
        
        if st.button("Upload Job Description"):
            if uploaded_file_job is not None:
                with st.spinner('Uploading Job Description'):
                    with open("temp2.pdf", "wb") as f:
                        f.write(uploaded_file_job.getbuffer())
                    text_job = get_resume_pdf_text("temp2.pdf")
                    st.session_state['final_text_job'] = generate_text(prompt_extract_text, text_job)
                    st.success("Job Description successfully uploaded and processed.")

    if match_score is not None:  # Check if match_score has been assigned a value
       
        st.markdown(f"<h1 style='font-size:36px;'>{match_score * 100:.2f}%</h1>", unsafe_allow_html=True)
    
    if st.button('Match'):
         with st.spinner("Matching..."):
             prompt_match_text = generate_match_text(st.session_state['final_text_resume'], st.session_state['final_text_job'])
             matching_text = generate_text(prompt_match_text,'')
             st.write(matching_text)
            

if __name__ == '__main__':
    main()