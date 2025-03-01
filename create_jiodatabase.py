import re
import torch
import chromadb
from sentence_transformers import SentenceTransformer

# Text Preprocessing Function
def preprocess_text(text):
    """
    Preprocesses the input text by converting it to lowercase,
    removing extra spaces, and stripping punctuation.
    """
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Sentence Splitting Function
def split_into_sentences(text):
    """
    Splits the text into individual sentences using regular expressions.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

# Batch Processing Function
def process_in_batches(data_list, batch_size):
    """
    Splits a list into smaller batches of specified size.
    """
    for i in range(0, len(data_list), batch_size):
        yield data_list[i:i + batch_size]

# Function to read the FAQ pairs from the provided structure
def read_faq_pairs(file_path):
    faq_pairs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()  # Read the entire file content
        # Match the structure "Question: <question> Answer: <answer>"
        pattern = r'Question:\s*(.*?)\s*Answer:\s*(.*?)(?=Question:|$)'
        matches = re.findall(pattern, content, re.DOTALL)  # Using DOTALL to match multi-line answers
        for question, answer in matches:
            faq_pairs.append((question.strip(), answer.strip()))
    return faq_pairs

# Reading FAQ pairs from the text file
txt_file = "scraped_data/scraped_faq_data.txt"
faq_pairs = read_faq_pairs(txt_file)

# Preprocess Questions and Answers
all_sentences = []
sentence_to_answer_mapping = []  # This will store sentence-to-answer mapping
for question, answer in faq_pairs:
    # Split both question and answer into sentences for indexing
    sentences = split_into_sentences(question) + split_into_sentences(answer)
    all_sentences.extend(sentences)
    
    # Map each sentence to its corresponding full answer (the last one in the pair)
    for _ in range(len(sentences)):
        sentence_to_answer_mapping.append(answer)

# Preprocess all sentences
preprocessed_sentences = [preprocess_text(sentence) for sentence in all_sentences]

# Load Model and Generate Embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(preprocessed_sentences, convert_to_tensor=True)

# Normalize embeddings
normalized_embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

# Convert embeddings to a list of lists for compatibility with Chroma
embedding_list = normalized_embeddings.tolist()

# Initialize Chroma Client
client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection("sentence_embeddings_collection")

# Add Embeddings to Database in Chunks
max_batch_size = 5000  # Adjust based on memory limits
sentence_batches = list(process_in_batches(all_sentences, max_batch_size))
embedding_batches = list(process_in_batches(embedding_list, max_batch_size))

# Add each batch to the Chroma collection
for i, (sentence_batch, embedding_batch) in enumerate(zip(sentence_batches, embedding_batches)):
    # Create unique IDs for the batch
    batch_ids = [f"id_{i}_{j}" for j in range(len(sentence_batch))]
    
    # Add the batch to the database
    collection.add(
        ids=batch_ids,
        embeddings=embedding_batch,
        metadatas=[{"sentence": sentence, "full_answer": sentence_to_answer_mapping[i]} for i, sentence in enumerate(sentence_batch)]
    )
    print(f"Batch {i + 1}/{len(sentence_batches)} added successfully.")

print("Database preparation completed.")
