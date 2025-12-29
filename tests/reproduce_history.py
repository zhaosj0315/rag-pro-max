
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chat.history_manager import HistoryManager
import shutil

# Setup test env
test_dir = "test_histories"
HistoryManager.HISTORY_DIR = test_dir
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)

# Test 1: Save standard KB history (Current Behavior)
print("--- Current Behavior ---")
kb_name = "test_kb"
msgs = [{"role": "user", "content": "Hello"}]
HistoryManager.save(kb_name, msgs)
print(f"Saved: {os.listdir(test_dir)}")

# Proposed structure:
# test_histories/test_kb/session_1.json
# test_histories/test_kb/session_2.json
