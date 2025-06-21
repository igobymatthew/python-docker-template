"""Example RAG engine using LlamaIndex and Mistral-7B."""

import os
import time

import chromadb
import torch
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.vector_stores.chroma import ChromaVectorStore


DOCUMENTS_DIR = "data"
INDEX_PATH = "./index_storage"
DB_PATH = "./rag_db"


def main() -> None:
    """Set up the query engine and print status messages."""

    print("\U0001F4E6 Starting rag_engine setup...")
    start_time = time.time()

    # Step 1: Setup CUDA
    torch.set_default_device("cuda" if torch.cuda.is_available() else "cpu")
    print("\u2705 [Step 1] Device setup in", time.time() - start_time, "seconds")

    # Step 2: Load LLM (Mistral-7B)
    llm = HuggingFaceLLM(
        context_window=3900,
        max_new_tokens=256,
        generate_kwargs={
            "temperature": 0.2,
            "top_p": 0.95,
            "do_sample": True,
            "pad_token_id": 2,  # Mistral's padding ID is 2
        },
        tokenizer_name="mistralai/Mistral-7B-Instruct-v0.1",
        model_name="mistralai/Mistral-7B-Instruct-v0.1",
        revision="Q4_0",
        device_map="auto",
    )
    Settings.llm = llm
    print("\u2705 [Step 2] LLM loaded in", time.time() - start_time, "seconds")

    # Step 3: Embeddings
    embed_model = HuggingFaceEmbedding(model_name="thenlper/gte-base")
    Settings.embed_model = embed_model
    print("\u2705 [Step 3] Embedding model loaded in", time.time() - start_time, "seconds")

    # Step 4: Add SentenceSplitter (chunk_size=512, overlap=50)
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    print("\u2705 [Step 4] Chunking config set in", time.time() - start_time, "seconds")

    # Step 5: Load .md documents with file metadata
    documents = SimpleDirectoryReader(
        input_dir=DOCUMENTS_DIR,
        recursive=True,
        required_exts=[".md"],
        file_metadata=lambda fn: {"source": fn},
    ).load_data()
    print("\u2705 [Step 5] Documents loaded in", time.time() - start_time, "seconds")

    # Step 6: Setup ChromaDB
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = chroma_client.get_or_create_collection("rag_collection")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    print("\u2705 [Step 6] CHROMA initialized in", time.time() - start_time, "seconds")

    # Step 7: Indexing
    if os.path.exists(INDEX_PATH) and os.path.exists(os.path.join(INDEX_PATH, "docstore.json")):
        print("\U0001F4E6 Loading existing index from disk...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
        index = load_index_from_storage(storage_context, vector_store=vector_store)
    else:
        print("\U0001F195 Building new index and saving to disk...")
        index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)
        index.storage_context.persist(persist_dir=INDEX_PATH)

    query_engine = index.as_query_engine(similarity_top_k=5)
    print("\u2705 RAG engine setup complete. Ready for queries!")

    # Keep the object in scope so it can be imported elsewhere
    return query_engine


if __name__ == "__main__":
    main()

