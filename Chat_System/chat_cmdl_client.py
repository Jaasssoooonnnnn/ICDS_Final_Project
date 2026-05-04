
from chat_client_class import Client as CommandLineClient

def main():
    import argparse
    parser = argparse.ArgumentParser(description='chat client argument')
    parser.add_argument('-d', type=str, default=None, help='server IP addr')
    parser.add_argument('--gui', action='store_true', help='start the GUI client')
    args = parser.parse_args()

    if args.gui:
        from chat_gui_client import GUIClient
        client = GUIClient(args)
    else:
        client = CommandLineClient(args)
    client.run_chat()

main()
