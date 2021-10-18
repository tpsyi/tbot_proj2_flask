from flask import (
    Flask, request, render_template, g
)
import main
import config
import app_dir.database.tabledef
import app_dir.database.db_util
from app_dir.blueprints.auth import auth_bp, login_required

main.main()


app = Flask(__name__, template_folder="app_dir/templates/", static_folder="app_dir/static")
app.secret_key = "b_5#y2L'F4Q8z\n\xec]'"

stat = "IDLE"
app.register_blueprint(auth_bp)


@app.route('/', methods=["GET", "POST"])
def main_app():
    if g.user:
        return render_template("main.html", name=g.user["username"])
    return render_template("main.html", name="Guest")

@app.route('/status', methods=["GET", "POST"])
@login_required
def status():
    global stat
    print(request)
    if request.method == "POST":
        if request.form.get("submit_a"):
            main.start()
            stat = "RUNNING"
        elif request.form.get("submit_b"):
            main.stop()
            stat = "IDLE"
    return render_template("status.html", status=stat)

# app.run(host="0.0.0.0")