"""
表格智能解析模块 - v2.1
自动识别表格结构，语义化表格内容，支持向量化
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import cv2
from PIL import Image
import camelot
import tabula
from io import StringIO
import json
import logging

class TableStructureAnalyzer:
    """表格结构分析器"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def analyze_structure(self, table_data: pd.DataFrame) -> Dict:
        """分析表格结构"""
        structure = {
            'rows': len(table_data),
            'columns': len(table_data.columns),
            'headers': list(table_data.columns),
            'data_types': {},
            'relationships': [],
            'semantic_info': {}
        }
        
        # 分析数据类型
        for col in table_data.columns:
            structure['data_types'][col] = self._infer_column_type(table_data[col])
        
        # 分析列关系
        structure['relationships'] = self._analyze_relationships(table_data)
        
        # 语义信息
        structure['semantic_info'] = self._extract_semantic_info(table_data)
        
        return structure
    
    def _infer_column_type(self, column: pd.Series) -> str:
        """推断列数据类型"""
        # 去除空值
        non_null_values = column.dropna()
        if len(non_null_values) == 0:
            return 'empty'
        
        # 尝试转换为数值
        try:
            pd.to_numeric(non_null_values)
            return 'numeric'
        except:
            pass
        
        # 尝试转换为日期
        try:
            pd.to_datetime(non_null_values)
            return 'datetime'
        except:
            pass
        
        # 检查是否为分类数据
        unique_ratio = len(non_null_values.unique()) / len(non_null_values)
        if unique_ratio < 0.1:
            return 'categorical'
        
        return 'text'
    
    def _analyze_relationships(self, table_data: pd.DataFrame) -> List[Dict]:
        """分析列之间的关系"""
        relationships = []
        
        for i, col1 in enumerate(table_data.columns):
            for j, col2 in enumerate(table_data.columns[i+1:], i+1):
                # 计算相关性
                try:
                    corr = table_data[col1].corr(table_data[col2])
                    if abs(corr) > 0.7:
                        relationships.append({
                            'column1': col1,
                            'column2': col2,
                            'correlation': corr,
                            'type': 'correlation'
                        })
                except:
                    pass
        
        return relationships
    
    def _extract_semantic_info(self, table_data: pd.DataFrame) -> Dict:
        """提取语义信息"""
        semantic_info = {
            'title_candidates': [],
            'key_columns': [],
            'summary_stats': {}
        }
        
        # 识别可能的标题列
        for col in table_data.columns:
            if any(keyword in col.lower() for keyword in ['name', 'title', 'id', '名称', '标题']):
                semantic_info['title_candidates'].append(col)
        
        # 识别关键列
        for col in table_data.columns:
            unique_ratio = len(table_data[col].unique()) / len(table_data)
            if unique_ratio > 0.8:  # 高唯一性
                semantic_info['key_columns'].append(col)
        
        # 统计信息
        for col in table_data.select_dtypes(include=[np.number]).columns:
            semantic_info['summary_stats'][col] = {
                'mean': float(table_data[col].mean()),
                'std': float(table_data[col].std()),
                'min': float(table_data[col].min()),
                'max': float(table_data[col].max())
            }
        
        return semantic_info

