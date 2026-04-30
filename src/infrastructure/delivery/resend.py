import httpx


def format_email_html(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    paragraphs = text.split("\n\n")
    return "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)


async def send_email(resend_key: str, to: str, subject: str, html: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}"},
            json={
                "from": "Alejandro Saavedra Ruiz <contact@asrdev.eu>",
                "to": [to],
                "subject": subject,
                "html": format_email_html(html),
            },
        )
        response.raise_for_status()
