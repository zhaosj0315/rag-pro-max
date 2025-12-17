"""
RAG Pro Max RESTful API Server
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

app = FastAPI(
    title="RAG Pro Max API",
    description="智能文档问答系统 API",
    version="1.8.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class QueryRequest(BaseModel):
    question: str
    kb_name: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    kb_name: str
    processing_time: float

class KBInfo(BaseModel):
    name: str
    document_count: int
    created_at: str
    size_mb: float

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

# API路由
@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "RAG Pro Max API",
        "version": "1.8.0",
        "status": "running",
        "endpoints": [
            "/docs - API文档",
            "/api/upload - 上传文档",
            "/api/query - 问答查询", 
            "/api/kb - 知识库管理"
        ]
    }

@app.post("/api/upload", response_model=APIResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    kb_name: str = Form(...)
):
    """上传文档到知识库"""
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        # 保存上传的文件
        for file in files:
            if file.size > 100 * 1024 * 1024:  # 100MB限制
                raise HTTPException(400, f"文件 {file.filename} 过大")
            
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            uploaded_files.append(file_path)
        
        # 调用文档处理逻辑
        from src.processors.enhanced_upload_handler import EnhancedUploadHandler
        
        handler = EnhancedUploadHandler()
        result = handler.process_files(uploaded_files, kb_name)
        
        # 清理临时文件
        shutil.rmtree(temp_dir)
        
        return APIResponse(
            success=True,
            message=f"成功上传 {len(files)} 个文件到知识库 '{kb_name}'",
            data={
                "kb_name": kb_name,
                "file_count": len(files),
                "processed_documents": result.get("document_count", 0)
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"上传失败: {str(e)}"
        )

@app.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """查询知识库"""
    try:
        import time
        start_time = time.time()
        
        # 加载知识库
        from src.kb.kb_loader import KBLoader
        from src.chat.chat_engine import ChatEngine
        
        kb_loader = KBLoader()
        chat_engine = ChatEngine()
        
        # 检查知识库是否存在
        kb_path = f"vector_db_storage/{request.kb_name}"
        if not os.path.exists(kb_path):
            raise HTTPException(404, f"知识库 '{request.kb_name}' 不存在")
        
        # 加载知识库
        index = kb_loader.load_knowledge_base(request.kb_name)
        if not index:
            raise HTTPException(500, "知识库加载失败")
        
        # 执行查询
        response = chat_engine.query(
            query=request.question,
            index=index,
            top_k=request.top_k
        )
        
        # 提取源文档信息
        sources = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                sources.append({
                    "text": getattr(node, 'text', '')[:200] + "...",
                    "score": getattr(node, 'score', 0.0),
                    "metadata": getattr(node, 'metadata', {})
                })
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=str(response),
            sources=sources,
            kb_name=request.kb_name,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"查询失败: {str(e)}")

@app.get("/api/kb", response_model=List[KBInfo])
async def list_knowledge_bases():
    """获取知识库列表"""
    try:
        kb_list = []
        kb_dir = "vector_db_storage"
        
        if os.path.exists(kb_dir):
            for kb_name in os.listdir(kb_dir):
                kb_path = os.path.join(kb_dir, kb_name)
                if os.path.isdir(kb_path):
                    # 获取知识库信息
                    manifest_path = os.path.join(kb_path, "manifest.json")
                    doc_count = 0
                    created_at = datetime.fromtimestamp(os.path.getctime(kb_path)).isoformat()
                    
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                doc_count = len(manifest.get('files', []))
                        except:
                            pass
                    
                    # 计算目录大小
                    size_bytes = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(kb_path)
                        for filename in filenames
                    )
                    size_mb = size_bytes / (1024 * 1024)
                    
                    kb_list.append(KBInfo(
                        name=kb_name,
                        document_count=doc_count,
                        created_at=created_at,
                        size_mb=round(size_mb, 2)
                    ))
        
        return kb_list
        
    except Exception as e:
        raise HTTPException(500, f"获取知识库列表失败: {str(e)}")

@app.delete("/api/kb/{kb_name}", response_model=APIResponse)
async def delete_knowledge_base(kb_name: str):
    """删除知识库"""
    try:
        kb_path = os.path.join("vector_db_storage", kb_name)
        
        if not os.path.exists(kb_path):
            raise HTTPException(404, f"知识库 '{kb_name}' 不存在")
        
        shutil.rmtree(kb_path)
        
        return APIResponse(
            success=True,
            message=f"知识库 '{kb_name}' 已删除"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"删除失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.8.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
