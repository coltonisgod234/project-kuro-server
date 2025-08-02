'''
uhh
'''
# pylint: disable=unused-import
from os import path
from json import load
from sqlalchemy.exc import IntegrityError, NoResultFound
from flask import Flask, request, send_file, send_from_directory
from . import gacha
from . import users
from . import db
from . import utils
from . import charts
from . import filters

# Remember how I said I wanted to kill myself?
PROJECT_ROOT = path.abspath(path.join(path.dirname(__file__), ".."))
DATA_DIR = path.join(PROJECT_ROOT, "static")
ASSETS_DIR = path.join(DATA_DIR, "assets")
CHARTS_DIR = path.join(DATA_DIR, "charts")
BANNERS_JSON_FILE = path.join(ASSETS_DIR, "banners.json")
RESOURCES_JSON_FILE = path.join(ASSETS_DIR, "resources.json")

app = Flask(
    __name__,
    static_folder=DATA_DIR
)

db.create_all_tables()

Ok = {"error": None}

###############################################################################
############ SERVER CONFIG
# robots.txt and such
#
# GET       /robots.txt
# GET       /sitemap.xml
# GET       /api
# GET       /
###############################################################################

@app.route("/robots.txt")
def robots_txt():
    '''
    send the robots.txt file (quit trackin me motherfucker)
    '''
    return send_from_directory(DATA_DIR, "robots.txt")

@app.route("/sitemap.xml")
def poison0():
    '''
    poison bots with cursed sitemap
    '''
    return send_from_directory(DATA_DIR, "poison.xml")

@app.route("/api/")
def api_index():
    '''
    API index
    '''
    return send_from_directory(DATA_DIR, "api_index.htm")

###############################################################################
############ USERS AND AUTH
# Manage users and authorization
#
# GET       /api/users
# GET       /api/whoami
# POST      /api/users
# DELETE    /api/users/<username>
# POST      /api/users/<username>/authenticate
# DELETE    /api/users/<username>/authenticate
# PATCH     /api/users/<username>/password
# GET       /api/users/<username>/asahi
###############################################################################


@app.route("/api/whoami", methods=["GET"])
@utils.require_bearer
@utils.db_transaction
@utils.tw(NoResultFound, {"error": "invalid bearer token"}, 401)
def user_whoami(token: str = None, session = None):
    '''
    web API to list users in JSON format
    '''
    user = session.query(users.User) \
        .where(users.User.token == token) \
        .one()

    return {
        "error": None,
        "username": user.username,
        "id": user.id,
    }, 200

@app.route("/api/users", methods=["GET"])
@utils.db_transaction
def query_users(session = None):
    '''
    web API to list users in JSON format
    '''
    data: dict = request.args
    # get parameters
    query = session.query(users.User)
    query = filters.comparisons(
        "username", query, data, users.User.username,
        cst=False, ops=filters.STIRNG_OPS
    )
    query = filters.comparisons("asahi", query, data, users.User.asahi)
    query = filters.comparisons("id", query, data, users.User.id)

    matches = query.all()
    json = []
    for match in matches:
        json.append(match.as_dict())

    return json, 201

@app.route("/api/users", methods=["POST"])
@utils.require_parameters(["username", "plaintext_password"])
@utils.tw(IntegrityError, {"error": "invalid username"}, 409)
def create_user():
    '''
    web API to do create_user()
    '''
    data = request.json
    users.create_user(
        username=data["username"],
        plaintext_password=data["plaintext_password"]
    )
    return Ok, 201

@app.route("/api/users/<username>", methods=["DELETE"])
@utils.db_transaction
@utils.require_bearer
@utils.tw(NoResultFound, {"error": "no user found"}, 401)
def bye_bye_user_fuck_you(username, token = None, session = None):
    '''
    web API to do create_user()
    '''
    obj = session.query(users.User) \
        .where(users.User.username == username) \
        .where(users.User.token == token) \
        .one()

    session.delete(obj)
    return Ok, 201

@app.route("/api/users/<username>/authenticate", methods=["POST"])
@utils.require_parameters(["plaintext_password"])
@utils.tw(NoResultFound, {"error": "no user found"}, 404)
@utils.tw(utils.UnauthorizedError, {"error": "auth failed"}, 401)
def authenticate(username: str):
    '''
    logs a user in
    '''
    data = request.json
    token = users.authenticate(
        username = username,
        plaintext_password = data["plaintext_password"]
    )
    return {
        "token": token,
        "error": "bad password" if token is None else None
    }, 401 if token is None else 200

@app.route("/api/users/<username>/authenticate", methods=["DELETE"])
@utils.require_bearer
@utils.tw(utils.UnauthorizedError, {"error": "unauthorized"}, 401)
def deauthenticate(username: str, token=None):
    '''
    logs a user out
    provided the user's session is valid
    '''
    token = users.deauthenticate(
        username = username,
        token = token
    )
    return ({
        "token": token,
        "error": "bad or null session" if token is not None else None
    })

@app.route("/api/users/<username>/password", methods=["PATCH"])
@utils.require_parameters(["plaintext_password"])
@utils.require_bearer
@utils.tw(utils.UnauthorizedError, {"error": "unauthorized"}, 401)
def change_password(username: str, token=None):
    '''
    changes a user's password via the API
    provided the user's session is valid
    '''
    data = request.json
    password = data["plaintext_password"]
    new_password = users.change_password(username, password, token)
    if new_password != password:
        return {"error": "password not changed"}, 400

    return {
        "error": None,
        "password": new_password,
        "old_passord": password
        }, 200

