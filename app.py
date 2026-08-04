"""
🏮 Trợ Lý Giải Đáp Phong Tục, Trang Phục & Lễ Hội Truyền Thống Việt Nam
Streamlit Application — Topic 6 (Vietnamese Folklore, Traditional Costumes & Festivals RAG)
Kết nối Task 10 (Document Reordering & Citation Generation)
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

# Import Task 10 generation function
try:
    from src.task10_generation import generate_with_citation
except ImportError:
    generate_with_citation = None

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
    </style>
    """,
    unsafe_allow_html=True,
)

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
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Điều kiện xin học bổng Academic Achievement?",
    ]

    for idx, sug in enumerate(suggestions):
        short_label = f"{sug[:38]}..."
        if st.button(f"📌 {short_label}", use_container_width=True, key=f"sug_btn_{idx}"):
            st.session_state["pending_query"] = sug

    st.divider()
    st.subheader("⚙️ Cấu Hình RAG Pipeline")
    top_k = st.slider("Số chunks retrieval (top_k)", min_value=1, max_value=10, value=5)

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

st.markdown(
    """
    <div class="main-header">
        <h1>🏮 Trợ Lý Văn Hóa, Phong Tục & Lễ Hội Truyền Thống</h1>
        <p>Hệ thống RAG tra cứu chuyên sâu kết nối Task 10 (Document Reordering & Citation Generation)</p>
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

    # Generate response from Task 10 generate_with_citation
    with st.chat_message("assistant"):
        with st.spinner("🔍 Đang thực thi Retrieval, Document Reordering và tổng hợp câu trả lời với Citation..."):
            start_time = time.time()
            answer = ""
            sources = []
            retrieval_src = "hybrid"

            try:
                if generate_with_citation is not None:
                    response = generate_with_citation(query, top_k=top_k)
                    answer = response.get("answer", "Chưa thể trả lời.")
                    sources = response.get("sources", [])
                    retrieval_src = response.get("retrieval_source", "hybrid")
                else:
                    answer = "⚠️ **Lỗi:** Không thể import `generate_with_citation` từ `src.task10_generation`."
            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy kiểm tra `src/task10_generation.py`!"
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"

            elapsed_ms = (time.time() - start_time) * 1000

            # Render answer
            st.markdown(answer)

            # Render Telemetry
            st.caption(f"⚡ Thời gian phản hồi: `{elapsed_ms:.1f} ms` | 🎯 Chunks: `{len(sources)}` | ⚙️ Pipeline: `{retrieval_src}`")

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
