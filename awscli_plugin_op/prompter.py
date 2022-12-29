# -*- coding: utf-8 -*-
from botocore.exceptions import ProfileNotFound
import subprocess
import sys


def _win_console_print(s):
    for c in s:
        msvcrt.putwch(c)
    msvcrt.putwch("\r")
    msvcrt.putwch("\n")


def _unix_console_print(s):
    with os.fdopen(os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY), "w", 1,) as tty:
        print(s, file=tty)


try:
    import msvcrt

    console_print = _win_console_print
except ImportError:
    import os

    console_print = _unix_console_print


class OpTotpPrompter(object):
    def __init__(self, op_identity, original_prompter=None):
        self.op_identity = op_identity
        self._original_prompter = original_prompter

    def __call__(self, prompt):
        try:
            console_print(
                "Taking OTP code from 1Password"
            )
            op_result = subprocess.run(
                ["op", "item", "get", self.op_identity, "--otp" ], capture_output=True
            )
            console_print("Successfully created OATH code.")
            token = op_result.stdout.decode("utf-8").strip()
            return token
        except subprocess.CalledProcessError:
            print("Problem accessing OP.", file=sys.stderr)

        if self._original_prompter:
            return self._original_prompter(prompt)

        return None


def inject_op_totp_prompter(session, **kwargs):
    try:
        providers = session.get_component("credential_provider")
    except ProfileNotFound:
        return

    config = session.get_scoped_config()
    op_identity = config.get("op_identity")
    if op_identity is None:
        # no MFA, so don't interfere with regular flow
        return

    assume_role_provider = providers.get_provider("assume-role")
    original_prompter = assume_role_provider._prompter
    assume_role_provider._prompter = OpTotpPrompter(
        op_identity, original_prompter=original_prompter
    )
