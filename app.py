import os
import tempfile
import streamlit as st
from embedchain import App
from langchain_ollama import OllamaLLM, OllamaEmbeddings  # Updated imports

def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "smollm2:360m",  # Valid model name on the Ollama server
                    "base_url": "http://143.110.227.159:11434",  # Update with your server's base URL
                    "temperature": 0.4,  # Lowered for efficiency
                    "max_tokens": 1500,  # Increased for more context
                    "stream": True,
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {
                    "collection_name": "chat-pdf",
                    "dir": db_path,
                    "allow_reset": True,
                    "indexing": {"speed": "high", "batch_size": 1000}  # Optimized indexing
                },
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": "smollm2:360m",
                    "base_url": "http://143.110.227.159:11434",
                },
            },
            "chunker": {"chunk_size": 3000, "chunk_overlap": 500, "length_function": "len"},  # Optimized chunking
        }
    )

def get_db_path():
    tmpdirname = tempfile.mkdtemp()
    return tmpdirname

def get_ec_app():
    if "app" in st.session_state:
        print("Found app in session state")
        app = st.session_state.app
    else:
        print("Creating app")
        db_path = get_db_path()
        app = embedchain_bot(db_path)
        st.session_state.app = app
    return app

with st.sidebar:
    "### CleverFlow Configuration"
    "Make sure your CleverFlow server is running."
    st.markdown(
        """
        Ensure the `smollm2:360m` model is available on your CleverFlow server. Run:
        ```
        ollama pull smollm2:360m
        ```
        """
    )

    pdf_files = st.file_uploader("Upload your PDF files", accept_multiple_files=True, type="pdf")
    add_pdf_files = st.session_state.get("add_pdf_files", [])

    for pdf_file in pdf_files:
        file_name = pdf_file.name
        if file_name in add_pdf_files:
            continue
        try:
            temp_file_name = None
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, prefix=file_name, suffix=".pdf") as f:
                f.write(pdf_file.getvalue())
                temp_file_name = f.name
            if temp_file_name:
                st.markdown(f"Adding {file_name} to knowledge base...")
                app = get_ec_app()
                app.add(temp_file_name, data_type="pdf_file")
                add_pdf_files.append(file_name)
                os.remove(temp_file_name)
            st.session_state.messages.append({"role": "assistant", "content": f"Added {file_name} to knowledge base!"})
        except Exception as e:
            st.error(f"Error adding {file_name} to knowledge base: {e}")
    st.session_state["add_pdf_files"] = add_pdf_files

st.title("📄CleverBot - Powered by CleverFlow")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
                Hi! I'm CleverBot. I can answer questions about your PDF documents.\n
                Upload your PDF documents here and I'll answer your questions about them! 
            """,
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything!"):
    with st.chat_message("user"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(prompt)

    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        msg_placeholder.markdown("Thinking...")
        full_response = ""

        try:
            app = get_ec_app()
            for response in app.chat(prompt):
                full_response += response
                msg_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"An error occurred: {e}")
