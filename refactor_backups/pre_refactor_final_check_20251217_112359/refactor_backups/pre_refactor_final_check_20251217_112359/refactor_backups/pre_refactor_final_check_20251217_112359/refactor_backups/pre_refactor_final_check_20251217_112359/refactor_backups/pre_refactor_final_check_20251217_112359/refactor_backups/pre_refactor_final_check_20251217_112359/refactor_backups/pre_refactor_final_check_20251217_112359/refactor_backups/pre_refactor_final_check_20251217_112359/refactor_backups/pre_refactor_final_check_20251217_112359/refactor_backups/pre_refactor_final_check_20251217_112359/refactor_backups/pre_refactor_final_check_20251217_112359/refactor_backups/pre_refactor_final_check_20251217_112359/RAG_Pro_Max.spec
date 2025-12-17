# -*- mode: python ; coding: utf-8 -*-
import sys
import sysconfig

block_cipher = None

# 获取 Python 动态库路径
libdir = sysconfig.get_config_var('LIBDIR')
python_lib = f"{libdir}/libpython3.12.dylib"

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[(python_lib, '.')],
    datas=[
        ('apppro.py', '.'),
        ('file_processor.py', '.'),
        ('terminal_logger.py', '.'),
        ('logger.py', '.'),
        ('rag_config.json', '.'),
        ('app_config.json', '.'),
        ('projects_config.json', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web',
        'streamlit.web.cli',
        'streamlit.web.server',
        'streamlit.web.server.server',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.components.v1',
        'llama_index.core',
        'llama_index.llms.ollama',
        'llama_index.llms.openai',
        'llama_index.embeddings.huggingface',
        'llama_index.vector_stores.chroma',
        'llama_index.readers.file',
        'llama_index.postprocessor.flag_embedding_reranker',
        'FlagEmbedding',
        'chromadb',
        'chromadb.config',
        'sentence_transformers',
        'torch',
        'transformers',
        'openpyxl',
        'docx',
        'pypdf',
        'markdown',
        'tiktoken',
        'click',
        'altair',
        'pandas',
        'numpy',
        'PIL',
        'watchdog',
        'validators',
        'packaging',
        'importlib_metadata',
        'pyarrow',
        'tokenizers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PySide6', 'matplotlib.tests', 'scipy', 'numpy.distutils',
        'tkinter', 'IPython', 'jupyter', 'notebook', 'pytest', 'sphinx',
        'metagpt', 'agentops', 'dashscope', 'qianfan', 'zhipuai', 'nltk',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name='RAG_Pro_Max',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
