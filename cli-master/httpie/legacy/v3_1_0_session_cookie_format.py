import argparse
from typing import Any, List, Dict, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from httpie.sessions import Session

from httpie.legacy_utils import build_warning
INSECURE_COOKIE_JAR_WARNING = '''\
Outdated layout detected for the current session. Please consider updating it,
in order to not get affected by potential security problems.

For fixing the current session:

    With binding all cookies to the current host (secure):
        $ httpie cli sessions upgrade --bind-cookies {hostname} {session_id}

    Without binding cookies (leaving them as is) (insecure):
        $ httpie cli sessions upgrade {hostname} {session_id}
'''


INSECURE_COOKIE_JAR_WARNING_FOR_NAMED_SESSIONS = '''\

For fixing all named sessions:

    With binding all cookies to the current host (secure):
        $ httpie cli sessions upgrade-all --bind-cookies

    Without binding cookies (leaving them as is) (insecure):
        $ httpie cli sessions upgrade-all
'''

INSECURE_COOKIE_SECURITY_LINK = '\nSee https://httpie.io/docs/security for more information.'

def convert_to_newer_format(session: 'Session', cookies: Dict) -> List[Dict[str, Any]]:
    """Convert legacy dict cookies to modern list format and warn user."""
    # Transforms dictionary to list format, preserving all cookie attributes
    normalized = [
        {
            'name': key,
            **value
        }
        for key, value in cookies.items()
    ]
    
    # Only warns if there are security issues (domain-less cookies)
    has_security_issue = any(
        cookie.get('domain', '') == ''
        for cookie in normalized
    )
    warning = None
    if has_security_issue:
        warning = build_warning(session.is_anonymous, INSECURE_COOKIE_JAR_WARNING, INSECURE_COOKIE_JAR_WARNING_FOR_NAMED_SESSIONS,
                               INSECURE_COOKIE_SECURITY_LINK, host_name=session.bound_host, session_id=session.session_id)
    return normalized, warning

def post_process(
    normalized_cookies: List[Dict[str, Any]],
    *,
    original_type: Type[Any]
) -> Any:
    """Convert the cookies to their original format for
    maximum compatibility."""

    if issubclass(original_type, dict):
        return {
            cookie['name']: {k: v for k, v in cookie.items() if k != 'name'}
            for cookie in normalized_cookies
        }
    else:
        return normalized_cookies