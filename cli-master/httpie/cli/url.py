import os
import re
from .constants import URL_SCHEME_RE

def process_url(raw_url: str, program_name: str, default_scheme: str) -> str:

    # Paste URL & add space shortcut: `http ://pie.dev` → `http://pie.dev`
    if raw_url.startswith("://"):
        raw_url = raw_url[3:]

    if not URL_SCHEME_RE.match(raw_url):

        scheme = _resolve_scheme(program_name, default_scheme)

        # See if we're using curl style shorthand for localhost (:3000/foo)
        shorthand = re.match(r'^:(?!:)(\d*)(/?.*)$', raw_url)
        if shorthand:
            port = shorthand.group(1)
            rest = shorthand.group(2)
            raw_url= scheme + 'localhost'
            if port:
                raw_url += ':' + port
            raw_url += rest
        else:
            raw_url = scheme + raw_url

    return raw_url

def _resolve_scheme(program_name: str, default_scheme: str) -> str:
    if os.path.basename(program_name) == 'https':
        scheme = 'https://'
    else:
        scheme = default_scheme + '://'

    return scheme
