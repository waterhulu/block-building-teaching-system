import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import re

REPO_PATH = Path("D:/block-building-teaching-system")
CHROMA_PATH = Path("D:/block-building-teaching-system/.chromadb")
GITHUB_REPO = "waterhulu/block-building-teaching-system"
DATA_FILE = CHROMA_PATH / "knowledge_base.json"

def calculate_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def split_document(content, chunk_size=500, overlap=50):
    chunks = []
    words = content.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def extract_metadata(file_path):
    relative_path = file_path.relative_to(REPO_PATH)
    parts = relative_path.parts
    
    metadata = {
        "source": str(relative_path),
        "age_group": None,
        "theme": None,
        "type": None,
        "modified": datetime.now().isoformat()
    }
    
    age_groups = ["3-4岁", "4-5岁", "5-6岁", "6-7岁", "4岁", "5岁", "6岁"]
    for age in age_groups:
        if age in str(parts):
            metadata["age_group"] = age
            break
    
    themes = ["桥梁", "城堡", "超市", "厨房", "卧室", "兵马俑", "西游记", 
              "工作细胞", "恐龙", "机器人", "桥梁搭建", "动物", "交通"]
    for theme in themes:
        if theme in str(parts):
            metadata["theme"] = theme
            break
    
    if "教案" in str(parts):
        metadata["type"] = "teaching-plan"
    elif "游戏" in str(parts):
        metadata["type"] = "game"
    elif "英语" in str(parts) or "bilingual" in str(parts):
        metadata["type"] = "bilingual"
    else:
        metadata["type"] = "other"
    
    return metadata

def scan_local_repository():
    documents = []
    
    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        
        for file in files:
            if file.endswith(('.md', '.mdx', '.txt')) and not file.startswith('.'):
                file_path = Path(root) / file
                
                if any(skip in str(file_path) for skip in ['README', 'LICENSE', 'CHANGELOG']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) < 50:
                        continue
                    
                    metadata = extract_metadata(file_path)
                    chunks = split_document(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "id": f"{file_path.stem}_{i}_{calculate_file_hash(file_path)[:8]}",
                            "content": chunk,
                            "metadata": {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
                        }
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return documents

def sync_to_json(documents):
    output_file = CHROMA_PATH / "knowledge_base.json"
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Saved {len(documents)} documents to {output_file}")
    return output_file

def search_knowledge_base(query, documents, top_k=3):
    keywords = query.lower().split()
    results = []
    
    for doc in documents:
        content_lower = doc['content'].lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            results.append((doc, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:top_k]]

def save_sync_state(documents):
    state_file = REPO_PATH / ".sync_state.json"
    state = {
        "last_sync": datetime.now().isoformat(),
        "document_count": len(documents),
        "files": [{"source": doc["metadata"]["source"]} for doc in documents]
    }
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    print("=== Syncing repository to RAG knowledge base ===")
    
    documents = scan_local_repository()
    print(f"[OK] Scanned {len(documents)} document chunks")
    
    sync_to_json(documents)
    save_sync_state(documents)
    
    print("[OK] Sync complete!")
    print(f"ChromaDB path: {CHROMA_PATH}")
    
    test_query = "桥梁搭建 教案"
    results = search_knowledge_base(test_query, documents)
    print(f"\n[Test] Query '{test_query}' returned {len(results)} results")

if __name__ == "__main__":
    main()
