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

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    auth = request.headers.get('Authorization',None)
    if not auth:
        print('not Auth')
        raise AuthError({
            'code':'authorization_header_missing',
            'description': 'Auhtorization header is expected'
        },401)
        
    parts = auth.split()
    
    if parts[0].lower() != 'bearer':
        print('!=bearer')
        raise AuthError({
            'code':'Invalid_header',
            'description':'Authorization header must start with "Bearer".'
        },401)
    elif len(parts) == 1:
        print('==1')
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found'
        },401)
    elif len(parts) > 2:
        print('>2')
        raise AuthError({
            'code':'Invalid_header',
            'description': 'It must be a bearer token'
        },401) 
    token = parts[1]
    return token

def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT'
        }, 400)
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description':'Permission not found'
        },403)

    return True

def verify_decode_jwt(token):
    url = 'https://coffeeshopbo.us.auth0.com/.well-known/jwks.json'
    
    jsonurl = urlopen(url,timeout=1)
   
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
                'description': 'Incorrect claims. Please, check the audience and issuer.'
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


def requires_auth(permission=''):
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