from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
# from src.utils.utils import oidc, mongoClient
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority, naive_admin_authority
from models import Role, RoleUpdate, SharingInput
from src.utils import RespondWithError
from src.admin_client import AdminClient


shareNamespace = Namespace('share')


parser = reqparse.RequestParser()
# parser.add_argument('skip', type=int, help='skip tasks')

@shareNamespace.route('/', methods=['POST', 'PUT', 'DELETE'])
class MainClass(Resource):

    @shareNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @taskNamespace.model(task_model)
    # @taskNamespace.param('id', 'id')

    @authentication
    @naive_admin_authority
    def post(self):
        try:
            body = SharingInput.parse_obj(request.json)
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "SHR0001")

        try:
            admin = AdminClient()
            group = admin.search_group(body.target_organization_name)
            target_members = admin.get_members(group.id)
        except Exception as err:
            return RespondWithError(err.args[1], "Could not fetch role.",
                                    err.args[0], "SHR0002")
        else:
            if body.rights == 'editor':
                key = 'editor_in_user_attr'
            elif body.rights == 'viewer':
                key = 'viewer_in_user_attr'
            else:
                return RespondWithError(400, "Could not update user's attributes.",
                                        "No such rights exist. Select among 'viewer' and 'editor'.", "SHR0003")

            for member in target_members:
                if member.attributes and key in member.attributes.keys():
                    shared_folders = member.attributes[key]
                    shared_folders.append(body.folder_id)
                else:
                    shared_folders = [body.folder_id]

                attrs = {key: shared_folders}

                try:
                    _ = admin.update_attributes(user_id=member.id, attributes=attrs)
                except Exception as e:
                    print(e)
                    return RespondWithError(e.args[1], "Could not update user's attributes.",
                                            e.args[0], "SHR0004")

        return None, 201

    @authentication
    @naive_admin_authority
    def delete(self):
        try:
            body = SharingInput.parse_obj(request.json)
        except Exception as e:
            return RespondWithError(400, "Could not resolve payload.", str(e), "SHR0001")

        try:
            admin = AdminClient()
            group = admin.search_group(body.target_organization_name)
            target_members = admin.get_members(group.id)
        except Exception as err:
            return RespondWithError(err.args[1], "Could not fetch role.",
                                    err.args[0], "SHR0002")
        else:
            for member in target_members:

                for key in ['editor_in_user_attr', 'viewer_in_user_attr']:
                    try:
                        _ = member.attributes[key].pop(member.attributes[key].index(body.folder_id))
                    except ValueError:
                        pass
                    except KeyError:
                        pass
                    except Exception as e:
                        return RespondWithError(500, "Could not delete sharing.",
                                                str(e), "SHR0002")


                try:
                    _ = admin.update_attributes(user_id=member.id, attributes=member.attributes)
                except Exception as e:
                    print(e)
                    return RespondWithError(e.args[1], "Could not update user's attributes.",
                                            e.args[0], "SHR0004")

        return None, 200

    @authentication
    @naive_admin_authority
    def put(self):
        self.delete()
        self.post()
        return None, 200