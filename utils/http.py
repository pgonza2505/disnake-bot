import asyncio, json, socket
import aiohttp

async def _get_json(url: str, *, headers: dict | None = None, timeout: int = 10, retries: int = 2):
    headers = headers or {}
    backoff = 0.6
    connector = aiohttp.TCPConnector(family=socket.AF_INET)  # IPv4 tends to be less cursed
    last_err = None

    for _ in range(retries + 1):
        try:
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status != 200:
                        await resp.read()
                        await asyncio.sleep(backoff); backoff *= 1.7
                        continue
                    try:
                        return await resp.json()
                    except aiohttp.ContentTypeError:
                        txt = await resp.text()
                        try:
                            return json.loads(txt)
                        except json.JSONDecodeError:
                            return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await asyncio.sleep(backoff); backoff *= 1.7
    return None
