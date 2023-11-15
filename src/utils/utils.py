import jwt
from jwt.api_jwt import decode_complete as decode_token
import requests
import json

def RespondWithError(code: int, message: str, reason: str, internal_code: str):
	error = {
        "message": message + " Please contact the BUILDSPACE Support Team.",
        "reason": reason,
        "status": code,
        "internal_status": internal_code
    }

	return error, code

def decode_n_verify(token, jwks_uri):
    jwks = requests.get(jwks_uri)
    jwks = jwks.json()

    public_keys = {jwk['kid']: jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk)) for jwk in jwks['keys']}

    kid = jwt.get_unverified_header(token)['kid']

    key = public_keys[kid]

    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience="account",
        options={"verify_exp": True}
    )