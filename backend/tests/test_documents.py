"""Errors & solutions PDFs: everyone signed in reads, only leads change."""
from pathlib import Path

from app.services import document_service

NOBODY = {"Authorization": ""}


def pdf(text: str = "hello") -> bytes:
    return f"%PDF-1.4\n% {text}\n%%EOF\n".encode()


def upload(client, name="Author errors.pdf", content=None, headers=None, **form):
    return client.post(
        "/documents",
        files={"file": (name, content if content is not None else pdf(), "application/pdf")},
        data=form,
        headers=headers or {},
    )


def test_lead_uploads_and_everyone_can_read(fresh_client, trainee_headers):
    created = upload(fresh_client, title="Author name errors", description="Common mistakes")
    assert created.status_code == 201, created.text
    doc = created.json()
    assert doc["title"] == "Author name errors"
    assert doc["original_filename"] == "Author errors.pdf"

    listed = fresh_client.get("/documents", headers=trainee_headers).json()
    assert [d["id"] for d in listed] == [doc["id"]]

    file = fresh_client.get(f"/documents/{doc['id']}/file", headers=trainee_headers)
    assert file.status_code == 200
    assert file.headers["content-type"] == "application/pdf"
    assert file.headers["content-disposition"].startswith("inline")
    assert file.content == pdf()

    download = fresh_client.get(f"/documents/{doc['id']}/file?download=true")
    assert download.headers["content-disposition"].startswith("attachment")


def test_title_defaults_to_file_name(fresh_client):
    doc = upload(fresh_client, name="affiliation_errors-and-fixes.pdf").json()
    assert doc["title"] == "Affiliation errors and fixes"


def test_documents_listed_in_upload_order(fresh_client):
    ids = [upload(fresh_client, name=f"doc{i}.pdf").json()["id"] for i in range(3)]
    assert [d["id"] for d in fresh_client.get("/documents").json()] == ids


def test_only_pdfs_are_accepted(fresh_client):
    response = upload(fresh_client, name="notes.pdf", content=b"just some text")
    assert response.status_code == 422
    assert response.json()["detail"] == "Only PDF files can be uploaded."
    assert upload(fresh_client, content=b"").status_code == 422


def test_unsafe_file_names_are_cleaned(fresh_client):
    doc = upload(fresh_client, name="../../etc/passwd").json()
    assert doc["original_filename"] == "passwd.pdf"
    assert document_service.safe_filename("a<b>?.PDF") == "a_b_.PDF"


def test_trainee_cannot_change_documents(fresh_client, trainee_headers):
    doc = upload(fresh_client).json()
    attempts = [
        upload(fresh_client, headers=trainee_headers),
        fresh_client.patch(f"/documents/{doc['id']}", json={"title": "x"}, headers=trainee_headers),
        fresh_client.put(
            f"/documents/{doc['id']}/file",
            files={"file": ("new.pdf", pdf("new"), "application/pdf")},
            headers=trainee_headers,
        ),
        fresh_client.delete(f"/documents/{doc['id']}", headers=trainee_headers),
    ]
    assert [r.status_code for r in attempts] == [403] * 4
    assert fresh_client.get(f"/documents/{doc['id']}").json()["title"] == doc["title"]


def test_not_signed_in_cannot_read(fresh_client):
    doc = upload(fresh_client).json()
    assert fresh_client.get("/documents", headers=NOBODY).status_code == 401
    assert fresh_client.get(f"/documents/{doc['id']}/file", headers=NOBODY).status_code == 401


def test_lead_edits_replaces_and_deletes(fresh_client):
    doc = upload(fresh_client).json()
    stored = document_service.documents_dir()

    edited = fresh_client.patch(
        f"/documents/{doc['id']}", json={"title": "  New title ", "description": ""}
    ).json()
    assert edited["title"] == "New title" and edited["description"] is None
    assert fresh_client.patch(f"/documents/{doc['id']}", json={"title": " "}).status_code == 422
    assert fresh_client.patch(f"/documents/{doc['id']}", json={"bogus": 1}).status_code == 422

    before = set(stored.iterdir())
    replaced = fresh_client.put(
        f"/documents/{doc['id']}/file",
        files={"file": ("v2.pdf", pdf("version two"), "application/pdf")},
    ).json()
    assert replaced["title"] == "New title" and replaced["original_filename"] == "v2.pdf"
    assert fresh_client.get(f"/documents/{doc['id']}/file").content == pdf("version two")
    assert len(set(stored.iterdir())) == len(before)  # the old file was removed

    assert fresh_client.delete(f"/documents/{doc['id']}").status_code == 204
    assert fresh_client.get(f"/documents/{doc['id']}").status_code == 404
    assert len(set(stored.iterdir())) == len(before) - 1


def test_seed_documents_from_folder(fresh_client, tmp_path: Path):
    from app.database import get_db
    from app.main import app

    (tmp_path / "Errors one.pdf").write_bytes(pdf("1"))
    (tmp_path / "errors_two.pdf").write_bytes(pdf("2"))
    (tmp_path / "broken.pdf").write_bytes(b"not a pdf")
    db = next(app.dependency_overrides[get_db]())
    assert document_service.seed_documents(db, tmp_path) == 2
    assert document_service.seed_documents(db, tmp_path) == 0  # not added twice
    titles = [d["title"] for d in fresh_client.get("/documents").json()]
    assert titles == ["Errors one", "Errors two"]
