import io, zipfile
import pytest
from app.integrations.obsidian import ObsidianImportAdapter

def test_obsidian_import_preserves_safe_paths_links_and_has_no_filesystem_access():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as archive:
        archive.writestr("release/auth.md","# Auth\nSee [[rollback]]")
        archive.writestr("release/rollback.md","# Rollback")
    notes=ObsidianImportAdapter().read("vault.zip",stream.getvalue())
    assert notes[0].relative_path == "release/auth.md"
    assert notes[0].links == ("rollback",)

def test_obsidian_rejects_unsafe_archive_path():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as archive: archive.writestr("../secret.md","no")
    with pytest.raises(ValueError): ObsidianImportAdapter().read("vault.zip",stream.getvalue())
