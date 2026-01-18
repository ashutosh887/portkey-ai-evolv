# ML Core Engine - Step-by-Step Algorithm Explanation

## Example Input Data

Let's trace through the pipeline with 4 example prompts:

```csv
prompt
"Summarize this article in 100 words"
"Give me a brief summary of the document"
"Translate this text to French"
"Convert the following to Spanish"
```

---

## Step 0: Normalization

**File:** `normalization.py`

```python
def normalize_and_id(prompts: List[str]) -> Dict[str, str]:
    result = {}
    for prompt in prompts:
        # Generate unique ID
        prompt_id = hashlib.md5(prompt.encode()).hexdigest()[:12]
        
        # Normalize text
        normalized = prompt.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        result[prompt_id] = normalized
    return result
```

**Example Output:**
```python
{
    "a1b2c3d4e5f6": "summarize this article in 100 words",
    "f7e8d9c0b1a2": "give me a brief summary of the document",
    "1234abcd5678": "translate this text to french",
    "9876fedc4321": "convert the following to spanish"
}
```

---

## Step 1: Embedding

**File:** `embedding.py`

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-en")

def embed_prompts(prompts: Dict[str, str]) -> Dict[str, List[float]]:
    embeddings = {}
    for prompt_id, text in prompts.items():
        # Convert text to 1024-dimensional vector
        vector = model.encode(text)  # Returns numpy array of shape (1024,)
        embeddings[prompt_id] = vector.tolist()
    return embeddings
```

**Example Output:**
```python
{
    "a1b2c3d4e5f6": [0.23, -0.45, 0.12, ..., 0.87],   # 1024 numbers (summarize)
    "f7e8d9c0b1a2": [0.21, -0.43, 0.11, ..., 0.85],   # 1024 numbers (summary) - SIMILAR!
    "1234abcd5678": [-0.15, 0.67, -0.33, ..., 0.44],  # 1024 numbers (translate)
    "9876fedc4321": [-0.17, 0.65, -0.35, ..., 0.42]   # 1024 numbers (convert) - SIMILAR!
}
```

**Key insight:** Similar prompts → Similar vectors!

---

## Step 2: HDBSCAN Clustering

**File:** `clustering.py`

```python
import hdbscan
import numpy as np

def cluster_hdbscan(embeddings: Dict[str, List[float]]) -> Tuple[...]:
    # Extract IDs and vectors
    prompt_ids = list(embeddings.keys())
    # ["a1b2c3d4e5f6", "f7e8d9c0b1a2", "1234abcd5678", "9876fedc4321"]
    
    embedding_matrix = np.array([embeddings[pid] for pid in prompt_ids])
    # Shape: (4, 1024) - 4 prompts, 1024 dimensions each
    
    # Normalize vectors (unit length)
    from sklearn.preprocessing import normalize
    embedding_matrix_normalized = normalize(embedding_matrix, norm='l2')
    
    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,           # Need at least 2 prompts per cluster
        min_samples=1,                # Core point threshold
        metric='euclidean',           # Distance metric
        cluster_selection_epsilon=0.15 # Merge distance
    )
    
    cluster_labels = clusterer.fit_predict(embedding_matrix_normalized)
    # Returns: [0, 0, 1, 1]
    #          ↑  ↑  ↑  ↑
    #          |  |  |  └── "convert to spanish" → Cluster 1
    #          |  |  └───── "translate to french" → Cluster 1
    #          |  └──────── "brief summary" → Cluster 0
    #          └─────────── "summarize article" → Cluster 0
```

**Example Output:**
```python
prompt_to_cluster = {
    "a1b2c3d4e5f6": 0,  # summarize → Cluster 0
    "f7e8d9c0b1a2": 0,  # summary   → Cluster 0 (same cluster!)
    "1234abcd5678": 1,  # translate → Cluster 1
    "9876fedc4321": 1   # convert   → Cluster 1 (same cluster!)
}

