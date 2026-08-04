"""
🏮 Trợ Lý Giải Đáp Phong Tục, Trang Phục & Lễ Hội Truyền Thống Việt Nam
Streamlit Application — Topic 6 (Vietnamese Folklore, Traditional Costumes & Festivals RAG)

Developer: Frontend UI & App Integration Dev
"""

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path to allow importing from src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIGURATION & CUSTOM STYLING
# =============================================================================

st.set_page_config(
    page_title="Trợ Lý Văn Hóa Dân Gian & Lễ Hội Việt Nam",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics (Crimson & Gold cultural theme)
st.markdown(
    """
    <style>
    /* Main Background & Accent Header */
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #B22222 50%, #D2691E 100%);
        padding: 24px;
        border-radius: 12px;
        color: #FFF8DC;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #FFD700 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .main-header p {
        color: #FFF8DC;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    
    /* Custom Badges & Tags */
    .tag-badge {
        background-color: rgba(255, 215, 0, 0.2);
        color: #FFD700;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid rgba(255, 215, 0, 0.4);
        margin-right: 6px;
        display: inline-block;
    }

    /* Metric Cards */
    .metric-card {
        background: #1E1E2F;
        border: 1px solid #3A3A55;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #FFD700;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #A0A0C0;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# MOCK DATA FOR DEMO & FRONTEND TESTING (Topic 6)
# =============================================================================

MOCK_TOPIC6_KNOWLEDGE = {
    "Ý nghĩa của tục xông đất đầu năm và những điều kiêng kỵ trong ngày Tết Nguyên Đán là gì?": {
        "answer": """### 🏮 Ý Nghĩa Tục Xông Đất & Các Điều Kiêng Kỵ Ngày Tết Nguyên Đán

**1. Ý nghĩa tục Xông Đất (Tục Xổi Đất) đầu năm:**
* **Khởi đầu vận hội:** Người Việt niệm rằng người đầu tiên bước vào nhà sau giờ giao thừa sẽ mang theo may mắn, tài lộc và vận khí cho cả gia đình trong suốt 365 ngày tới `[1]`.
* **Tiêu chí chọn người:** Gia chủ thường chọn người có **tuổi hợp với gia chủ**, tính tình hòa nhã, xởi lởi, gia đạo êm ấm, làm ăn phát đạt `[1]`.

---

**2. Những điều kiêng kỵ quan trọng ngày Tết:**
* 🚫 **Không quét nhà, đổ rác ngày Mùng 1:** Theo tích cổ, việc quét nhà là quét đi tài lộc và thần may mắn ra khỏi cửa `[2]`.
* 🚫 **Kiêng làm vỡ bát đĩa, đồ sành sứ:** Sự đổ vỡ tượng trưng cho sự chia cắt, rạn nứt gia đạo `[2]`.
* 🚫 **Kiêng cho vay mượn tiền bạc:** Đầu năm mở quẻ vay mượn báo hiệu một năm túng thiếu, nợ nần `[2]`.
* 🚫 **Kiêng mặc đồ màu đen hoặc trắng toàn bộ:** Ưu tiên các trang phục sắc đỏ, vàng rực rỡ tượng trưng cho may mắn `[3]`.
""",
        "sources": [
            {
                "content": "Tục xông đất (xổi đất) xuất phát từ ước vọng về một năm mới an lành. Người đầu tiên bước vào nhà sau thời khắc Giao thừa mang ý nghĩa mở cổng vận khí...",
                "metadata": {"source": "Phong_Tuc_Tet_Nguyen_Dan_Viendong.md", "type": "folklore_book"},
                "score": 0.9452,
            },
            {
                "content": "Các điều kiêng kỵ dân gian ngày Tết: Tránh quét nhà Mùng 1 (theo tích Triệu Đức và Như Nguyện), kiêng làm vỡ chén bát, kiêng vay tiền...",
                "metadata": {"source": "Van_Hoa_Dan_Gian_Tap_1.md", "type": "cultural_docs"},
                "score": 0.9120,
            },
            {
                "content": "Hồ sơ Di sản Văn hóa Phi vật thể Quốc gia: Tập quán xã hội và tín ngưỡng Tết Nguyên Đán của người Việt...",
                "metadata": {"source": "Ho_So_Di_San_UNESCO_Tet.md", "type": "heritage_file"},
                "score": 0.8765,
            },
        ],
    },
    "Trang phục Áo ngũ thân nam truyền thống gồm những chi tiết nào và sự khác biệt với Áo dài tân thời?": {
        "answer": """### 👘 Áo Ngũ Thân Nam Truyền Thống vs. Áo Dài Tân Thời (Lemur/Lê Phổ)

**1. Cấu tạo chi tiết của Áo Ngũ Thân Nam:**
* **5 Thân áo (Ngũ thân):** Gồm 2 thân trước, 2 thân sau và 1 thân con (tấm tạ) ẩn bên trong thân trước bên phải — tượng trưng cho **Ngũ thường (Nhân, Lễ, Nghĩa, Trí, Tín)** và tình cha mẹ che chở con cái `[1]`.
* **5 Cúc áo (Khuy):** Làm bằng ngọc, kim loại hoặc gỗ quý — tượng trưng cho **Ngũ luân (Quân thần, Phụ tử, Phu thê, Huynh đệ, Bằng hữu)** `[1]`.
* **Cổ áo:** Cổ đứng, vuông vắn, ôm sát cổ (gọi là cổ chầu), cài cúc bên phải (lập lĩnh) `[1]`.
* **Áo lót bên trong:** Luôn mặc kèm áo lót màu trắng (áo lót đơn) bên trong tỏ ý khiêm nhường, sạch sẽ `[2]`.

---

**2. Sự khác biệt cốt lõi với Áo Dài Tân Thời:**
| Đặc Điểm | Áo Ngũ Thân Truyền Thống | Áo Dài Tân Thời (Modern) |
| :--- | :--- | :--- |
| **Phom dáng** | Rộng rãi, suông nhẹ, không chiết eo, có lớp tạ con | Chít eo sát thân người, tôn nét cong cơ thể |
| **Cổ áo** | Cổ đứng cao (chầu), kín đáo, viền cổ trắng | Cổ hở, cổ thuyền, cổ tròn hoặc cách tân |
| **Tay áo** | Tay thụng (hoặc tay chẽn) khâu thủ công | Tay ráp lăng (Raglan), ôm sát cánh tay |
| **Số thân** | 5 thân ghép lại | 2 thân (thân trước và thân sau) |
""",
        "sources": [
            {
                "content": "Áo ngũ thân lập lĩnh ra đời dưới thời chúa Nguyễn Phúc Khoát (1744) và được vua Minh Mạng định hình làm quốc phục. Áo có 5 thân tượng trưng ngũ thường...",
                "metadata": {"source": "Nghien_Cuu_Trang_Phuc_Nguyen.md", "type": "heritage_file"},
                "score": 0.9580,
            },
            {
                "content": "So sánh áo ngũ thân và áo dài Lemur thập niên 1930: Áo tân thời cắt bỏ thân con, chít eo theo phương Tây, sử dụng cúc bấm thay cho 5 khuy cài truyền thống...",
                "metadata": {"source": "Lich_Su_Ao_Dai_Viet_Nam.md", "type": "folklore_book"},
                "score": 0.9240,
            },
        ],
    },
    "Nguồn gốc và ý nghĩa tâm linh của Lễ hội Đền Gióng (Phù Đổng & Sóc Sơn)?": {
        "answer": """### 🥁 Nguồn Gốc & Ý Nghĩa Tâm Linh Của Lễ Hội Đền Gióng

**1. Nguồn gốc truyền thuyết:**
* Lễ hội tưởng nhớ công đức của **Thánh Gióng (Phù Đổng Thiên Vương)** — một trong **Tứ Bất Tử** của tín ngưỡng dân gian Việt Nam, người đã đánh đuổi giặc Ân giữ cõi bờ đất nước `[1]`.
* Được tổ chức thường niên tại xã Phù Đổng (nơi sinh) và huyện Sóc Sơn (nơi Thánh Gióng cưỡi ngựa sắt bay về trời) `[1]`.

---

**2. Giá trị di sản & Ý nghĩa tâm linh:**
* 🏆 **Di sản thế giới:** Được UNESCO công nhận là *Di sản văn hóa phi vật thể đại diện của nhân loại* năm 2010 `[2]`.
* 🛡️ **Diễn xướng trận đánh kịch tính:** Lễ hội khao quân, cướp giò hoa tre, chém tướng giặc (ông Hiệu Cờ, Hiệu Trống, Hiệu Chiêng) mô phỏng sinh động chiến tranh nhân dân bảo vệ Tổ quốc `[1]`.
* 🌾 **Cầu mong mưa thuận gió hòa:** Khát vọng hòa bình, mùa màng bội thu và tinh thần đoàn kết cộng đồng làng xã `[2]`.
""",
        "sources": [
            {
                "content": "Lễ hội Đền Gióng Phù Đổng và Sóc Sơn là một kịch trường dân gian khổng lồ với sự tham gia của hàng ngàn dân làng. Các nghi thức cướp giò hoa tre...",
                "metadata": {"source": "Di_San_Le_Hoi_Giong_UNESCO.md", "type": "heritage_file"},
                "score": 0.9631,
            },
            {
                "content": "Ý nghĩa biểu tượng Tứ Bất Tử trong tâm thức Việt: Thánh Gióng tượng trưng cho sức mạnh chống ngoại xâm và tinh thần tuổi trẻ...",
                "metadata": {"source": "Tin_Nghuong_Dan_Gian_Viet_Nam.md", "type": "cultural_docs"},
                "score": 0.8990,
            },
        ],
    },
}

# Generic fallback mock for any other query
GENERIC_MOCK_RESPONSE = {
    "answer": """### 🏮 Kết Quả Tra Cứu Tri Thức Văn Hóa

Dựa trên dữ liệu từ *Viện Nghiên cứu Văn hóa* và *Hồ sơ Di sản Văn hóa Phi vật thể*:

* **Về phong tục & lễ hội:** Các tập quán truyền thống Việt Nam đều gửi gắm triết lý nhân sinh, lòng biết ơn tổ tiên và ước vọng hòa hợp với thiên nhiên đất trời `[1]`.
* **Về trang phục:** Trang phục truyền thống của 54 dân tộc anh em là di sản mỹ thuật tinh tế, từ thổ cẩm rực rỡ của vùng cao đến chiếc Áo ngũ thân, Áo dài thanh lịch nơi đồng bằng `[2]`.

*Ghi chú:* Để xem chi tiết chuẩn xác nhất, bạn có thể thử các câu hỏi mẫu trong thanh Sidebar!`,
""",
    "sources": [
        {
            "content": "Tổng quan văn hóa dân gian Việt Nam: Tập quán, di sản phi vật thể và nghệ thuật truyền thống...",
            "metadata": {"source": "Tong_Quan_Van_Hoa_Viet_Nam.md", "type": "cultural_docs"},
            "score": 0.8500,
        }
    ],
}

# =============================================================================
# SIDEBAR — CONTROLS & SETTINGS
# =============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; padding: 10px;'>
            <h2 style='color: #FFD700; margin-bottom: 0;'>🏮 Nét Việt AI</h2>
            <p style='color: #E0E0E0; font-size: 0.9rem;'>Trợ Lý Văn Hóa, Phong Tục & Lễ Hội</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("💡 Câu Hỏi Mẫu Dân Gian")
    suggestions = [
        "Ý nghĩa của tục xông đất đầu năm và những điều kiêng kỵ trong ngày Tết Nguyên Đán là gì?",
        "Trang phục Áo ngũ thân nam truyền thống gồm những chi tiết nào và sự khác biệt với Áo dài tân thời?",
        "Nguồn gốc và ý nghĩa tâm linh của Lễ hội Đền Gióng (Phù Đổng & Sóc Sơn)?",
        "Ý nghĩa của tục dựng cây Nêu ngày Tết và lễ Cúng Táo Quân (23 tháng Chạp)?",
        "Đặc điểm hoa văn và ý nghĩa biểu tượng trên trang phục truyền thống của người H'Mông?",
    ]

    for idx, sug in enumerate(suggestions):
        short_label = f"{sug[:38]}..."
        if st.button(f"📌 {short_label}", use_container_width=True, key=f"sug_btn_{idx}"):
            st.session_state["pending_query"] = sug

    st.divider()
    st.subheader("⚙️ Cấu Hình RAG Pipeline")

    execution_mode = st.radio(
        "Chế độ chạy (Execution Mode)",
        options=["Auto-Detect (Backend / Mock)", "Mock Demo Mode", "Force Task 10 Backend"],
        index=0,
    )

    top_k = st.slider("Số chunks retrieval (top_k)", min_value=1, max_value=10, value=5)

    rerank_strategy = st.selectbox(
        "Thuật toán Reranking",
        options=["RRF (Reciprocal Rank Fusion)", "Cross-Encoder", "MMR (Maximal Marginal Relevance)"],
    )

    st.divider()
    st.caption("**📚 Nguồn dữ liệu tích hợp:**")
    st.markdown("- 📜 *Viện Nghiên cứu Văn hóa Việt Nam*\n- 📖 *Sách Văn hóa Dân gian Việt Nam*\n- 🏛️ *Hồ sơ Di sản Phi vật thể UNESCO*")

    st.divider()
    if st.button("🗑️ Xóa Lịch Sử Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN INTERFACE
# =============================================================================

# Banner Header
st.markdown(
    """
    <div class="main-header">
        <h1>🏮 Trợ Lý Văn Hóa, Phong Tục & Lễ Hội Truyền Thống</h1>
        <p>Hệ thống RAG tra cứu chuyên sâu kiến thức dân gian Việt Nam, Áo ngũ thân, Áo dài & Di sản văn hóa phi vật thể.</p>
        <div style="margin-top: 12px;">
            <span class="tag-badge">🌾 Phong Tục Tết</span>
            <span class="tag-badge">👘 Áo Ngũ Thân & Áo Dài</span>
            <span class="tag-badge">🥁 Lễ Hội Dân Gian</span>
            <span class="tag-badge">🏛️ Di Sản UNESCO</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"📚 Nguồn tham khảo trích dẫn ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Tài liệu Văn hóa")
                    doc_type = meta.get("type", "cultural_doc")
                    score = src.get("score", 0.0)
                    st.markdown(f"**[{i}] {source_name}** | loại: `{doc_type}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:350] + "...")
                    st.divider()

