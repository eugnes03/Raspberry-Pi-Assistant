import html as html_lib
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.constants import ParseMode
from assistant.modules import news, sysinfo, research, quotes
from assistant.utils import state
from assistant.utils.logger import setup_logger

logger = setup_logger()

scheduler = AsyncIOScheduler()
_app = None


def init(app):
    """Call once at startup, passing the Telegram Application instance."""
    global _app
    _app = app

    scheduler.add_job(daily_digest,   'cron',     hour=8, minute=0, id='daily_digest',  replace_existing=True)
    scheduler.add_job(monitor_system, 'interval', minutes=2,        id='sys_monitor',   replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started (digest @ 08:00, monitor every 2 min)")


MAX_MSG = 4000  # Telegram limit is 4096; stay under it


async def _send_all(text: str):
    if not _app:
        return
    chunks = [text[i:i + MAX_MSG] for i in range(0, len(text), MAX_MSG)]
    for chat_id in state.get_chat_ids():
        for chunk in chunks:
            try:
                await _app.bot.send_message(chat_id=chat_id, text=chunk, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")


async def daily_digest():
    logger.info("Running daily digest")
    q = quotes.get_quote()
    header = (
        f"Good morning! Here is your Daily Digest\n\n"
        f'<i>"{html_lib.escape(q["text"])}"</i>\n'
        f"— {html_lib.escape(q['author'])}"
    )
    await _send_all(header)

    # News — one message per category
    for category in ['world', 'tech', 'science']:
        items = news.fetch_headlines(category, count=5)
        if items:
            block = f"<b>{category.capitalize()} News</b>\n\n"
            for i, item in enumerate(items, 1):
                title = html_lib.escape(item['title'])
                link  = item['link']
                block += f"{i}. <a href=\"{link}\">{title}</a>\n"
            await _send_all(block)

    # Research papers — one message per topic
    topics = research.load_topics()
    if topics:
        for topic in topics:
            papers = research.get_papers(topic, max_results=5)
            if papers:
                block = f"<b>Papers: {html_lib.escape(topic.title())}</b>\n\n"
                for p in papers:
                    title   = html_lib.escape(p['title'])
                    authors = html_lib.escape(', '.join(p['authors'][:3]))
                    link    = p['link']
                    block  += f"• <a href=\"{link}\">{title}</a>\n  {authors}\n\n"
                await _send_all(block)
    else:
        await _send_all("No research topics set. Use /settopics topic1, topic2 to configure.")

    # System status
    await _send_all("<b>System</b>\n\n" + html_lib.escape(sysinfo.handle()))


async def monitor_system():
    stats = sysinfo.get_stats()
    warnings = sysinfo.check_thresholds(stats)

    if warnings and not state.is_paused():
        reason = "; ".join(warnings)
        state.pause(reason)
        logger.warning(f"Auto-pausing: {reason}")
        msg = "<b>Bot auto-paused due to system stress</b>\n\n"
        msg += "\n".join(f"  \u26a0\ufe0f {html_lib.escape(w)}" for w in warnings)
        msg += "\n\nThe bot will resume automatically when metrics return to normal."
        msg += "\nYou can also use /resume to override."
        await _send_all(msg)

    elif state.is_paused() and not warnings:
        state.resume()
        logger.info("Auto-resuming: system back to normal")
        await _send_all("System back to normal. Bot resumed.\n\n" + html_lib.escape(sysinfo.handle()))
