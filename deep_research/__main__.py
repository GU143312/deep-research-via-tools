"""CLI entry point: python -m deep_research 'your research question'."""

import argparse
import asyncio
import sys

from .research_manager import ResearchManager


async def research(query: str, send_email: bool, recipient: str = ""):
    seen = 0
    async for update in ResearchManager().run(query, send_email, recipient):
        lines = update.status.splitlines()
        for line in lines[seen:]:
            print(line, flush=True)
        seen = len(lines)
    print("\nGenerated files:")
    for path in update.files:
        print(path)


def main():
    parser = argparse.ArgumentParser(description="Deep Research: orchestration via tools")
    parser.add_argument("query", help="The research question")
    parser.add_argument("--send-email", action="store_true", help="Send using configured SMTP")
    parser.add_argument("--recipient", default="", help="Recipient address for this run")
    args = parser.parse_args()
    try:
        asyncio.run(research(args.query, args.send_email, args.recipient))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(
            f"Research failed ({type(exc).__name__}). Check API/SMTP configuration. "
            "Partial results are in outputs/.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
