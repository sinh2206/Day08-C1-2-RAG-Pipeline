# src/task2_crawl_news.py

import asyncio
import json
import os
from datetime import datetime, timezone
from crawl4ai import AsyncWebCrawler

OUTPUT_DIR = "data/landing/news"

# TODO: Thay bằng 5+ URL thật về phong tục / trang phục / lễ hội truyền thống
URLS = [
    "https://vinpearl.com/vi/le-hoi-den-hung-phu-tho-bieu-tuong-van-hoa-cao-dep-cua-dan-toc",
    "https://trangphuchonghanh.com/y-nghia-cua-bo-ao-dai-truyen-thong-viet-nam-bid33.html",
    "https://www.bachhoaxanh.com/kinh-nghiem-hay/tet-trung-thu-2022-vao-ngay-nao-y-nghia-nguon-goc-ngay-tet-trung-thu-1179527",
    "https://www.bachhoaxanh.com/kinh-nghiem-hay/le-hoi-chua-huong-o-dau-dien-ra-khi-nao-nguon-goc-y-nghia-1495188",
    "https://cardina.vn/blogs/kien-thuc-thoi-trang/ao-tu-than?srsltid=AfmBOordbjjlJLGyAwWc7QuUf6th1qEmNIrBhfkRPjp6JtpZTFpzNxQw",
]


def slugify(title: str, fallback: str) -> str:
    """Tạo tên file an toàn từ tiêu đề hoặc dùng fallback nếu tiêu đề rỗng."""
    if not title:
        return fallback
    slug = title.lower().strip()
    slug = "".join(c if c.isalnum() or c in " -" else "" for c in slug)
    slug = slug.replace(" ", "-")[:60]
    return slug or fallback


async def crawl_article(crawler: AsyncWebCrawler, url: str, index: int) -> dict:
    """Crawl 1 URL, trả về dict metadata + nội dung markdown."""
    result = await crawler.arun(url=url)

    title = getattr(result, "metadata", {}).get("title", "") if result.metadata else ""
    fname_base = slugify(title, f"article-{index}")

    record = {
        "url": url,
        "title": title,
        "crawl_date": datetime.now(timezone.utc).isoformat(),
        "content_markdown": result.markdown,
        "success": result.success,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{fname_base}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"[{'OK' if result.success else 'FAIL'}] {url} -> {out_path}")
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

    ok_count = sum(1 for r in results if r.get("success"))
    print(f"\nHoàn tất: {ok_count}/{len(URLS)} bài crawl thành công.")


if __name__ == "__main__":
    asyncio.run(main())