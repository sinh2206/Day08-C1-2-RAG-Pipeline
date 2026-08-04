# Role 4 — BM25 & Retrieval QA

## Phạm vi đã kiểm tra

- Task 6: tokenization tiếng Việt, alias truy vấn, BM25 ranking, metadata và `top_k`.
- Checkpoint 3: chuẩn bị truy vấn trong domain/ngoài domain và kiểm tra contract `source="pageindex"`.
- Checkpoint 5: thay golden dataset RMIT bằng 18 câu đúng chủ đề phong tục và trang phục Việt Nam.

## Kết quả BM25 trên corpus hiện tại

| Truy vấn | Top-1 | BM25 score | Nhận xét |
|---|---|---:|---|
| Ý nghĩa tục xổi đất đầu năm | `news/article_01.md` | 24.7464 | Pass; alias “xổi đất” được chuẩn hóa thành “xông đất” |
| Chi tiết áo ngũ thân nam truyền thống | `legal/ao-dai-o-Hue.md` | 10.3181 | Pass; kết quả thuộc đúng chủ đề, nhưng chunk top-3 trực tiếp hơn |
| Ai cải tiến áo dài Le Mur | `news/article_02.md` | 24.1778 | Pass |
| Cách bảo quản áo dài lụa tơ tằm | `news/article_05.md` | 28.7245 | Pass |
| Giá Bitcoin hôm nay | `legal/Gia-tri-tham-mi-trong-ao-dai.md` | 4.6128 | OOD vẫn có điểm do trùng từ phổ thông |

## Kết luận QA

1. BM25 hoạt động đúng để xếp hạng từ khóa, nhưng điểm BM25 không phải xác suất và không dùng làm ngưỡng fallback.
2. Điều kiện fallback phải sử dụng cosine score gốc của Semantic Search. Không dùng điểm RRF hoặc lấy BM25 chia cho một hằng số để giả lập cosine.
3. Task 9 đã được tích hợp ở commit `15260b6`; kiểm thử mock xác nhận pipeline dùng cosine gốc để kích hoạt fallback và không dùng điểm RRF làm ngưỡng.
4. Task 8 trên `main` trả placeholder khi chưa upload được tài liệu. Kết quả này chỉ thỏa schema, không chứng minh PageIndex retrieval đúng và cần Role 3 xử lý.

## Trạng thái kiểm thử

- QA Role 4 + OOD + logic Task 9: `12 passed`.
- Test chính thức `TestTask6`: `1 passed, 3 skipped`.
- Ba test bị skip vì test starter dùng truy vấn university (`tuition`, `library`), trong khi corpus nhóm đã chuyển sang văn hóa Việt Nam và không trả kết quả cho các từ khóa đó.

## Lệnh kiểm tra

```bash
.venv/bin/python -m pytest tests/test_role4.py -q
.venv/bin/python -m pytest tests/test_out_of_domain_fallback.py -q
```

## Phần còn chờ

- Role 3: xác nhận tài liệu đã upload/index thật trên PageIndex, loại bỏ nội dung placeholder.
- Chạy live Task 9 đang cần tải embedding model BGE; test chính thức đã được dừng sau 100 giây chờ tải model.
- Sau khi PageIndex thật và model sẵn sàng: chạy 18 câu golden dataset, đánh giá faithfulness, answer relevance, context recall và context precision.
