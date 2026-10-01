from dataclasses import dataclass
from typing import IO, List, Optional, Any

# designed to be immutable (frozen=True)

@dataclass(frozen=True)
class HTTPieRawArgs:
    args_list: Optional[List[str]]
    stdin: Any
    stdin_isatty: bool

@dataclass(frozen=True)
class HTTPieParsedArgs:
    debug: bool
    traceback: bool
    ignore_stdin: bool
    raw: Optional[str]
    has_stdin_data: bool
    has_input_data: bool
    legacy_namespace: Any

    # not used yet and not complete, 
    # but this should contain variables migrated from the old namespace.
    # e.g self.args.download, (--dowload) needs a immutable variable download: bool, and so on.
    # download: bool
    # download_resume: bool
    # output_file: Optional[IO[bytes]] = None
    # ...