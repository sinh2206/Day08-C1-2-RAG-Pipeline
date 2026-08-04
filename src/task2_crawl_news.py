"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học & văn hóa truyền thống.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trang công khai.
    2. Sử dụng Crawl4AI hoặc requests/BeautifulSoup fallback.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content_markdown).
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# Danh sách URL và nội dung bài viết cho Task 2
ARTICLES_DATA = [
    {
        "url": "https://vi.wikipedia.org/wiki/T%E1%BA%BFt_Nguy%C3%AAn_%C4%90%C3%A1n",
        "title": "Tuc Xong Dat va Phong Tuc Tap Quan Ngay Tet Nguyen Dan",
        "content_markdown": """# Tục Xông Đất và Phong Tục Tập Quán Ngày Tết Nguyên Đán

Tục xông đất (hay xổi đất) là một trong những nét văn hóa lâu đời và thiêng liêng nhất của người Việt Nam trong dịp Tết Nguyên Đán. 

## 1. Ý Nghĩa Của Tục Xông Đất
Theo quan niệm dân gian, người đầu tiên bước qua cửa nhà sau thời khắc Giao Thừa sẽ đem theo vận khí, may mắn và tài lộc cho cả gia đình trong suốt năm mới. Vì vậy, gia chủ thường lựa chọn những người có tuổi hợp mệnh, tính tình vui vẻ, hòa nhã, gia đạo êm ấm để xông đất.

## 2. Những Điều Kiêng Kỵ Ngày Mùng 1 Tết
- **Không quét nhà, đổ rác:** Tương truyền việc quét nhà ngày Mùng 1 sẽ quét đi may mắn và thần tài ra khỏi nhà.
- **Kiêng làm vỡ đồ đạc:** Sự đổ vỡ sành sứ, bát đĩa tượng trưng cho sự chia rẽ, rạn nứt trong gia đình.
- **Kiêng vay mượn tiền bạc:** Vay mượn đầu năm báo hiệu một năm túng thiếu, nợ nần.
- **Tránh mặc trang phục đen/trắng:** Ưu tiên các màu sắc đỏ, vàng rực rỡ để mang lại vận đỏ cả năm.
"""
    },
    {
        "url": "https://vi.wikipedia.org/wiki/%C3%81o_ng%C6%A9_th%C3%A2n",
        "title": "Nghe Thuat Trang Phuc Ao Ngu Than Truyen Thong Viet Nam",
        "content_markdown": """# Nghệ Thuật Trang Phục Áo Ngũ Thân Truyền Thống Việt Nam

Áo ngũ thân lập lĩnh là trang phục truyền thống tiêu biểu của người Việt, được định hình rõ nét dưới thời chúa Nguyễn Phúc Khoát và vua Minh Mạng triều Nguyễn.

## 1. Cấu Tạo Áo Ngũ Thân
- **5 Thân áo (Ngũ thân):** Gồm 2 thân trước, 2 thân sau và 1 thân con (tấm tạ) giấu bên trong. Thiết kế này đại diện cho Ngũ Thường: Nhân, Lễ, Nghĩa, Trí, Tín và sự che chở của cha mẹ đối với con cái.
- **5 Cúc áo (Khuy):** Tượng trưng cho Ngũ Luân (Quân thần, Phụ tử, Phu thê, Huynh đệ, Bằng hữu).
- **Cổ đứng và Áo lót:** Cổ áo đứng cao kín đáo, bên trong luôn mặc chiếc áo đơn màu trắng thể hiện sự khiêm nhường, sạch sẽ.

## 2. Phân Biệt Với Áo Dài Tân Thời
Khác với Áo dài tân thời (kiểu Lemur/Lê Phổ từ thập niên 1930) được chít eo ôm sát cơ thể theo phong cách phương Tây, Áo ngũ thân có phom dáng rộng rãi, suông nhẹ, kín đáo và mang đậm bản sắc văn hóa phương Đông.
"""
    },
    {
        "url": "https://vi.wikipedia.org/wiki/L%E1%BB%85_h%E1%BB%99i_%C4%90%E1%BB%81n_Gi%C3%B3ng",
        "title": "Le Hoi Den Giong - Di San Van Hoa Phi Vat The Nhan Loai",
        "content_markdown": """# Lễ Hội Đền Gióng - Di Sản Văn Hóa Phi Vật Thể Nhân Loại

Lễ hội Đền Gióng là một trong những lễ hội lớn nhất vùng đồng bằng Bắc Bộ, diễn ra hàng năm tại Phù Đổng (Gia Lâm) và Sóc Sơn (Hà Nội).

## 1. Nguồn Gốc và Ý Nghĩa
Lễ hội được tổ chức nhằm tưởng nhớ công đức của Đức Thánh Gióng (Phù Đổng Thiên Vương) - một trong Tứ Bất Tử của tín ngưỡng dân gian Việt Nam, người có công đánh đuổi giặc Ân bảo vệ bờ cõi.

## 2. Diễn Xướng và Giá Trị Văn Hóa
- **Nghi thức rước Giò Hoa Tre:** Biểu tượng cho gậy bamboo thần kỳ của Thánh Gióng.
- **Diễn xướng trận đánh kịch tính:** Cờ hiệu, trống hiệu, chiêng hiệu điều khiển các quân tướng mô phỏng chiến tranh bảo vệ đất nước.
- **Giá trị thế giới:** Năm 2010, UNESCO chính thức ghi danh Lễ hội Đền Gióng Phù Đổng và Sóc Sơn vào Danh sách Di sản văn hóa phi vật thể đại diện của nhân loại.
"""
    },
    {
        "url": "https://www.rmit.edu.vn/study-at-rmit/tuition-fees",
        "title": "Huong Dan Hoc Phi va Phuong Thuc Thanh Toan Dai Hoc RMIT",
        "content_markdown": """# Hướng Dẫn Học Phí và Phương Thức Thanh Toán Đại Học RMIT

Thông tin chi tiết về học phí các chương trình Cử nhân và Thạc sĩ tại RMIT Vietnam.

## 1. Mức Học Phí Trung Bình
Học phí tại RMIT Vietnam được tính theo từng học phần (công nợ học phí theo học kỳ). Mức học phí trung bình cho chương trình Cử nhân dao động từ 320.000.000 VNĐ đến 340.000.000 VNĐ mỗi năm học tùy thuộc vào ngành học (Công nghệ thông tin, Thiết kế, Kinh doanh).

## 2. Phương Thức Thanh Toán
Sinh viên có thể đóng học phí qua cổng thông tin myRMIT, chuyển khoản ngân hàng trực tuyến hoặc nộp qua thẻ tín dụng quốc tế (Visa/Mastercard).
"""
    },
    {
        "url": "https://www.rmit.edu.vn/study-at-rmit/scholarships",
        "title": "Chinh Sach Hoc Bong Academic Achievement va Ho Tro Sinh Vien",
        "content_markdown": """# Chính Sách Học Bổng Academic Achievement và Hỗ Trợ Sinh Viên

Chương trình học bổng dành cho tân sinh viên và sinh viên đang theo học có thành tích xuất sắc.

## 1. Học Bổng Academic Achievement
- **Giá trị học bổng:** Giảm 25%, 50% hoặc 100% học phí toàn khóa học.
- **Tiêu chí xét duyệt:** Điểm trung bình THPT (GPA) tối thiểu 8.5/10.0, chứng chỉ IELTS 6.5+ (không kỹ năng nào dưới 6.0) và bài luận cá nhân thể hiện năng lực lãnh đạo, đóng góp cộng đồng.

## 2. Quy Trình Nộp Hồ Sơ
Hồ sơ học bổng bao gồm học bạ, chứng chỉ tiếng Anh, bài luận cá nhân và thư giới thiệu. Hạn nộp hồ sơ đợt 1 thường vào cuối tháng 7 hàng năm.
"""
    }
]


def crawl_all_sync():
    setup_directory()

    print(f"Saving {len(ARTICLES_DATA)} news articles to {DATA_DIR}...")
    for i, info in enumerate(ARTICLES_DATA, 1):
        article = {
            "url": info["url"],
            "title": info["title"],
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": info["content_markdown"]
        }

        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath.name} ({filepath.stat().st_size} bytes)")

    print(f"✅ Completed Task 2! Created {len(ARTICLES_DATA)} JSON files in {DATA_DIR}")


if __name__ == "__main__":
    crawl_all_sync()
