import os, faiss, numpy as np
from sentence_transformers import SentenceTransformer
class RAGService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []
        self.is_ready = False
        self.ingest()
    def ingest(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.chunks = []
        for f in os.listdir(data_dir):
            if f.endswith('.txt'):
                text = open(os.path.join(data_dir, f), 'r', encoding='utf-8').read()
                self.chunks.extend([text[i:i+500] for i in range(0, len(text), 400)])
        if self.chunks:
            emb = self.model.encode(self.chunks)
            self.index = faiss.IndexFlatL2(emb.shape[1])
            self.index.add(np.array(emb))
            self.is_ready = True
    def retrieve(self, query: str, top_k=2):
        if not self.is_ready: return []
        q_emb = self.model.encode([query])
        D, I = self.index.search(np.array(q_emb), top_k)
        return [{"content": self.chunks[i], "score": float(D[0][j])} for j, i in enumerate(I[0]) if i < len(self.chunks)]
