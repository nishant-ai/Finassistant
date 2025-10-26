import os
import re
from bs4 import BeautifulSoup
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class VectorStore:
    """
    Handles parsing, embedding, indexing, and querying of financial data.
    """
    def __init__(self, pinecone_api_key: str, index_name: str):
        """
        Initializes the embeddings model and the Pinecone vector store.
        """
        print("Initializing embeddings model: 'sentence-transformers/all-MiniLM-L6-v2'...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
        
        # --- THIS IS THE FIX ---
        # Instead of accessing a non-existent '.embedding_dim' attribute,
        # we create a dummy embedding and check its length. This is the robust way.
        print("Determining embedding dimension...")
        dummy_embedding = self.embeddings_model.embed_query("test")
        dimension = len(dummy_embedding)
        print(f"Embedding dimension is {dimension}.")

        self.index = self._initialize_pinecone(pinecone_api_key, index_name, dimension)

    def _initialize_pinecone(self, api_key: str, index_name: str, dimension: int):
        """Initializes Pinecone and creates a new index if it doesn't exist."""
        pc = Pinecone(api_key=api_key)
        
        if index_name not in pc.list_indexes().names():
            print(f"Creating a new Pinecone index: '{index_name}'")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            print("Index created successfully.")
        else:
            print(f"Index '{index_name}' already exists.")
            
        return pc.Index(index_name)

    def _load_and_parse_xml(self, file_path: str):
        """Loads the cleaned XML and extracts text chunks with metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
            return []

        soup = BeautifulSoup(content, 'lxml-xml')
        contexts = {}
        for context in soup.find_all('context'):
            context_id = context.get('id')
            if not context_id: continue
            
            period_info = "N/A"
            period = context.find('period')
            if period:
                instant = period.find('instant')
                if instant and instant.string:
                    period_info = instant.string.strip()
                else:
                    start, end = period.find('startDate'), period.find('endDate')
                    if start and start.string and end and end.string:
                        period_info = f"{start.string.strip()} to {end.string.strip()}"
            contexts[context_id] = period_info

        docs = []
        for tag in soup.find_all(contextRef=True):
            if tag.string and tag.string.strip():
                context_id = tag.get('contextRef')
                period = contexts.get(context_id, "N/A")
                text_for_embedding = f"{tag.name}: {tag.string.strip()}"
                metadata = {
                    'source_tag': tag.name,
                    'text': tag.string.strip(),
                    'period': period
                }
                docs.append({'text': text_for_embedding, 'metadata': metadata})
        return docs

    # def embed_and_upsert(self, file_path: str, document_id: str, batch_size: int = 128):
    #     """Parses the XML, creates embeddings, and upserts them to Pinecone."""
    #     docs = self._load_and_parse_xml(file_path)
    #     if not docs:
    #         print("No documents were parsed. Aborting upsert.")
    #         return

    #     print(f"Embedding and upserting {len(docs)} documents to Pinecone...")
    #     for i in tqdm(range(0, len(docs), batch_size)):
    #         i_end = min(i + batch_size, len(docs))
    #         batch = docs[i:i_end]
            
    #         texts_to_embed = [item['text'] for item in batch]
            
    #         metadata_to_upsert = []
    #         for item in batch:
    #             meta = item['metadata'].copy()
    #             meta['doc_id'] = document_id
    #             metadata_to_upsert.append(meta)

            
    #         embeddings = self.embeddings_model.embed_documents(texts_to_embed)

    #         ids = [f"document_{document_id}_{i+j}" for j in range(len(batch))]
    #         vectors_to_upsert = list(zip(ids, embeddings, metadata_to_upsert))
            
    #         self.index.upsert(vectors=vectors_to_upsert)
    #     print("Upsert process completed.")

    def embed_and_upsert(self, file_path: str, document_id: str, ticker: str, batch_size: int = 128, max_workers: int = 4):
        """
        Parses a file, creates embeddings, and uses a thread pool to upsert batches in parallel.
        Now includes the ticker in the metadata.
        """
        print("Loading and parsing the document...")
        docs = self._load_and_parse_xml(file_path)
        if not docs:
            print("No documents were parsed from the file. Aborting.")
            return

        print(f"Starting parallel upsert for {len(docs)} chunks with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in tqdm(range(0, len(docs), batch_size), desc="Submitting batches"):
                # 1. Prepare the data for the current batch
                i_end = min(i + batch_size, len(docs))
                batch = docs[i:i_end]
                
                texts_to_embed = [item['text'] for item in batch]
                
                # --- KEY CHANGE IS HERE ---
                metadata_to_upsert = []
                for item in batch:
                    meta = item['metadata'].copy()
                    meta['doc_id'] = document_id
                    meta['ticker'] = ticker.upper() # Add the ticker for caching/checking
                    metadata_to_upsert.append(meta)
                
                # 2. Create embeddings for this specific batch
                embeddings = self.embeddings_model.embed_documents(texts_to_embed)
                
                # 3. Create unique IDs for this specific batch
                ids = [f"{document_id}_{i+j}" for j in range(len(batch))]
                
                # 4. Zip all components together for the upsert payload
                vectors_to_upsert = list(zip(ids, embeddings, metadata_to_upsert))
                
                # 5. Submit the upsert task to a worker thread
                future = executor.submit(self.index.upsert, vectors=vectors_to_upsert)
                futures.append(future)

            # 6. Monitor the completion of the background tasks
            print("\nAll batches submitted. Waiting for uploads to complete...")
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing batches"):
                try:
                    future.result()
                except Exception as e:
                    print(f"\nAn error occurred during a parallel upsert batch: {e}")
                    
        print("\nParallel upsert process completed successfully.")

    def check_if_ticker_exists(self, ticker: str) -> str | None:
        """
        Checks if vectors for a given ticker exist by querying the metadata.
        Returns the existing document_id if found, otherwise returns None.
        """
        try:
            # We query with a dummy vector because we only care about the metadata filter.
            # Pinecone requires a vector for a query operation.
            dummy_vector = [0.0] * self.index.describe_index_stats()['dimension']
            
            result = self.index.query(
                vector=dummy_vector,
                top_k=1,
                filter={"ticker": {"$eq": ticker.upper()}},
                include_metadata=True
            )
            
            if result['matches']:
                # If we found at least one chunk, we can grab its doc_id.
                existing_doc_id = result['matches'][0]['metadata']['doc_id']
                print(f"✅ Found existing document for ticker {ticker} with doc_id: {existing_doc_id}")
                return existing_doc_id
            
            return None
        except Exception as e:
            print(f"⚠️ Error checking for ticker {ticker}: {e}. Will proceed as if it doesn't exist.")
            return None

    def query(self, query_text: str, document_id: str, top_k: int = 5):
        """Queries the Pinecone index and returns the top k results."""
        query_embedding = self.embeddings_model.embed_query(query_text)

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"doc_id": {"$eq": document_id}} # This is the filter logic
        )
        return results.get('matches', [])
