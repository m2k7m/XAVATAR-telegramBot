import asyncio
import contextlib
import json
import logging
import os

import git
from dotenv import load_dotenv
from pyrogram import Client, idle

from storage import setup_database

load_dotenv()

with open("lang.json", "r", encoding="utf-8") as f:
    lang = json.load(f)

with open("supportedFormats.json", "r", encoding="utf-8") as f:
    supported_formats = json.load(f)


def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill in your values."
        )
    return value


API_ID = int(env("API_ID"))
API_HASH = env("API_HASH")
BOT_TOKEN = env("BOT_TOKEN")
ownerID = int(env("OWNER_ID"))

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()


class CustomFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        fmt = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        fmt = fmt.replace("(black)", self.black + self.bold)
        fmt = fmt.replace("(reset)", self.reset)
        fmt = fmt.replace("(levelcolor)", log_color)
        fmt = fmt.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(
    CustomFormatter("%(asctime)s - %(name)s - %(levellevel)s - %(message)s")
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[stdout_handler],
)


async def main():
    app = Client(
        "PS4AVATARS",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins={"root": "Plugins"},
    )

    try:
        git.Repo()
    except git.exc.InvalidGitRepositoryError:
        if not GITHUB_REPO_URL:
            logging.warning(
                "GITHUB_REPO_URL is not set. Skipping repository initialization."
            )
        else:
            repo_url = GITHUB_REPO_URL
            if GITHUB_TOKEN and repo_url.startswith("https://"):
                repo_url = repo_url.replace(
                    "https://", f"https://{GITHUB_TOKEN}@", 1
                )
            repo = git.Repo.init()
            origin = repo.create_remote("origin", repo_url)
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)

    logging.info("Git initialized successfully.")

    await setup_database()

    logging.info("Databases initialized successfully.")
    await app.start()
    logging.info("Bot has started.")

    await idle()
    await app.stop()
    logging.info("Bot has stopped.")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        try:
            import uvloop  # type: ignore

            uvloop.install()
        except ImportError:
            logging.warning("uvloop not installed. Install with: pip install uvloop")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(main())
        except (KeyboardInterrupt, SystemExit):
            logging.info("Bot was stopped.")
