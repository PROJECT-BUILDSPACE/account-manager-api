from flask import request, g
from flask_restx import reqparse, fields,  Namespace, Resource
from flask import Response
import requests
from functools import wraps
from datetime import datetime
from src.decorators import authentication, admin_authority
from models import Group, Role, JoinGroupBody, UserData, LoginParams, UserRegistration, Credentials
from src.utils import RespondWithError, Globals
from src.admin_client import AdminClient
import io


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
        # elif list(body.keys())[0] == 'attributes':
        elif 'attributes' in list(body.keys()):
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
        # client_secret = Globals().get_env("CLIENT_SECRET", "JSbJwHs0HPCDbvr1gcID76AV0RxZfsuw")

        client_secret = Globals().get_env("CLIENT_SECRET", "cD9VJiGEttbogB8UBcRSi0ZrJobaWCcN")

        issuer = Globals().get_env("ISSUER", "http://minikube.local:30105/auth")
        # issuer = Globals().get_env("ISSUER", "http://localhost:30105/auth")
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


@userNamespace.route('/register/', methods=['POST'])
class MainClass(Resource):

    @userNamespace.doc(responses={201: 'Created', 400: 'Bad request', 409: 'Conflict', 500: 'Server Error'})
    # @admin_authority
    def post(self):
        try:
            admin = AdminClient()
        except Exception as e:
            return RespondWithError(e.args[1], "Cannot get admin client.",
                                    e.args[0], "USR0007")

        try:
            email = request.form.get('email')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            picture = request.form.get('picture')

            credentials = Credentials(value=password)
            body = UserRegistration(username=email, email=email, credentials=[credentials], lastName=last_name, firstName=first_name, attributes={"picture": ""})

            if picture:
               body.attributes = {"picture": picture}
            else:
                picture = Globals().get_env("USER_DEFAULT_PICTURE", "default_user_icon.png")
                body.attributes = {"picture": picture}
        except Exception as e:
            return RespondWithError(400, "Could not resolve encoded params.", str(e), "USR0001")

        else:
            try:
                _ = admin.register_user(body)
            except Exception as err:
                return RespondWithError(err.args[1], "Could not register user.",
                                        err.args[0], "USR0006")
            else:
                user = admin.search_user(email)

                try:
                    copernicus_id = Globals().get_env("COPERNICUS_BUCKET_ID", "1ae79ed4-b1c0-49fb-a762-ed289663fa2c")
                    admin.join_group(copernicus_id, user.id)
                except Exception as err:
                    return RespondWithError(err.args[1], f"Could not join user {user.id} to Copernicus public organization.",
                                            err.args[0], "USR0008")

        return user.dict(), 201


@userNamespace.route('/picture/<id>', methods=['POST'])
class MainClass(Resource):

    @userNamespace.doc(responses={201: 'Created', 400: 'Bad request', 409: 'Conflict', 500: 'Server Error'})
    @authentication
    def post(self, id):
        id = request.view_args['id']
        storage = Globals().get_env('STORAGE', 'minikube.local:30900')
        pictures_bucket = Globals().get_env('PICTURES_BUCKET_ENDPOINT', 'pictures')
        access_key = Globals().get_env('ACCESS_KEY', 'NhBMrNSmM5nErUpB64zZ') #jQ9Ec11FhlQxxZyLPGXY
        secret_key = Globals().get_env('SECRET_ACCESS_KEY', 'Lbkgsp5LQ3yfjC2CZARMMi9urKHkFdmZgP5Xr1Nx') #DKDsTKhUiPuZdCytM4mTAFsPanbPfkHrJ9yUZPXK

        picture = io.BytesIO(request.data) # As a stream

        from minio import Minio
        from minio.error import S3Error

        # Initialize the MinIO client
        client = Minio(
            storage,
            access_key=access_key,
            secret_key=secret_key,
            secure=True  # Set to True if using HTTPS
        )

        try:
            client.put_object(
                bucket_name=pictures_bucket,
                object_name=id,
                data=picture,
                length=len(request.data),
            )
        except S3Error as err:
            return RespondWithError(err.args[1], "Cannot upload user's image.",
                                    err.args[0], "USR0009")
        else:
            try:
                admin = AdminClient()
                admin.update_attributes(g.user.sub, {"picture": id})
            except Exception as e:
                return RespondWithError(err.args[1], "Cannot assign image to user.",
                                        err.args[0], "USR0010")
        return None, 201


@userNamespace.route('/refresh', methods=['POST'])
class MainClass(Resource):

    @userNamespace.doc(responses={200: 'OK', 500: 'Server Error'})
    def post(self):
        refresh_token = request.form.get('refresh_token')

        realm = Globals().get_env("REALM", "buildspace")
        client_id = Globals().get_env("CLIENT_ID", "minioapi")
        client_secret = Globals().get_env("CLIENT_SECRET", "cD9VJiGEttbogB8UBcRSi0ZrJobaWCcN")

        issuer = Globals().get_env("ISSUER", "http://minikube.local:30105/auth")
        issuer = f'{issuer}/realms/{realm}/protocol/openid-connect/token'

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(issuer, data=payload)

        return response.json(), response.status_code
