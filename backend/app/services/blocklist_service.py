"""Checking whether the domain or its sending addresses have been listed.

A blocklist entry is one of the few reputation problems that is both sudden
and invisible: mail simply stops arriving somewhere, with no bounce anybody
reads. A daily lookup is cheap and turns that into something the trust panel
shows the next morning.

Lookups are plain DNS — no account, no key, no vendor. A listed target
resolves inside the list's zone; an unlisted one does not resolve at all.
"""
import asyncio
import logging
import socket

logger = logging.getLogger(__name__)

# Zones that take a domain name directly.
DOMAIN_LISTS = (
    "dbl.spamhaus.org",
    "multi.surbl.org",
)

# Zones that take a reversed IPv4 address.
IP_LISTS = (
    "zen.spamhaus.org",
    "b.barracudacentral.org",
    "bl.spamcop.net",
)

# Spamhaus answers in 127.255.255.0/24 to say "we are refusing this query",
# not "this target is listed" — which is what happens when lookups come from
# a public resolver like Google's rather than the network's own. Reading that
# as a listing would report the domain as blocklisted everywhere, every day,
# for a configuration reason that has nothing to do with reputation.
REFUSAL_PREFIX = "127.255.255."

DNS_TIMEOUT_SECONDS = 5.0


class BlocklistError(Exception):
    """The lookup could not be completed. Distinct from "not listed"."""


def reverse_ipv4(ip: str) -> str:
    parts = ip.strip().split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        raise BlocklistError(f"Not an IPv4 address: {ip}")
    return ".".join(reversed(parts))


async def _resolve(name: str) -> list[str]:
    """Addresses `name` resolves to, or an empty list when it does not exist.

    NXDOMAIN is the normal answer for an unlisted target, so it is not an
    error — it is the result.
    """
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.getaddrinfo(name, None, family=socket.AF_INET),
            timeout=DNS_TIMEOUT_SECONDS,
        )
    except (socket.gaierror, asyncio.TimeoutError):
        return []
    return sorted({info[4][0] for info in infos})


async def check_domain(domain: str, zone: str) -> dict:
    answers = await _resolve(f"{domain.strip().lower()}.{zone}")
    return _interpret(domain, zone, answers)


async def check_ip(ip: str, zone: str) -> dict:
    answers = await _resolve(f"{reverse_ipv4(ip)}.{zone}")
    return _interpret(ip, zone, answers)


def _interpret(target: str, zone: str, answers: list[str]) -> dict:
    if not answers:
        return {"target": target, "blocklist": zone, "listed": False, "response": ""}
    if any(a.startswith(REFUSAL_PREFIX) for a in answers):
        # Reported as an error rather than a listing, so a resolver problem
        # never shows up on the trust panel as a reputation problem.
        logger.warning("%s refused the query for %s (public resolver?)", zone, target)
        return {
            "target": target, "blocklist": zone, "listed": False,
            "response": f"query refused ({answers[0]})", "error": True,
        }
    return {
        "target": target, "blocklist": zone, "listed": True,
        "response": ",".join(answers),
    }


async def check_all(*, domains: list[str], ips: list[str]) -> list[dict]:
    """Every list against every target, concurrently.

    These are independent DNS lookups with nothing shared between them, so
    running them in sequence would just multiply the timeout by the number of
    checks for no benefit.
    """
    tasks = []
    for domain in domains:
        tasks.extend(check_domain(domain, zone) for zone in DOMAIN_LISTS)
    for ip in ips:
        tasks.extend(check_ip(ip, zone) for zone in IP_LISTS)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("blocklist lookup failed: %s", result)
            continue
        out.append(result)
    return out
