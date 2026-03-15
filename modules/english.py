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

    def _parse_date(self, date_str):
        """Parse da dinh dang ngay (YYYY-MM-DD hoặc DD/MM/YYYY)."""
        if not date_str: return None
        date_str = str(date_str).strip()
        if not date_str or date_str == "DONE": return None
        
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def get_session_words(self, num_new=0, num_recap=0, num_old=0):
        """
        Lấy từ vựng cho phiên hiện tại linh hoạt theo 3 nhóm.
        QUAN TRỌNG: Thứ tự lấy từ trong code phải là Recap -> Old -> New.
        Việc này đảm bảo 'New Words' (từ vừa bốc) sẽ không bị trùng vào danh sách 'Recap' 
        của chính phiên này.
        - num_recap: Số từ đã học TRONG HÔM NAY để nhắc lại (Full details)
        - num_old: Số từ đã học CÁC NGÀY TRƯỚC đến hạn ôn tập (Summary)
        - num_new: Số từ mới toanh để học (đánh dấu date_learned = hôm nay)
        Nếu truyền vào None có nghĩa là lấy TOÀN BỘ danh sách có sẵn của nhóm đó.
        Return theo thứ tự: new words, recap words, old words
        Sử dụng _parse_date để xử lý sai lệch định dạng DD/MM/YYYY vs YYYY-MM-DD.
        """
        all_vocab = self.gs.get_all_records(self.sheet_name)
        now_dt = datetime.now(self.tz).date()
        now_str = now_dt.strftime("%d/%m/%Y") # Dùng định dạng của Sheet để ghi lại nếu cần
        
        # 1. Recap Words (Từ vừa học hôm nay)
        target_recap = []
        if num_recap is None or num_recap > 0:
            def is_learned_today(w):
                d = self._parse_date(w.get("date_learned"))
                return d == now_dt

            available_today = [w for w in all_vocab if is_learned_today(w)]
            if available_today:
                count = len(available_today) if num_recap is None else min(num_recap, len(available_today))
                target_recap = random.sample(available_today, count)

        # 2. Old Review Words (Từ các ngày trước đến hạn)
        target_old = []
        if num_old is None or num_old > 0:
            def is_due(w):
                nr = self._parse_date(w.get("next_review"))
                dl = self._parse_date(w.get("date_learned"))
                if not nr: return False
                # Den han (<= today) va khong phai vua hoc hom nay
                return nr <= now_dt and dl != now_dt

            due_reviews = [w for w in all_vocab if is_due(w)]
            if due_reviews:
                # BUOI TOI (num_old=None): Gioi han toi da 15 tu de tranh lag message
                limit = 15 if num_old is None else num_old
                count = min(limit, len(due_reviews))
                target_old = random.sample(due_reviews, count)
                for w in target_old:
                    self._update_srs(w)

        # 3. New Words (Từ mới toanh)
        target_new = []
        if num_new is None or num_new > 0:
            available_new = [w for w in all_vocab if not w.get("date_learned")]
            if available_new:
                count = len(available_new) if num_new is None else min(num_new, len(available_new))
                target_new = random.sample(available_new, count)
                for w in target_new:
                    # Ghi ngay hoc theo dinh dang hien tai cua Sheet (DD/MM/YYYY)
                    self.gs.update_cell_by_match(self.sheet_name, "word", w["word"], "date_learned", now_str)
                    w["date_learned"] = now_str
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
        now_dt = datetime.now(self.tz)
        
        if is_initial:
            next_date = (now_dt + timedelta(days=intervals[0])).strftime("%d/%m/%Y")
            self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "next_review", next_date)
            self.gs.update_cell_by_match(self.sheet_name, "word", word_dict["word"], "review_count", 0)
        else:
            if count < len(intervals):
                days = intervals[count]
                next_date = (now_dt + timedelta(days=days)).strftime("%d/%m/%Y")
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
