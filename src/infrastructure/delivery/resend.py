import httpx


async def send_email(resend_key: str, to: str, subject: str, html: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}"},
            json={
                "from": "Alejandro Saavedra Ruiz <contact@asrdev.eu>",
                "to": [to],
                "subject": subject,
                "html": html,
            },
        )
        response.raise_for_status()
