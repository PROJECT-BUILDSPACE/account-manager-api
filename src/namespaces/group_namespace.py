from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
# from src.utils.utils import oidc, mongoClient
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority
from models import Group, Role, JoinGroupBody
from src.utils import RespondWithError
from src.admin_client import AdminClient


groupNamespace = Namespace('group')


parser = reqparse.RequestParser()
# parser.add_argument('skip', type=int, help='skip tasks')

@groupNamespace.route('/', methods=['POST', 'GET'])
class MainClass(Resource):

    @groupNamespace.doc(responses={201: 'Created', 400: 'Bad request', 401: 'Unauthorized',
                                   409: 'Conflict', 500: 'Server Error'}, security='Bearer')

    @authentication
    def post(self):
        try:
            body = Group.parse_obj(request.json)
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "GRP0001")

        # Create current timestamp
        body.attributes['created'] = [str(datetime.now())]

        # Create group
        try:
            admin = AdminClient()
            admin.create_group(body)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not create group.",
                                    e.args[0], "GRP0001")

        # Get group created
        try:
            groupId = admin.search_group(body.name).id
            group = admin.get_group(groupId)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not fetch created group.",
                                    e.args[0], "GRP0001")

        # Add user in new group and give admin priviledges
        try:
            _ = admin.join_group(groupId, g.user.sub)

            admin_role = admin.get_role('group-admin')
            admin_role.attributes[groupId] = [g.user.sub]
            admin.update_role(admin_role)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not create roles.",
                                    e.args[0], "GRP0001")

        return group.dict(), 201

    @authentication
    def get(self):
        try:
            admin = AdminClient()
            groups = admin.get_user_groups(g.user.sub)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not fetch groups.",
                                    e.args[0], "GRP0001")

        # get group names from IDs
        return groups, 200


@groupNamespace.route('/<group_id>', methods=['POST', 'PUT', 'GET', 'DELETE'])
class MainClass(Resource):

    @groupNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @taskNamespace.model(task_model)
    # @taskNamespace.param('id', 'id')

    @authentication
    @admin_authority
    def delete(self, group_id):
        groupId = request.view_args['group_id']

        # admin delete group
        try:
            g.admin.delete_group(group_id)
        except Exception as err:
            return RespondWithError(err.args[1], "Could not delete group.",
                                    err.args[0], "GRP0001")

        # delete roles
        try:
            admin_role = g.admin.get_role('group-admin')
            _ = admin_role.attributes.pop(groupId)
            g.admin.update_role(admin_role)
        except Exception as e:
            return RespondWithError(e.args[1], "Could not update roles.",
                                    e.args[0], "GRP0001")
        return None, 204


    @authentication
    @admin_authority
    def post(self, group_id):
        groupId = request.view_args['group_id']

        #resolve body
        try:
            body = JoinGroupBody.parse_obj(request.json)
        except Exception as err:
            return RespondWithError(400, "Could not resolve body of request.",
                                    err.args[0], "GRP0001")
        # admin delete group
        for item in body.users:
            uid = list(item.keys())[0]
            adm = list(item.values())[0].admin
            try:
                g.admin.join_group(group_id, uid)
            except Exception as err:
                return RespondWithError(err.args[1], f"Could not join user {uid}.",
                                        err.args[0], "GRP0001")

            if adm:
                # Add admin priviledges
                try:
                    admin_role = g.admin.get_role('group-admin')
                    admin_role.attributes[group_id][0] += f',{uid}'
                    g.admin.update_role(admin_role)
                except Exception as e:
                    return RespondWithError(e.args[1], f"Could not make user {uid} admin.",
                                            e.args[0], "GRP0001")

        return None, 204
