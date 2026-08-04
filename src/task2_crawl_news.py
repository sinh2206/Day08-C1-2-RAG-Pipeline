# src/task2_crawl_news.py

import asyncio
import json
import os
from datetime import datetime, timezone
from crawl4ai import AsyncWebCrawler

OUTPUT_DIR = "data/landing/news"
MIN_CONTENT_LENGTH = 200  
DELAY_BETWEEN_REQUESTS = 2  

URLS = [
    "http://dulichphutho.gov.vn/diemden/le-hoi-den-hung",
    "https://trangphuchonghanh.com/y-nghia-cua-bo-ao-dai-truyen-thong-viet-nam-bid33.html",
    "https://www.bachhoaxanh.com/kinh-nghiem-hay/tet-trung-thu-2022-vao-ngay-nao-y-nghia-nguon-goc-ngay-tet-trung-thu-1179527",
    "https://www.bachhoaxanh.com/kinh-nghiem-hay/le-hoi-chua-huong-o-dau-dien-ra-khi-nao-nguon-goc-y-nghia-1495188",
    "https://cardina.vn/blogs/kien-thuc-thoi-trang/ao-tu-than",
]


def slugify(title: str, fallback: str) -> str:
    """Tạo tên file an toàn từ tiêu đề hoặc dùng fallback nếu tiêu đề rỗng."""
    if not title:
        return fallback
    slug = title.lower().strip()
    slug = "".join(c if c.isalnum() or c in " -" else "" for c in slug)
    slug = slug.replace(" ", "-")[:60]
    return slug or fallback


def extract_title(result) -> str:
    """Lấy title an toàn, tránh crash nếu metadata là None hoặc thiếu key."""
    metadata = getattr(result, "metadata", None)
    if metadata and isinstance(metadata, dict):
        return metadata.get("title", "") or ""
    return ""


async def crawl_article(crawler: AsyncWebCrawler, url: str, index: int) -> dict:
    """Crawl 1 URL, trả về dict metadata + nội dung markdown."""
    result = await crawler.arun(url=url)

    title = extract_title(result)
    fname_base = f"{index:02d}-{slugify(title, f'article-{index}')}"

    content = result.markdown or ""
    is_success = bool(result.success) and len(content.strip()) >= MIN_CONTENT_LENGTH

    record = {
        "url": url,
        "title": title,
        "crawl_date": datetime.now(timezone.utc).isoformat(),
        "content_markdown": content,
        "content_length": len(content.strip()),
        "success": is_success,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{fname_base}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    status = "OK" if is_success else "WEAK/FAIL"
    print(f"[{status}] {url} -> {out_path} ({len(content.strip())} ký tự)")
    return record


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    async with AsyncWebCrawler() as crawler:
        for i, url in enumerate(URLS, start=1):
            try:
                record = await crawl_article(crawler, url, i)
                results.append(record)
            except Exception as e:
                print(f"[ERROR] {url}: {e}")

            if i < len(URLS):
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    ok_count = sum(1 for r in results if r.get("success"))
    print(f"\nHoàn tất: {ok_count}/{len(URLS)} bài crawl thành công thật sự (đủ nội dung).")
    if ok_count < 5:
        print("⚠️  Chưa đủ 5 bài đạt yêu cầu — kiểm tra file .json để xem trang nào bị crawl rỗng/yếu.")


if __name__ == "__main__":
    asyncio.run(main())