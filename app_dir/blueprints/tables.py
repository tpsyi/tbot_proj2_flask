from flask import Flask, Blueprint, render_template
from app_dir.blueprints.auth import login_required
from app_dir.database import db_util as wdb_util
from database import db_util as tdb_util
from app_dir.database.tabledef import web_admin
from database.tabledef import db_User, Order, Meal

table_bp = Blueprint('tables', __name__, url_prefix='/table')

@table_bp.route("/admins")
@login_required
def admin_db():
    headings = ["ID", "Username", "Status", "Registration Date"]
    table = []
    bool_str = ["Inactive", "Active"]
    local_session = wdb_util.Session()
    for i in local_session.query(web_admin).all():
        table.append([i.id, i.username, bool_str[i.active], i.reg_date])
    local_session.close()
    return render_template("base_table.html", headings=headings, data=table, table_name="Admins")

@table_bp.route("/users")
@login_required
def users_db():
    headings = ["ID", "Phone Number", "Username", "Status", "Registration Date"]
    table = []
    bool_str = ["Client", "Chef"]
    local_session = tdb_util.Session()
    for i in local_session.query(db_User).all():
        table.append([i.id, i.phone_number, i.name, bool_str[i.is_chef], i.reg_date])
    local_session.close()
    return render_template("base_table.html", headings=headings, data=table, table_name="Users")

@table_bp.route("/meals")
@login_required
def meals_db():
    headings = ["ID", "Name", "Price", "Order Count"]
    table = []
    local_session = tdb_util.Session()
    for i in local_session.query(Meal).all():
        table.append([i.id, i.name, i.cost, len(i.orders)])
    local_session.close()
    return render_template("base_table.html", headings=headings, data=table, table_name="Meals")

@table_bp.route("/orders")
@login_required
def orders_db():
    headings = ["ID", "User ID", "Phone Number", "Content", "Status", "Date"]
    table = []
    local_session = tdb_util.Session()
    for i in local_session.query(Order).all():
        table.append([i.id, i.user_id, i.contact_phone_number, i.content, i.status.capitalize(), i.ins_date])
    local_session.close()
    return render_template("base_table.html", headings=headings, data=table, table_name="Orders")

