from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from assistant.utils.config import TELEGRAM_TOKEN
from assistant.utils import state
from assistant.modules import news, research, sysinfo, scheduler
from assistant.modules import email as email_mod
from assistant.router import route


# ---------------------------------------------------------------------------
# Pause guard — wraps every handler
# ---------------------------------------------------------------------------

async def _paused_reply(update: Update) -> bool:
    """Sends a paused notice and returns True if the bot is currently paused."""
    if state.is_paused():
        reason = state.get_pause_reason()
        await update.message.reply_text(
            f"Bot is paused: {reason}\n\nUse /resume to override."
        )
        return True
    return False


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.register_chat(update.effective_chat.id)
    await update.message.reply_text(
        "Assistant is online. Use /help to see available commands."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Available commands:\n\n"
        "/papers [topic]     — 5 newest arXiv papers (topic or saved list)\n"
        "/settopics t1, t2   — Set your research topics\n"
        "/topics             — Show current research topics\n"
        "/news [category]    — Headlines (world, tech, science, us, business)\n"
        "/inbox              — Check unread emails\n"
        "/send to sub body   — Send an email\n"
        "/sysinfo            — CPU / RAM / disk / temp\n"
        "/digest             — Trigger the daily digest now\n"
        "/pause              — Manually pause the bot\n"
        "/resume             — Resume the bot\n"
        "/status             — Show pause state + system info\n"
        "/help               — This message"
    )
    await update.message.reply_text(text)


async def cmd_papers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    query = ' '.join(context.args).strip()
    if query:
        response = research.handle(query)
    else:
        topics = research.load_topics()
        if not topics:
            response = "No topics saved and no query given.\nUse /settopics or /papers <topic>."
        else:
            parts = []
            for topic in topics:
                papers = research.get_papers(topic, max_results=5)
                if papers:
                    parts.append(f"[{topic.upper()}]\n" + research.format_papers(papers))
            response = '\n\n'.join(parts) if parts else "No papers found."
    await update.message.reply_text(response)


async def cmd_settopics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = ' '.join(context.args)
    await update.message.reply_text(research.set_topics(args))


async def cmd_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(research.list_topics())


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    category = context.args[0] if context.args else 'general'
    await update.message.reply_text(news.format_headlines(category))


async def cmd_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    await update.message.reply_text(email_mod.inbox())


async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /send <to> <subject> <body>")
        return
    to, subject, *body_parts = context.args
    await update.message.reply_text(email_mod.send(to, subject, ' '.join(body_parts)))


async def cmd_sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(sysinfo.handle())


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.register_chat(update.effective_chat.id)
    await update.message.reply_text("Generating digest...")
    await scheduler.daily_digest()


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = ' '.join(context.args) or "manually paused"
    state.pause(reason)
    await update.message.reply_text(f"Bot paused: {reason}\n\nUse /resume to unpause.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.resume()
    await update.message.reply_text("Bot resumed.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_paused():
        status = f"PAUSED — {state.get_pause_reason()}"
    else:
        status = "Running"
    await update.message.reply_text(f"Status: {status}\n\n" + sysinfo.handle())


# ---------------------------------------------------------------------------
# Fallback plain-text handler
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_paused():
        await update.message.reply_text(
            f"Bot is paused: {state.get_pause_reason()}\n\nUse /resume to override."
        )
        return
    state.register_chat(update.effective_chat.id)
    response = route(update.message.text)
    await update.message.reply_text(response)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _post_init(app):
    """Called by PTB after the event loop starts — safe to start async scheduler here."""
    scheduler.init(app)


def run_bot():
    state.load_chat_ids()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CommandHandler("papers",     cmd_papers))
    app.add_handler(CommandHandler("settopics",  cmd_settopics))
    app.add_handler(CommandHandler("topics",     cmd_topics))
    app.add_handler(CommandHandler("news",       cmd_news))
    app.add_handler(CommandHandler("inbox",      cmd_inbox))
    app.add_handler(CommandHandler("send",       cmd_send))
    app.add_handler(CommandHandler("sysinfo",    cmd_sysinfo))
    app.add_handler(CommandHandler("digest",     cmd_digest))
    app.add_handler(CommandHandler("pause",      cmd_pause))
    app.add_handler(CommandHandler("resume",     cmd_resume))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Assistant is running...")
    app.run_polling()
