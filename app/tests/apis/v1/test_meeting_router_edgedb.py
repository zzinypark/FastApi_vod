import datetime

import httpx
from httpx import AsyncClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_204_NO_CONTENT,
)

from app import app
from app.dtos.update_meeting_request import MEETING_DATE_MAX_RANGE
from app.utils.edge import edgedb_client


async def test_api_create_meeting_edgedb() -> None:
    # When
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            url="/v1/edgedb/meetings",
        )

    # Then
    assert response.status_code == HTTP_200_OK
    url_code = response.json()["url_code"]
    assert await edgedb_client.query_single(f"select exists (select Meeting filter .url_code = '{url_code}');") is True


async def test_api_get_meeting() -> None:
    # Given
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_meeting_response = await client.post(
            url="/v1/edgedb/meetings",
        )
        url_code = create_meeting_response.json()["url_code"]

        # When
        response = await client.get(url=f"/v1/edgedb/meetings/{url_code}")

    # Then
    assert response.status_code == HTTP_200_OK
    response_body = response.json()
    assert response_body["url_code"] == url_code
    assert response_body["start_date"] is None
    assert response_body["end_date"] is None
    assert response_body["title"] == ""
    assert response_body["location"] == ""



async def test_api_get_meeting_404() -> None:
    # Given
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # When
        response = await client.get(
            url="/v1/edgedb/meetings/invalid_url",
        )

    # Then
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "meeting with url_code: invalid_url not found"


async def test_api_update_meeting_date_range() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        create_meeting_response = await client.post(url="/v1/edgedb/meetings")
        url_code = create_meeting_response.json()["url_code"]

        # When
        response = await client.patch(
            url=f"/v1/edgedb/meetings/{url_code}/date_range",
            json={"start_date": "2025-10-10", "end_date": "2025-10-20"},
        )

    # Then
    assert response.status_code == HTTP_200_OK
    response_body = response.json()
    assert response_body["start_date"] == "2025-10-10"
    assert response_body["end_date"] == "2025-10-20"
    meeting = await edgedb_client.query_single(
        f"select Meeting {{start_date, end_date}} filter .url_code = '{url_code}'"
    )
    assert meeting.start_date == datetime.date(2025, 10, 10)
    assert meeting.end_date == datetime.date(2025, 10, 20)


async def test_can_not_update_meeting_date_range_when_range_is_too_long() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        create_meeting_response = await client.post(url="/v1/edgedb/meetings")
        url_code = create_meeting_response.json()["url_code"]

        # When
        response = await client.patch(
            url=f"/v1/edgedb/meetings/{url_code}/date_range",
            json={"start_date": (start := "2025-10-10"), "end_date": (end := "2030-10-20")},
        )

    # Then
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    response_body = response.json()
    assert response_body["detail"] == f"start {start} and end {end} should be within {MEETING_DATE_MAX_RANGE.days} days"


async def test_can_not_update_meeting_date_range_when_it_is_already_set() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        create_meeting_response = await client.post(url="/v1/edgedb/meetings")
        url_code = create_meeting_response.json()["url_code"]
        await client.patch(
            url=f"/v1/edgedb/meetings/{url_code}/date_range",
            json={"start_date": "2025-10-10", "end_date": "2025-10-20"},
        )

        # When
        response = await client.patch(
            url=f"/v1/edgedb/meetings/{url_code}/date_range",
            json={"start_date": "2025-10-12", "end_date": "2025-10-22"},
        )

    # Then
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    response_body = response.json()
    assert response_body["detail"] == f"meeting: {url_code} start: 2025-10-10 end: 2025-10-20 are already set"


async def test_can_not_update_meeting_does_not_exists() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        url_code = "invalid_url"

        # When
        response = await client.patch(
            url=f"/v1/edgedb/meetings/{url_code}/date_range",
            json={"start_date": "2025-10-12", "end_date": "2025-10-22"},
        )

    # Then
    assert response.status_code == HTTP_404_NOT_FOUND
    response_body = response.json()
    assert response_body["detail"] == "meeting with url_code: invalid_url not found"


async def test_api_update_meeting_title() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_meeting_response = await client.post(url="/v1/edgedb/meetings")
        url_code = create_meeting_response.json()["url_code"]

        response = await client.patch(f"/v1/edgedb/meetings/{url_code}/title", json={"title": (title := "abc")})

    assert response.status_code == HTTP_204_NO_CONTENT
    meeting = await edgedb_client.query_single(f"select Meeting {{title}} filter .url_code = '{url_code}'")
    assert meeting.title == title


async def test_can_not_update_meeting_title_when_meeting_does_not_exists() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        url_code = "invalid_url_code"

        # When
        response = await client.patch(f"/v1/edgedb/meetings/{url_code}/title", json={"title": "abc"})

    # Then
    assert response.status_code == HTTP_404_NOT_FOUND


async def test_api_update_meeting_location() -> None:
    # given
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_meeting_response = await client.post(url="/v1/edgedb/meetings")
        url_code = create_meeting_response.json()["url_code"]
        location = "test location"

        # when
        response = await client.patch(f"/v1/edgedb/meetings/{url_code}/location", json={"location": location})

    # then
    assert response.status_code == HTTP_204_NO_CONTENT


async def test_can_not_update_meeting_location_when_meeting_does_not_exists() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Given
        url_code = "invalid_url_code"

        # When
        response = await client.patch(f"/v1/edgedb/meetings/{url_code}/location", json={"location": "abc"})

    # Then
    assert response.status_code == HTTP_404_NOT_FOUND
