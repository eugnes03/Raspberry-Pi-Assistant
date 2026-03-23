from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from assistant.utils.config import TELEGRAM_TOKEN
from assistant.utils import state, conversation
from assistant.modules import news, research, sysinfo, scheduler, quotes, qrcode_gen, wiki, saved_papers
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
        "/papers [topic/cat]  — 5 newest arXiv papers (topic, category like math.AG, or saved list)\n"
        "/save <url>          — Save an arXiv paper to your library\n"
        "/saved               — List saved papers\n"
        "/unsave <# or id>    — Remove a saved paper\n"
        "/abstract <url>      — Raw abstract of one arXiv paper (no AI)\n"
        "/summarize <url>     — AI summary of one arXiv paper (uses full HTML when available)\n"
        "/ask <question>      — Follow-up on the last summarized paper\n"
        "/settopics t1, t2    — Set your research topics\n"
        "/topics              — Show current research topics\n"
        "/news [category]     — Headlines (world, tech, science, us, business)\n"
        "/wiki <query>        — Wikipedia summary\n"
        "/quote               — Random philosophy quote\n"
        "/qr <text or url>    — Generate a QR code image\n"
        "/inbox               — Check unread emails\n"
        "/send to sub body    — Send an email\n"
        "/sysinfo             — CPU / RAM / disk / temp\n"
        "/digest              — Trigger the daily digest now\n"
        "/pause               — Manually pause the bot\n"
        "/resume              — Resume the bot\n"
        "/status              — Show pause state + system info\n"
        "/help                — This message"
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


async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(quotes.format_quote())


async def cmd_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    data = ' '.join(context.args).strip()
    if not data:
        await update.message.reply_text("Usage: /qr <text or URL>")
        return
    buf = qrcode_gen.generate(data)
    if buf is None:
        await update.message.reply_text("Failed to generate QR code. Make sure qrcode[pil] is installed.")
        return
    await update.message.reply_photo(photo=buf, caption=data)


async def cmd_wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    query = ' '.join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /wiki <search term>")
        return
    await update.message.reply_text("Searching Wikipedia...")
    result = wiki.search(query)
    await update.message.reply_text(result)


async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    url = ' '.join(context.args).strip()
    if not url:
        await update.message.reply_text("Usage: /summarize <arxiv URL>\nExample: /summarize https://arxiv.org/abs/2301.12345")
        return
    from assistant.utils.config import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        await update.message.reply_text("OpenAI API key not set. Add OPENAI_API_KEY to your .env file.")
        return
    await update.message.reply_text("Fetching paper...")
    paper = research.get_paper_by_id(url)
    if paper is None:
        await update.message.reply_text("Could not find that paper. Make sure the URL contains a valid arXiv ID (e.g. 2301.12345).")
        return
    # Try to get full HTML text; fall back to abstract
    full_text = research.fetch_paper_full_text(paper["arxiv_id"])
    is_full = full_text is not None
    content = full_text if is_full else paper["summary"]
    await update.message.reply_text("Summarizing" + (" full paper..." if is_full else " abstract (HTML version unavailable)..."))
    try:
        from assistant.utils.openai_client import start_paper_thread
        thread_id, summary = start_paper_thread(content, is_full_text=is_full)
    except Exception as e:
        await update.message.reply_text(f"OpenAI error: {e}")
        return
    conversation.set_thread(update.effective_chat.id, thread_id)
    await update.message.reply_text(f"{summary}\n\nUse /ask <question> to ask about theorems, proofs, or concepts in this paper.")


async def cmd_abstract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    url = ' '.join(context.args).strip()
    if not url:
        await update.message.reply_text("Usage: /abstract <arxiv URL>\nExample: /abstract https://arxiv.org/abs/2301.12345")
        return
    await update.message.reply_text("Fetching paper...")
    paper = research.get_paper_by_id(url)
    if paper is None:
        await update.message.reply_text("Could not find that paper. Make sure the URL contains a valid arXiv ID.")
        return
    authors = ', '.join(paper['authors'][:3])
    text = f"{paper['title']}\n{authors}\n\n{paper['summary']}\n\n{paper['link']}"
    await update.message.reply_text(text)


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    question = ' '.join(context.args).strip()
    if not question:
        await update.message.reply_text("Usage: /ask <question>\nExample: /ask What theorem does this paper prove?")
        return
    thread_id = conversation.get_thread(update.effective_chat.id)
    if not thread_id:
        await update.message.reply_text("No active paper session. Use /summarize <arxiv URL> first.")
        return
    try:
        from assistant.utils.openai_client import ask_thread
        answer = ask_thread(thread_id, question)
    except Exception as e:
        await update.message.reply_text(f"OpenAI error: {e}")
        return
    await update.message.reply_text(answer)


async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _paused_reply(update):
        return
    url = ' '.join(context.args).strip()
    if not url:
        await update.message.reply_text("Usage: /save <arxiv URL>")
        return
    await update.message.reply_text("Fetching paper...")
    paper = research.get_paper_by_id(url)
    if paper is None:
        await update.message.reply_text("Could not find that paper. Check the arXiv URL.")
        return
    await update.message.reply_text(saved_papers.save_paper(paper))


async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(saved_papers.list_papers())


async def cmd_unsave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arg = ' '.join(context.args).strip()
    if not arg:
        await update.message.reply_text("Usage: /unsave <number or arXiv ID>\nSee /saved for the list.")
        return
    await update.message.reply_text(saved_papers.remove_paper(arg))


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
    app.add_handler(CommandHandler("quote",      cmd_quote))
    app.add_handler(CommandHandler("qr",         cmd_qr))
    app.add_handler(CommandHandler("wiki",       cmd_wiki))
    app.add_handler(CommandHandler("abstract",   cmd_abstract))
    app.add_handler(CommandHandler("summarize",  cmd_summarize))
    app.add_handler(CommandHandler("ask",        cmd_ask))
    app.add_handler(CommandHandler("save",       cmd_save))
    app.add_handler(CommandHandler("saved",      cmd_saved))
    app.add_handler(CommandHandler("unsave",     cmd_unsave))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Assistant is running...")
    app.run_polling()
