from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownImport:
    relative_path: str
    title: str
    text: str
    links: tuple[str, ...]


class ObsidianImportAdapter:
    provider = "obsidian"
    max_files = 200

    def read(self, filename: str, data: bytes) -> list[MarkdownImport]:
        if len(data) > 20_000_000: raise ValueError("The selected import is too large.")
        if filename.lower().endswith(".md"):
            return [self._note(filename, data)]
        if not filename.lower().endswith(".zip"): raise ValueError("Choose a Markdown file or Markdown ZIP.")
        notes: list[MarkdownImport] = []
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".md") and not name.startswith(("/", "\\"))]
            if len(names) > self.max_files: raise ValueError("The import contains too many Markdown files.")
            for name in names:
                if ".." in name.replace("\\", "/").split("/"): raise ValueError("Unsafe archive path.")
                payload = archive.read(name)
                if len(payload) > 1_000_000: raise ValueError("A Markdown file exceeds the safe size limit.")
                notes.append(self._note(name.replace("\\", "/"), payload))
        return notes

    def _note(self, path: str, data: bytes) -> MarkdownImport:
        text = data.decode("utf-8")
        links: list[str] = []
        for section in text.split("[[")[1:]:
            target = section.split("]]", 1)[0].strip()
            if target and len(target) <= 300: links.append(target)
        title = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return MarkdownImport(path, title, text, tuple(dict.fromkeys(links)))
