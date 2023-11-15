from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
# from src.utils.utils import oidc, mongoClient
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority
from models import Role, RoleUpdate
from src.utils import RespondWithError
from src.admin_client import AdminClient


roleNamespace = Namespace('role')


parser = reqparse.RequestParser()
# parser.add_argument('skip', type=int, help='skip tasks')

@roleNamespace.route('/group-admin/<group_id>', methods=['POST', 'PUT', 'GET', 'DELETE'])
class MainClass(Resource):

    @roleNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @taskNamespace.model(task_model)
    # @taskNamespace.param('id', 'id')

    @authentication
    @admin_authority
    def get(self, group_id):

        try:
            role = g.admin.get_role('group-admin')
        except Exception as err:
            return RespondWithError(err.args[1], "Could not getch role.",
                                    err.args[0], "GRP0001")

        return {group_id: role.attributes.pop(group_id)}, 200

    @authentication
    @admin_authority
    def put(self, group_id):
        try:
            body = RoleUpdate.parse_obj(request.json)
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "GRP0001")

        try:
            role = g.admin.get_role('group-admin')
            role.attributes = body.attributes
            _ = g.admin.update_role(role)
        except Exception as err:
            return RespondWithError(err.args[1], "Could not update role.",
                                    err.args[0], "GRP0001")

        return None, 204