class TableExtractor:
    """表格提取器"""
    
    def __init__(self):
        self.methods = ['camelot', 'tabula', 'pandas']
    
    def extract_from_pdf(self, pdf_path: str, page_num: int = None) -> List[pd.DataFrame]:
        """从PDF提取表格"""
        tables = []
        
        # 方法1: Camelot (更准确)
        try:
            if page_num:
                camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_num))
            else:
                camelot_tables = camelot.read_pdf(pdf_path, pages='all')
            
            for table in camelot_tables:
                if table.parsing_report['accuracy'] > 80:
                    tables.append(table.df)
        except Exception as e:
            logging.warning(f"Camelot提取失败: {e}")
        
        # 方法2: Tabula (备选)
        if not tables:
            try:
                if page_num:
                    tabula_tables = tabula.read_pdf(pdf_path, pages=page_num)
                else:
                    tabula_tables = tabula.read_pdf(pdf_path, pages='all')
                tables.extend(tabula_tables)
            except Exception as e:
                logging.warning(f"Tabula提取失败: {e}")
        
        return tables
    
    def extract_from_image(self, image_path: str) -> List[pd.DataFrame]:
        """从图片提取表格"""
        tables = []
        
        try:
            # 使用OpenCV检测表格
            image = cv2.imread(image_path)
            table_regions = self._detect_table_regions(image)
            
            for region in table_regions:
                # 提取表格区域
                table_image = image[region['y']:region['y']+region['h'], 
                                  region['x']:region['x']+region['w']]
                
                # OCR识别表格内容
                table_data = self._ocr_table_content(table_image)
                if table_data is not None:
                    tables.append(table_data)
        
        except Exception as e:
            logging.error(f"图片表格提取失败: {e}")
        
        return tables
    
    def _detect_table_regions(self, image: np.ndarray) -> List[Dict]:
        """检测图片中的表格区域"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检测水平线
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 检测垂直线
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # 合并线条
        table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
        
        # 查找轮廓
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100 and h > 50:  # 过滤小区域
                regions.append({'x': x, 'y': y, 'w': w, 'h': h})
        
        return regions
    
    def _ocr_table_content(self, table_image: np.ndarray) -> Optional[pd.DataFrame]:
        """OCR识别表格内容"""
        try:
            # 这里可以集成更专业的表格OCR工具
            # 如PaddleOCR的表格识别功能
            return None
        except Exception as e:
            logging.error(f"表格OCR失败: {e}")
            return None

class TableVectorizer:
    """表格向量化器"""
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
    
    def vectorize_table(self, table_data: pd.DataFrame, structure_info: Dict) -> Dict:
        """表格向量化"""
        vectors = {
            'header_vector': None,
            'content_vectors': [],
            'structure_vector': None,
            'semantic_vector': None
        }
        
        # 1. 表头向量化
        headers_text = ' '.join(table_data.columns)
        vectors['header_vector'] = self._text_to_vector(headers_text)
        
        # 2. 内容向量化（按行）
        for idx, row in table_data.iterrows():
            row_text = ' '.join([str(val) for val in row.values if pd.notna(val)])
            if row_text.strip():
                vectors['content_vectors'].append({
                    'row_id': idx,
                    'vector': self._text_to_vector(row_text),
                    'text': row_text
                })
        
        # 3. 结构向量化
        structure_text = self._structure_to_text(structure_info)
        vectors['structure_vector'] = self._text_to_vector(structure_text)
        
        # 4. 语义向量化
        semantic_text = self._semantic_to_text(structure_info.get('semantic_info', {}))
        vectors['semantic_vector'] = self._text_to_vector(semantic_text)
        
        return vectors
    
    def _text_to_vector(self, text: str) -> Optional[np.ndarray]:
        """文本转向量"""
        if not self.embedding_model or not text.strip():
            return None
        
        try:
            # 使用嵌入模型
            return self.embedding_model.encode(text)
        except Exception as e:
            logging.error(f"文本向量化失败: {e}")
            return None
    
    def _structure_to_text(self, structure_info: Dict) -> str:
        """结构信息转文本"""
        text_parts = []
        
        text_parts.append(f"表格有{structure_info['rows']}行{structure_info['columns']}列")
        text_parts.append(f"列名: {', '.join(structure_info['headers'])}")
        
        # 数据类型信息
        type_info = []
        for col, dtype in structure_info['data_types'].items():
            type_info.append(f"{col}是{dtype}类型")
        text_parts.append(' '.join(type_info))
        
        return ' '.join(text_parts)
    
    def _semantic_to_text(self, semantic_info: Dict) -> str:
        """语义信息转文本"""
        text_parts = []
        
        if semantic_info.get('title_candidates'):
            text_parts.append(f"标题列: {', '.join(semantic_info['title_candidates'])}")
        
        if semantic_info.get('key_columns'):
            text_parts.append(f"关键列: {', '.join(semantic_info['key_columns'])}")
        
        # 统计信息
        for col, stats in semantic_info.get('summary_stats', {}).items():
            text_parts.append(f"{col}平均值{stats['mean']:.2f}范围{stats['min']:.2f}到{stats['max']:.2f}")
        
        return ' '.join(text_parts)

class SmartTableParser:
    """智能表格解析器（主入口）"""
    
    def __init__(self, embedding_model=None):
        self.extractor = TableExtractor()
        self.analyzer = TableStructureAnalyzer()
        self.vectorizer = TableVectorizer(embedding_model)
    
    def parse_table(self, file_path: str, file_type: str = 'auto') -> List[Dict]:
        """解析表格文件"""
        results = []
        
        # 1. 提取表格
        if file_type == 'pdf' or file_path.endswith('.pdf'):
            tables = self.extractor.extract_from_pdf(file_path)
        elif file_type == 'image' or file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            tables = self.extractor.extract_from_image(file_path)
        else:
            # Excel, CSV等
            try:
                tables = [pd.read_excel(file_path)] if file_path.endswith('.xlsx') else [pd.read_csv(file_path)]
            except Exception as e:
                logging.error(f"读取表格文件失败: {e}")
                return results
        
        # 2. 分析每个表格
        for i, table in enumerate(tables):
            if table.empty:
                continue
            
            try:
                # 结构分析
                structure = self.analyzer.analyze_structure(table)
                
                # 向量化
                vectors = self.vectorizer.vectorize_table(table, structure)
                
                results.append({
                    'table_id': i,
                    'data': table,
                    'structure': structure,
                    'vectors': vectors,
                    'source_file': file_path
                })
                
            except Exception as e:
                logging.error(f"表格{i}解析失败: {e}")
        
        return results
