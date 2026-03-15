
import unittest
from unittest.mock import MagicMock
from datetime import datetime
import pytz
from modules.english import EnglishModule

class TestEnglishRecap(unittest.TestCase):
    def setUp(self):
        # Mock GoogleSheetManager
        self.mock_gs = MagicMock()
        self.tz = pytz.timezone("Asia/Ho_Chi_Minh")
        self.module = EnglishModule(self.mock_gs, timezone="Asia/Ho_Chi_Minh")
        self.now_date = datetime.now(self.tz).strftime("%Y-%m-%d")

    def test_recap_logic(self):
        # 1. Giả lập dữ liệu trong Sheet
        # - 2 từ đã học ngày hôm nay (trong phiên trước đó)
        # - 2 từ mới (chưa đánh dấu ngày học)
        # - 1 từ đã học ngày hôm qua
        mock_data = [
            {"word": "today1", "date_learned": self.now_date, "next_review": "2026-03-16", "review_count": 0},
            {"word": "today2", "date_learned": self.now_date, "next_review": "2026-03-16", "review_count": 0},
            {"word": "new1", "date_learned": "", "next_review": "", "review_count": 0},
            {"word": "new2", "date_learned": "", "next_review": "", "review_count": 0},
            {"word": "yesterday1", "date_learned": "2026-03-14", "next_review": self.now_date, "review_count": 0},
        ]
        self.mock_gs.get_all_records.return_value = mock_data

        # Chạy hàm lấy từ (Session này: 1 từ mới, 2 từ recap, 5 từ cũ)
        # Theo triết lý Recap -> Old -> New
        new_w, recap_w, old_w = self.module.get_session_words(num_new=1, num_recap=2, num_old=5)

        # KIỂM TRA 1: Recap phải lấy đúng 2 từ có date_learned == today
        self.assertEqual(len(recap_w), 2)
        words_in_recap = [w["word"] for w in recap_w]
        self.assertIn("today1", words_in_recap)
        self.assertIn("today2", words_in_recap)

        # KIỂM TRA 2: New word được bốc trong session này KHÔNG ĐƯỢC nằm trong recap_w của chính nó
        self.assertEqual(len(new_w), 1)
        new_word_name = new_w[0]["word"]
        self.assertNotIn(new_word_name, words_in_recap)

        # KIỂM TRA 3: Old word phải là từ của hôm qua (next_review <= today)
        self.assertEqual(len(old_w), 1)
        self.assertEqual(old_w[0]["word"], "yesterday1")

        print("[OK] Test Recap Logic thành công!")

    def test_date_format_robustness(self):
        # Giả lập trường hợp Google Sheet có định dạng ngày có khoảng trắng thừa
        mock_data = [
            {"word": "format1", "date_learned": self.now_date + " ", "next_review": ""}, 
        ]
        self.mock_gs.get_all_records.return_value = mock_data
        
        new_w, recap_w, old_w = self.module.get_session_words(num_new=0, num_recap=5, num_old=0)
        
        # Với .strip() mới, cái này phải thành công
        self.assertEqual(len(recap_w), 1)
        self.assertEqual(recap_w[0]["word"], "format1")
        print("[OK] Test Date Robustness (.strip()) thành công!")

if __name__ == "__main__":
    unittest.main()
