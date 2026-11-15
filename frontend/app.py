import os
import pathlib
import requests
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from garden import build

load_dotenv()

API = os.getenv("API_URL")
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


def save(tid, skey, nkey, stopkey, n, advance):
    status = st.session_state[skey]
    call("PUT", f"/progress/{tid}", json={"status": status, "notes": st.session_state[nkey]})
    st.toast("A new flower bloomed 🌸" if status == "done" else "Saved 🌷")
    if advance:
        st.session_state[stopkey] = min(st.session_state[stopkey] + 1, n - 1)


def step(stopkey, delta, n):
    st.session_state[stopkey] = min(max(st.session_state[stopkey] + delta, 0), n - 1)


def roadmap_screen(slug):
    data = call("GET", f"/roadmaps/{slug}").json()
    flat = [t for s in data["sections"] for t in s["topics"]]
    n = len(flat)
    done = sum(t["status"] == "done" for t in flat)
    growing = sum(t["status"] == "in_progress" for t in flat)
    stopkey = f"stop_{slug}"
    if stopkey not in st.session_state:  # start the walk at the first unfinished stop
        st.session_state[stopkey] = next((i for i, t in enumerate(flat) if t["status"] != "done"), n - 1)
    cur = st.session_state[stopkey]

    st.markdown(f"<div class='hand'>{data['description']}</div>", unsafe_allow_html=True)
    st.title(f"{data['emoji']} {data['title']}")
    st.markdown(f"<div class='chips'><span>🌸 {done} bloomed</span><span>🌱 {growing} growing</span>"
                f"<span>🫘 {n - done - growing} seeds waiting</span></div>", unsafe_allow_html=True)
    st.progress(done / max(n, 1))
    if done == n:
        st.success("Your garden is in full bloom, and the cottage lights are on. 🌸")

    garden, panel = st.columns([3, 2], gap="large")
    with garden:
        components.html(build(data, cur), height=780, scrolling=True)
    with panel:
        t = flat[cur]
        back, fwd = st.columns(2)
        back.button("← Step back", on_click=step, args=(stopkey, -1, n), disabled=cur == 0, use_container_width=True)
        fwd.button("Step forward →", on_click=step, args=(stopkey, 1, n), disabled=cur == n - 1, use_container_width=True)
        with st.container(border=True):
            st.markdown(f"<div class='hand'>stop {cur + 1} of {n}</div>", unsafe_allow_html=True)
            st.subheader(t["title"])
            st.write(t["description"])
            for x in t["resources"]:
                st.markdown(f"- [{x['title']}]({x['url']})")
            keys = list(STATUS)
            skey, nkey = f"s{t['id']}", f"n{t['id']}"
            st.selectbox("Status", keys, index=keys.index(t["status"]), format_func=STATUS.get, key=skey)
            st.text_area("My notes", t["notes"], key=nkey)
            c1, c2 = st.columns(2)
            c1.button("Save", on_click=save, args=(t["id"], skey, nkey, stopkey, n, False), use_container_width=True)
            c2.button("Save & walk on 🌷", on_click=save, args=(t["id"], skey, nkey, stopkey, n, True),
                      type="primary", use_container_width=True)
        st.selectbox("Jump to a stop", range(n), key=stopkey,
                     format_func=lambda i: f"{FLOWER[flat[i]['status']]} {i + 1}. {flat[i]['title']}")


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
