from __future__ import annotations

import os
import streamlit as st

from news_writer.config import AppConfig, apply_runtime_overrides
from news_writer.graph import build_graph, stream_run
from news_writer.tracing import LocalTrace

st.set_page_config(page_title="Conchita News Writer", page_icon="📰", layout="wide")

st.title("📰 Conchita News Writer")
st.caption("LangGraph + Gemini + Tavily. Genera un artículo con trace.")

cfg = AppConfig()

with st.sidebar:
    st.header("🔐 Claves y tracing")
    google_api_key = st.text_input("GOOGLE_API_KEY (Gemini)", value=cfg.google_api_key or "", type="password")
    tavily_api_key = st.text_input("TAVILY_API_KEY (búsqueda)", value=cfg.tavily_api_key or "", type="password")

    enable_langsmith = st.toggle("Activar LangSmith tracing (opcional)", value=bool(cfg.langchain_tracing_v2))
    langsmith_api_key = st.text_input("LANGCHAIN_API_KEY / LANGSMITH_API_KEY", value=cfg.langsmith_api_key or "", type="password")
    project_name = st.text_input("LANGCHAIN_PROJECT", value=cfg.langchain_project or "conchita-news-writer")

    st.divider()
    st.header("⚙️ Modelo y búsqueda")
    model = st.selectbox("Modelo Gemini", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"], index=0)
    max_results = st.slider("Resultados Tavily", min_value=3, max_value=10, value=5, step=1)

def content_to_text(content) -> str:
    """Normaliza msg.content (puede ser str o list[parts]) a str."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict):
                # Formato típico: {"type": "text", "text": "..."}
                if "text" in part and isinstance(part["text"], str):
                    chunks.append(part["text"])
                else:
                    chunks.append(str(part))
            else:
                chunks.append(str(part))
        return "\n".join(chunks)
    return str(content)


apply_runtime_overrides(
    google_api_key=google_api_key.strip() or None,
    tavily_api_key=tavily_api_key.strip() or None,
    enable_tracing=enable_langsmith,
    langsmith_api_key=langsmith_api_key.strip() or None,
    project_name=project_name.strip() or None,
)

missing = []
if not os.getenv("GOOGLE_API_KEY"):
    missing.append("GOOGLE_API_KEY")
if not os.getenv("TAVILY_API_KEY"):
    missing.append("TAVILY_API_KEY")
if missing:
    st.warning(f"Faltan claves: {', '.join(missing)}. Añádelas en la barra lateral o en un .env")

user_prompt = st.text_area(
    "¿Qué artículo quieres generar?",
    value="Escribe un artículo sobre las tendencias más recientes en IA aplicadas a educación superior, con foco en Europa.",
    height=140,
)

colA, colB = st.columns([1, 2], gap="large")
with colA:
    run_btn = st.button("🚀 Generar artículo", type="primary", use_container_width=True)
    show_events = st.checkbox("Mostrar eventos del grafo (trace local)", value=True)
    show_all_messages = st.checkbox("Mostrar mensajes intermedios (incluye outline)", value=False)

with colB:
    st.markdown(
        """**Flujo**
1) `search`: busca noticias (Tavily)  
2) `outliner`: crea outline + fuentes  
3) `writer`: redacta artículo final  

**Trace**
- Con LangSmith: activa el toggle y añade tu API key.
- Sin LangSmith: verás un trace local (eventos) aquí mismo.
"""
    )

if run_btn:
    trace = LocalTrace()

    try:
        graph = build_graph(model=model, tavily_max_results=max_results)
    except Exception as e:
        st.error(f"No pude construir el grafo: {e}")
        st.stop()

    st.info("Ejecutando… (streaming en vivo)")
    messages_box = st.empty()
    events_box = st.empty()
    final_box = st.empty()

    transcript = ""
    final_text = ""

    try:
        for event in stream_run(graph, user_prompt, stream_mode="values"):
            if show_events:
                trace.log("event", {"keys": list(event.keys())})

            if isinstance(event, dict) and "messages" in event and event["messages"]:
                msg = event["messages"][-1]
                raw_content = getattr(msg, "content", "")
                content = content_to_text(raw_content)
            if content:
                if show_all_messages:
                    transcript += "\n\n---\n\n" + content
                    messages_box.markdown(transcript)
                else:
                    messages_box.markdown(content)
                final_text = content


            if show_events:
                events_box.markdown("### 🧵 Trace local\n" + trace.to_markdown(max_entries=120))

        if final_text:
            final_box.markdown("### ✅ Artículo final\n" + str(final_text))

        else:
            final_box.warning("No apareció texto final. Activa 'mensajes intermedios' para depurar.")

        if enable_langsmith:
            st.success("Tracing activado. Revisa tu proyecto en LangSmith para ver el trace completo.")
    except Exception as e:
        st.error(f"Error durante la ejecución: {e}")
        st.stop()
