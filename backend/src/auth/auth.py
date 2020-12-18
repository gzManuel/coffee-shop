import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from socket import timeout
from urllib.request import urlopen
import logging

AUTH0_DOMAIN = 'coffeeshopbo.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drink'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
def get_token_auth_header():
    """Check if the bearer web token has the correct format

    Raises:
        AuthError: If there's not the authorization header
        AuthError: If doesn't start with "bearer" 
        AuthError: If there's not token
        AuthError: If the authorization header has more information.

    Returns:
        string: jwt token with the information of the user
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Auhtorization header is expected'
        }, 401)
    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'Invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)
    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found'
        }, 401)
    elif len(parts) > 2:
        raise AuthError({
            'code': 'Invalid_header',
            'description': 'It must be a bearer token'
        }, 401)
    token = parts[1]
    return token

def verify_decode_jwt(token):
    """ Verify the jwt and decode it with JSON Web Key Sets
        'https://coffeeshopbo.us.auth0.com/.well-known/jwks.json'

    Args:
        token (String): token got it by get_token_auth_header function

    Raises:
        AuthError: If the auhotization is malformed
        AuthError: If the token is expired
        AuthError: if have incorrect claims 
        AuthError: Can't authenticate token
        AuthError: The key provided is erroneous

    Returns:
        list: The payload obtained decoding the token.
    """
    url = 'https://coffeeshopbo.us.auth0.com/.well-known/jwks.json'

    jsonurl = urlopen(url, timeout=1)

    jwks = json.loads(jsonurl.read())

    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': '''Incorrect claims. Please, check the
                audience and issuer.'''
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

def check_permissions(permission, payload):
    """Check if the api permission is in the payload of the user

    Args:
        permission (String): The needy permission of the api
        payload (list): The data decoded of the token

    Raises:
        AuthError: The Payload don't have permissions.
        AuthError: The permission of the api, isn't in permissions.

    Returns:
        bool: True, exist the permission in the payload.
    """
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT'
        }, 400)
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found'
        }, 403)

    return True



def requires_auth(permission=''):
    """This is a decorator used with all the apis that need to check the authentification
    and permissions of the api.

    Executes all the functions written above to verify, authentificate jwt, and check 
    its permissions.

    Args:
        permission (str, optional): The permission of the api, for example 'patch:drinks'. Defaults to ''.
    """
    def requires_auth_decorator(f):
        @wraps(f)
        
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)
            check_permissions(permission, payload)

            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
