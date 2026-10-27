"""Command line: run the daemon, spawn and despawn Pokémon, drop berries."""

import argparse
import shlex
import shutil
import subprocess
import sys

from . import config, daemon, i18n
from .i18n import text
from .pokemon import berries, names, party, pokedex, sprites

DEFAULT_MENU = "rofi -dmenu -i -p Pokémon"


def notify(enabled: bool, message: str) -> None:
    if enabled and shutil.which("notify-send"):
        subprocess.run(["notify-send", "Pokémon", message], check=False)


def fail(args: argparse.Namespace, message: str) -> None:
    print(f"waybar-pokemon: {message}", file=sys.stderr)
    notify(getattr(args, "notify", False), message)
    sys.exit(1)


def explain(error: Exception, no_match: str = "no_pokemon", many: str = "many_pokemon") -> str:
    """The message for an error, in the language of the user interface."""
    if isinstance(error, names.NotFound):
        if error.count == 0:
            return text(no_match, query=error.query)
        return text(many, query=error.query, count=error.count, matches=", ".join(error.matches))
    if isinstance(error, pokedex.NoCandidates):
        return text("no_generation", generations=",".join(map(str, error.generations)))
    if isinstance(error, OSError):
        return text("offline", error=error)
    return str(error)


def label(member: party.Member, settings: config.Config) -> str:
    name = pokedex.get(member.species_id).name(settings.names_language)
    return f"{name}{' ✨' if member.shiny else ''}"


def random_generations(args: argparse.Namespace) -> list[int]:
    """Generations for random spawns: --generations, else the config file."""
    if getattr(args, "generations", None):
        return config.parse_generations(args.generations)
    return args.settings.random_generations


def spawn(args: argparse.Namespace, query: str | None) -> None:
    language = args.settings.names_language
    try:
        species = pokedex.find(query, language) if query else pokedex.random_species(random_generations(args))
        shiny = args.shiny or pokedex.roll_shiny()
        sprites.pokemon(species.id, shiny)  # download now, so errors show here
    except (LookupError, OSError, ValueError) as error:
        fail(args, explain(error))
    with party.editing() as members:
        if len(members) >= party.MAX_SIZE:
            fail(args, text("full", max=party.MAX_SIZE))
        member = party.Member(party.next_uid(members), species.id, shiny)
        members.append(member)
    name = species.name(language)
    notify(args.notify, text("wild_shiny" if shiny else "wild", name=name))
    print(label(member, args.settings))


def despawn(args: argparse.Namespace, query: str | None, everyone: bool = False) -> None:
    """Removes everyone, the member with the given uid or name, or the newest one."""
    language = args.settings.names_language
    with party.editing() as members:
        if not members:
            fail(args, text("nobody"))
        if everyone:
            leaving = list(members)
        elif query is None:
            leaving = [members[-1]]
        elif query.isdigit() and any(m.uid == int(query) for m in members):
            leaving = [m for m in members if m.uid == int(query)]
        else:
            key = names.normalize(query)

            def matches(member: party.Member) -> bool:
                species = pokedex.get(member.species_id)
                return any(names.normalize(n).startswith(key) for n in (species.name(language), species.name("en"), species.identifier))

            matching = [m for m in members if matches(m)]
            if not matching:
                fail(args, text("not_in_habitat", query=query))
            leaving = [matching[-1]]
        for member in leaving:
            members.remove(member)
    leaving_names = ", ".join(pokedex.get(m.species_id).name(language) for m in leaving)
    notify(args.notify, text("returned_many" if len(leaving) > 1 else "returned_one", names=leaving_names))


def berry(args: argparse.Namespace, query: str | None) -> None:
    """Asks the daemon to drop a berry (a random one without a name)."""
    language = args.settings.names_language
    try:
        name = berries.find(query, language) if query else berries.random_name()
        sprites.berry(name)  # download now, so errors show here
        display_name = berries.display_name(name, language)
    except (LookupError, OSError) as error:
        fail(args, explain(error, "no_berry", "many_berries"))
    berries.request(name)
    notify(args.notify, text("berry_fell", berry=display_name))
    print(display_name)


def download() -> None:
    def progress(done: int, total: int) -> None:
        print("\r" + text("progress", done=done, total=total), end="", file=sys.stderr, flush=True)

    try:
        failed = sprites.download_all(progress)
    except OSError as error:
        print(f"\nwaybar-pokemon: {explain(error)}", file=sys.stderr)
        sys.exit(1)
    print(file=sys.stderr)
    if failed:
        print(text("failed", failed=failed), file=sys.stderr)
        sys.exit(1)


