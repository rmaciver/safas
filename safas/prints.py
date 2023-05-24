"""
safas/prints.py

"""
import logging
# https://rich.readthedocs.io/en/stable/appendix/colors.html
from rich.logging import RichHandler

#level = "NOTSET"
level = "INFO"

formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
fhandler = logging.FileHandler(".log")
fhandler.setFormatter(formatter)

logging.basicConfig(
    level=level,
    format="%(message)s",
    datefmt="|",  # Not needed w/balena, use [%X] otherwise
    handlers=[RichHandler(markup=True), fhandler],
    )

log = logging.getLogger("rich")

def print_process(
    color, process_name, *args, error=False, warning=False, exception=False, **kwargs
    ):
    msg = " ".join([str(arg) for arg in args])  # Concatenate all incoming strings or objects
    rich_msg = f"[{color}]{process_name}[/{color}] | {msg}"
    
    if error:
        log.error(rich_msg)
    elif warning:
        log.warning(rich_msg)
    elif exception:
        log.exception(rich_msg)
    else:
        log.info(rich_msg)

def print_cli(*args, **kwargs):
    print_process("cyan", "main", *args, **kwargs)

def print_app(*args, **kwargs):
    print_process("yellow", "app", *args, **kwargs)

def print_handler(*args, **kwargs):
    print_process("dark_green", "handler", *args, **kwargs)

def print_viewer(*args, **kwargs):
    print_process("dark_violet", "qtviewer", *args, **kwargs)

def print_params(*args, **kwargs):
    print_process("yellow", "qtparams", *args, **kwargs)

def print_labeler(*args, **kwargs):
    print_process("bright_yellow", "labeler", *args, **kwargs)

def print_linker(*args, **kwargs):
    print_process("white", "linker", *args, **kwargs)

def print_writer(*args, **kwargs):
    print_process("dark_green", "writer", *args, **kwargs)

# "dark_magenta", "dark_green", "bright_yellow", "bright_green", "white", "bright_cyan", "bright_red", "deep_pink4"