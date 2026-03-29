# RAG知识库同步脚本
# 自动同步仓库内容到ChromaDB向量数据库

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 配置
REPO_PATH = Path("D:/block-building-teaching-system")
CHROMA_PATH = Path("D:/block-building-teaching-system/.chromadb")

def calculate_file_hash(file_path):
    """计算文件哈希，用于检测变更"""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def split_document(content, chunk_size=500, overlap=50):
    """将文档分割成小块"""
    chunks = []
    words = content.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def extract_metadata(file_path):
    """从文件路径提取元数据"""
    relative_path = file_path.relative_to(REPO_PATH)
    parts = relative_path.parts
    
    metadata = {
        "source": str(relative_path),
        "age_group": None,
        "theme": None,
        "type": None,
        "modified": datetime.now().isoformat()
    }
    
    # 提取年龄段
    age_groups = ["3-4岁", "4-5岁", "5-6岁", "6-7岁", "4岁", "5岁", "6岁"]
    for age in age_groups:
        if age in str(parts):
            metadata["age_group"] = age
            break
    
    # 提取主题
    themes = ["桥梁", "城堡", "超市", "厨房", "卧室", "兵马俑", "西游记", 
              "工作细胞", "恐龙", "机器人", "桥梁搭建", "动物", "交通"]
    for theme in themes:
        if theme in str(parts):
            metadata["theme"] = theme
            break
    
    # 提取类型
    if "教案" in str(parts):
        metadata["type"] = "teaching-plan"
    elif "游戏" in str(parts):
        metadata["type"] = "game"
    elif "英语" in str(parts) or "bilingual" in str(parts):
        metadata["type"] = "bilingual"
    else:
        metadata["type"] = "other"
    
    return metadata

def scan_repository():
    """扫描仓库中的所有文档"""
    documents = []
    
    for root, dirs, files in os.walk(REPO_PATH):
        # 跳过隐藏目录和特殊目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        
        for file in files:
            if file.endswith(('.md', '.mdx', '.txt')) and not file.startswith('.'):
                file_path = Path(root) / file
                
                # 跳过非内容文件
                if any(skip in str(file_path) for skip in ['README', 'LICENSE', 'CHANGELOG']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) < 50:  # 跳过太短的文件
                        continue
                    
                    metadata = extract_metadata(file_path)
                    chunks = split_document(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "id": f"{file_path.stem}_{i}_{calculate_file_hash(file_path)[:8]}",
                            "content": chunk,
                            "metadata": {
                                **metadata,
                                "chunk_index": i,
                                "total_chunks": len(chunks)
                            }
                        }
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return documents

def save_sync_state(documents):
    """保存同步状态"""
    state_file = REPO_PATH / ".sync_state.json"
    state = {
        "last_sync": datetime.now().isoformat(),
        "document_count": len(documents),
        "files": [
            {
                "source": doc["metadata"]["source"],
                "hash": doc["id"].split("_")[1] if "_" in doc["id"] else None
            }
            for doc in documents
        ]
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    print("🔄 开始扫描仓库...")
    
    documents = scan_repository()
    print(f"✅ 扫描完成，共发现 {len(documents)} 个文档块")
    
    print("💾 保存同步状态...")
    save_sync_state(documents)
    
    print("🎉 同步完成！")
    print(f"📁 文档总数: {len(documents)}")
    print(f"📍 仓库路径: {REPO_PATH}")

if __name__ == "__main__":
    main()
