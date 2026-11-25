# app.py - ConsoleFlare BI Agent chat screen
# Run: streamlit run app.py
#
# Files this app uses:
#   .streamlit/config.toml        theme colours
#   assets/consoleflare_logo.png  logo in the sidebar
#   chats.json                    saved chat history (created automatically)

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from agent import agent

CHATS_FILE = Path("chats.json")
LOGO = "assets/consoleflare_logo.png"

st.set_page_config(page_title="BI Agent | ConsoleFlare", page_icon="📊", layout="centered")

# ---------------------------------------------------------------------------
# 1. Brand styling (ConsoleFlare colours + DM Sans font)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap');

:root {
  --background: #0d0f12; --foreground: #ffffff; --muted: #a7a7a7;
  --brand: #7833fe; --brand-dark: #652bd6; --brand-soft: #c7aaff;
  --brand-secondary: #ffd21f; --surface: #1a1a1a; --surface-soft: #2a2a2a;
  --font: "DM Sans", Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}

/* font everywhere (icons keep their own font) */
html, body, .stApp, .stMarkdown, p, li, h1, h2, h3, h4, label,
button, input, textarea, [data-testid="stChatInput"] textarea { font-family: var(--font) !important; }

.stApp { background: var(--background); }
header[data-testid="stHeader"] { background: transparent; }
.stAppDeployButton, #MainMenu { display: none; }
.block-container { padding-top: 2.2rem; padding-bottom: 6rem; max-width: 820px; }

/* ---- sidebar ---- */
section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--surface-soft); }
section[data-testid="stSidebar"] .stButton button {
  justify-content: flex-start; border-radius: 10px; border: 1px solid transparent;
  background: transparent; color: var(--foreground); min-height: 40px;
}
section[data-testid="stSidebar"] .stButton button p {
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left;
}
section[data-testid="stSidebar"] .stButton button:hover { background: var(--surface-soft); border-color: var(--surface-soft); }
section[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: rgba(120, 51, 254, .18); border-color: var(--brand); color: var(--brand-soft);
}
.side-label { color: var(--muted); font-size: 12px; font-weight: 500; margin: 18px 0 6px; }
.side-foot { color: var(--muted); font-size: 12px; margin-top: 24px; line-height: 1.5; }

/* new chat button */
.st-key-new_chat button {
  justify-content: center !important; background: var(--brand) !important;
  border-color: var(--brand) !important; font-weight: 700;
}
.st-key-new_chat button:hover { background: var(--brand-dark) !important; }

/* ---- header ---- */
.cf-header { margin-bottom: 18px; }
.cf-pill {
  display: inline-block; background: var(--brand-secondary); color: #0d0f12;
  font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 999px;
}
.cf-title { font-size: 34px; font-weight: 700; line-height: 1.1; margin: 10px 0 6px; }
.cf-title span { color: var(--brand-soft); }
.cf-sub { color: var(--muted); font-size: 16px; margin: 0; }

