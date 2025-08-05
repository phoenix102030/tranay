from pathlib import Path

StrPath = str | Path


def generate_file(content: str, output_file: StrPath) -> None:
    with open(str(output_file), "w") as file:
        file.write(content)


def read_file_content(file_path: StrPath) -> str:
    with open(str(file_path), "r", encoding="utf-8") as file:
        return file.read()


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]