cluster_to_prompts = {
    0: ["a1b2c3d4e5f6", "f7e8d9c0b1a2"],  # Summarization family
    1: ["1234abcd5678", "9876fedc4321"]   # Translation family
}
```

---

## Step 3: Compute Cluster Centroids

```python
def compute_cluster_centroids(embeddings, cluster_to_prompts):
    centroids = {}
    
    for cluster_id, prompt_ids in cluster_to_prompts.items():
        # Get all embeddings in this cluster
        cluster_embeddings = [embeddings[pid] for pid in prompt_ids]
        
        # Centroid = average of all vectors
        centroid = np.mean(cluster_embeddings, axis=0)
        centroids[cluster_id] = centroid.tolist()
    
    return centroids
```

**Example Output:**
```python
centroids = {
    0: [0.22, -0.44, 0.115, ..., 0.86],  # Average of summarization prompts
    1: [-0.16, 0.66, -0.34, ..., 0.43]   # Average of translation prompts
}
```

---

## Step 4: Build FAISS Index

**File:** `retrieval.py`

```python
import faiss
import numpy as np

class FAISSIndex:
    def __init__(self, dimension=1024):
        self.dimension = dimension
        # Create index (IVF = Inverted File for fast search)
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        self.id_map = []  # Maps FAISS index → prompt_id
    
    def add(self, embeddings: Dict[str, List[float]]):
        for prompt_id, vector in embeddings.items():
            # Normalize for cosine similarity
            vec = np.array([vector], dtype=np.float32)
            faiss.normalize_L2(vec)
            
            # Add to index
            self.index.add(vec)
            self.id_map.append(prompt_id)
    
    def search(self, query_vector: List[float], k=5):
        # Normalize query
        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Search for k nearest neighbors
        distances, indices = self.index.search(query, k)
        
        # Return (prompt_id, similarity) pairs
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                results.append((self.id_map[idx], float(dist)))
        return results
```

**Example Usage:**
```python
# Build index with 4 prompts
index = FAISSIndex(dimension=1024)
index.add(embeddings)

# Search for similar prompts
query = "Summarize the report"
query_vector = model.encode(query)  # [0.22, -0.43, ...]

results = index.search(query_vector, k=3)
# Returns:
# [
#     ("a1b2c3d4e5f6", 0.97),  # "summarize this article" - 97% similar
#     ("f7e8d9c0b1a2", 0.94),  # "brief summary" - 94% similar
#     ("1234abcd5678", 0.23)   # "translate to french" - 23% similar
# ]
```

---

## K-Means (Alternative to HDBSCAN)

```python
from sklearn.cluster import KMeans

def cluster_kmeans(embeddings, k=2):
    prompt_ids = list(embeddings.keys())
    embedding_matrix = np.array([embeddings[pid] for pid in prompt_ids])
    
    # K-Means with k=2 clusters
    kmeans = KMeans(n_clusters=k, random_state=42)
    cluster_labels = kmeans.fit_predict(embedding_matrix)
    # Returns: [0, 0, 1, 1] (same as HDBSCAN in this case)
    
    # Get centroids directly from KMeans
    centroids = kmeans.cluster_centers_
    # Shape: (2, 1024) - 2 centroids, 1024 dimensions each
```

---

## Summary Table

| Step | Input | Output | Algorithm |
|------|-------|--------|-----------|
| 0. Normalize | Raw prompts | ID → normalized text | Regex |
| 1. Embed | Normalized text | ID → 1024-dim vector | Sentence Transformer |
| 2. Cluster | Vectors | ID → cluster_id | HDBSCAN/K-Means |
| 3. Centroids | Vectors + clusters | cluster_id → centroid | Mean |
| 4. Index | Vectors | FAISS Index | FAISS IVF/HNSW |

---

## Visual Flow

```
"Summarize article" ──┐
                      │ Embed ──► [0.23, -0.45, ...] ──┐
"Brief summary"    ───┘                                │ Cluster ──► Cluster 0
                                                       │
"Translate French" ──┐                                 │
                     │ Embed ──► [-0.15, 0.67, ...] ───┘ Cluster ──► Cluster 1
"Convert Spanish"  ──┘
```
