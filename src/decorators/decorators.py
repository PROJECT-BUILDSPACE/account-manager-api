from src.utils import Globals, RespondWithError, decode_n_verify
# import jwt
# from jwt.api_jwt import decode_complete as decode_token
from functools import wraps
from flask import request, g
from models import BearerToken, ErrorReport, Role
from src.admin_client import AdminClient


def authentication(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = token.split(" ")[1]
        if not token:
            return RespondWithError(401, "Unauthorized.", "No Bearer token.", "MID0002")

        base = Globals().get_env("ISSUER", "https://keycloak-inherit.euinno.eu")
        # base = Globals().get_env("ISSUER", "http://localhost:30105/auth")
        bs_certs = Globals().get_env("BS_CERTS", "/realms/inherit/protocol/openid-connect/certs")

        # jwks_client = PyJWKClient(base + bs_certs)
        try:
            # signing_key = jwks_client.get_signing_key_from_jwt(token)
            # import time
            # time.sleep(0.8)
            data = decode_n_verify(token, base + bs_certs)
        except Exception as e:
            g.user = None
            return RespondWithError(400, "Could not resolve request.", str(e), "MID0002")

        g.user = BearerToken.parse_obj(data)
        return f(*args, **kwargs)
    return wrap

def admin_authority(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            admin = AdminClient()
        except Exception as e:
            return RespondWithError(e.args[1], "Cannot get admin client.",
                                    e.args[0], "MID0002")

        groupId = request.view_args['group_id']

        try:
            admin_role: Role = admin.get_role('group-admin')
            admins = [item.strip() for item in admin_role.attributes[groupId][0].split(',')]
        except Exception as e:
            # print(f"Admin Authority Role Retrieval Error: {e}")
            return RespondWithError(403, "User is not allowed to perform this action",
                                    "User requires admin priviledges.", "MID0002")
        else:
            if g.user.sub not in admins:
                # print(f"Admin Authority User {g.user.sub} is not an admin for group_name {groupName}. Admins: {admins}")
                return RespondWithError(403, "User is not allowed to perform this action",
                                        "User requires admin priviledges.", "MID0002")
            g.admin = admin
        return f(*args, **kwargs)
    return wrap

def admin_authority_name(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            admin = AdminClient()
        except Exception as e:
            # print(f"AdminClient Initialization Error: {e}")
            return RespondWithError(e.args[1], "Cannot get admin client.",
                                    e.args[0], "MID0002")

        groupName = request.view_args['group_name']
        if not groupName:
            # print("Missing group_name in request")
            return RespondWithError(400, "Bad Request", "Missing group_name in request.", "MID0002")

        try:
            group = admin.search_group(groupName)
            print(f"Group Retrieved: {group}")
        except Exception as e:
            return RespondWithError(e.args[1], "Could not get group.",
                                    e.args[0], "MID0002")

        try:
            admin_role: Role = admin.get_role('group-admin')
            admins = [item.strip() for item in admin_role.attributes[group.id][0].split(',')]
            # print(f"Admin Role Retrieved: {admin_role}")
            # print(f"Admins List for group_name {groupName} (group_id {group.id}): {admins}")
        except Exception as e:
            # print(f"Role Retrieval Error: {e}")
            return RespondWithError(403, "User is not allowed to perform this action",
                                    "User requires admin priviledges.", "MID0002")
        else:
            if g.user.sub not in admins:
                # print(f"User {g.user.sub} is not an admin for group_name {groupName}. Admins: {admins}")
                return RespondWithError(403, "User is not allowed to perform this action",
                                        "User requires admin priviledges.", "MID0002")
            g.admin = admin
        return f(*args, **kwargs)
    return wrap

def naive_admin_authority(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            admin = AdminClient()
        except Exception as e:
            return RespondWithError(e.args[1], "Cannot get admin client.",
                                    e.args[0], "MID0002")

        else:
            g.admin = admin
        return f(*args, **kwargs)
    return wrap


