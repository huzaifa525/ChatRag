import os
import time
import tempfile
import streamlit as st
from PyPDF2 import PdfReader
from langchain_ollama import OllamaLLM, OllamaEmbeddings

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
    prompt = f"Context:\n{pdf_text}\n\nQuestion: {question}\n\nAnswer:"
    response = llm.invoke(prompt)
    return response

def format_response_html(response):
    """Format the response for simple and clean HTML/CSS visualization."""
    styled_response = "<div style='font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333;'>"
    for line in response.split("\n"):
        if line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3."):
            styled_response += f"<p style='font-weight: bold;'>{line.strip()}</p>"
        elif "**" in line:
            styled_response += f"<p><b>{line.strip().replace('**', '')}</b></p>"
        else:
            styled_response += f"<p>{line.strip()}</p>"
    styled_response += "</div>"
    return styled_response

def typing_effect_html(response, placeholder):
    """Simulates typing effect for HTML-based responses."""
    words = response.split(" ")
    typed_response = ""
    for word in words:
        typed_response += word + " "
        placeholder.markdown(typed_response, unsafe_allow_html=True)
        time.sleep(0.05)  # Adjust typing speed here

st.title("📄CleverBot - Powered by CleverFlow")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm CleverBot. I can answer questions about your PDF documents.\n\nUpload your PDF document and ask a question about it!"
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_pdf = st.file_uploader("Upload your PDF", type="pdf")
if uploaded_pdf:
    extracted_text = extract_text_from_pdf(uploaded_pdf)
    st.session_state.pdf_text = extracted_text  # Store extracted text in session state
    st.markdown("**PDF uploaded and processed successfully!**")

if prompt := st.chat_input("Ask me anything about the uploaded PDF!"):
    with st.chat_message("user"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(prompt)

    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        msg_placeholder.markdown("<i>Thinking...</i>", unsafe_allow_html=True)
        full_response = ""

        try:
            if "pdf_text" not in st.session_state or not st.session_state.pdf_text:
                st.error("Please upload a PDF first.")
            else:
                full_response = query_pdf_with_llm(st.session_state.pdf_text, prompt)
                formatted_response = format_response_html(full_response)
                msg_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
        except Exception as e:
            st.error(f"An error occurred: {e}")
