import os
import sys
import re
from bs4 import BeautifulSoup
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm.auto import tqdm

def load_and_parse_xml(file_path: str):
    """
    Loads the cleaned XML file and extracts meaningful text chunks. This version
    correctly links facts to their periods using the contextRef attribute and
    handles the default XML namespace.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

    soup = BeautifulSoup(content, 'lxml-xml')
    
    # --- STEP 1: Pre-process and map all contexts by their ID ---
    # This correctly finds <context> tags, which are in the default namespace.
    contexts = {}
    for context in soup.find_all('context'):
        context_id = context.get('id')
        if not context_id:
            continue
            
        period_info = "N/A"
        period = context.find('period')
        if period:
            instant = period.find('instant')
            if instant and instant.string:
                period_info = instant.string.strip()
            else:
                start = period.find('startDate')
                end = period.find('endDate')
                if start and start.string and end and end.string:
                    period_info = f"{start.string.strip()} to {end.string.strip()}"
        contexts[context_id] = period_info

    # --- STEP 2: Iterate through all tags and extract facts and their metadata ---
    docs = []
    # Find all tags that have a contextRef attribute (these are the financial facts)
    for tag in soup.find_all(contextRef=True):
        # We only care about tags with direct, non-empty text content
        if tag.string and tag.string.strip():
            
            context_id = tag.get('contextRef')
            period = contexts.get(context_id, "N/A") # Look up period from our map
            
            # Build the document and metadata
            text_for_embedding = f"{tag.name}: {tag.string.strip()}"
            metadata = {
                'source_tag': tag.name,
                'text': tag.string.strip(),
                'period': period  # This will now be correctly populated
            }
            
            docs.append({'text': text_for_embedding, 'metadata': metadata})
            
    return docs

def initialize_pinecone(api_key: str, index_name: str, dimension: int):
    """Initializes Pinecone and creates a new index if it doesn't exist."""
    pc = Pinecone(api_key=api_key)
    
    if index_name not in pc.list_indexes().names():
        print(f"Creating a new Pinecone index: '{index_name}'")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print("Index created successfully.")
    else:
        print(f"Index '{index_name}' already exists.")
        
    return pc.Index(index_name)

def embed_and_upsert(index, docs, embeddings_model, batch_size=32):
    """
    Creates vector embeddings for the documents and upserts them to Pinecone in batches.
    """
    print(f"Embedding and upserting {len(docs)} documents to Pinecone...")
    for i in tqdm(range(0, len(docs), batch_size)):
        i_end = min(i + batch_size, len(docs))
        batch = docs[i:i_end]
        
        texts_to_embed = [item['text'] for item in batch]
        metadata_to_upsert = [item['metadata'] for item in batch]
        
        embeddings = embeddings_model.embed_documents(texts_to_embed)
        ids = [f"doc_{i+j}" for j in range(len(batch))]
        vectors_to_upsert = list(zip(ids, embeddings, metadata_to_upsert))
        
        index.upsert(vectors=vectors_to_upsert)
    print("Upsert process completed.")

def query_pinecone(index, query_text: str, embeddings_model, top_k=5):
    """Queries the Pinecone index and returns the top k results."""
    print(f"\n--- Querying for: '{query_text}' ---")
    
    query_embedding = embeddings_model.embed_query(query_text)
    
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    if results['matches']:
        for i, match in enumerate(results['matches']):
            print(f"Result {i+1} (Score: {match['score']:.4f}):")
            print(f"  Text: {match['metadata'].get('text', 'N/A')}")
            print(f"  Tag: {match['metadata'].get('source_tag', 'N/A')}")
            print(f"  Period: {match['metadata'].get('period', 'N/A')}")
            print("-" * 20)
    else:
        print("No results found.")


if __name__ == '__main__':
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    
    if not PINECONE_API_KEY:
        print("Error: Please set your 'PINECONE_API_KEY' environment variable.")
        sys.exit(1)
        
    PINECONE_INDEX_NAME = "sec-filings-aapl"
    XML_FILE_PATH = "cleaned_financial_data.xml"
    
    print("Initializing local Hugging Face embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="hkunlp/instructor-large",
        model_kwargs={'device': 'cpu'}
    )
    EMBEDDING_DIMENSION = 768

    documents = load_and_parse_xml(XML_FILE_PATH)
    if not documents:
        print("No data was loaded from the XML file. Exiting.")
        sys.exit(1)

    pinecone_index = initialize_pinecone(PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBEDDING_DIMENSION)

    # Optional: Uncomment the next two lines to clear the index before uploading new data
    # print("Clearing all previous entries from the index...")
    # pinecone_index.delete(delete_all=True)

    embed_and_upsert(pinecone_index, documents, embeddings)
    
    print("\n--- Starting Queries ---")
    query_pinecone(pinecone_index, "What were the total revenues for the last three years?", embeddings)
    query_pinecone(pinecone_index, "How much was spent on research and development in 2024?", embeddings)
    query_pinecone(pinecone_index, "What was the net income in 2023?", embeddings)

