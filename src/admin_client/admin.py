import requests
from src.utils import Globals
from urllib.parse import urlencode
from src.utils import RespondWithError
from models import Group, Role, List, UserData, UserAttrs

class AdminClient():
    def __init__(self):
        # self.base = Globals().get_env("ISSUER", "http://minikube.local:30105/auth")
        self.base = Globals().get_env("ISSUER", "http://localhost:30105/auth")
        self.realm = Globals().get_env("REALM", "buildspace")
        self.token_path = '/realms/master/protocol/openid-connect/token'
        self.admin_client = Globals().get_env("ADMIN_CLIENT", "admin-cli")
        self.admin_uname = Globals().get_env("ADMIN_UNAME", "buildspace")
        self.admin_pwd = Globals().get_env("ADMIN_PWD", "4@8<lk4<iAhp&of")
        self.__master_token__ = 'Bearer ' + self.__get_master_token__()

    def __get_master_token__(self):
        payload = {
            'grant_type': 'password',
            'client_id': self.admin_client,
            'username': self.admin_uname,
            'password': self.admin_pwd,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.base + self.token_path, headers=headers, data=payload)

        if response.status_code < 300:
            master_token = response.json()['access_token']
        else:
            raise ConnectionError('Could not get admin.', response.status_code)
        return  master_token

    def create_group(self, group: Group):
        headers = {'Authorization': self.__master_token__}
        payload = group.dict(exclude_unset=True)
        response = requests.post(self.base + f'/admin/realms/{self.realm}/groups', json = payload, headers=headers)

        if response.status_code >= 300:
            raise ConnectionError(response.reason, response.status_code)
        return payload

    def get_group(self, group_id: str) -> Group:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/groups/{group_id}', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError(response.reason, response.status_code)
        return Group.parse_obj(response.json())


    def get_members(self, group_id: str) -> List[UserData]:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/groups/{group_id}/members', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError(response.reason, response.status_code)
        return [UserData.parse_obj(item) for item in response.json()]

    def search_group(self, group_name: str) -> Group:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/groups/?search={group_name}', headers=headers)
        print("group_name:", group_name)
        if response.status_code >= 300:
            raise ConnectionError(response.reason, response.status_code)

        return Group.parse_obj(response.json()[0])

    def delete_group(self, group_id: str):
        headers = {'Authorization': self.__master_token__}
        response = requests.delete(self.base + f'/admin/realms/{self.realm}/groups/{group_id}', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError(response.reason, response.status_code)
        return response

    def get_role(self, role_name: str) -> Role:
        headers = {'Authorization': self.__master_token__}

        response = requests.get(self.base + f'/admin/realms/{self.realm}/roles/{role_name}', headers=headers)
        if response.status_code < 300:
            role = Role.parse_obj(response.json())
        else:
            raise ConnectionError('Could not get role.', response.status_code)
        return role

    def update_role(self, role: Role):
        headers = {'Authorization': self.__master_token__}
        payload = role.dict()
        response = requests.put(self.base + f'/admin/realms/{self.realm}/roles-by-id/{role.id}', json=payload, headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get role.', response.status_code)
        return response

    def get_user_groups(self, user_id: str) -> List[Group]:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/users/{user_id}/groups', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get user groups.', response.status_code)
        return response.json()


    def join_group(self, group_id: str, user_id: str) -> List[Group]:
        headers = {'Authorization': self.__master_token__}
        response = requests.put(self.base + f'/admin/realms/{self.realm}/users/{user_id}/groups/{group_id}', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get user groups.', response.status_code)
        return response


    def leave_group(self, group_id: str, user_id: str) -> List[Group]:
        headers = {'Authorization': self.__master_token__}
        response = requests.delete(self.base + f'/admin/realms/{self.realm}/users/{user_id}/groups/{group_id}', headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get user groups.', response.status_code)
        return response

    def get_userdata(self, user_id: str) -> UserData:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/users/{user_id}',headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get user data.', response.status_code)
        return response.json()

    def get_userdata_by_email(self, user_email: str) -> UserData:
        headers = {'Authorization': self.__master_token__}
        response = requests.get(self.base + f'/admin/realms/{self.realm}/users/?search={user_email}',headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not get user data.', response.status_code)
        return UserData.model_validate(response.json()[0])

    def update_password(self, user_id: str, new_pwd: str):
        headers = {'Authorization': self.__master_token__}
        payload = {
            "credentials": [
                {
                    "type": "password",
                    "value": new_pwd
                }
            ]
        }
        response = requests.put(self.base + f'/admin/realms/{self.realm}/users/{user_id}', json=payload, headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not update user password.', response.status_code)
        return response

    def update_attributes(self, user_id: str, attributes: dict):
        headers = {'Authorization': self.__master_token__}
        try:
            print("attributes: ", attributes)
            _ = UserAttrs.parse_obj(attributes)
        except:
            raise ConnectionError('Not valid attributes', 400)

        payload = {"attributes": attributes}
        response = requests.put(self.base + f'/admin/realms/{self.realm}/users/{user_id}', json=payload, headers=headers)
        if response.status_code >= 300:
            raise ConnectionError('Could not update user attributes.', response.status_code)
        return response