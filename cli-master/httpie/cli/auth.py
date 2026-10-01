from ..plugins.registry import plugin_manager
from urllib.parse import urlsplit
from .argtypes import AuthCredentials, parse_auth
from .constants import SEPARATOR_CREDENTIALS
from requests.utils import get_netrc_auth
from ..utils import ExplicitNullAuth

def process_auth(url, auth_type, auth, ignore_netrc, ignore_stdin, error):
    auth_plugin = None
    split_url = urlsplit(url)

    auth = _resolve_credentials(split_url, auth_type, auth)
    plugin, auth_type, auth = _resolve_plugin(auth, auth_type, ignore_netrc, split_url, error)

    if plugin:
        auth_plugin, auth = _init_auth_plugin(plugin, auth, split_url, ignore_stdin, error)

    if not auth and ignore_netrc:
        # Set a no-op auth to force requests to ignore .netrc
        # <https://github.com/psf/requests/issues/2773#issuecomment-174312831>
        auth = ExplicitNullAuth()

    return auth_plugin, auth, auth_type


def _resolve_credentials(url_split, auth_type, auth):
    if auth is None and not auth_type and url_split.username:
        # Handle http://username:password@hostname/
        username = url_split.username
        password = url_split.password or ''
        return AuthCredentials(
            key=username,
            value=password,
            sep=SEPARATOR_CREDENTIALS,
            orig=SEPARATOR_CREDENTIALS.join([username, password])
        )
    return auth


def _resolve_plugin(auth, auth_type, ignore_netrc, url_split, error):
    auth_type_set = auth_type is not None
    if not (auth or auth_type_set):
        return None, None, auth
    
    default_plugin = plugin_manager.get_auth_plugins()[0]
    plugin_type = auth_type or default_plugin.auth_type
    plugin = plugin_manager.get_auth_plugin(plugin_type)()

    # .netrc lookup if enabled and no credentials were given
    if not ignore_netrc and not auth and plugin.netrc_parse:
        netrc_auth = get_netrc_auth(url_split.geturl())
        if netrc_auth:
            auth = AuthCredentials(
                key=netrc_auth[0],
                value=netrc_auth[1],
                sep=SEPARATOR_CREDENTIALS,
                orig=SEPARATOR_CREDENTIALS.join(netrc_auth)
            )
    
    
    if plugin.auth_require and not auth:
        error(f'--auth required')

    return plugin, plugin_type, auth


def _init_auth_plugin(plugin, raw_auth, url_split, ignore_stdin, error):
    plugin.raw_auth = raw_auth
    already_parsed = isinstance(raw_auth, AuthCredentials)

    # no auth provided or plugin get default
    if raw_auth is None or not plugin.auth_parse:
        return plugin, plugin.get_auth()

    auth = raw_auth if already_parsed else parse_auth(raw_auth)

    # password prompting
    if not auth.has_password() and plugin.prompt_password:
        if ignore_stdin:
            error('Unable to prompt for passwords because --ignore-stdin is set.')
        auth.prompt_password(url_split.netloc)

    if auth.key and auth.value:
        plugin.raw_auth = f"{auth.key}:{auth.value}"

    final_auth = plugin.get_auth(
        username=auth.key,
        password=auth.value,
    )
    
    return plugin, final_auth