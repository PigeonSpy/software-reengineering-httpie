from typing import Dict, List, Union

def is_old_format(data: Union[Dict, List]) -> bool:
    """Check if cookies or headers are in legacy dict format."""
    return isinstance(data, dict)

def build_warning(
        is_anonymous_session: bool,
        base_warning: str, 
        named_session_suffix: str, 
        link: str,
        *,
        host_name: str,
        session_id: str
    ) -> str:
    """Assemble a legacy format warning to be handled by Session"""
    warning = base_warning.format(hostname = host_name, session_id = session_id)
    if not is_anonymous_session:
        warning += named_session_suffix
    warning += link
    return warning
