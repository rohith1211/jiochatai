from sentence_transformers import SentenceTransformer
import torch
import chromadb
import numpy as np

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Chroma Client and Collection
client = chromadb.PersistentClient(path="db")
collection = client.get_collection("sentence_embeddings_collection")

# Query the Database
def query_database(query, top_k=1):
    """
    Searches the Chroma database for the most relevant full answer.
    :param query: User's search query
    :param top_k: Number of top results to retrieve
    :return: Full answer to the query
    """
    # Preprocess the query
    query_embedding = model.encode(query, convert_to_tensor=True)
    query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=0).tolist()

    # Perform a nearest neighbor search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Retrieve the full answer from the results
    matched_answers = []
    for result in results["metadatas"][0]:
        full_answer = result["full_answer"]  # Extract full answer
        matched_answers.append(full_answer)

    return matched_answers

# Main Functionality
if __name__ == "__main__":
    # Prompt user for query input
    user_query = input("Enter your query: ")

    # Retrieve results from the existing database
    results = query_database(user_query, top_k=1)  # Adjust top_k if you want more than one result

    # Display results
    if results:
        print("\nMatched Answer:")
        print(results[0])  # Display the full answer
    else:
        print("No relevant answer found.")
