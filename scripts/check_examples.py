import json
import sys
from pathlib import Path


def load_json_with_comments(path: Path):
    lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('#') or not stripped:
            continue
        lines.append(line)
    return json.loads('\n'.join(lines))


def is_absolute(arg: str) -> bool:
    if arg.startswith('/'):
        return True
    if len(arg) > 1 and arg[1] == ':' and arg[2:3] in ('\\', '/'):
        return True
    return False


def check_file(path: Path) -> int:
    try:
        data = load_json_with_comments(path)
    except json.JSONDecodeError as e:
        print(f"{path}: invalid JSON - {e}")
        return 1
    try:
        args = data['mcpServers']['boomi']['args']
    except KeyError as e:
        print(f"{path}: missing key {e}")
        return 1
    # Ensure '--directory' is followed by absolute path
    if '--directory' in args:
        idx = args.index('--directory') + 1
        if idx >= len(args) or not is_absolute(args[idx]):
            print(f"{path}: '--directory' must be followed by an absolute path")
            return 1
    return 0


def main(paths):
    ret = 0
    for p in paths:
        ret |= check_file(Path(p))
    return ret


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
