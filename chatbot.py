import streamlit as st
import pandas as pd
import chromadb
import os
import google.generativeai as genai
from datetime import datetime
from system import chatbot_response  # Importing system for fallback responses

# Configuration
CSV_FILE = "cleaned_data_updated.csv"
BOT_NAME = "Appsgenii AI Assistant"
PERSIST_DIRECTORY = "chroma_db"
GEMINI_API_KEY = "AIzaSyCVxEGp1eWPbyKVYFGOUIMgcjVuFDzX2-I"
DOCUMENT_LIMIT = 30  # New document limit setting

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

class GeminiEmbeddingFunction:
    def __init__(self):
        self.max_content_length = 3000

    def __call__(self, input):
        try:
            return genai.embed_content(
                model="models/embedding-001",
                content=[text[:self.max_content_length] for text in input],
                task_type="retrieval_document"
            )['embedding']
        except Exception as e:
            st.error(f"🔧 Embedding Error: {str(e)}")
            st.stop()

@st.cache_resource(show_spinner=False)
def initialize_chroma():
    try:
        client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        existing_collections = client.list_collections()
        
        if "appsgenii_knowledge" in [col.name for col in existing_collections]:
            return client.get_collection("appsgenii_knowledge")

        # Create new collection
        collection = client.create_collection(
            name="appsgenii_knowledge",
            embedding_function=GeminiEmbeddingFunction()
        )

        # Load and validate CSV data
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f"Missing data file: {CSV_FILE}")
            
        df = pd.read_csv(CSV_FILE)
        if 'content' not in df.columns:
            raise ValueError("CSV file must contain 'content' column")

        # Limit documents to first 30 entries
        documents = df['content'].dropna().astype(str).tolist()[:DOCUMENT_LIMIT]
        if not documents:
            raise ValueError("No valid content found in CSV file")

        # Add documents with metadata
        collection.add(
            documents=documents,
            ids=[f"doc_{i}" for i in range(len(documents))],
            metadatas=[{
                "source": "csv_upload",
                "timestamp": datetime.now().isoformat()
            } for _ in documents]
        )

        return collection

    except Exception as e:
        st.error(f"🚨 Initialization Failed: {str(e)}")
        st.stop()

def generate_response(prompt, context):
    try:
        # First check if context is provided (relevant info found in the knowledge base)
        if context:
            response = gemini_model.generate_content(f"""
            Context: {context}
            Question: {prompt}
            
            Answer in friendly, professional tone. Structure response with:
            - Clear heading
            - Bullet points if listing services
            - Emojis for visual breaks
            - Follow-up question suggestion
            
            If no context match: "I'll check with our team and get back to you!"
            """)
            return response.text
        
        # If no relevant context found, fallback to system response (like system instructions)
        system_answer = chatbot_response(prompt)
        
        # If system provides a non-generic response, return it
        if "I'm not sure" not in system_answer:
            return system_answer
        
        # Default fallback response if no context is found in the knowledge base or system.py
        return "🤖 I couldn’t find an answer in our knowledge base. Let me check with the team and get back to you! Meanwhile, feel free to ask anything else."

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def chat_interface(collection):
    st.title(f"Appsgenii AI Assistant")
    
    # Initialize chat history and prompt storage
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "🌟 Welcome! Ask me anything about Appsgenii services!",
            "avatar": "AppsGenii-Technologies.png"
        }]
    if "user_prompts" not in st.session_state:
        st.session_state.user_prompts = []

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "AppsGenii-Technologies.png")):
            st.markdown(msg["content"])

    # Handle user input
    if prompt := st.chat_input("Type your question here..."):
        # Immediately store user prompt before processing
        st.session_state.user_prompts.append(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "avatar": "👤"
        })
        
        with st.spinner("🔍 Analyzing your question..."):
            try:
                # Check for prompt history queries
                history_keywords = [
                    "prompt history", "previous questions", "what did i ask",
                    "my queries", "history", "my questions", "past queries",
                    "show my questions", "list my prompts"
                ]
                
                if any(keyword in prompt.lower() for keyword in history_keywords):
                    previous_prompts = st.session_state.user_prompts[:-1]  # Exclude current
                    if not previous_prompts:
                        response = "📋 You haven't asked any questions yet. Feel free to ask anything! 🌟"
                    else:
                        response = "📜 Your Question History:\n\n" + "\n".join(
                            [f"{i+1}. {q}" for i, q in enumerate(previous_prompts)]
                        ) + "\n\n💡 Total questions: {}".format(len(previous_prompts))
                else:
                    # Original processing logic
                    system_answer = chatbot_response(prompt)
                    
                    if "I couldn't find a specific answer" not in system_answer:
                        response = system_answer
                    else:
                        context = ""
                        lower_prompt = prompt.lower()
                        
                        if "services" not in lower_prompt and "provide" not in lower_prompt:
                            results = collection.query(
                                query_texts=[prompt],
                                n_results=3,
                                include=["documents", "distances"]
                            )
                            context = "\n".join([doc for doc, dist in zip(results['documents'][0], results['distances'][0])
                                                if dist < 1.2])

                        response = generate_response(prompt, context)

                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "avatar": "AppsGenii-Technologies.png"
                })
                
            except Exception as e:
                error_msg = f"⚠️ Oops! Something went wrong: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "avatar": "AppsGenii-Technologies.png"
                })
                st.error(f"❌ Processing Error: {str(e)}")
        
        st.rerun()

def main():
    st.set_page_config(page_title=BOT_NAME, page_icon="AppsGenii-Technologies.png")
    
    try:
        with st.spinner("⚙️ Loading knowledge base..."):
            collection = initialize_chroma()
            
            # Verify data loaded
            if collection.count() == 0:
                st.error("No data loaded in ChromaDB!")
                st.stop()
                
        chat_interface(collection)
        
    except Exception as e:
        st.error(f"Initialization Failed: {str(e)}")
        if "FileNotFoundError" in str(e):
            st.error(f"Ensure {CSV_FILE} exists in the directory")
        st.stop()

if __name__ == "__main__":
    # Clear previous session data
    if os.path.exists(PERSIST_DIRECTORY):
        try:
            import shutil
            shutil.rmtree(PERSIST_DIRECTORY, ignore_errors=True)
        except:
            pass
    main()