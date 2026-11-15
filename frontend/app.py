import os
import pathlib
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8051")
SERVICE_KEY = os.getenv("SERVICE_KEY", "")
STATUS = {"not_started": "Not started", "in_progress": "In progress", "done": "Done"}
FLOWER = {"done": "🌸", "in_progress": "🌱", "not_started": "▫️"}

st.set_page_config(page_title="Bloom Roadmaps", page_icon="🌸", layout="wide")
st.markdown(f"<style>{(pathlib.Path(__file__).parent / 'style.css').read_text()}</style>",
            unsafe_allow_html=True)


def call(method, path, **kw):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if "token" in st.session_state else {}
    try:
        r = requests.request(method, API + path, headers=headers, timeout=15, **kw)
    except requests.RequestException:
        st.error("Can't reach the server. Check that the API is running at " + API)
        st.stop()
    if r.status_code == 401 and "token" in st.session_state:
        st.session_state.pop("token")  # API token expired; it is re-issued from the Streamlit login
        st.rerun()
    return r


def auth_screen():
    st.markdown("<div class='hand'>a quiet corner for learning</div>", unsafe_allow_html=True)
    st.title("🌸 Bloom Roadmaps")
    st.write("Pick a roadmap, work through it at your own pace, and watch your garden grow.")
    st.button("Continue with Google", on_click=st.login, type="primary")


def get_api_token():
    """Trade the identity Streamlit verified for an API token (runs once per browser session)."""
    if not st.user.get("email_verified", True):
        st.error("Your Google email isn't verified, so we can't sign you in.")
        st.stop()
    try:
        r = requests.post(API + "/auth/sso", headers={"X-Service-Key": SERVICE_KEY}, timeout=15,
                          json={"email": st.user.email, "name": st.user.get("name") or ""})
    except requests.RequestException:
        st.error("Can't reach the server. Check that the API is running at " + API)
        st.stop()
    if not r.ok:
        st.error("The server rejected the sign-in. Check that SERVICE_KEY matches on both sides.")
        st.stop()
    st.session_state.update(token=r.json()["token"], name=r.json()["name"])


def roadmap_screen(slug):
    data = call("GET", f"/roadmaps/{slug}").json()
    topics = [t for s in data["sections"] for t in s["topics"]]
    done = sum(t["status"] == "done" for t in topics)
    st.markdown(f"<div class='hand'>{data['description']}</div>", unsafe_allow_html=True)
    st.title(f"{data['emoji']} {data['title']}")
    st.progress(done / max(len(topics), 1), text=f"{done} of {len(topics)} topics complete")
    st.markdown("<div class='garden'>" + "".join(FLOWER[t["status"]] for t in topics) + "</div>",
                unsafe_allow_html=True)
    st.caption("🌸 done   🌱 in progress   ▫️ not started")

    for s in data["sections"]:
        sd = sum(t["status"] == "done" for t in s["topics"])
        st.header(s["title"])
        st.write(f"{s['summary']}  ({sd}/{len(s['topics'])} done)")
        for t in s["topics"]:
            with st.expander(f"{FLOWER[t['status']]}  {t['title']}"):
                st.write(t["description"])
                for x in t["resources"]:
                    st.markdown(f"- [{x['title']}]({x['url']})")
                keys = list(STATUS)
                status = st.selectbox("Status", keys, index=keys.index(t["status"]),
                                      format_func=STATUS.get, key=f"s{t['id']}")
                notes = st.text_area("My notes", t["notes"], key=f"n{t['id']}")
                if st.button("Save", key=f"b{t['id']}"):
                    call("PUT", f"/progress/{t['id']}", json={"status": status, "notes": notes})
                    st.toast("Saved 🌷")
                    st.rerun()


if not getattr(st.user, "is_logged_in", False):
    auth_screen()
    st.stop()
if "token" not in st.session_state:
    get_api_token()

roadmaps = call("GET", "/roadmaps").json()
with st.sidebar:
    st.markdown(f"<div class='hand'>hello, {st.session_state.name}</div>", unsafe_allow_html=True)
    if not roadmaps:
        st.info("No roadmaps yet. Run `python -m backend.seed`.")
        st.stop()
    labels = {r["slug"]: f"{r['emoji']} {r['title']} ({r['done']}/{r['total']})" for r in roadmaps}
    pick = st.radio("Your roadmaps", list(labels), format_func=labels.get)
    st.button("Sign out", on_click=st.logout)
roadmap_screen(pick)
