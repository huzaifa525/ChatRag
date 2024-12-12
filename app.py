import os
import tempfile
import streamlit as st
from PyPDF2 import PdfReader
from langchain_ollama import OllamaLLM, OllamaEmbeddings  # Updated imports

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file."""
    pdf_reader = PdfReader(pdf_file)
    text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    return text

def query_pdf_with_llm(pdf_text, question):
    """Queries the extracted text using the LLM."""
    llm = OllamaLLM(
        model="smollm2:360m",
        base_url="http://143.110.227.159:11434/",
        temperature=0.3,
        max_tokens=2000,
    )
    prompt = f"Context: {pdf_text}\n\nQuestion: {question}\n\nAnswer:"
    response = llm(prompt)
    return response

st.title("📄CleverBot - Powered by CleverFlow")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
                Hi! I'm CleverBot. I can answer questions about your PDF documents.\n
                Upload your PDF document and ask a question about it! 
            """,
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_pdf = st.file_uploader("Upload your PDF", type="pdf")
if uploaded_pdf:
    extracted_text = extract_text_from_pdf(uploaded_pdf)
    st.session_state.pdf_text = extracted_text  # Store extracted text in session state
    st.markdown("PDF uploaded and processed successfully!")

if prompt := st.chat_input("Ask me anything about the uploaded PDF!"):
    with st.chat_message("user"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(prompt)

    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        msg_placeholder.markdown("Thinking...")
        full_response = ""

        try:
            if "pdf_text" not in st.session_state or not st.session_state.pdf_text:
                st.error("Please upload a PDF first.")
            else:
                full_response = query_pdf_with_llm(st.session_state.pdf_text, prompt)
                msg_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"An error occurred: {e}")
