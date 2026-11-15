from datetime import datetime
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .auth import current_user, make_token, require_service_key
from .db import Base, engine, get_db
from .models import Progress, Roadmap, Section, Topic, User

Base.metadata.create_all(engine)
app = FastAPI(title="Bloom Roadmaps API")


class SSO(BaseModel):
    email: str = Field(min_length=5)
    name: str = ""


class ProgressIn(BaseModel):
    status: Literal["not_started", "in_progress", "done"]
    notes: str = ""


@app.post("/auth/sso", dependencies=[Depends(require_service_key)])
def sso(body: SSO, db: Session = Depends(get_db)):
    """Called only by the Streamlit server, after Streamlit has verified the user with OIDC."""
    email = body.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, name=body.name or email.split("@")[0])
        db.add(user)
        db.commit()
    return {"token": make_token(user.id), "name": user.name}


@app.get("/roadmaps")
def list_roadmaps(db: Session = Depends(get_db), user: User = Depends(current_user)):
    done = set(db.scalars(select(Progress.topic_id).where(
        Progress.user_id == user.id, Progress.status == "done")))
    out = []
    for r in db.scalars(select(Roadmap).options(
            selectinload(Roadmap.sections).selectinload(Section.topics))):
        ids = [t.id for s in r.sections for t in s.topics]
        out.append({"slug": r.slug, "title": r.title, "emoji": r.emoji,
                    "description": r.description, "total": len(ids),
                    "done": sum(1 for i in ids if i in done)})
    return out


@app.get("/roadmaps/{slug}")
def get_roadmap(slug: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.scalar(select(Roadmap).where(Roadmap.slug == slug).options(
        selectinload(Roadmap.sections).selectinload(Section.topics).selectinload(Topic.resources)))
    if not r:
        raise HTTPException(404, "Roadmap not found")
    prog = {p.topic_id: p for p in db.scalars(select(Progress).where(Progress.user_id == user.id))}
    return {
        "slug": r.slug, "title": r.title, "emoji": r.emoji, "description": r.description,
        "sections": [{
            "title": s.title, "summary": s.summary,
            "topics": [{
                "id": t.id, "title": t.title, "description": t.description,
                "resources": [{"title": x.title, "url": x.url} for x in t.resources],
                "status": prog[t.id].status if t.id in prog else "not_started",
                "notes": prog[t.id].notes if t.id in prog else "",
            } for t in s.topics]} for s in r.sections],
    }


@app.put("/progress/{topic_id}")
def save_progress(topic_id: int, body: ProgressIn, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    if not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found")
    p = db.scalar(select(Progress).where(Progress.user_id == user.id, Progress.topic_id == topic_id))
    if not p:
        p = Progress(user_id=user.id, topic_id=topic_id)
        db.add(p)
    p.status, p.notes, p.updated_at = body.status, body.notes, datetime.utcnow()
    db.commit()
    return {"ok": True}
