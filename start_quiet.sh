#!/bin/bash
export STREAMLIT_LOGGER_LEVEL=ERROR
export PYTHONWARNINGS=ignore
export STREAMLIT_SERVER_HEADLESS=true
streamlit run src/apppro.py --server.headless true --logger.level error 2>/dev/null