@app.route("/api/users/<username>/asahi", methods=["GET"])
@utils.db_transaction
@utils.tw(NoResultFound, {"error": "user not found"}, 404)
def get_asahi_user(username: str = None, session = None):
    '''
    get a user's asahi
    '''
    user = session.query(users.User) \
        .where(users.User.username == username) \
        .one()

    return {
        "username": user.username,
        "user_asahi": user.asahi
    }, 200

###############################################################################
############ CHART STORAGE AND STUFF
#
# Requests
# GET       /api/charts
# GET       /api/charts/<chart_uuid>/tar
#               ?attachment
#
# GET       /api/charts/<chart_uuid>
###############################################################################

@app.route("/api/charts")
@utils.db_transaction
@utils.tw(NoResultFound, {"error": "no result found"}, 404)
def get_charts(session = None):
    '''
    get a chart
    '''
    data: dict = request.args
    query = session.query(charts.Chart)
    query = filters.comparisons("id", query, data, charts.Chart.id)
    query = filters.comparisons("song_title", query, data,
                                charts.Chart.song_title)
    result = query.all()
    return [obj.to_dict() for obj in result]

@app.route("/api/charts/<chart_id>")
@utils.db_transaction
@utils.tw(NoResultFound, {"error": "no result found"}, 404)
def get_chart(chart_id, session = None):
    '''
    get JSON info about a chart at a given URL
    '''
    obj = session.query(charts.Chart) \
        .where(charts.Chart.id == chart_id) \
        .one()

    return obj.to_dict()

@app.route("/api/charts/<chart_id>/zip", methods=["GET"])
def download_chart(chart_id="0"):
    '''
    downloads/sends a chart
    '''
    mediapath = path.join(DATA_DIR, "charts/", chart_id)
    utils.path_validate_abort(mediapath)

    attachment = int(request.args.get("attachment", 0))  # fucked
    return send_file(
        mediapath,
        as_attachment=bool(attachment),
        mimetype="text/plain"
    )

@app.route("/api/charts", methods=["POST"])
def upload_chart():
    '''
    uploads a chart
    '''
    file = request.files.get("zip")
    if file is None:
        return {
            "error": "no file"
        }, 415

    match file.content_type:
        case "application/zip":
            charts.upload_chart_zip(file, DATA_DIR)
        case _:
            return {"error": "bad file type"}, 415

###############################################################################
############ GACHA STUFF
#
# Requests
# GET       /api/gacha/banners/
# GET       /api/gacha/latest_banner/
# GET       /api/gacha/banners/<banner>/
# POST      /api/gacha/banners/<banner>/pull/1
# POST      /api/gacha/banners/<banner>/pull/1
# GET       /api/gacha/users/<username>/items
###############################################################################
@app.route("/api/gacha/banners")
def get_banners():
    '''
    returns the BANNERS_JSON_FILE (typically /static/assets/banners.json)
    '''
    return send_file(BANNERS_JSON_FILE)

@app.route("/api/gacha/banners/<string:banner>")
@utils.tw(KeyError, {"error": "banner does not exist"}, 404)
def get_banner(banner: str = None):
    '''
    get a given banner in the URL
    '''
    data: dict = {}
    with open(BANNERS_JSON_FILE, mode="r", encoding="utf-8") as f:
        data = load(f)

    return data[banner]

@app.route("/api/gacha/banners/<string:banner>/pull/1", methods=["POST"])
@utils.require_bearer
@utils.db_transaction
@utils.tw(gacha.NotEnoughAsahi, {"error": "not enough Asahi"}, 403)
@utils.tw(KeyError, {"error": "banner does not exist"}, 404)
@utils.tw(NoResultFound, {"error": "unauthorized"}, 401)
def pull1(banner: str = None, token: str = None, session = None):
    '''
    preforms a single pull for the logged in user on a given banner
    '''
    user = session.query(users.User) \
        .where(users.User.token == token) \
        .one()

    banners = {}
    with open(BANNERS_JSON_FILE, mode="r", encoding="utf-8") as f:
        banners = load(f)

    _id, drop = gacha.pull1(user, banners[banner])
    return {
        "name": drop["item"],
        "id": _id,
        "error": None
    }, 200

@app.route("/api/gacha/users/<username>/items", methods=["GET"])
@utils.db_transaction
def get_items_list(username: str = None, session = None):
    '''
    gets the list of items a user owns
    '''
    json = []
    items = session.query(gacha.UserItem) \
            .join(users.User) \
            .where(users.User.username == username) \
            .all()

    for item in items:
        json.append({
            "id": item.id,
            "name": item.name,
        })

    return json, 200

@app.route("/dev")
def team_c00lkid_join_today():
    '''
    team c00lkid join today
    Why do I put FORSAKEN references in my code?
    '''
    data = "err"
    with open(path.join(PROJECT_ROOT, "frontend.html"),
              mode="r",
              encoding="utf-8") as f:
        data = f.read()
    return data, 200

app.run(
    "0.0.0.0", 8080,
    debug=True,
    threaded=False,
    processes=4
)
