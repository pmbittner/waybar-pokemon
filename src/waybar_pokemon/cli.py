"""Command line: parses the arguments, calls the library interface (api.py)
and tells the user what happened, in the terminal and optionally as a
desktop notification."""

import argparse
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, NoReturn

from . import __version__, api, config, daemon, i18n
from .i18n import text
from .pokemon import names, pokedex

DEFAULT_MENU = "rofi -dmenu -i -p Pokémon"


@dataclass(frozen=True)
class Context:
    """What every command needs besides its own arguments."""

    config: config.Config
    notify: bool = False  # also show messages as desktop notifications
    menu: str = DEFAULT_MENU  # dmenu-like command for the menus

    def tell(self, message: str) -> None:
        if self.notify and shutil.which("notify-send"):
            subprocess.run(["notify-send", "Pokémon", message], check=False)

    def fail(self, error: Exception) -> NoReturn:
        message = explain(error)
        print(f"waybar-pokemon: {message}", file=sys.stderr)
        self.tell(message)
        sys.exit(1)


def explain(error: Exception) -> str:
    """The message for an error, in the language of the user interface."""
    if isinstance(error, names.NotFound):
        berry = error.kind == "berry"
        if error.count == 0:
            return text("no_berry" if berry else "no_pokemon", query=error.query)
        return text("many_berries" if berry else "many_pokemon", query=error.query, count=error.count, matches=", ".join(error.matches))
    if isinstance(error, pokedex.NoCandidates):
        return text("no_generation", generations=",".join(map(str, error.generations)))
    if isinstance(error, api.Full):
        return text("full", max=api.MAX_RESIDENTS)
    if isinstance(error, api.Empty):
        return text("nobody")
    if isinstance(error, api.NotInHabitat):
        return text("not_in_habitat", query=error.query)
    if isinstance(error, OSError):
        return text("offline", error=error)
    return str(error)


def label(resident: api.Resident) -> str:
    return f"{resident.name}{' ✨' if resident.shiny else ''}"


def generations(args: argparse.Namespace) -> tuple[int, ...] | None:
    """--generations, if given (else the settings apply)."""
    return config.parse_generations(args.generations) if getattr(args, "generations", None) else None


# Commands

ERRORS = (LookupError, OSError, ValueError, api.Full)


def spawn(ctx: Context, args: argparse.Namespace) -> None:
    try:
        resident = api.spawn(ctx.config, args.pokemon, shiny=args.shiny, generations=generations(args))
    except ERRORS as error:
        ctx.fail(error)
    ctx.tell(text("wild_shiny" if resident.shiny else "wild", name=resident.name))
    print(label(resident))


def despawn(ctx: Context, args: argparse.Namespace) -> None:
    try:
        leaving = api.despawn_all(ctx.config) if args.all else [api.despawn(ctx.config, args.pokemon)]
    except ERRORS as error:
        ctx.fail(error)
    leaving_names = ", ".join(r.name for r in leaving)
    ctx.tell(text("returned_many" if len(leaving) > 1 else "returned_one", names=leaving_names))


def berry(ctx: Context, args: argparse.Namespace) -> None:
    try:
        dropped = api.drop_berry(ctx.config, args.name)
    except ERRORS as error:
        ctx.fail(error)
    ctx.tell(text("berry_fell", berry=dropped.name))
    print(dropped.name)


def show_party(ctx: Context, args: argparse.Namespace) -> None:
    for resident in api.residents(ctx.config):
        print(f"{resident.uid}: {label(resident)}")


def show_pokemon_names(ctx: Context, args: argparse.Namespace) -> None:
    print("\n".join(api.pokemon_names(ctx.config)))


def show_berry_names(ctx: Context, args: argparse.Namespace) -> None:
    print("\n".join(api.berry_names(ctx.config)))


def download(ctx: Context, args: argparse.Namespace) -> None:
    def progress(done: int, total: int) -> None:
        print("\r" + text("progress", done=done, total=total), end="", file=sys.stderr, flush=True)

    try:
        failed = api.download(progress)
    except OSError as error:
        print(file=sys.stderr)
        ctx.fail(error)
    print(file=sys.stderr)
    if failed:
        print(text("failed", failed=failed), file=sys.stderr)
        sys.exit(1)


