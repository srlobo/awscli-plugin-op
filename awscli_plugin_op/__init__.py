# -*- coding: utf-8 -*-
from .prompter import inject_op_totp_prompter
from .commands import SessionEnv, OpenConsole


def awscli_initialize(cli):
    cli.register(
        "session-initialized",
        inject_op_totp_prompter,
        unique_id="inject_op_totp_provider",
    )
    cli.register("building-command-table.main", awscli_register_commands)


def awscli_register_commands(command_table, session, **kwargs):
    command_table["session-env"] = SessionEnv(session)
    command_table["open-console"] = OpenConsole(session)
