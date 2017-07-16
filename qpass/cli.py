# qpass: Frontend for pass (the standard unix password manager).
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: July 16, 2017
# URL: https://github.com/xolox/python-qpass

"""
Usage: qpass [OPTIONS] KEYWORD..

Search your password store for the given keywords or patterns and copy the
password of the matching entry to the clipboard. When more than one entry
matches you will be prompted to select the password to copy.

If you provide more than one KEYWORD all of the given keywords must match,
in other words you're performing an AND search instead of an OR search.

Instead of matching on keywords you can also enter just a few of the characters
in the name of a password, as long as those characters are in the right order.
Some examples to make this more concrete:

- The pattern 'pe/zbx' will match the name 'Personal/Zabbix'.
- The pattern 'ba/cc' will match the name 'Bank accounts/Creditcard'.

Supported options:

  -e, --edit

    Edit the matching entry instead of copying it to the clipboard.

  -l, --list

    List the matching entries on standard output.

  -n, --no-clipboard

    Don't copy the password of the matching entry to the clipboard, instead
    show the password on the terminal (by default the password is copied to
    the clipboard but not shown on the terminal).

  -p, --password-store=DIRECTORY

    Search the password store in DIRECTORY. If this option isn't given
    the password store is located using the $PASSWORD_STORE_DIR
    environment variable. If that environment variable isn't
    set the directory ~/.password-store is used.

  -v, --verbose

    Increase logging verbosity (can be repeated).

  -q, --quiet

    Decrease logging verbosity (can be repeated).

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import getopt
import logging
import sys

# External dependencies.
import coloredlogs
from humanfriendly.terminal import output, usage, warning

# Modules included in our package.
from qpass import PasswordStore
from qpass.exceptions import PasswordStoreError

# Public identifiers that require documentation.
__all__ = (
    'edit_matching_entry',
    'list_matching_entries',
    'logger',
    'main',
    'show_matching_entry',
)

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``qpass`` program."""
    # Initialize logging to the terminal.
    coloredlogs.install()
    # Parse the command line arguments.
    program_opts = {}
    action = show_matching_entry
    try:
        options, arguments = getopt.gnu_getopt(sys.argv[1:], 'elnp:vqh', [
            'edit', 'list', 'no-clipboard', 'password-store=',
            'verbose', 'quiet', 'help',
        ])
        for option, value in options:
            if option in ('-e', '--edit'):
                action = edit_matching_entry
            elif option in ('-l', '--list'):
                action = list_matching_entries
            elif option in ('-n', '--no-clipboard'):
                program_opts['clipboard_enabled'] = False
            elif option in ('-p', '--password-store'):
                program_opts['directory'] = value
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(__doc__)
                return
            else:
                raise Exception("Unhandled option! (programming error)")
        if not (arguments or action == list_matching_entries):
            usage(__doc__)
            return
    except Exception as e:
        warning("Error: %s", e)
        sys.exit(1)
    # Execute the requested action.
    try:
        program = PasswordStore(**program_opts)
        action(program, arguments)
    except PasswordStoreError as e:
        # Known issues don't get a traceback.
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        # If the user interrupted an interactive prompt they most likely did so
        # intentionally, so there's no point in generating more output here.
        sys.exit(1)


def edit_matching_entry(program, arguments):
    """Edit the matching entry."""
    name = program.select_entry(*arguments)
    program.context.execute('pass', 'edit', name)


def list_matching_entries(program, arguments):
    """List the entries matching the given keywords/patterns."""
    output('\n'.join(program.smart_search(*arguments)))


def show_matching_entry(program, arguments):
    """Show the matching entry on the terminal (and copy the password to the clipboard)."""
    name = program.select_entry(*arguments)
    output(program.format_entry(name))
    program.copy_password(name)