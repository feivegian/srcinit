import os
import shutil
from argparse import ArgumentParser
from time import time
from zipfile import ZipFile


import platformdirs
import requests
from tqdm import tqdm


ARGPARSE_PROG = "srcinit"
ARGPARSE_DESCRIPTION = "Simplified source code generator"
ARGPARSE_EPILOG = "For more information, visit https://github.com/feivegian/srcinit"


PLATFORMDIRS_APP_NAME = "srcinit"
PLATFORMDIRS_APP_AUTHOR = "feivegian"
PLATFORMDIRS_APP_VERSION = "1.0"


##
# If you wish to use your own srcinit templates,
# point SYNC_URL to your repository's latest release download URL
##
SYNC_REMOTE_URL = "https://github.com/feivegian/srcinit-templates/releases/latest/download/templates.zip"
SYNC_LOCAL_DIR = platformdirs.user_data_dir(PLATFORMDIRS_APP_NAME
                                           , PLATFORMDIRS_APP_AUTHOR
                                           , PLATFORMDIRS_APP_VERSION)
SYNC_LOCAL_FILE = os.path.join(SYNC_LOCAL_DIR, "templates.zip")
SYNC_LOCAL_FILE_OLD = f"{SYNC_LOCAL_FILE}.old"


verbose: bool = False
imported: bool = __name__ != "__main__"


def print_normal(value):
    if imported:
        return


    print(value)


def print_verbose(value):
    if not verbose:
        return


    print_normal(value)


def sync(rollback: bool = False) -> bool:
    # If rollback is set to True, replace the current sync with the previous available sync
    # But if there isn't any available previous sync, we can just do nothing.
    if rollback:
        if not os.path.isfile(SYNC_LOCAL_FILE_OLD):
            print_normal("There is no previous sync to rollback.")
            return True


        # Ask one more time before the user can change their minds
        override = input("This is a serious question, do you really want to rollback since the previous sync? (Y/n) ")

        
        # If the user somehow responded with nothing, or just said N
        # FORCEFULLY abort the operation (jesus why do they have to do it)
        if len(override) < 1 or override.lower() == "n":
            print_normal("Rollback aborted.")
            return True
        if os.path.isfile(SYNC_LOCAL_FILE):
            print_verbose(f"remove: \"{SYNC_LOCAL_FILE}\"")
            os.remove(SYNC_LOCAL_FILE)
        

        print_verbose(f"rename: \"{SYNC_LOCAL_FILE_OLD}\" -> \"{SYNC_LOCAL_FILE}\"")
        os.rename(SYNC_LOCAL_FILE_OLD, SYNC_LOCAL_FILE)
        print_normal("Successfully rolled back to previous sync.")
        return True
    # If SYNC_LOCAL_FILE exists in filesystem, rename by appending it with an ".old" extension
    #
    # However, if a sync was previously initiated, delete it first before turning the current sync
    # into the previous one. Otherwise if SYNC_LOCAL_FILE doesn't really exist at all, just make
    # sure the local sync directory is created properly.
    if os.path.isfile(SYNC_LOCAL_FILE):
        if os.path.isfile(SYNC_LOCAL_FILE_OLD):
            print_verbose(f"remove: \"{SYNC_LOCAL_FILE_OLD}\"")
            os.remove(SYNC_LOCAL_FILE_OLD)
        

        print_verbose(f"rename: \"{SYNC_LOCAL_FILE}\" -> \"{SYNC_LOCAL_FILE_OLD}\"")
        os.rename(SYNC_LOCAL_FILE, SYNC_LOCAL_FILE_OLD)
    elif not os.path.isdir(SYNC_LOCAL_DIR):
        print_verbose(f"directory created: \"{SYNC_LOCAL_DIR}\"")
        os.makedirs(SYNC_LOCAL_DIR, exist_ok=True)


    # Synchronize from remote templates by downloading the file from SYNC_REMOTE_URL
    print_verbose(f"syncing from remote url: \"{SYNC_REMOTE_URL}\"")
    

    try:
        response = requests.get(SYNC_REMOTE_URL, stream=True)
        total = int(response.headers.get("content-length", 0))
    except requests.RequestException as e:
        print_normal(f"An error occurred while synchronizing: {str(e)}")
        return False
    except KeyboardInterrupt:
        return True
    # Create some cool progress bar to keep track of the download progress
    with open(SYNC_LOCAL_FILE, "wb") as file, tqdm(desc="Synchronizing from remote URL"
                                                   , total=total
                                                   , unit="iB"
                                                   , unit_scale=True
                                                   , unit_divisor=1024) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


    print_normal("Finished syncing templates from remote to local")
    return True


