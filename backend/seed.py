"""Load every roadmaps/*.yaml into the database. Safe to re-run:  python -m backend.seed"""
import pathlib
import yaml
from sqlalchemy import select
from .db import Base, SessionLocal, engine
from .models import Resource, Roadmap, Section, Topic

Base.metadata.create_all(engine)
for path in sorted(pathlib.Path("roadmaps").glob("*.yaml")):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        old = db.scalar(select(Roadmap).where(Roadmap.slug == data["slug"]))
        if old:  # simple reseed for the scaffold (topic ids change; see README next steps)
            db.delete(old)
            db.flush()
        r = Roadmap(slug=data["slug"], title=data["title"], emoji=data.get("emoji", "🌸"),
                    description=data.get("description", ""))
        for si, s in enumerate(data["sections"]):
            sec = Section(title=s["title"], summary=s.get("summary", ""), position=si)
            for ti, t in enumerate(s["topics"]):
                top = Topic(title=t["title"], description=t.get("description", ""), position=ti)
                top.resources = [Resource(title=x[0], url=x[1]) for x in t.get("resources", [])]
                sec.topics.append(top)
            r.sections.append(sec)
        db.add(r)
        db.commit()
        print(f"Seeded {r.title}")
