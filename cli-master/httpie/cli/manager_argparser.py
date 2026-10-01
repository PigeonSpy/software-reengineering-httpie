import argparse

from .base_argparser import BaseHTTPieArgumentParser

class HTTPieManagerArgumentParser(BaseHTTPieArgumentParser):
    def parse_known_args(self, args=None, namespace=None):
        try:
            return super().parse_known_args(args, namespace)
        except SystemExit as exc:
            if not hasattr(self, 'root') and exc.code == 2:  # Argument Parser Error
                raise argparse.ArgumentError(None, None)
            raise       