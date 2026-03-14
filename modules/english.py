import random
from datetime import datetime, timedelta
import pytz

class EnglishModule:
    """
    Module học tiếng Anh mỗi ngày với thuật toán Spaced Repetition (SRS).
    TODO: Dựa theo đường cong quên lãng
    """

    def __init__(self, google_manager, sheet_name="english_vocab", timezone="Asia/Ho_Chi_Minh"):
        self.gs = google_manager
        self.sheet_name = sheet_name
        self.tz = pytz.timezone(timezone)

    def _normalize_date(self, date_str):
        """Standardize date string from Google Sheets to YYYY-MM-DD format."""
        if not date_str: return ""
        date_str = str(date_str).strip()
        try:
            if "/" in date_str:
                parts = date_str.split("/")
                if len(parts) == 3:
                    if len(parts[0]) == 4: # YYYY/MM/DD
                        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                    # Assume DD/MM/YYYY
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        except Exception:
            pass
        return date_str

    def get_session_words(self, num_new=0, num_recap=0, old_ratio=None):
        """
        Lấy từ vựng cho phiên hiện tại linh hoạt theo 3 nhóm:
        - num_new: Số từ mới toanh để học (đánh dấu date_learned = hôm nay)
        - num_recap: Số từ đã học TRONG HÔM NAY để nhắc lại (Full details)
        - old_ratio: Tỉ lệ từ đã học CÁC NGÀY TRƯỚC đến hạn ôn tập. Dict chứa "target" (số phần) và "remaining" (tổng số phần còn lại).
        Nếu truyền vào None có nghĩa là lấy TOÀN BỘ danh sách có sẵn của nhóm đó.
        """
        all_vocab = self.gs.get_all_records(self.sheet_name)
        now_date = datetime.now(self.tz).strftime("%Y-%m-%d")

        # Normalize dates to YYYY-MM-DD for accurate comparison
        for w in all_vocab:
            w["date_learned_norm"] = self._normalize_date(w.get("date_learned"))
            w["next_review_norm"] = self._normalize_date(w.get("next_review"))

        # 2. Recap Words (Từ vừa học hôm nay)
        target_recap = []
        if num_recap is None or num_recap > 0:
            available_today = [w for w in all_vocab if w.get("date_learned_norm") == now_date]
            if available_today:
                count = len(available_today) if num_recap is None else min(num_recap, len(available_today))
                target_recap = random.sample(available_today, count)
        
        # 3. Old Review Words (Từ các ngày trước đến hạn)
        target_old = []
        due_reviews = [w for w in all_vocab if w.get("next_review_norm") and w.get("next_review_norm") <= now_date 
                       and w.get("date_learned_norm") != now_date]
        
        if due_reviews:
            if old_ratio is None:
                # Không truyền tỉ lệ -> Lấy tất cả từ còn lại (vd: buổi tối)
                target_old = list(due_reviews)
            else:
                target_parts = old_ratio.get("target", 0)
                remaining_parts = old_ratio.get("remaining", 1)
                
                # Tính tổng số từ còn lại phải ôn
                X = len(due_reviews)
                if remaining_parts > 0:
                    num_to_take = max(0, min(X, round(X * (target_parts / remaining_parts))))
                    target_old = random.sample(due_reviews, num_to_take)
                
            for w in target_old:
                self._update_srs(w)


        # 1. New Words (Từ mới toanh) lấy cuối cùng
        target_new = []
        if num_new is None or num_new > 0:
            available_new = [w for w in all_vocab if not w.get("date_learned")]
            if available_new:
                count = len(available_new) if num_new is None else min(num_new, len(available_new))
                target_new = random.sample(available_new, count)
                for w in target_new:
                    self.gs.update_cell_by_match(self.sheet_name, "word", w["word"], "date_learned", now_date)
                    w["date_learned"] = now_date
                    self._update_srs(w, is_initial=True)


        return target_new, target_recap, target_old

    def _update_srs(self, word_dict, is_initial=False):
        """
        Cập nhật chu kỳ Spaced Repetition (SRS).
        Chu kỳ chuẩn: 1 ngày -> 3 ngày -> 7 ngày -> 30 ngày -> 90 ngày.
        """
        count = int(word_dict.get("review_count", 0) or 0)
        # Quãng thời gian (ngày) cho từng lần ôn tập:
        # Lần 1: 1 ngày sau khi học
        # Lần 2: 3 ngày sau lần ôn 1
        # Lần 3: 7 ngày sau lần ôn 2
        # Lần 4: 30 ngày sau lần ôn 3
        # Lần 5: Ngẫu nhiên trong 3 tháng sau lần ôn 4
        intervals = [1, 3, 7, 30, random.randint(60, 90)]
        
        if is_initial:
            # Lần đầu học: Lần ôn đầu tiên là 1 ngày sau
            next_date = (datetime.now(self.tz) + timedelta(days=intervals[0])).strftime("%Y-%m-%d")
            self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "next_review", next_date)
            # review_count lúc này là 0, sẽ được tăng lên sau mỗi buổi ôn
            self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "review_count", 0)
        else:
            # Các lần ôn tập tiếp theo
            if count < len(intervals):
                days = intervals[count]
                next_date = (datetime.now(self.tz) + timedelta(days=days)).strftime("%Y-%m-%d")
                self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "next_review", next_date)
                self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "review_count", count + 1)
            else:
                # Đã hoàn thành toàn bộ chu kỳ ôn tập
                self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "status", "Mastered")
                self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "next_review", "DONE")

    GRAMMAR_B2 = [
        "Present Perfect Continuous",
        "Past Perfect Simple/Continuous",
        "Future Continuous/Perfect",
        "Mixed Conditionals",
        "Wish / If only",
        "Modal Verbs of Deduction (Past/Present)",
        "Passive Voice (Complex structures)",
        "Reported Speech (Advanced)",
        "Inversion with negative adverbials"
    ]

    def format_bulletin(self, title, new_words=None, recap_words=None, old_words=None):
        """Format Telegram message with 3 flexible groups."""
        text = f"📖 <b>{title}</b>\n"
        
        # Nhóm 1: Từ mới học buổi này
        if new_words:
            text += "\n✨ <b>Từ mới buổi này:</b>\n"
            for w in new_words:
                text += self._format_word_detail(w)
                
        # Nhóm 2: Ôn tập từ vừa học trong ngày
        if recap_words:
            text += "\n🔄 <b>Ôn tập từ mới học trong ngày:</b>\n"
            for w in recap_words:
                text += self._format_word_detail(w)
                
        # Nhóm 3: Ôn tập từ các ngày trước
        if old_words:
            text += "\n📚 <b>Ôn tập từ các ngày trước:</b>\n"
            for w in old_words:
                text += f"• <b>{w.get('word', 'N/A')}</b> ({w.get('type', 'n/a')})\n"
                
        if not any([new_words, recap_words, old_words]):
            return f"📖 <b>{title}</b>: Hiện tại không có từ vựng nào cần xử lý."
            
        return text

    def _format_word_detail(self, w):
        """Helper to format full details of a word."""
        word = w.get('word', 'N/A')
        w_type = w.get('type', 'n/a')
        ipa = w.get('ipa', '')
        meaning = w.get('meaning', '')
        example = w.get('example', '')
        
        detail = f"• <b>{word}</b> ({w_type})"
        if ipa: detail += f" /{ipa}/"
        detail += "\n"
        
        if meaning:
            detail += f"  └ Nghĩa: {meaning}\n"
        
        if example:
            detail += f"  <i>Ex: {example}</i>\n"
        else:
            grammar = random.choice(self.GRAMMAR_B2)
            detail += f"  🔥 <b>Challenge:</b> Đặt câu với cấu trúc: <u>{grammar}</u>\n"
        
        return detail + "\n"
