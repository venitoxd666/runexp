import os
import argparse
import rich

HELP = f"""
Cleantemp Erases ALL temporal files at %TEMP%(=\"{os.environ['TEMP']}\")
"""

ap = argparse.ArgumentParser(
    prog='cleantemp',
    description='Clean all the temporary files'
)

def print_help():
    argparse.ArgumentParser.print_help(ap)
    rich.print(HELP)

ap.print_help = print_help

def main():
    for obj in os.listdir(os.environ['TEMP']):
        try:
            os.remove(os.path.join(os.environ['TEMP'], obj))
        except (OSError, Exception) as e:
            continue
        except KeyboardInterrupt as e:
            rich.print("[red]^C[/red]")
    
if __name__ == '__main__':
    ap.parse_args()
    main()