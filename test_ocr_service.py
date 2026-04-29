import json
import unittest
from unittest.mock import patch

import httpx

from app.config import settings
from app.services.ocr_service import OCRError, GeminiOCRError, _extract_text_with_ocr_space, extract_text


def _response(status_code: int, payload: dict | None = None, text: str = "") -> httpx.Response:
    request = httpx.Request("POST", "https://api.ocr.space/parse/image")
    content = json.dumps(payload).encode("utf-8") if payload is not None else text.encode("utf-8")
    return httpx.Response(status_code=status_code, request=request, content=content)


class FakeAsyncClient:
    def __init__(self, responses: list[httpx.Response]):
        self._responses = responses
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        response = self._responses[self.calls]
        self.calls += 1
        return response


class OcrServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_ocr_space_resource_exhaustion_is_reported_clearly(self):
        payload = {
            "IsErroredOnProcessing": True,
            "ErrorDetails": "Error E500: System Resource Exhaustion (OCR Binary Failed)",
        }
        fake_client = FakeAsyncClient([_response(200, payload=payload)])

        with patch.object(settings, "OCR_API_KEY", "test-key"), patch(
            "app.services.ocr_service.httpx.AsyncClient", return_value=fake_client
        ):
            with self.assertRaises(OCRError) as ctx:
                await _extract_text_with_ocr_space(b"image-bytes", "prescription.jpg")

        self.assertIn("temporarily overloaded", str(ctx.exception))
        self.assertIn("System Resource Exhaustion", str(ctx.exception))

    async def test_ocr_space_retries_transient_http_errors(self):
        fake_client = FakeAsyncClient(
            [
                _response(503, text="service unavailable"),
                _response(
                    200,
                    payload={
                        "IsErroredOnProcessing": False,
                        "ParsedResults": [{"ParsedText": "Aspirin 500mg"}],
                    },
                ),
            ]
        )

        with patch.object(settings, "OCR_API_KEY", "test-key"), patch(
            "app.services.ocr_service.httpx.AsyncClient", return_value=fake_client
        ):
            text = await _extract_text_with_ocr_space(b"image-bytes", "prescription.jpg")

        self.assertEqual(text, "Aspirin 500mg")
        self.assertEqual(fake_client.calls, 2)

    async def test_gemini_400_does_not_fall_back_to_ocr_space(self):
        fake_client = FakeAsyncClient(
            [
                _response(400, text='{"error":{"message":"Invalid argument"}}'),
                _response(400, text='{"error":{"message":"Invalid argument"}}'),
            ]
        )

        with patch.object(settings, "GEMINI_API_KEY", "test-key"), patch.object(settings, "OCR_API_KEY", "test-key"), patch(
            "app.services.ocr_service.httpx.AsyncClient", return_value=fake_client
        ), patch("app.services.ocr_service._extract_text_with_ocr_space") as fallback_mock:
            fallback_mock.side_effect = AssertionError("OCR.space fallback should not be called")

            with self.assertRaises(GeminiOCRError) as ctx:
                await extract_text(b"image-bytes", "prescription.jpg")

        self.assertIn("Gemini OCR request was rejected as invalid", str(ctx.exception))
        self.assertEqual(fake_client.calls, 1)
        fallback_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()