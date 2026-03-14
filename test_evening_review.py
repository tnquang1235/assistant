import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the project directory to sys.path
sys.path.append(os.path.abspath(r"c:\Users\tnqua\.gemini\antigravity\scratch\assistant_v1.2"))

from modules.english import EnglishModule

class MockGoogleSheetManager:
    def get_all_records(self, sheet_name):
        return []
    def update_cell_by_match(self, *args, **kwargs):
        pass

def test_evening_format():
    eng = EnglishModule(MockGoogleSheetManager())
    
    new_words = [
        {"word": "Magnificent", "type": "adj", "ipa": "mæɡˈnɪfɪsnt", "meaning": "Tuyệt vời", "example": "The view from the top is magnificent."},
        {"word": "Inevitable", "type": "adj", "ipa": "ɪnˈevɪtəbl", "meaning": "Không thể tránh khỏi"}
    ]
    
    review_words = [
        {"word": "Persistence", "type": "n"},
        {"word": "Resilient", "type": "adj"}
    ]
    
    print("--- TESTING EVENING BULLETIN ---")
    bulletin = eng.format_bulletin(new_words, review_words, session_name="Evening")
    print(bulletin)
    
    # Simple validation
    assert "Phần 1: Từ mới học trong ngày" in bulletin
    assert "Phần 2: Ôn từ các ngày trước" in bulletin
    assert "Magnificent" in bulletin
    assert "Tuyệt vời" in bulletin
    assert "Persistence" in bulletin
    assert "Resilient" in bulletin
    
    print("\n--- TESTING MORNING BULLETIN ---")
    morning_bulletin = eng.format_bulletin(new_words, review_words, session_name="Morning")
    print(morning_bulletin)
    assert "Từ mới hôm nay" in morning_bulletin
    assert "Ôn tập định kỳ" in morning_bulletin

if __name__ == "__main__":
    test_evening_format()
    print("\nVerification successful!")