def reset() -> bool:
    # This operation is similar to the roll-back option in sync operation
    # Check if there are any local templates synced, if not, it would do nothing
    if not os.path.isfile(SYNC_LOCAL_FILE):
        print_normal("There is nothing to reset.")
        return


    # Ask one more time before the user can change their minds
    question = input("Are you sure you want to reset srcinit? (Y/n) ")

    # If the user somehow responded with nothing, or just said N
    # do nothing and return false
    if len(question) < 1 or question.lower() == "n":
        print_normal("Reset oeration aborted.")
        return False


    shutil.rmtree(SYNC_LOCAL_DIR, ignore_errors=True)
    print("Reset operation successful")
    return True


def list() -> list[str]:
    # If no synchronization ever happened, or out-of-date, perform syncing first.
    #
    # But if syncing fails, probably due to unstable network, or no connection
    # the user can retry retrieving the template list when they have good connection
    if not os.path.isfile(SYNC_LOCAL_FILE):
        print_normal("Local templates are out-of-date, syncing..")
        if not sync(): return []

    template_list = []
    print_verbose(f"open: {SYNC_LOCAL_FILE}")
    zip = ZipFile(SYNC_LOCAL_FILE, "r")
    zip_info_list = zip.infolist()
    zip.close()


    for zip_info in zip_info_list:
        if not zip_info.is_dir():
            print_verbose(f"entry check: \"{zip_info.filename}\"")
            continue

        dir_name = zip_info.filename.removesuffix("/")
        template_list.append(dir_name)


    return template_list


def generate(template: str, destination: str = os.getcwd()) -> bool:
    # Store local template list
    template_list = list()


    # If not found in local template list, do nothing
    if template not in template_list:
        print_normal(f"\"{template}\" not found")
        return False


    # Create a time instance & unpack the right contents to the destination
    # This implementation is done poorly, might be refactored soon.
    timed = time()
    print_verbose(f"open: {SYNC_LOCAL_FILE}")
    zip = ZipFile(SYNC_LOCAL_FILE, "r")
    name = f"{template}/"

    for entry in zip.namelist():
        if not entry.startswith(name) or entry == name:
            print_verbose(f"skip: \"{entry}\"")
            continue


        output = os.path.join(destination, entry[len(name):])
        print_verbose(f"create directory: \"{destination}\"")
        os.makedirs(destination, exist_ok=True)


        with zip.open(entry) as file, open(output, "wb") as out:
            print_verbose(f"generate: \"{entry}\" -> \"{output}\"")
            shutil.copyfileobj(file, out)

    # Done, print elapsed time
    print_normal(f"Finished in {round(time() - timed, 2)} seconds")
    return True


def main():
    global verbose
    # Construct command-line argument parser
    argument_parser = ArgumentParser(prog=ARGPARSE_PROG
                                     , description=ARGPARSE_DESCRIPTION
                                     , epilog=ARGPARSE_EPILOG)
    # Use subparsers for parsing sub-commands to ease up tasks
    subparsers = argument_parser.add_subparsers(title="subcommands", dest="subcommand")
    parser_generate = subparsers.add_parser("generate", help="generate source using a template")
    parser_generate.add_argument("template", metavar="<TEMPLATE>"
                                 , help="specify source template")
    parser_generate.add_argument("-o", "--output", metavar="<DIR>"
                                 , help="specify output directory"
                                 , default=os.getcwd())
    parser_sync = subparsers.add_parser("sync", help="sync latest templates from remote to local")
    parser_sync.add_argument("-r", "--rollback", help="replace with previous sync if available"
                             , action="store_true")
    parser_list = subparsers.add_parser("list", help="print a list of templates locally")
    parser_reset = subparsers.add_parser("reset", help="delete synced data & reset srcinit")
    # Add optional flags for command-line parsing
    argument_parser.add_argument("-v", "--verbose", help="print verbose information"
                                 , action="store_true")
    # Parse passed command-line arguments
    args = argument_parser.parse_args()
    verbose = args.verbose


    match args.subcommand:
        case "generate":
            generate(args.template, destination=args.output)
        case "list":
            template_list = list()


            if len(template_list) > 0:
                print_normal(f"{len(template_list)} template(s) are locally available:")
                print_normal(", ".join(template_list))
            else:
                print_normal("No entries to list, a proper sync might be required")
        case "sync":
            sync(args.rollback)
        case "reset":
            reset()
        case _:
            argument_parser.print_help()


if not imported:
    main()