import argparse
import errno
#import os
import re
import sys
from textwrap import dedent
#from urllib.parse import urlsplit

from requests.utils import get_netrc_auth

from .argtypes import (
    AuthCredentials, SSLCredentials, KeyValueArgType,
    PARSED_DEFAULT_FORMAT_OPTIONS,
    parse_auth,
    parse_format_options,
)
from .constants import (
    HTTP_GET, HTTP_POST, BASE_OUTPUT_OPTIONS, OUTPUT_OPTIONS, OUTPUT_OPTIONS_DEFAULT,
    OUTPUT_OPTIONS_DEFAULT_OFFLINE, OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED,
    OUT_RESP_BODY, PRETTY_MAP, PRETTY_STDOUT_TTY_ONLY, RequestType,
    SEPARATOR_CREDENTIALS,
    SEPARATOR_GROUP_ALL_ITEMS, SEPARATOR_GROUP_DATA_ITEMS, KNOWN_METHODS,
)
from .exceptions import ParseError
from .requestitems import RequestItems
from ..context import Environment
#from ..plugins.registry import plugin_manager
from ..utils import ExplicitNullAuth, get_content_type

from .url import process_url
from .auth import process_auth
from .help_formatter import HTTPieHelpFormatter
from .base_argparser import BaseHTTPieArgumentParser
from .argument_error import HTTPieArgumentError
from .argument_processor import HTTPieArgumentProcessor
from .environment_processor import HTTPieEnvironmentProcessor


class HTTPieArgumentParser(HTTPieEnvironmentProcessor):
    """Adds additional logic to `argparse.ArgumentParser`.

    Handles all input (CLI args, file args, stdin), applies defaults,
    and performs extra validation.

    """

    def __init__(self, *args, formatter_class=HTTPieHelpFormatter, **kwargs):
        kwargs.setdefault('add_help', False)
        super().__init__(*args, formatter_class=formatter_class, **kwargs)

    # noinspection PyMethodOverriding
    def parse_args(
        self,
        env: Environment,
        args=None,
        namespace=None
    ) -> argparse.Namespace:
        self.env = env
        self.env.args = namespace = namespace or argparse.Namespace()
        self.args, no_options = super().parse_known_args(args, namespace)
        if self.args.debug:
            self.args.traceback = True
        self.has_stdin_data = (
            self.env.stdin
            and not self.args.ignore_stdin
            and not self.env.stdin_isatty
        )
        self.has_input_data = self.has_stdin_data or self.args.raw is not None

        try:
            self._apply_no_options(no_options)
            self._process_request_type()
            self._process_download_options()
            self._setup_standard_streams()
            self._process_output_options()
            self._process_pretty_options()
            self._process_format_options()
            self._guess_method()
            self._parse_items()
            self._process_url()
            self._process_auth()
            self._process_ssl_cert()
            
            if self.args.raw is not None:
                self._body_from_input(self.args.raw)
            elif self.has_stdin_data:
                self._body_from_file(self.env.stdin)

            if self.args.compress:
                # TODO: allow --compress with --chunked / --multipart
                if self.args.chunked:
                    self.error('cannot combine --compress and --chunked')
                if self.args.multipart:
                    self.error('cannot combine --compress and --multipart')
        except HTTPieArgumentError as e:
            self.error(str(e))

        return self.args

    def _apply_no_options(self, no_options):
        """For every `--no-OPTION` in `no_options`, set `args.OPTION` to
        its default value. This allows for un-setting of options, e.g.,
        specified in config.

        """
        invalid = []

        for option in no_options:
            if not option.startswith('--no-'):
                invalid.append(option)
                continue

            # --no-option => --option
            inverted = '--' + option[5:]
            for action in self._actions:
                if inverted in action.option_strings:
                    setattr(self.args, action.dest, action.default)
                    break
            else:
                invalid.append(option)

        if invalid:
            self.error(f'unrecognized arguments: {" ".join(invalid)}')

    def print_manual(self):
        from httpie.output.ui import man_pages

        if man_pages.is_available(self.env.program_name):
            man_pages.display_for(self.env, self.env.program_name)
            return None

        text = self.format_help()
        with self.env.rich_console.pager():
            self.env.rich_console.print(
                text,
                highlight=False
            )

    def print_usage(self, file):
        from rich.text import Text
        from httpie.output.ui import rich_help

        whitelist = set()
        _, exception, _ = sys.exc_info()
        if (
            isinstance(exception, argparse.ArgumentError)
            and len(exception.args) >= 1
            and isinstance(exception.args[0], argparse.Action)
            and exception.args[0].option_strings
        ):
            # add_usage path is also taken when you pass an invalid option,
            # e.g --style=invalid. If something like that happens, we want
            # to include to action that caused to the invalid usage into
            # the list of actions we are displaying.
            whitelist.add(exception.args[0].option_strings[0])

        usage_text = Text('usage', style='bold')
        usage_text.append(':\n    ')
        usage_text.append(rich_help.to_usage(self.spec, whitelist=whitelist))
        self.env.rich_error_console.print(usage_text)

    def error(self, message):
        """Prints a usage message incorporating the message to stderr and
        exits."""
        self.print_usage(sys.stderr)
        self.env.rich_error_console.print(
            dedent(
                f'''
                [bold]error[/bold]:
                    {message}

                [bold]for more information[/bold]:
                    run '{self.prog} --help' or visit https://httpie.io/docs/cli
                '''.rstrip()
            )
        )
        self.exit(2)
