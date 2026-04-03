from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Design
from ai_generator import generate_design

app = Flask(__name__)
app.secret_key = "moletom-secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generator", methods=["GET", "POST"])
def generator():
    selected_color = request.args.get("color", "preto")

    if request.method == "POST":
        prompt = request.form["prompt"]
        color = request.form["color"]

        image_url = generate_design(prompt)

        design = Design(
            prompt=prompt,
            image_url=image_url,
            color=color
        )

        db.session.add(design)
        db.session.commit()

        return redirect(url_for("preview", design_id=design.id))

    return render_template("generator.html", selected_color=selected_color)

@app.route("/preview/<int:design_id>")
def preview(design_id):
    design = Design.query.get_or_404(design_id)

    return render_template("preview.html", design=design)


@app.route("/checkout/<int:design_id>")
def checkout(design_id):
    design = Design.query.get_or_404(design_id)
    return render_template("checkout.html", design=design)