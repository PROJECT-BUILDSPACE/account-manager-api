from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
# from src.utils.utils import oidc, mongoClient
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority
from models import Group, Role, JoinGroupBody, UserData
from src.utils import RespondWithError
from src.admin_client import AdminClient


userNamespace = Namespace('user')


parser = reqparse.RequestParser()
# parser.add_argument('skip', type=int, help='skip tasks')

@userNamespace.route('/<user_id>', methods=['GET', 'PUT'])
class MainClass(Resource):

    @userNamespace.doc(responses={201: 'Created', 400: 'Bad request', 401: 'Unauthorized',
                                   409: 'Conflict', 500: 'Server Error'}, security='Bearer')

    @authentication
    def get(self, user_id):
        try:
            admin = AdminClient()
            user_data = admin.get_userdata(user_id)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not fetch user data.",
                                    e.args[0], "USR0001")

        # get group names from IDs
        return user_data, 200


    @authentication
    def put(self, user_id):
        try:
            body = request.json
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "GRP0001")

        try:
            admin = AdminClient()
            admin.update_password(user_id, body['password'])
        except Exception as e:
            return RespondWithError(e.args[1], "Could not update user's password.",
                                    e.args[0], "USR0002")

        return 204

