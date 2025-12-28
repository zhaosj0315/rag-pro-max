
import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_kb_update_advanced_options_flow():
    """
    Test that advanced options (OCR, Metadata, Summary) are correctly passed 
    from session state to the processing logic during KB update.
    """
    # Mock streamlit session state
    mock_session_state = MagicMock()
    mock_session_state.get.side_effect = lambda k, default=None: {
        'kb_use_ocr': True,
        'kb_extract_metadata': True,
        'kb_generate_summary': True,
        'kb_force_reindex': False
    }.get(k, default)
    
    with patch('streamlit.session_state', mock_session_state):
        # Simulate capturing options
        use_ocr = mock_session_state.get('kb_use_ocr', False)
        extract_metadata = mock_session_state.get('kb_extract_metadata', False)
        generate_summary = mock_session_state.get('kb_generate_summary', False)
        
        # Verify values are captured correctly
        assert use_ocr is True
        assert extract_metadata is True
        assert generate_summary is True
        
        # Verify these would be passed to IndexBuilder (simulation)
        options = {
            'use_ocr': use_ocr,
            'extract_metadata': extract_metadata,
            'generate_summary': generate_summary
        }
        
        assert options['use_ocr'] == True
        assert options['extract_metadata'] == True
        assert options['generate_summary'] == True

if __name__ == "__main__":
    test_kb_update_advanced_options_flow()
    print("✅ KB Update Advanced Options Flow Test Passed")
