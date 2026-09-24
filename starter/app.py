from flask import render_template

from workshop import create_app

app = create_app(__name__)


@app.get("/")
def index():
    return render_template("index.html", sample_word="apple")
