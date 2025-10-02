import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)




# قاعدة البيانات (SQLite افتراضيًا)
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///football1.db"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------- Models --------
class Match(db.Model):
    __tablename__ = "matches"
    match_id = db.Column(db.Integer, primary_key=True)
    match_name = db.Column(db.String(200))  # ← هنا العمود الجديد

    team1 = db.Column(db.String(200))
    team2 = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, server_default=db.func.now())

class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.match_id"), nullable=False)
    team = db.Column(db.String(100))
    player = db.Column(db.String(200))
    event = db.Column(db.String(100))
    outcome = db.Column(db.String(100))
    mins = db.Column(db.Integer)
    secs = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    x2 = db.Column(db.Float, nullable=True)
    y2 = db.Column(db.Float, nullable=True)

# -------- Routes --------
@app.route("/")
def index():
    return send_from_directory("static", "tag.html")

@app.route("/api/saveMatch", methods=["POST"])
def save_match():
    data = request.get_json() or {}
    match_name = data.get("matchName", "Untitled Match")
    team1 = data.get("team1", "")
    team2 = data.get("team2", "")
    events = data.get("events", [])

    match = Match(match_name=match_name, team1=team1, team2=team2)
    db.session.add(match)
    db.session.commit()

    # حفظ الأحداث
    for ev in events:
        def to_float(v):
            try:
                if v == '' or v is None:
                    return None
                return float(v)
            except:
                return None

        e = Event(
            match_id=match.match_id,
            team=ev.get("Team"),
            player=ev.get("Player"),
            event=ev.get("Event"),
            outcome=ev.get("Outcome"),
            mins=int(ev.get("Mins") or 0),
            secs=int(ev.get("Secs") or 0),
            x=to_float(ev.get("X")),
            y=to_float(ev.get("Y")),
            x2=to_float(ev.get("X2")),
            y2=to_float(ev.get("Y2"))
        )
        db.session.add(e)

    db.session.commit()
    return jsonify({"success": True, "matchId": match.match_id})

@app.route("/api/matches", methods=["GET"])
def get_matches():
    rows = Match.query.order_by(Match.date_created.desc()).all()
    out = []
    for m in rows:
        count = Event.query.filter_by(match_id=m.match_id).count()
        out.append({
        "match_id": m.match_id,
        "match_name": m.match_name,
        "team1": m.team1,
        "team2": m.team2,
        "date_created": m.date_created.isoformat(),
        "events_count": count
    })

    return jsonify(out)

@app.route("/api/events/<int:match_id>", methods=["GET"])
def get_events(match_id):
    rows = Event.query.filter_by(match_id=match_id).all()
    out = []
    for r in rows:
        out.append({
            "event_id": r.event_id,
            "team": r.team,
            "player": r.player,
            "event": r.event,
            "outcome": r.outcome,
            "mins": r.mins,
            "secs": r.secs,
            "x": r.x,
            "y": r.y,
            "x2": r.x2,
            "y2": r.y2
        })
    return jsonify(out)
from flask import Response

@app.route("/api/export/<int:match_id>", methods=["GET"])
def export_match_csv(match_id):
    rows = Event.query.filter_by(match_id=match_id).all()
    if not rows:
        return jsonify({"error": "No events"}), 404

    # عنوان الأعمدة
    header = "Team,Player,Event,Outcome,Mins,Secs,X,Y,X2,Y2\n"
    lines = []
    for r in rows:
        lines.append(f"{r.team},{r.player},{r.event},{r.outcome},{r.mins},{r.secs},{r.x},{r.y},{r.x2 or ''},{r.y2 or ''}")

    csv_data = header + "\n".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=match_{match_id}.csv"}
    )


# -------- Run --------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
