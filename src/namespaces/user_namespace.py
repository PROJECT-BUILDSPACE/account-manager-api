from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
import requests
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority
from models import Group, Role, JoinGroupBody, UserData, LoginParams
from src.utils import RespondWithError, Globals
from src.admin_client import AdminClient


userNamespace = Namespace('user')


parser = reqparse.RequestParser()

@userNamespace.route('/', methods=['GET', 'PUT', 'POST'])
class MainClass(Resource):

    @userNamespace.doc(responses={201: 'Created', 200: 'OK', 204: 'No Content', 400: 'Bad request', 401: 'Unauthorized',
                                   409: 'Conflict', 500: 'Server Error'}, security='Bearer')
    @authentication
    def get(self):
        try:
            admin = AdminClient()
            user_data = admin.get_userdata(g.user.sub)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not fetch user data.",
                                    e.args[0], "USR0001")

        # get group names from IDs
        return user_data, 200

    @authentication
    def put(self):
        try:
            body = request.json
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "GRP0001")

        if len(body.keys()) > 1:
            return RespondWithError(e.args[1], "Mixed content on update. Update either the password or the attributes.",
                                    e.args[0], "USR0002")
        elif list(body.keys())[0] == 'attributes':
            try:
                admin = AdminClient()
                admin.update_attributes(g.user.sub, body['attributes'])
            except Exception as e:
                return RespondWithError(e.args[1], "Could not update user's attributes.",
                                        e.args[0], "USR0003")
        else:
            try:
                admin = AdminClient()
                admin.update_password(g.user.sub, body['password'])
            except Exception as e:
                return RespondWithError(e.args[1], "Could not update user's password.",
                                        e.args[0], "USR0004")

        return None, 204

    def post(self):
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            body = LoginParams(username=username, password=password)
        except Exception as e:
            return RespondWithError(400, "Could not resolve encoded params.", str(e), "USR0001")

        realm = Globals().get_env("REALM", "buildspace")

        client_id = Globals().get_env("CLIENT_ID", "minioapi")
        client_secret = Globals().get_env("CLIENT_SECRET", "xdoNxAmEDv0zZuoskyh87gEMPNARWkID")

        issuer = Globals().get_env("ISSUER", "http://minikube.local:30105/auth")
        issuer = f'{issuer}/realms/{realm}/protocol/openid-connect/token'

        body.grant_type = 'password'
        body.client_id = client_id
        body.client_secret = client_secret

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = body.dict(exclude_unset=False)
        response = requests.post(issuer, headers=headers, data=payload)
        if response.status_code >= 300:
            return RespondWithError(401, "Unauthorized.", "User not authenticated. Check whether email and password are correct.", "USR0005")
        return response.json(), 201


