import argparse
import sys

import os
import pkg_resources
from babel.messages import frontend as babel
from gosa.common import Environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, help='pybabel command to run', nargs='?')
    parser.add_argument('-l', '--locale', dest='locale', help='locale')
    args = parser.parse_args()
    env = Environment.getInstance()

    if env.config.get("core.workflow-path") is None:
        print("Error: no workflow path specified")
        sys.exit(1)

    if args.command is None:
        print("Error: no command specified")
        sys.exit(1)

    command_name = args.command
    if hasattr(babel, command_name):

        for workflow in os.listdir(env.config.get("core.workflow-path")):
            dir = os.path.join(env.config.get("core.workflow-path"), workflow)
            if os.path.isdir(dir) and not workflow.startswith("."):
                print("{:.<80}".format("processing '{}' in workflow '{}'".format(command_name, workflow, "")), end='')
                command = getattr(babel, command_name)()
                command.initialize_options()

                i18n_dir = os.path.join(dir, "i18n")
                if not os.path.exists(i18n_dir):
                    os.makedirs(i18n_dir)

                if command_name == "extract_messages":
                    command.mapping_file = pkg_resources.resource_filename("gosa.utils", "data/workflow-mapping.cfg")
                    command.output_file = os.path.join(i18n_dir, "messages.pot")
                    command.input_paths = [dir]
                    print(dir)

                elif command_name == "compile_catalog":
                    command.directory = i18n_dir
                    command.locale = args.locale

                elif command_name == "init_catalog":
                    command.input_file = os.path.join(i18n_dir, "messages.pot")
                    command.output_dir = i18n_dir
                    command.locale = args.locale

                elif command_name == "compile_catalog":
                    command.directory = i18n_dir
                    command.locale = args.locale

                command.finalize_options()
                command.run()
                print(" done")


if __name__ == "__main__":  # pragma: nocover
    main()