# =============================================================================
# QUERY PROCESSING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi về phong tục, trang phục hoặc lễ hội truyền thống Việt Nam...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Append user question
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Đang truy vấn ChromaDB, tính điểm RRF Rerank và tổng hợp tri thức dân gian..."):
            start_time = time.time()
            answer = ""
            sources = []
            is_mock = False

            if execution_mode == "Mock Demo Mode":
                is_mock = True
            else:
                try:
                    # Attempt calling actual backend Task 10
                    from src.task10_generation import generate_with_citation
                    response = generate_with_citation(query, top_k=top_k)
                    answer = response.get("answer", "")
                    sources = response.get("sources", [])
                except (NotImplementedError, ModuleNotFoundError, Exception):
                    if execution_mode == "Force Task 10 Backend":
                        answer = "⚠️ **Task 10 chưa hoàn thiện:** Backend `src/task10_generation.py` chưa sẵn sàng. Hãy chọn *Mock Demo Mode* trong Sidebar để xem giao diện thử nghiệm."
                        sources = []
                    else:
                        is_mock = True

            # Use realistic mock response if in mock mode or fallback
            if is_mock:
                time.sleep(0.5)  # Simulate smooth retrieval latency
                mock_entry = MOCK_TOPIC6_KNOWLEDGE.get(query.strip(), GENERIC_MOCK_RESPONSE)
                answer = mock_entry["answer"]
                sources = mock_entry["sources"][:top_k]

            elapsed_ms = (time.time() - start_time) * 1000

            # Render answer
            st.markdown(answer)

            # Render RAG Telemetry Badges
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"⚡ Thời gian phản hồi: `{elapsed_ms:.1f} ms`")
            with col2:
                st.caption(f"🎯 Số chunks trích dẫn: `{len(sources)}`")
            with col3:
                st.caption(f"⚙️ Nguồn: `{'Mock Demo (Frontend)' if is_mock else 'Live RAG Backend'}`")

            # Render Sources Expander
            if sources:
                with st.expander(f"📚 Nguồn tham khảo trích dẫn ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Tài liệu Văn hóa")
                        doc_type = meta.get("type", "cultural_doc")
                        score = src.get("score", 0.0)
                        st.markdown(f"**[{i}] {source_name}** | loại: `{doc_type}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:350] + "...")
                        st.divider()

    # Save to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
