'''
uhh
'''
# pylint: disable=unused-import
from os import path
from sqlalchemy.exc import IntegrityError, NoResultFound
from flask import Flask, request, send_file, send_from_directory
from . import gacha
from . import users
from . import db
from . import utils

# Remember how I said I wanted to kill myself?
PROJECT_ROOT = path.abspath(path.join(path.dirname(__file__), ".."))
DATA_DIR = path.join(PROJECT_ROOT, "static")
ASSETS_DIR = path.join(DATA_DIR, "assets")
BANNERS_JSON_FILE = path.join(ASSETS_DIR, "banners.json")
RESOURCES_JSON_FILE = path.join(ASSETS_DIR, "resources.json")

app = Flask(
    __name__,
    static_folder=DATA_DIR
)

db.create_all_tables()

NO_ERROR = {"error": None}

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
# POST      /api/users
# DELETE    /api/users/<username>
# POST      /api/users/<username>/authenticate
# DELETE    /api/users/<username>/authenticate
# PATCH     /api/users/<username>/password
###############################################################################

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
    return NO_ERROR, 201


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
    return NO_ERROR, 201

@app.route("/api/users/<username>/authenticate", methods=["POST"])
@utils.require_parameters(["plaintext_password"])
@utils.tw(NoResultFound, {"error": "no user found"}, 401)
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

###############################################################################
############ CHART STORAGE AND STUFF
#
# Requests
# GET       /api/charts/<chart_uuid>/download
# GET       /api/charts/<chart_uuid>
###############################################################################

@app.route("/api/charts/<chart_uuid>/download", methods=["GET"])
def download_chart(chart_uuid="0"):
    '''
    downloads a chart
    '''
    mediapath = path.join(DATA_DIR, "charts/", chart_uuid)

    # check if someone is doing some non-Asahi approved shit (path traversal)
    if not utils.is_safe_path_component(mediapath):
        return {
            "error": "Asahi doesn't approve of what you're doing, ******boy",
            "If you're a user": "yeah you're not meant to see this page",
            "If you're a hacker": "my security measures aren't the greatest.\
                also there's no credit card info on my server so why would you\
                give a fuck?",
        }, 418

    if not path.isfile(mediapath):
        return {
            "error": "Resource not found (did you type the right UUID?)",
            "faulting_mediapath": mediapath,
            "If you're a user": "this is a '404 not found' page"
        }, 404

    return send_file(
        mediapath,
        as_attachment=True
    )

###############################################################################
############ GACHA STUFF
#
# Requests
# GET       /api/gacha/banners/
# GET       /api/gacha/banners/<banner>/
# POST      /api/gacha/banners/<banner>/pull/1
# POST      /api/gacha/banners/<banner>/pull/10
###############################################################################
@app.route("/api/gacha/banners")
def get_banners():
    return send_file(BANNERS_JSON_FILE)

@app.route("/api/gacha/banners/<banner>/pull/1", methods=["POST"])
def pull1():
    return send_file(BANNERS_JSON_FILE)

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

app.run("0.0.0.0", 8080)
