
"""Sets the system mode."""

from argparse import ArgumentParser
from subprocess import DEVNULL, CalledProcessError, check_call, run
from sys import stderr

from tabletmode.config import load_configuration


DESCRIPTION = 'Sets or toggles the system mode.'
LAPTOP_MODE_SERVICE = 'laptop-mode.service'
TABLET_MODE_SERVICE = 'tablet-mode.service'


def get_arguments():
    """Returns the CLI arguments."""

    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        '-n', '--notify', action='store_true',
        help='display an on-screen notification')
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.add_parser('toggle', help='toggles the system mode')
    subparsers.add_parser('laptop', help='switch to laptop mode')
    subparsers.add_parser('tablet', help='switch to tablet mode')
    subparsers.add_parser('default', help='do not disable any input devices')
    return parser.parse_args()


def systemctl(action, unit, *, root=False):
    """Runs systemctl."""

    command = ['/usr/bin/sudo'] if root else []
    command.append('systemctl')
    command.append(action)
    command.append(unit)

    try:
        check_call(command, stdout=DEVNULL)     # Return 0 on success.
    except CalledProcessError:
        return False

    return True


def notify_send(summary, body=None):
    """Sends the respective message."""

    command = ['/usr/bin/notify-send', summary]

    if body is not None:
        command.append(body)

    return run(command, stdout=DEVNULL, check=False)


def notify_laptop_mode():
    """Notifies about laptop mode."""

    return notify_send('Laptop mode.', 'The system is now in laptop mode.')


def notify_tablet_mode():
    """Notifies about tablet mode."""

    return notify_send('Tablet mode.', 'The system is now in tablet mode.')


def toggle_mode(notify=False):
    """Toggles between laptop and tablet mode."""

    if systemctl('status', TABLET_MODE_SERVICE):
        systemctl('stop', TABLET_MODE_SERVICE, root=True)
        systemctl('start', LAPTOP_MODE_SERVICE, root=True)

        if notify:
            notify_tablet_mode()
    else:
        systemctl('stop', LAPTOP_MODE_SERVICE, root=True)
        systemctl('start', TABLET_MODE_SERVICE, root=True)

        if notify:
            notify_laptop_mode()


def default_mode(notify=False):
    """Restores all blocked input devices."""

    systemctl('stop', LAPTOP_MODE_SERVICE, root=True)
    systemctl('stop', TABLET_MODE_SERVICE, root=True)

    if notify:
        notify_send('Default mode.', 'The system is now in default mode.')


def laptop_mode(notify=False):
    """Starts the laptop mode."""

    systemctl('stop', TABLET_MODE_SERVICE, root=True)
    systemctl('start', LAPTOP_MODE_SERVICE, root=True)

    if notify:
        notify_laptop_mode()


def tablet_mode(notify=False):
    """Starts the tablet mode."""

    systemctl('stop', LAPTOP_MODE_SERVICE, root=True)
    systemctl('start', TABLET_MODE_SERVICE, root=True)

    if notify:
        notify_tablet_mode()


def main():
    """Runs the main program."""

    arguments = get_arguments()
    configuration = load_configuration()
    notify = configuration.get('notify', False) or arguments.notify

    if arguments.mode == 'toggle':
        toggle_mode(notify=notify)
    elif arguments.mode == 'default':
        default_mode(notify=notify)
    elif arguments.mode == 'laptop':
        laptop_mode(notify=notify)
    elif arguments.mode == 'tablet':
        tablet_mode(notify=notify)
    else:
        print('Must specify a mode.', file=stderr, flush=True)
