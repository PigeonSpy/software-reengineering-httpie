import argparse
import sys

from ..context import Environment
from ..cli.models import HTTPieRawArgs, HTTPieParsedArgs


class BaseHTTPieArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = None
        self.args = None
        self.has_stdin_data = False
        self.has_input_data = False

    # noinspection PyMethodOverriding
    def parse_args(
        self,
        env: Environment,
        args=None,
        namespace=None
    ) -> argparse.Namespace:
        self.env = env
        self.args, no_options = self.parse_known_args(args, namespace)


        raw_inputs = HTTPieRawArgs(args_list=args, stdin=self.env.stdin, stdin_isatty=self.env.stdin_isatty)
        im_res = self.process_httpie_args(raw_inputs, self.args)

        # mirror the results for backwards compatibility
        self.has_stdin_data = im_res.has_stdin_data
        self.has_input_data = im_res.has_input_data

        return self.args

    
    def process_httpie_args(self, raw: HTTPieRawArgs, parsed_ns: argparse.Namespace) -> HTTPieParsedArgs:
        debug = getattr(parsed_ns, 'debug', False)
        traceback = debug or getattr(parsed_ns, 'traceback', False)
        ignore_stdin = getattr(parsed_ns, 'ignore_stdin', False)
        raw_data = getattr(parsed_ns, 'raw', None)

        has_stdin_data = (
            raw.stdin
            and not ignore_stdin
            and not raw.stdin_isatty
        )
        
        has_input_data = has_stdin_data or raw_data is not None

        return HTTPieParsedArgs(
            debug=debug,
            traceback=traceback,
            ignore_stdin=ignore_stdin,
            raw=raw_data,
            has_stdin_data=has_stdin_data,
            has_input_data=has_input_data,
            legacy_namespace=parsed_ns,
        )


    # noinspection PyShadowingBuiltins
    def _print_message(self, message, file=None):
        # Sneak in our stderr/stdout.
        if hasattr(self, 'root'):
            env = self.root.env
        else:
            env = self.env

        if env is not None:
            file = {
                sys.stdout: env.stdout,
                sys.stderr: env.stderr,
                None: env.stderr
            }.get(file, file)

        if not hasattr(file, 'buffer') and isinstance(message, str):
            message = message.encode(env.stdout_encoding)
        super()._print_message(message, file)