/* ---- empty state suggestions ---- */
.st-key-suggestions .stButton button {
  width: 100%; min-height: 64px; text-align: left; justify-content: flex-start;
  background: var(--surface); border: 1px solid var(--surface-soft); border-radius: 14px;
  padding: 12px 16px; color: var(--foreground);
}
.st-key-suggestions .stButton button:hover { border-color: var(--brand); background: #1f1730; }

/* ---- chat messages ---- */
[data-testid="stChatMessage"] {
  background: var(--surface); border: 1px solid var(--surface-soft);
  border-radius: 16px; padding: 14px 16px; margin-bottom: 12px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: rgba(120, 51, 254, .14); border-color: rgba(120, 51, 254, .45);
}
[data-testid="stChatMessageAvatarAssistant"] { background: var(--brand); color: #fff; }
[data-testid="stChatMessageAvatarUser"] { background: var(--brand-secondary); color: #0d0f12; }
[data-testid="stChatMessage"] code { color: var(--brand-soft); }
[data-testid="stExpander"] details { border-color: var(--surface-soft); border-radius: 10px; }

/* ---- chat input ---- */
[data-testid="stBottom"] > div { background: var(--background); }
[data-testid="stChatInput"] { border-radius: 14px; border: 1px solid var(--surface-soft); background: var(--surface); }
[data-testid="stChatInput"]:focus-within { border-color: var(--brand); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Language: English / Hinglish
#    Screen text changes, and the agent is told which language to answer in.
# ---------------------------------------------------------------------------
TEXT = {
    "English": {
        "sub": "Ask questions about your business data in plain language. I find the data, run the queries and explain what I see.",
        "lang": "Answer language",
        "new": "New chat",
        "history": "Previous chats",
        "empty": "No chats yet.",
        "try": "Try one of these",
        "input": "Ask about sales, targets, promotions, reviews...",
        "thinking": "Looking at the data...",
        "sql": "Show SQL",
        "error": "Sorry, something went wrong:",
        "foot": "Read-only access. Answers come from your data; the SQL used is shown under each answer.",
        "examples": [
            "What was total revenue by month in 2018?",
            "Why did revenue drop in June compared to May?",
            "Which regions missed their target in June 2018?",
            "Are late deliveries affecting review scores?",
        ],
    },
    "Hinglish": {
        "sub": "Apne business data ke baare mein simple language mein sawaal poochiye. Main data dhoondh kar, query chala kar, result samjhaunga.",
        "lang": "Jawab ki language",
        "new": "Nayi chat",
        "history": "Pichhli chats",
        "empty": "Abhi tak koi chat nahi.",
        "try": "Inme se koi try kijiye",
        "input": "Sales, targets, promotions, reviews ke baare mein poochiye...",
        "thinking": "Data check kar raha hoon...",
        "sql": "SQL dekhiye",
        "error": "Maaf kijiye, kuch galat ho gaya:",
        "foot": "Sirf read-only access. Jawab aapke data se aate hain; har jawab ke neeche SQL dikhaya gaya hai.",
        "examples": [
            "2018 mein har mahine ka total revenue kitna tha?",
            "June mein May ke comparison mein revenue kyun gira?",
            "June 2018 mein kaun se regions ne target miss kiya?",
            "Kya late delivery se review score par asar pada?",
        ],
    },
}

LANG_INSTRUCTION = {
    "English": "Answer in simple English.",
    "Hinglish": ("Answer in Hinglish: Hindi written in English letters, the way people chat in India "
                 "(for example: 'June mein revenue 8% kam hua'). Keep numbers, months, region names "
                 "and business terms like revenue and target in English."),
}

if "lang" not in st.session_state:
    st.session_state.lang = "English"


# ---------------------------------------------------------------------------
# 3. Saved chats
# ---------------------------------------------------------------------------
def load_chats():
    if CHATS_FILE.exists():
        return json.loads(CHATS_FILE.read_text(encoding="utf-8"))
    return {}


def save_chats():
    CHATS_FILE.write_text(json.dumps(st.session_state.chats, indent=2, ensure_ascii=False), encoding="utf-8")


def start_new_chat():
    st.session_state.current_id = str(uuid.uuid4())


if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
if "current_id" not in st.session_state:
    start_new_chat()


# ---------------------------------------------------------------------------
# 4. Sidebar
# ---------------------------------------------------------------------------
try:
    st.logo(LOGO, size="large")
except TypeError:            # older Streamlit without the size option
    st.logo(LOGO)

with st.sidebar:
    st.radio(TEXT[st.session_state.lang]["lang"], ["English", "Hinglish"],
             key="lang", horizontal=True)
    t = TEXT[st.session_state.lang]

    if st.button(t["new"], key="new_chat", icon=":material/add:", use_container_width=True):
        start_new_chat()
        st.rerun()

    st.markdown(f'<div class="side-label">{t["history"]}</div>', unsafe_allow_html=True)
    chats = st.session_state.chats
    current_id = st.session_state.current_id
    if not chats:
        st.caption(t["empty"])

    for chat_id, chat in sorted(chats.items(), key=lambda c: c[1]["created"], reverse=True):
        is_current = chat_id == current_id
        col1, col2 = st.columns([6, 1], vertical_alignment="center")
        if col1.button(chat["title"], key=f"open_{chat_id}", use_container_width=True,
                       type="primary" if is_current else "secondary"):
            st.session_state.current_id = chat_id
            st.rerun()
        if col2.button("", key=f"del_{chat_id}", icon=":material/delete:", help="Delete"):
            del chats[chat_id]
            save_chats()
            if is_current:
                start_new_chat()
            st.rerun()

    st.markdown(f'<div class="side-foot">{t["foot"]}</div>', unsafe_allow_html=True)

t = TEXT[st.session_state.lang]
chats = st.session_state.chats
current_id = st.session_state.current_id
current_messages = chats.get(current_id, {}).get("messages", [])


# ---------------------------------------------------------------------------
# 5. Helpers
# ---------------------------------------------------------------------------
def sql_from_this_turn(all_messages):
    """Only the SQL run for the latest question (the agent returns the whole chat)."""
    last_question = max(i for i, m in enumerate(all_messages) if m.type == "human")
    queries = []
    for m in all_messages[last_question + 1:]:
        if m.type == "ai":
            for call in m.tool_calls or []:
                if call["name"] == "run_sql":
                    queries.append(call["args"]["query"])
    return queries


def show_sql(queries):
    if queries:
        with st.expander(t["sql"], icon=":material/code:"):
            for q in queries:
                st.code(q, language="sql")


def show_message(msg):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        show_sql(msg.get("sql"))


# ---------------------------------------------------------------------------
# 6. Main area
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="cf-header">
  <span class="cf-pill">AI Data Analyst</span>
  <div class="cf-title">Business Intelligence <span>Agent</span></div>
  <p class="cf-sub">{t["sub"]}</p>
</div>
""", unsafe_allow_html=True)

if not current_messages:
    st.markdown(f'<div class="side-label">{t["try"]}</div>', unsafe_allow_html=True)
    with st.container(key="suggestions"):
        cols = st.columns(2)
        for i, q in enumerate(t["examples"]):
            if cols[i % 2].button(q, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending = q
                st.rerun()

for msg in current_messages:
    show_message(msg)


# ---------------------------------------------------------------------------
# 7. New question
# ---------------------------------------------------------------------------
question = st.chat_input(t["input"])
if "pending" in st.session_state:
    question = st.session_state.pop("pending")

if question:
    if current_id not in chats:
        chats[current_id] = {
            "title": question[:40] + ("..." if len(question) > 40 else ""),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": [],
        }
    user_msg = {"role": "user", "content": question}
    chats[current_id]["messages"].append(user_msg)
    show_message(user_msg)

    # the language instruction goes to the agent only, not on screen
    agent_input = f"{question}\n\n({LANG_INSTRUCTION[st.session_state.lang]})"

    with st.chat_message("assistant"):
        with st.spinner(t["thinking"]):
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": agent_input}]},
                    config={"configurable": {"thread_id": current_id}},
                )
                answer = result["messages"][-1].content
                sql = sql_from_this_turn(result["messages"])
            except Exception as e:
                answer = f"{t['error']} {e}"
                sql = []
        st.markdown(answer)
        show_sql(sql)

    chats[current_id]["messages"].append({"role": "assistant", "content": answer, "sql": sql})
    save_chats()
    st.rerun()
