"""
FastAPI服务器
提供RESTful API接口
v2.0: 新增增量更新、多模态支持
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
import tempfile
from datetime import datetime

from src.app_logging import LogManager
from src.utils.enhanced_cache import smart_cache_manager
from src.kb.kb_manager import KBManager
from src.processors.multimodal_processor import MultimodalProcessor
from src.core.version import get_version_info

logger = LogManager()
version_info = get_version_info()
CURRENT_VERSION = version_info.get("version", "3.2.7")

# 原有数据模型
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

# v2.0 新增数据模型
class IncrementalUpdateRequest(BaseModel):
    kb_name: str
    file_paths: List[str]
    force_update: Optional[bool] = False

class IncrementalUpdateResponse(BaseModel):
    status: str
    changes: Dict[str, List[str]]
    processed_files: List[str]
    skipped_files: List[str]

class MultimodalQueryRequest(BaseModel):
    query: str
    kb_name: str
    include_images: Optional[bool] = True
    include_tables: Optional[bool] = True
    top_k: Optional[int] = 5

# FastAPI应用
app = FastAPI(
    title="RAG Pro Max API",
    description="Enterprise RAG System API Interface",
    version=CURRENT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化管理器
kb_manager = KBManager()
multimodal_processor = MultimodalProcessor()

@app.get("/")
async def root():
    """根路径"""
    return {"message": f"RAG Pro Max API v{CURRENT_VERSION}", "status": "running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": CURRENT_VERSION}

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

# ==================== v2.0 新增接口 ====================

@app.post("/incremental-update", response_model=IncrementalUpdateResponse)
async def incremental_update(request: IncrementalUpdateRequest):
    """增量更新知识库"""
    try:
        if not kb_manager.exists(request.kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 '{request.kb_name}' 不存在")
        
        changes = kb_manager.check_incremental_changes(request.kb_name, request.file_paths)
        if not changes:
            raise HTTPException(status_code=500, detail="无法检查文件变化")
        
        processed_files = []
        skipped_files = []
        
        if request.force_update:
            files_to_process = request.file_paths
        else:
            files_to_process = changes['new'] + changes['modified']
            skipped_files = changes['unchanged']
        
        # ⚠️ MOCK IMPLEMENTATION: This is a placeholder. Real processing logic needs to be connected to KBManager.
        logger.warning("Executing MOCK incremental update - no actual files are processed", stage="API")
        for file_path in files_to_process:
            try:
                processed_files.append(file_path)
            except Exception as e:
                logger.log_error(f"处理文件失败: {file_path}", str(e))
                continue
        
        if processed_files:
            kb_manager.mark_files_processed(request.kb_name, processed_files)
        
        return IncrementalUpdateResponse(
            status="success",
            changes=changes,
            processed_files=processed_files,
            skipped_files=skipped_files
        )
        
    except Exception as e:
        logger.log_error("增量更新失败", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-multimodal")
async def upload_multimodal_file(
    kb_name: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """上传多模态文件"""
    try:
        if not kb_manager.exists(kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 '{kb_name}' 不存在")
        
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_type = multimodal_processor.detect_file_type(temp_file_path)
        file_id = f"{kb_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        # 处理文件
        result = multimodal_processor.process_multimodal_file(temp_file_path)
        
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return {
            "status": "success",
            "file_id": file_id,
            "file_name": file.filename,
            "file_type": file_type,
            "processed": True,
            "result": result
        }
        
    except Exception as e:
        logger.log_error("多模态文件上传失败", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query-multimodal")
async def query_multimodal(request: MultimodalQueryRequest):
    """多模态查询"""
    try:
        if not kb_manager.exists(request.kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 '{request.kb_name}' 不存在")
        
        result = await multimodal_processor.query(
            kb_name=request.kb_name,
            query=request.query,
            include_images=request.include_images,
            include_tables=request.include_tables,
            top_k=request.top_k
        )
        
        return result
        
    except Exception as e:
        logger.log_error("多模态查询失败", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kb/{kb_name}/incremental-stats")
async def get_incremental_stats(kb_name: str):
    """获取增量更新统计信息"""
    try:
        if not kb_manager.exists(kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 '{kb_name}' 不存在")
        
        updater = kb_manager.get_incremental_updater(kb_name)
        if not updater:
            raise HTTPException(status_code=500, detail="无法获取增量更新器")
        
        stats = updater.get_stats()
        return {
            "kb_name": kb_name,
            "incremental_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_error("获取增量统计失败", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/multimodal/formats")
async def get_multimodal_formats():
    """获取支持的多模态格式"""
    try:
        formats = multimodal_processor.get_supported_formats()
        return formats
    except Exception as e:
        logger.log_error("获取多模态格式失败", str(e))
        raise HTTPException(status_code=500, detail=str(e))

def start_api_server(host: str = "0.0.0.0", port: int = 8502):
    """启动API服务器"""
    logger.info(f"🚀 启动FastAPI服务器: http://{host}:{port}")
    logger.info("📋 v2.0 新功能: 增量更新、多模态支持")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api_server(port=8502)
