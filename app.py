import os
import tempfile
import streamlit as st
from embedchain import App

def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "smollm2:360m",
                    "base_url": "http://143.110.227.159:11434",
                    "temperature": 0.5,
                    "max_tokens": 1000,
                    "top_p": 1,
                    "stream": False,
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {"collection_name": "chat-pdf", "dir": db_path, "allow_reset": True},
            },
            "embedder": {
                "provider": "ollama", 
                "config": {
                    "model": "smollm2:360m",  # Added required model parameter
                    "base_url": "http://143.110.227.159:11434"
                }
            },
            "chunker": {"chunk_size": 2000, "chunk_overlap": 0, "length_function": "len"},
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

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": """
                    Hi! I'm docGPT. I can answer questions about your pdf documents.\n
                    Upload your pdf documents here and I'll answer your questions about them! 
                """,
            }
        ]
    if "add_pdf_files" not in st.session_state:
        st.session_state.add_pdf_files = []

def main():
    initialize_session_state()
    
    st.title("📄docGPT")
    
    with st.sidebar:
        st.write("We use Ollama's locally hosted LLM for processing. No API key needed.")
        pdf_files = st.file_uploader("Upload your PDF files", accept_multiple_files=True, type="pdf")
        handle_pdf_uploads(pdf_files)

    display_chat_messages()
    handle_user_input()

def handle_pdf_uploads(pdf_files):
    app = get_ec_app()
    for pdf_file in pdf_files:
        file_name = pdf_file.name
        if file_name in st.session_state.add_pdf_files:
            continue
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, prefix=file_name, suffix=".pdf") as f:
                f.write(pdf_file.getvalue())
                temp_file_name = f.name
                st.markdown(f"Adding {file_name} to knowledge base...")
                app.add(temp_file_name, data_type="pdf_file")
                st.markdown("")
                st.session_state.add_pdf_files.append(file_name)
                os.remove(temp_file_name)
            st.session_state.messages.append({"role": "assistant", "content": f"Added {file_name} to knowledge base!"})
        except Exception as e:
            st.error(f"Error adding {file_name} to knowledge base: {e}")
            st.stop()

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_input():
    if prompt := st.chat_input("Ask me anything!"):
        app = get_ec_app()
        
        with st.chat_message("user"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            msg_placeholder.markdown("Thinking...")
            full_response = ""
            
            try:
                for response in app.chat(prompt):
                    msg_placeholder.empty()
                    full_response += response
                
                st.write(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
