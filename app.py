import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

# ====================================================================
# 1. SECURITY AND SETUP CONFIGURATION
# ====================================================================

# This must be set on the hosting service as a SECRET VARIABLE
# (I will show you where to put this later)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") 

# YOUR UNIQUE USER ID - Only this ID can use the bot!
# --------------------------------------------------------------------
AUTHORIZED_USER_ID = 6629263251
# --------------------------------------------------------------------

# In-memory storage for the workout history.
# NOTE: This data will be LOST every time the bot restarts on the server.
# For permanent storage, a database is required (we can upgrade later!)
WORKOUT_HISTORY = {}

def authorized(func):
    """Decorator to ensure only the authorized user can run a command."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != AUTHORIZED_USER_ID:
            print(f"Unauthorized access attempt by user ID: {update.effective_user.id}")
            await update.message.reply_text("⛔️ Access Denied. This bot is private.")
            return
        await func(update, context)
    return wrapper

# ====================================================================
# 2. BOT COMMANDS (WORKOUT TRACKER)
# ====================================================================

@authorized
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting when the command /start is issued."""
    await update.message.reply_text(
        f"👋 Welcome back, {update.effective_user.first_name}! I'm your private Workout Tracker.\n"
        "Use /log followed by your workout details to save an entry.\n"
        "Try: /log 45m weightlifting, 10 min cardio"
    )

@authorized
async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs the user's workout and saves it to the history."""
    
    # The workout text is everything after the /log command
    workout_entry = ' '.join(context.args)
    
    if not workout_entry:
        await update.message.reply_text(
            "📝 Please tell me what you did! Example: /log 30m run, 3 sets of 10 pull-ups"
        )
        return

    # Use the current time as the unique key
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    WORKOUT_HISTORY[timestamp] = workout_entry

    await update.message.reply_text(
        f"✅ Workout logged successfully on **{timestamp}**:\n*{workout_entry}*",
        parse_mode="Markdown"
    )

@authorized
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the last 5 workout entries."""
    if not WORKOUT_HISTORY:
        await update.message.reply_text("⏳ Your workout history is currently empty. Use /log to add an entry!")
        return
    
    # Get the last 5 entries (newest first)
    history_list = list(WORKOUT_HISTORY.items())
    latest_entries = history_list[-5:]
    
    response = "🗓 **Your Latest Workout History:**\n\n"
    for timestamp, entry in reversed(latest_entries):
        response += f"• **{timestamp}:** {entry}\n"
        
    response += "\n*Note: This history is temporary (in-memory storage) and resets when the server restarts.*"
    
    await update.message.reply_text(response, parse_mode="Markdown")

@authorized
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the entire in-memory workout history."""
    WORKOUT_HISTORY.clear()
    await update.message.reply_text("🗑 Workout history has been cleared.")

# ====================================================================
# 3. MAIN FUNCTION
# ====================================================================

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Register all command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Ignore all other text messages, since we only care about commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, authorized(lambda update, context: None)))

    # Start the Bot using polling (regularly asking Telegram for updates)
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
