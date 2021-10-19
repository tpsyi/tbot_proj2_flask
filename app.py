from flask import (
    Flask, request, render_template, g
)
import main
import config
from app_dir.blueprints.auth import auth_bp, login_required
from app_dir.blueprints.tables import table_bp

main.main()


app = Flask(__name__, template_folder="app_dir/templates/", static_folder="app_dir/static")
app.secret_key = "dev"

stat = "Idle"
app.register_blueprint(auth_bp)
app.register_blueprint(table_bp)


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
        if request.form.get("run"):
            main.start()
            stat = "Running"
        elif request.form.get("stop"):
            main.stop()
            stat = "Idle"
    return render_template("status.html", status=stat)

class CLASS:
  def __init__(self, name, age, test):
    self.name = name
    self.age = age
    self.test = test

# @app.route('/admins')
# def admins_db():
#     h_test = ["1st", "2nd", "propaty"]
#     local_session = db
#     return render_template("base_table.html", headings=h_test, data=test)

app.run(host="0.0.0.0")