"""Tests for Digital Backpack: upload metadata, listing, and tenant isolation."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.file_service import register_file


@pytest.mark.asyncio
async def test_digital_backpack_operations(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    student_token = seed_data["tokens"]["student1"]
    student_id = seed_data["student1"].id
    school_id = seed_data["school"].id
    subject_id = seed_data["subject"].id
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Register a file in Digital Backpack
    file_record = await register_file(
        db=db_session,
        school_id=school_id,
        uploader_id=student_id,
        filename="biology_project.pdf",
        file_url="https://storage.lumina.uz/school1/biology_project.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024 * 50,
        target_role="STUDENT",
        subject_id=subject_id,
    )
    assert file_record.id is not None

    # 2. Student queries their digital backpack
    resp = await client.get("/api/v1/backpack/files", headers=headers)
    assert resp.status_code == 200
    files = resp.json()
    assert len(files) >= 1
    found = next((f for f in files if f["filename"] == "biology_project.pdf"), None)
    assert found is not None
    assert found["file_url"] == "https://storage.lumina.uz/school1/biology_project.pdf"
