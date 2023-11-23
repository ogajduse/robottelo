# General utility functions which does not fit into other util modules OR
# Independent utility functions that doesnt need separate module
import base64
import re

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from packaging.version import Version

from robottelo.config import settings


def gen_ssh_keypairs():
    """Generates private SSH key with its public key"""
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )
    return private.decode('utf-8'), public.decode('utf-8')


def validate_ssh_pub_key(key):
    """Validates if a string is in valid ssh pub key format
    :param key: A string containing a ssh public key encoded in base64
    :return: Boolean
    """

    if not isinstance(key, str):
        raise ValueError(f"Key should be a string type, received: {type(key)}")

    # 1) a valid pub key has 3 parts separated by space
    # 2) The second part (key string) should be a valid base64
    try:
        key_type, key_string, _ = key.split()  # need more than one value to unpack
        base64.decodebytes(key_string.encode('ascii'))
        return key_type in ('ecdsa-sha2-nistp256', 'ssh-dss', 'ssh-rsa', 'ssh-ed25519')
    except (ValueError, base64.binascii.Error):
        return False


def slugify_component(string, keep_hyphens=True):
    """Make component name a slug
       Arguments:
        string {str} -- Component name e.g: ActivationKeys
        keep_hyphens {bool} -- Keep hyphens or replace with underscores
    return:
        str -- component slug e.g: activationkeys
    """
    string = string.replace(" and ", "&")
    if not keep_hyphens:
        string = string.replace('-', '_')
    return re.sub("[^-_a-zA-Z0-9]", "", string.lower())


def get_content_host_os_config(os_id, os_version, host_type='vm', os_sub_type=None):
    '''Get the configuration for a given OS ID, version and host type from settings.content_host'''
    os_version = str(Version(str(os_version)).major)
    if os_sub_type and isinstance(os_sub_type, str):
        os_sub_type = f'_{os_sub_type.lower()}'
    else:
        os_sub_type = ''
    if not (
        o_systems := [
            sys for sys in settings.content_host.keys() if re.match(fr'{os_id}\d+.*', sys)
        ]
    ):
        raise ValueError(f'Unsupported ContentHost OS ID: {os_id}')
    if not (o_systems := [sys for sys in o_systems if re.match(fr'{os_id}{os_version}.*', sys)]):
        raise ValueError(f'Unsupported ContentHost OS version: {os_id}{os_version}')
    try:
        os_config = settings.content_host[f'{os_id}{os_version}{os_sub_type}']
    except KeyError:
        raise ValueError(f'Unsupported ContentHost OS: {os_id}{os_version}{os_sub_type}')
    try:
        return os_config[host_type]
    except KeyError:
        raise ValueError(f'Unsupported ContentHost type: {host_type}')
