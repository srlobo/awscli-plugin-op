# -*- coding: utf-8 -*-
from awscli.customizations.commands import BasicCommand
import sys
import json
import webbrowser
from urllib import parse, request
from . import boto_plugin
import os


class SessionEnv(BasicCommand):
    NAME = "session-env"
    DESCRIPTION = (
        "prints the current session's credentials in the form of "
        "environment variables.\n"
        "\n"
        "You can use the ``--profile`` argument to select a different set "
        "of credentials.\n"
        "\n"
        ".. note::\n"
        "  If you have set the environment variables in your shell, subsequent "
        "  calls to aws session-env will use those credentials. In order to use "
        "  your default profile, you have to explicitly specify it::\n"
        "\n"
        "    $(aws session-env --profile default\n"
    )
    SYNOPSIS = "aws session-env"
    EXAMPLES = (
        "Print temporary session tokens for a given profile::\n"
        "\n"
        "  $ aws session-env --profile profile_name\n"
        "  export AWS_ACCESS_KEY_ID=AKIAI44QH8DHBEXAMPLE\n"
        "  export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "  export AWS_SESSION_TOKEN=AQoDYXdzEJr...\n"
        "  The acquired credentials will be valid for 60:00 minutes\n"
        "\n"
        "Directly set the environment variables for use in other applications::\n"
        "\n"
        "  $ $(aws session-env --profile profile_name\n"
        "  The acquired credentials will be valid for 60:00 minutes\n"
    )

    ARG_TABLE = []

    def _run_main(self, args, parsed_globals):
        credentials = self._session.get_credentials()

        frozen_credentials = credentials.get_frozen_credentials()
        print("export AWS_ACCESS_KEY_ID={}".format(frozen_credentials.access_key))
        print("export AWS_SECRET_ACCESS_KEY={}".format(frozen_credentials.secret_key))
        if frozen_credentials.token is None:
            print("unset AWS_SESSION_TOKEN")
        else:
            print("export AWS_SESSION_TOKEN={}".format(frozen_credentials.token))

        if hasattr(credentials, "_seconds_remaining"):
            seconds_to_expire = int(credentials._seconds_remaining())
            print(
                "The acquired credentials will be valid for {:.0f}:{:02.0f} minutes".format(
                    seconds_to_expire // 60, seconds_to_expire % 60
                ),
                file=sys.stderr,
            )
        return 0


class OpenConsole(BasicCommand):
    # Reference:
    # https://gist.github.com/ottokruse/1c0f79d51cdaf82a3885f9b532df1ce5
    NAME = "open-console"
    DESCRIPTION = (
        "Opens the web AWS console using the current session's credentials"
        "\n"
        "You can use the ``--profile`` argument to select a different set "
        "of credentials.\n"
    )
    SYNOPSIS = "aws open-console"
    EXAMPLES = (
        ""
    )

    ARG_TABLE = []

    def _run_main(self, args, parsed_globals):
        credentials = self._session.get_credentials()

        frozen_credentials = credentials.get_frozen_credentials()

        from pprint import pprint
        url_credentials = dict(sessionId=frozen_credentials.access_key,
                               sessionKey=frozen_credentials.secret_key,
                               sessionToken=frozen_credentials.token)

        request_parameters = "?Action=getSigninToken"
        request_parameters += "&DurationSeconds=43200"
        request_parameters += "&RoleSessionName=perola"
        request_parameters += "&Session=" + parse.quote_plus(json.dumps(url_credentials))
        request_url = "https://signin.aws.amazon.com/federation" + request_parameters
        with request.urlopen(request_url) as response:
            if not response.status == 200:
                raise Exception("Failed to get federation token")
            signin_token = json.loads(response.read())

        request_parameters = "?Action=login"
        request_parameters += "&Destination=" + parse.quote_plus("https://console.aws.amazon.com/")
        request_parameters += "&SigninToken=" + signin_token["SigninToken"]
        request_parameters += "&Issuer=" + parse.quote_plus("https://example.com")
        request_url = "https://signin.aws.amazon.com/federation" + request_parameters

        try:
            webbrowser.open(request_url)
        except:
            print("Some error has happened opening the console url, "
                  "try this instead")
            print(request_url)
        # os.system("open %s" % request_url)

        return 0
