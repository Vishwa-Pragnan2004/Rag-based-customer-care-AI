import os
import logging
import math
import requests

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "text-embedding-004"
        self.chunks = []
        self.embeddings = []  # List of embedding vectors
        self.is_ready = False
        self.ingest()

    def _get_embedding(self, text: str) -> list:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": f"models/{self.model_name}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            res.raise_for_status()
            res_json = res.json()
            return res_json.get("embedding", {}).get("values", [])
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def _get_embeddings_batch(self, texts: list) -> list:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents?key={api_key}"
            headers = {"Content-Type": "application/json"}
            reqs = []
            for t in texts:
                reqs.append({
                    "model": f"models/{self.model_name}",
                    "content": {
                        "parts": [{"text": t}]
                    }
                })
            payload = {"requests": reqs}
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            res.raise_for_status()
            res_json = res.json()
            embs = res_json.get("embeddings", [])
            return [e.get("values", []) for e in embs]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Fallback to single requests if batch fails
            logger.info("Retrying with individual embedding requests...")
            results = []
            for t in texts:
                results.append(self._get_embedding(t))
            return results

    def ingest(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.chunks = []
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory not found: {data_dir}")
            return

        for f in os.listdir(data_dir):
            if f.endswith('.txt'):
                try:
                    with open(os.path.join(data_dir, f), 'r', encoding='utf-8') as file:
                        text = file.read()
                        # Chunking window (500 characters, 100 overlap)
                        self.chunks.extend([text[i:i+500] for i in range(0, len(text), 400)])
                except Exception as e:
                    logger.error(f"Error reading file {f}: {e}")

        if not self.chunks:
            logger.warning("No chunks found to ingest.")
            return

        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured, skipping ingestion embedding step. Local RAG will be unavailable until key is set.")
            return

        logger.info(f"Generating embeddings for {len(self.chunks)} chunks using Gemini...")
        embeddings = self._get_embeddings_batch(self.chunks)
        
        # Filter out empty embeddings (in case of API failures)
        valid_chunks = []
        valid_embeddings = []
        for c, e in zip(self.chunks, embeddings):
            if e:
                valid_chunks.append(c)
                valid_embeddings.append(e)
        
        self.chunks = valid_chunks
        self.embeddings = valid_embeddings
        
        if self.embeddings:
            self.is_ready = True
            logger.info("RAG ingestion completed successfully.")
        else:
            logger.error("Failed to generate any embeddings.")

    def retrieve(self, query: str, top_k=2):
        # Dynamically check for key update in case it was missing during init
        if not self.is_ready:
            self.ingest()
            
        if not self.is_ready or not self.embeddings:
            logger.warning("RAG service is not ready. Returning empty retrieval results.")
            return []
            
        q_emb = self._get_embedding(query)
        if not q_emb:
            return []

        # Calculate cosine similarity in pure Python
        scored_chunks = []
        for i, emb in enumerate(self.embeddings):
            score = self._cosine_similarity(q_emb, emb)
            scored_chunks.append({"content": self.chunks[i], "score": score})

        # Sort by similarity score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def _cosine_similarity(self, v1, v2):
        if len(v1) != len(v2) or not v1 or not v2:
            return 0.0
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x * x for x in v1))
        magnitude2 = math.sqrt(sum(x * x for x in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
