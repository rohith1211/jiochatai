import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai  
from fastapi.middleware.cors import CORSMiddleware  
from typing import List

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize templates folder for Jinja2
templates = Jinja2Templates(directory="templates")

# Initialize Chroma client and collection
client = chromadb.PersistentClient(path="db")
collection = client.get_collection("sentence_embeddings_collection")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Set up Gemini API Key
genai.configure(api_key="geminiapikey")

# Initialize chat history and context variables
chat_history = []
chat_history_string = ""

# Helper function to retrieve context
def get_context(sentence_index, all_sentences, context_range=5):
    start = max(0, sentence_index - context_range)
    end = min(len(all_sentences), sentence_index + context_range + 1)
    return " ".join(all_sentences[start:end])

# Query function to interact with Chroma DB
def query_database(query, top_k=1, context_range=5):
    query_embedding = model.encode(query, convert_to_tensor=True)
    query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=0).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    all_sentences = [metadata["sentence"] for metadata in collection.get()["metadatas"]]

    matched_sentences = []
    for result in results["metadatas"][0]:
        matched_sentence = result["sentence"]
        sentence_index = all_sentences.index(matched_sentence)
        context = get_context(sentence_index, all_sentences, context_range)
        matched_sentences.append({
            "matched_sentence": matched_sentence,
            "context": context
        })
    return matched_sentences

# Function to generate AI response based on the context using Gemini API
def generate_ai_response(query, context, chat_history):
    prompt = """You are an AI helpdesk agent for JioPay Business, providing clear, concise, and professional support.  

- Greet users naturally with a friendly and engaging message (e.g., *"Welcome to JioPay Business support! How can I assist you today?"*).  
- Answer queries using only the provided context.  
- If the information is unavailable, respond with:  
  *"I'm sorry, but I couldn't find that information in the provided context."*  
- If a question is unclear and not available, politely ask:  
  *"Could you be more specific?"*  
- Keep responses direct, helpful, and professional while maintaining a warm tone.  
- Avoid unnecessary pleasantries and focus on efficient assistance."""

    if len(chat_history) > 0:
        prompt += '\n' + "This is the previous exchange you had with the user" + '\n' + chat_history

    prompt += '\n \n' + f"Context: {context}"
    prompt += '\n \n' + "Based on the above instructions and context, respond to the query below."
    prompt += '\n \n' + f"Query: {query}"
    prompt += "Your response: "
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating Gemini AI response: {e}")
        return "Unable to generate Gemini AI response at this time."

# FastAPI route for the home page (index)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "query": None, "answer": None})

# FastAPI route to send and receive messages
@app.post("/send_message")
async def send_message(request: Request):
    data = await request.json()
    user_message = data.get('message')
    global chat_history
    global chat_history_string

    # Add user's message to the chat history
    chat_history.append({"user": user_message})

    if user_message:
        # Query the database for matching context
        results = query_database(user_message, top_k=1, context_range=5)
        if results:
            matched_context = results[0]["context"]
            # Use Gemini API to generate AI response
            bot_response = generate_ai_response(user_message, matched_context, chat_history_string)
        else:
            bot_response = "Sorry, I could not find an answer to your question."

        # Update the chat history string
        chat_history_string += f"User: {user_message} \n"
        chat_history_string += f"Bot: {bot_response} \n"

        # Add bot response and context to chat history
        chat_history.append({'bot': bot_response, 'context': matched_context})

        return JSONResponse({"response": bot_response, "context": matched_context})

    return JSONResponse({"response": "No message received!"})
