import argparse

from httpie.sessions import SESSIONS_DIR_NAME, get_httpie_session
from httpie.status import ExitStatus
from httpie.context import Environment
from httpie.legacy_utils import is_old_format
from httpie.legacy import (
    v3_1_0_session_cookie_format as legacy_cookies,
    v3_2_0_session_header_format as legacy_headers
)
from httpie.manager.cli import missing_subcommand, parser
from httpie.utils import is_version_greater


COOKIE_CHOICE = 'cookies'
HEADER_CHOICE = 'headers'

FIXERS_TO_VERSIONS = {
    '3.1.0': [COOKIE_CHOICE, legacy_cookies],
    '3.2.0': [HEADER_CHOICE, legacy_headers],
}

def cli_sessions(env: Environment, args: argparse.Namespace) -> ExitStatus:
    action = args.cli_sessions_action
    if action is None:
        parser.error(missing_subcommand('cli', 'sessions'))

    if action == 'upgrade':
        return cli_upgrade_session(env, args)
    elif action == 'upgrade-all':
        return cli_upgrade_all_sessions(env, args)
    else:
        raise ValueError(f'Unexpected action: {action}')


def upgrade_session(env: Environment, args: argparse.Namespace, hostname: str, session_name: str):
    session = get_httpie_session(
        env=env,
        config_dir=env.config.directory,
        session_name=session_name,
        host=hostname,
        url=hostname,
        suppress_legacy_warnings=True
    )

    session_name = session.path.stem
    if session.is_new():
        env.log_error(f'{session_name!r} @ {hostname!r} does not exist.')
        return ExitStatus.ERROR

    fixers = [
        fixer
        for version, fixer in FIXERS_TO_VERSIONS.items()
        if is_version_greater(version, session.version)
    ]

    if len(fixers) == 0:
        env.stdout.write(f'{session_name!r} @ {hostname!r} is already up to date.\n')
        return ExitStatus.SUCCESS

    for fixer in fixers:
        key = fixer[0]
        converter = fixer[1].convert_to_newer_format

        if (is_old_format(session[key])):
            normalized, _ = converter(session, session[key])
            session[key] = normalized

        if (key == COOKIE_CHOICE):
            for cookie in session.cookies:
                if cookie.domain == '':
                    if args.bind_cookies:
                        cookie.domain = hostname
                    else:
                        cookie._rest['is_explicit_none'] = True
    
    session.save(bump_version=True)
    env.stdout.write(f'Upgraded {session_name!r} @ {hostname!r} to v{session.version}\n')
    return ExitStatus.SUCCESS


def cli_upgrade_session(env: Environment, args: argparse.Namespace) -> ExitStatus:
    return upgrade_session(
        env,
        args=args,
        hostname=args.hostname,
        session_name=args.session
    )


def cli_upgrade_all_sessions(env: Environment, args: argparse.Namespace) -> ExitStatus:
    session_dir_path = env.config_dir / SESSIONS_DIR_NAME

    status = ExitStatus.SUCCESS
    for host_path in session_dir_path.iterdir():
        hostname = host_path.name
        for session_path in host_path.glob("*.json"):
            session_name = session_path.stem
            status |= upgrade_session(
                env,
                args=args,
                hostname=hostname,
                session_name=session_name
            )
    return status