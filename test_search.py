import chromadb

from sentence_transformers import SentenceTransformer


VECTOR_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "web_scraper_rag"


print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


collection = client.get_collection(
    name=COLLECTION_NAME
)


print("\nNumber of chunks in ChromaDB:")
print(collection.count())


question = "What is the SKU ID?"


print("\nSearching for:")
print(question)


question_embedding = embedding_model.encode(
    question
).tolist()


results = collection.query(
    query_embeddings=[question_embedding],
    n_results=10
)


print("\n==============================")
print("SEARCH RESULTS")
print("==============================")


documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]


for i in range(len(documents)):

    print("\n------------------------------")

    print(f"RESULT {i + 1}")

    print("------------------------------")

    print("\nDistance:")
    print(distances[i])

    print("\nTitle:")
    print(metadatas[i]["title"])

    print("\nURL:")
    print(metadatas[i]["url"])

    print("\nContent:")
    print(documents[i])