from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

ADMIN_ID = 1719767885  # Remplace par ton ID Telegram
TOKEN = "8425592604:AAEyj5zoSaMfbgefieQGtDoTtq4d-fGzLCM"

# Liste des quiz
quizzes = []  # Chaque quiz est un dict avec question, options, bonne_reponse
user_sessions = {}  # Pour suivre la progression des utilisateurs


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue ! Tape 'commence' pour faire le quiz.")


# /quiz - Ajout d’un quiz par l’admin
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Tu n'es pas autorisé à ajouter des quiz.")
        return

    lines = update.message.text.strip().split("\n")[1:]
    if len(lines) < 3:
        await update.message.reply_text("❌ Format invalide.")
        return

    question = lines[0]
    options = []
    bonne_reponse = None

    for line in lines[1:]:
        if line.lower().startswith("réponse:"):
            bonne_reponse = line.split(":")[1].strip()
        else:
            options.append(line)

    if not bonne_reponse or not options:
        await update.message.reply_text("❌ Format invalide (réponse manquante ou options).")
        return

    quizzes.append({
        "question": question,
        "options": options,
        "bonne_reponse": bonne_reponse
    })

    await update.message.reply_text("✅ Quiz ajouté avec succès !")


# /delete - Supprimer tous les quiz
async def delete_quizzes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Tu n'es pas autorisé.")
        return

    quizzes.clear()
    await update.message.reply_text("🗑️ Tous les quiz ont été supprimés.")


# Réception du mot "commence"
async def start_quiz_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not quizzes:
        await update.message.reply_text("Aucun quiz disponible.")
        return

    user_sessions[user_id] = {
        "index": 0,
        "score": 0,
        "total": len(quizzes),
        "reponses": []
    }
   
    await send_next_quiz(update, context)


async def send_next_quiz(update, context):
    # Gérer selon que 'update' soit un message ou un CallbackQuery
    if isinstance(update, Update):
        user_id = update.effective_user.id
        send = update.message.reply_text
    else:
        user_id = update.from_user.id
        send = update.message.reply_text

    session = user_sessions.get(user_id)

    if not session or session["index"] >= session["total"]:
        bonnes = session["score"]
        mauvaises = session["total"] - bonnes
        await send(f"🎯 Quiz terminé !\n✅ Bonnes réponses : {bonnes}\n❌ Mauvaises réponses : {mauvaises}")
        user_sessions.pop(user_id)
        return

    current_quiz = quizzes[session["index"]]
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"{session['index']}|{opt.split(')')[0].strip()}")]
        for opt in current_quiz["options"]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send(current_quiz["question"], reply_markup=reply_markup)
# Réception du clic utilisateur
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await query.edit_message_text("Session expirée ou invalide.")
        return

    payload = query.data.split("|")
    index = int(payload[0])
    user_choice = payload[1]

    current_quiz = quizzes[index]
    bonne_reponse = current_quiz["bonne_reponse"]

    if user_choice == bonne_reponse:
        session["score"] += 1
        await query.edit_message_text("✅ Bonne réponse !")
    else:
        await query.edit_message_text(f"❌ Mauvaise réponse. La bonne réponse était : {bonne_reponse}")

    session["index"] += 1
    await send_next_quiz(query, context)


# Lancer l'application
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("delete", delete_quizzes))
    app.add_handler(MessageHandler(filters.Regex("(?i)^commence$"), start_quiz_for_user))
    app.add_handler(CallbackQueryHandler(handle_answer))

    print("🤖 Bot en ligne.")
    app.run_polling()