def choose(menu_command: str, options: list[str]) -> str | None:
    """Lets the user pick one of the options with a dmenu-like program."""
    result = subprocess.run(shlex.split(menu_command), input="\n".join(options), capture_output=True, text=True)
    choice = result.stdout.strip()
    return choice if result.returncode == 0 and choice else None


def spawn_menu(args: argparse.Namespace) -> None:
    try:
        options = [s.name(args.settings.names_language) for s in pokedex.all_species()]
        generations = random_generations(args)
    except (OSError, ValueError) as error:
        fail(args, explain(error))
    random_label = text("random_from", generations=",".join(map(str, generations))) if generations else text("random")
    choice = choose(args.menu, [random_label] + options)
    if choice:
        spawn(args, None if choice == random_label else choice)


def despawn_menu(args: argparse.Namespace) -> None:
    members = party.load()
    if not members:
        fail(args, text("nobody"))
    everyone = text("everyone")
    options = [f"{m.uid}: {label(m, args.settings)}" for m in members] + [everyone]
    choice = choose(args.menu, options)
    if choice == everyone:
        despawn(args, None, everyone=True)
    elif choice:
        despawn(args, choice.split(":", 1)[0])


def main() -> None:
    parser = argparse.ArgumentParser(prog="waybar-pokemon", description="Little Pokémon walking around in waybar.")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("daemon", help="simulate the Pokémon and render the frames for waybar")

    p = commands.add_parser("spawn", help="send out a Pokémon (a random one without a name)")
    p.add_argument("pokemon", nargs="?", help="name (or its beginning) or Pokédex number")
    p.add_argument("--shiny", action="store_true", help="make it shiny (otherwise 1 in 4096)")

    p = commands.add_parser("despawn", help="return a Pokémon (the newest one without a name)")
    p.add_argument("pokemon", nargs="?", help="name or number from `list`")
    p.add_argument("--all", action="store_true", help="return everyone")

    p = commands.add_parser("berry", help="drop a berry for the Pokémon to race for (a random one without a name)")
    p.add_argument("name", nargs="?", help="name of the berry (or its beginning), e.g. oran")

    commands.add_parser("list", help="show the party: number and name")
    commands.add_parser("download", help="download all names and sprites now, for spawning without internet")
    commands.add_parser("names", help="show all Pokémon names")
    commands.add_parser("berries", help="show all berry names")

    p = commands.add_parser("spawn-menu", help="choose a Pokémon to spawn from a menu")
    p.add_argument("--shiny", action="store_true", help=argparse.SUPPRESS)
    commands.add_parser("despawn-menu", help="choose a Pokémon to despawn from a menu")

    for name, sub in commands.choices.items():
        if name not in ("daemon", "list", "names", "berries"):
            sub.add_argument("--notify", action="store_true", help="show the result as a desktop notification")
        if name.endswith("-menu"):
            sub.add_argument("--menu", default=DEFAULT_MENU, help=f"dmenu-like command (default: {DEFAULT_MENU})")
        if name in ("spawn", "spawn-menu"):
            sub.add_argument("--generations", help='random ones only from these generations, e.g. "1-4" (default: from the config file)')

    args = parser.parse_args()
    try:
        args.settings = config.load()
    except ValueError as error:
        sys.exit(f"waybar-pokemon: {error}")
    i18n.set_language(args.settings.ui_language)

    if args.command == "daemon":
        daemon.run(args.settings)
    elif args.command == "spawn":
        spawn(args, args.pokemon)
    elif args.command == "despawn":
        despawn(args, args.pokemon, everyone=args.all)
    elif args.command == "berry":
        berry(args, args.name)
    elif args.command == "list":
        for member in party.load():
            print(f"{member.uid}: {label(member, args.settings)}")
    elif args.command == "download":
        download()
    elif args.command == "names":
        print("\n".join(s.name(args.settings.names_language) for s in pokedex.all_species()))
    elif args.command == "berries":
        print("\n".join(berries.display_name(n, args.settings.names_language) for n in berries.NAMES))
    elif args.command == "spawn-menu":
        spawn_menu(args)
    elif args.command == "despawn-menu":
        despawn_menu(args)
