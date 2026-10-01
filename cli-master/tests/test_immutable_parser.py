from httpie.cli.argparser import BaseHTTPieArgumentParser
from httpie.cli.models import HTTPieRawArgs
import argparse

def test_pure_argument_processing():
    parser = BaseHTTPieArgumentParser()
    parser.add_argument('--debug', action='store_true')

    raw = HTTPieRawArgs(args_list=['--debug'], stdin=True, stdin_isatty=False)
    ns = argparse.Namespace(debug=True, ignore_stdin=False, raw=None)
    
    result = parser.process_httpie_args(raw, ns)
    assert result.debug == True
    assert result.traceback == True

def test_ignore_stdin():
    parser = BaseHTTPieArgumentParser()
    parser.add_argument('--ignore-stdin', action='store_true')

    raw = HTTPieRawArgs(args_list=['--ignore-stdin'], stdin=True, stdin_isatty=False)
    ns = argparse.Namespace(debug=False, ignore_stdin=True, raw=None)
    
    result = parser.process_httpie_args(raw, ns)
    
    assert result.ignore_stdin == True
    assert result.has_stdin_data == False
    assert result.has_input_data == False
