from typing import Any, List, Dict, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from httpie.sessions import Session

from httpie.legacy_utils import build_warning
OLD_HEADER_STORE_WARNING = '''\
Outdated layout detected for the current session. Please consider updating it,
in order to use the latest features regarding the header layout.

For fixing the current session:

    $ httpie cli sessions upgrade {hostname} {session_id}
'''

OLD_HEADER_STORE_WARNING_FOR_NAMED_SESSIONS = '''\

For fixing all named sessions:

    $ httpie cli sessions upgrade-all
'''

OLD_HEADER_STORE_LINK = '\nSee https://httpie.io/docs/security for more information.'

def convert_to_newer_format(session: 'Session', headers: Dict) -> List[Dict[str, Any]]:
    """Convert legacy dict headers to modern list format and warn user."""

    warning = build_warning(session.is_anonymous, OLD_HEADER_STORE_WARNING, OLD_HEADER_STORE_WARNING_FOR_NAMED_SESSIONS,
                            OLD_HEADER_STORE_LINK, host_name=session.bound_host, session_id=session.session_id)
    return list(headers.items()), warning

def post_process(
    normalized_headers: List[Dict[str, Any]],
    *,
    original_type: Type[Any]
) -> Any:
    """Deserialize given header store into the original form it was
    used in."""

    if issubclass(original_type, dict):
        # For the legacy behavior, preserve the last value.
        return {
            item['name']: item['value']
            for item in normalized_headers
        }
    else:
        return normalized_headers