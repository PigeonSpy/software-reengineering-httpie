from argparse import RawDescriptionHelpFormatter
from textwrap import dedent
import argparse
import sys

class HTTPieHelpFormatter(RawDescriptionHelpFormatter):
    """
    A nicer help formatter.

    Help for arguments can be indented and contain new lines.
    It will be de-dented and arguments in the help
    will be separated by a blank line for better readability.

    """

    def __init__(self, max_help_position=6, *args, **kwargs):
        # A smaller indent for args help.
        kwargs['max_help_position'] = max_help_position
        super().__init__(*args, **kwargs)

    def _split_lines(self, text, width):
        text = dedent(text).strip() + '\n\n'
        return text.splitlines()

    def add_usage(self, usage, actions, groups, prefix=None):
        # Only display the positional arguments
        displayed_actions = [
            action
            for action in actions
            if not action.option_strings
        ]

        _, exception, _ = sys.exc_info()
        if (
            isinstance(exception, argparse.ArgumentError)
            and len(exception.args) >= 1
            and isinstance(exception.args[0], argparse.Action)
        ):
            # add_usage path is also taken when you pass an invalid option,
            # e.g --style=invalid. If something like that happens, we want
            # to include to action that caused to the invalid usage into
            # the list of actions we are displaying.
            displayed_actions.insert(0, exception.args[0])

        super().add_usage(
            usage,
            displayed_actions,
            groups,
            prefix="usage:\n    "
        )