def choose(ctx: Context, options: list[str]) -> str | None:
    """Lets the user pick one of the options with the dmenu-like menu."""
    result = subprocess.run(shlex.split(ctx.menu), input="\n".join(options), capture_output=True, text=True)
    choice = result.stdout.strip()
    return choice if result.returncode == 0 and choice else None


def spawn_menu(ctx: Context, args: argparse.Namespace) -> None:
    try:
        options = api.pokemon_names(ctx.config)
        chosen_generations = generations(args) or ctx.config.random_generations
    except ERRORS as error:
        ctx.fail(error)
    random_label = text("random_from", generations=",".join(map(str, chosen_generations))) if chosen_generations else text("random")
    choice = choose(ctx, [random_label] + options)
    if choice:
        args.pokemon = None if choice == random_label else choice
        spawn(ctx, args)


def despawn_menu(ctx: Context, args: argparse.Namespace) -> None:
    residents = api.residents(ctx.config)
    if not residents:
        ctx.fail(api.Empty())
    everyone = text("everyone")
    choice = choose(ctx, [f"{r.uid}: {label(r)}" for r in residents] + [everyone])
    if choice:
        args.all = choice == everyone
        args.pokemon = None if args.all else choice.split(":", 1)[0]
        despawn(ctx, args)


def run_daemon(ctx: Context, args: argparse.Namespace) -> None:
    daemon.run(ctx.config)


# Arguments

def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="waybar-pokemon", description="Little Pokémon walking around in waybar.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name: str, function: Callable[[Context, argparse.Namespace], None], help: str, notify: bool = True) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help)
        sub.set_defaults(function=function)
        if notify:
            sub.add_argument("--notify", action="store_true", help="show the result as a desktop notification")
        return sub

    command("daemon", run_daemon, "simulate the Pokémon and render the frames for waybar", notify=False)

    p = command("spawn", spawn, "send out a Pokémon (a random one without a name)")
    p.add_argument("pokemon", nargs="?", help="name (or its beginning) or Pokédex number")
    p.add_argument("--shiny", action="store_true", help="make it shiny (otherwise 1 in 4096)")
    p.add_argument("--generations", help='random ones only from these generations, e.g. "1-4" (default: from the config file)')

    p = command("despawn", despawn, "return a Pokémon (the newest one without a name)")
    p.add_argument("pokemon", nargs="?", help="name or number from `list`")
    p.add_argument("--all", action="store_true", help="return everyone")

    p = command("berry", berry, "drop a berry for the Pokémon to race for (a random one without a name)")
    p.add_argument("name", nargs="?", help="name of the berry (or its beginning), e.g. oran")

    command("list", show_party, "show the party: number and name", notify=False)
    command("download", download, "download all names and sprites now, for spawning without internet", notify=False)
    command("names", show_pokemon_names, "show all Pokémon names", notify=False)
    command("berries", show_berry_names, "show all berry names", notify=False)

    p = command("spawn-menu", spawn_menu, "choose a Pokémon to spawn from a menu")
    p.add_argument("--generations", help='random ones only from these generations, e.g. "1-4" (default: from the config file)')
    p.set_defaults(shiny=False)
    p = command("despawn-menu", despawn_menu, "choose a Pokémon to despawn from a menu")
    for p in (commands.choices["spawn-menu"], commands.choices["despawn-menu"]):
        p.add_argument("--menu", default=DEFAULT_MENU, help=f"dmenu-like command (default: {DEFAULT_MENU})")
    return parser


def main() -> None:
    args = parser().parse_args()
    try:
        settings = config.load()
    except ValueError as error:
        sys.exit(f"waybar-pokemon: {error}")
    i18n.set_language(settings.ui_language)
    ctx = Context(settings, notify=getattr(args, "notify", False), menu=getattr(args, "menu", DEFAULT_MENU))
    args.function(ctx, args)
