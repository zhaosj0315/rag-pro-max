"""
FastAPI服务器
提供RESTful API接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from src.logging import LogManager
from src.utils.enhanced_cache import smart_cache_manager

logger = LogManager()

# 数据模型
class QueryRequest(BaseModel):
    query: str
    kb_name: str
    top_k: Optional[int] = 5
    use_cache: Optional[bool] = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    cached: bool = False

class KnowledgeBaseInfo(BaseModel):
    name: str
    document_count: int
    created_at: str
    size_mb: float

# FastAPI应用
app = FastAPI(
    title="RAG Pro Max API",
    description="RAG Pro Max RESTful API接口",
    version="1.7.2"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "RAG Pro Max API v1.7.2", "status": "running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "2025-12-10"}

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """查询知识库"""
    try:
        # 这里集成实际的查询逻辑
        # 暂时返回模拟数据
        
        result = {
            "answer": f"针对查询'{request.query}'的回答",
            "sources": [
                {
                    "file_name": "example.pdf",
                    "score": 0.95,
                    "text": "相关文档片段..."
                }
            ],
            "metadata": {
                "kb_name": request.kb_name,
                "query_time": "0.5s",
                "top_k": request.top_k
            },
            "cached": False
        }
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"API查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-bases", response_model=List[KnowledgeBaseInfo])
async def list_knowledge_bases():
    """列出所有知识库"""
    try:
        # 模拟知识库列表
        kbs = [
            {
                "name": "示例知识库",
                "document_count": 10,
                "created_at": "2025-12-10",
                "size_mb": 25.6
            }
        ]
        
        return [KnowledgeBaseInfo(**kb) for kb in kbs]
        
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        return smart_cache_manager.cache.get_stats()
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache")
async def clear_cache():
    """清空缓存"""
    try:
        smart_cache_manager.cache.clear()
        return {"message": "缓存已清空"}
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务器"""
    logger.info(f"🚀 启动FastAPI服务器: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api_server()
