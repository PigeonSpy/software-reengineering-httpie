import argparse
import re

from .argtypes import (SSLCredentials, KeyValueArgType,
    PARSED_DEFAULT_FORMAT_OPTIONS,
    parse_format_options,
)
from .constants import (
    HTTP_GET, HTTP_POST, BASE_OUTPUT_OPTIONS, OUTPUT_OPTIONS, OUTPUT_OPTIONS_DEFAULT,
    OUTPUT_OPTIONS_DEFAULT_OFFLINE, OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED,
    OUT_RESP_BODY, PRETTY_MAP, PRETTY_STDOUT_TTY_ONLY, RequestType,
    SEPARATOR_GROUP_ALL_ITEMS, SEPARATOR_GROUP_DATA_ITEMS, KNOWN_METHODS,
)
from .exceptions import ParseError
from .requestitems import RequestItems
from ..utils import get_content_type

from .url import process_url
from .auth import process_auth
from .base_argparser import BaseHTTPieArgumentParser
from .argument_error import HTTPieArgumentError

class HTTPieArgumentProcessor(BaseHTTPieArgumentParser):
    """Handles normalisation and enrichment of parsed arguments.
    
    Operates on a fully parsed args namespace, inferring missing values,
    validating combinations, and preparing the request for execution.
    """

    def _guess_method(self):
        """Set `args.method` if not specified to either POST or GET
        based on whether the request has data or not.

        """
        if self.args.method is None:
            # Invoked as `http URL'.
            assert not self.args.request_items
            if self.has_input_data:
                self.args.method = HTTP_POST
            else:
                self.args.method = HTTP_GET

        elif self.args.method.upper() not in KNOWN_METHODS:
            # Invoked as `http URL item+'. The URL is now in `args.method`
            # and the first ITEM is now incorrectly in `args.url`.
            if re.match('^[a-zA-Z]+$', self.args.method):
                # Looks like an intended method name but isn't recognised. Forward it as-is
                pass
            else:
                try:
                    # Parse the URL as an ITEM and store it as the first ITEM arg.
                    self.args.request_items.insert(0, KeyValueArgType(
                        *SEPARATOR_GROUP_ALL_ITEMS).__call__(self.args.url))

                except argparse.ArgumentTypeError as e:
                    if self.args.traceback:
                        raise
                    raise HTTPieArgumentError(e.args[0])

                else:
                    # Set the URL correctly
                    self.args.url = self.args.method
                    # Infer the method
                    has_data = (
                        self.has_input_data
                        or any(
                            item.sep in SEPARATOR_GROUP_DATA_ITEMS
                            for item in self.args.request_items)
                    )
                    self.args.method = HTTP_POST if has_data else HTTP_GET

    def _body_from_input(self, data):
        """Read the data from the CLI.

        """
        self._ensure_one_data_source(self.has_stdin_data, self.args.data,
                                     self.args.files)
        self.args.data = data.encode()

    def _ensure_one_data_source(self, *other_sources):
        """There can only be one source of input request data.

        """
        if any(other_sources):
            raise HTTPieArgumentError('Request body (from stdin, --raw or a file) and request '
                       'data (key=value) cannot be mixed. Pass '
                       '--ignore-stdin to let key/value take priority. '
                       'See https://httpie.io/docs#scripting for details.')
      
    def _body_from_file(self, fd):
        """Read the data from a file-like object.

        Bytes are always read.

        """
        self._ensure_one_data_source(self.args.data, self.args.files)
        self.args.data = getattr(fd, 'buffer', fd)

    def _process_request_type(self):
        request_type = self.args.request_type
        self.args.json = request_type is RequestType.JSON
        self.args.multipart = request_type is RequestType.MULTIPART
        self.args.form = request_type in {
            RequestType.FORM,
            RequestType.MULTIPART,
        }

    def _process_download_options(self):
        if self.args.offline:
            self.args.download = False
            self.args.download_resume = False
            return
        if not self.args.download:
            if self.args.download_resume:
                raise HTTPieArgumentError('--continue only works with --download')
        if self.args.download_resume and not (
                self.args.download and self.args.output_file):
            raise HTTPieArgumentError('--continue requires --output to be specified')

    def _process_output_options(self):
        """Apply defaults to output options, or validate the provided ones.

        The default output options are stdout-type-sensitive.

        """

        def check_options(value, option):
            unknown = set(value) - OUTPUT_OPTIONS
            if unknown:
                raise HTTPieArgumentError(f'Unknown output options: {option}={",".join(unknown)}')

        if self.args.verbose:
            self.args.all = True

        if self.args.output_options is None:
            if self.args.verbose >= 2:
                self.args.output_options = ''.join(OUTPUT_OPTIONS)
            elif self.args.verbose == 1:
                self.args.output_options = ''.join(BASE_OUTPUT_OPTIONS)
            elif self.args.offline:
                self.args.output_options = OUTPUT_OPTIONS_DEFAULT_OFFLINE
            elif not self.env.stdout_isatty:
                self.args.output_options = OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED
            else:
                self.args.output_options = OUTPUT_OPTIONS_DEFAULT

        if self.args.output_options_history is None:
            self.args.output_options_history = self.args.output_options

        check_options(self.args.output_options, '--print')
        check_options(self.args.output_options_history, '--history-print')

        if self.args.download and OUT_RESP_BODY in self.args.output_options:
            # Response body is always downloaded with --download and it goes
            # through a different routine, so we remove it.
            self.args.output_options = str(
                set(self.args.output_options) - set(OUT_RESP_BODY))

    def _process_pretty_options(self):
        if self.args.prettify == PRETTY_STDOUT_TTY_ONLY:
            self.args.prettify = PRETTY_MAP[
                'all' if self.env.stdout_isatty else 'none']
        elif (self.args.prettify and self.env.is_windows
              and self.args.output_file):
            raise HTTPieArgumentError('Only terminal output can be colorized on Windows.')
        else:
            # noinspection PyTypeChecker
            self.args.prettify = PRETTY_MAP[self.args.prettify]

    def _process_format_options(self):
        format_options = self.args.format_options or []
        parsed_options = PARSED_DEFAULT_FORMAT_OPTIONS
        for options_group in format_options:
            parsed_options = parse_format_options(options_group, defaults=parsed_options)
        self.args.format_options = parsed_options

    def _process_url(self):
        self.args.url = process_url(
            raw_url=self.args.url,
            program_name=self.env.program_name,
            default_scheme=self.args.default_scheme
        )

    def _process_auth(self):
        self.args.auth_plugin, self.args.auth, self.args.auth_type = process_auth(
            url=self.args.url,
            auth_type=self.args.auth_type,
            auth=self.args.auth,
            ignore_netrc=self.args.ignore_netrc,
            ignore_stdin=self.args.ignore_stdin,
            error = self.error
        )

    def _process_ssl_cert(self):
        from httpie.ssl_ import _is_key_file_encrypted

        if self.args.cert_key_pass is None:
            self.args.cert_key_pass = SSLCredentials(None)

        if (
            self.args.cert_key is not None
            and self.args.cert_key_pass.value is None
            and _is_key_file_encrypted(self.args.cert_key)
        ):
            self.args.cert_key_pass.prompt_password(self.args.cert_key)

    def _parse_items(self):
        """
        Parse `args.request_items` into `args.headers`, `args.data`,
        `args.params`, and `args.files`.

        """

        self._process_request_items()
        self._process_file()


    def _process_request_items(self):

        """
        Extracts the request items and stores them in the appropriate args attributes
        """

        try:
            request_items = RequestItems.from_args(
                request_item_args=self.args.request_items,
                request_type=self.args.request_type,
            )
        except ParseError as e:
            if self.args.traceback:
                raise
            self.error(e.args[0])
        else:

            fields = ["headers", "data", "files", "params", "multipart_data"]
            for field in fields:
                setattr(self.args, field, getattr(request_items, field))

    def _process_file(self):

        if self.args.files and not self.args.form:
            request_file = self._get_request_file()

            fn, fd, _ = request_file
            self.args.files = {}

            self._body_from_file(fd)

            if 'Content-Type' not in self.args.headers:
                content_type = get_content_type(fn)
                if content_type:
                    self.args.headers['Content-Type'] = content_type

    def _get_request_file(self):
            
        # `http url @/path/to/file`
        request_file = None
        for key, file in self.args.files.items():
            if key != '':
                self.error(
                    'Invalid file fields (perhaps you meant --form?):'
                    f' {",".join(self.args.files.keys())}')
            if request_file is not None:
                self.error("Can't read request from multiple files")
            request_file = file
        return request_file
