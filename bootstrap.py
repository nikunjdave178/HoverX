import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
STRUCTURE_FILE = BASE_DIR / "structure.json"


def create_structure(base_path: Path, node: dict):
    for name, value in node.items():
        path = base_path / name

        if isinstance(value, dict):
            path.mkdir(parents=True, exist_ok=True)
            print(f"DIR  : {path}")
            create_structure(path, value)

        elif value is None:
            if not path.exists():
                path.touch()
                print(f"FILE : {path}")
            else:
                print(f"SKIP : {path}")


def main():
    if not STRUCTURE_FILE.exists():
        raise FileNotFoundError("structure.json not found")

    with STRUCTURE_FILE.open("r", encoding="utf-8") as f:
        structure = json.load(f)

    create_structure(BASE_DIR, structure)
    print("\nProject structure created successfully.")


if __name__ == "__main__":
    main()
