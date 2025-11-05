import requests
import time
from pathlib import Path
from fpdf import FPDF

BASE = "http://localhost:18000"

def wait_for_service():
    """Wait until the FastAPI service is available."""
    for _ in range(30):
        try:
            r = requests.get(f"{BASE}/health")
            if r.status_code == 200:
                return
        except:
            pass
        time.sleep(1)
    raise RuntimeError("Service not available")


def test_health():
    wait_for_service()
    r = requests.get(f"{BASE}/health")
    assert r.json()["status"] == "healthy" 


def test_upload_and_retrieve(tmp_path: Path):
    """Test text file upload + metadata retrieval"""
    dummy = tmp_path / "sample.txt"
    dummy.write_text("hello world")

    with open(dummy, "rb") as f:
        r = requests.post(f"{BASE}/upload", files={"file": f})
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    r2 = requests.get(f"{BASE}/metadata/{doc_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["filename"] == "sample.txt"
    assert data["minio_path"].startswith("s3://")


def create_dummy_pdf(path: Path, text: str = "Hello PDF World!"):
    """Helper to create a simple one-page PDF with FPDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=text, ln=1)
    pdf.output(str(path))


def test_pdf_ingest(tmp_path: Path):
    """Test single PDF ingestion"""
    pdf_path = tmp_path / "sample.pdf"
    create_dummy_pdf(pdf_path)

    with open(pdf_path, "rb") as f:
        r = requests.post(f"{BASE}/ingest-pdf", files={"file": f})
    assert r.status_code == 200
    result = r.json()

    assert result["filename"] == "sample.pdf"
    assert result["chunks_created"] > 0
    assert result["pages_processed"] == 1
    assert result["document_task"] is not None
    assert result["chunk_task"] is not None


def test_pdf_batch_ingest(tmp_path: Path):
    """Test batch PDF ingestion"""
    files = []
    for i in range(2):
        pdf_path = tmp_path / f"batch_{i}.pdf"
        create_dummy_pdf(pdf_path, text=f"Hello batch PDF {i}")
        files.append(("files", (pdf_path.name, open(pdf_path, "rb"), "application/pdf")))

    r = requests.post(f"{BASE}/ingest-pdf-batch", files=files)
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    for res in results:
        assert "filename" in res
        assert res["chunks_created"] > 0
        assert res["pages_processed"] == 1
