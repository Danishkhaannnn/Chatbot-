from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
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
            raise HTTPException(status_code=500, detail=f"Embedding Error: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Initialization Failed: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# FastAPI Setup
app = FastAPI()

# Request body schema
class QueryRequest(BaseModel):
    prompt: str

class Response(BaseModel):
    response: str

@app.on_event("startup")
async def startup_event():
    # Initialize ChromaDB when FastAPI starts
    global collection
    collection = initialize_chroma()

@app.post("/chat", response_model=Response)
async def chat(request: QueryRequest):
    prompt = request.prompt
    
    # Query processing
    try:
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

        response_text = generate_response(prompt, context)
        return {"response": response_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing your request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
