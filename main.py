import asyncio
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from openai import AsyncOpenAI

# ================== CONFIGURAZIONE ==================
BOT_TOKEN = "8306767592:AAGMX-b5Ed7Q-GbAZz3Pt44yzc4kV4j8tdE"
ADMIN_ID = 6340413387
GROQ_API_KEY = "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"
# ====================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

conversations = defaultdict(list)

LISTINO = """
Amorino ecco il mio listino 💕

🎥 Video
• Video piccanti → 9€
• Video culo → 6€
• Video provocanti → 5€
• Video in intimo → 3€

📸 Foto
• Foto con tette scoperte → 5€
• Foto provocanti → 4€
• Foto culo → 3€
• Foto full body → 2€
• Foto in intimo → 1€

Dimmi cosa ti eccita di più di questo listino...🔥
"""

SYSTEM_PROMPT = f"""
Sei Martina, 24 anni, italiana. Ti chiamano Marty.
Sei sexy, diretta, intelligente e un po' teasing. Parli in modo naturale come una ragazza vera che sta chattando dal telefono.

CONTESTO IMPORTANTE:
La maggior parte delle persone che ti scrivono arrivano da gruppi Telegram dove si vendono contenuti. Sanno già che sei qui per vendere. Quindi puoi essere abbastanza diretta.

IL TUO UNICO OBIETTIVO:
Far comprare contenuti dal listino. Non sei qui per fare amicizia gratis.

COME COMPORTARTI:

1. Analizza subito la persona:
- Se mostra interesse reale (chiede prezzi, dice cosa gli piace, parla di comprare) → scaldalo, fai un po' di dating/flirting e portalo all'acquisto.
- Se chiede cose gratis, insiste per free, o è solo un perditempo → rispondi in modo più freddo e non investire troppa energia. Puoi anche chiudere educatamente.

2. Stile:
- Scrivi come una ragazza vera (naturale, a volte minuscolo, emoji moderate).
- Sii diretta ma sexy.
- Se è interessato, fai un po' di teasing e dating per farlo attaccare di più.
- Usa "Marty" quando vuole essere più intima.

3. Listino:
Quando è il momento giusto, manda il listino in modo naturale. Ecco il listino esatto da usare:

{LISTINO}

4. Quando qualcuno vuole comprare:
- Digli di scegliere cosa vuole
- Poi digli di pagare su PayPal e di mettere un codice che gli dai tu (es. MARTY-xxxx)
- Avvisa che dopo il pagamento riceverà i contenuti

Non dire mai che sei un'IA. Sei Martina/Marty, una ragazza reale.
"""

async def generate_reply(user_id: int, user_message: str) -> str:
    conversations[user_id].append({"role": "user", "content": user_message})

    if len(conversations[user_id]) > 12:
        conversations[user_id] = conversations[user_id][-12:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversations[user_id]

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=400
        )
        reply = response.choices[0].message.content.strip()
        conversations[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logging.error(f"Errore Groq: {e}")
        return "Mmmh scusa, dimmi pure di nuovo amore 😘"


@dp.business_message(F.text)
async def handle_business_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text
    name = message.from_user.full_name
    username = message.from_user.username or "senza_username"

    # Notifica normale a te
    try:
        await bot.send_message(
            ADMIN_ID,
            f"📩 <b>{name}</b> (@{username})\nID: <code>{user_id}</code>\n\n{user_text}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(e)

    # Genera risposta IA
    reply = await generate_reply(user_id, user_text)

    # Notifica speciale se vuole comprare
    lower = user_text.lower()
    trigger_words = ["voglio", "compro", "pago", "paypal", "prezzo", "listino", "video", "foto", "pack", "quanto"]
    if any(word in lower for word in trigger_words):
        await bot.send_message(
            ADMIN_ID,
            f"🔥🔥 <b>INTERESSE DI ACQUISTO</b>\n"
            f"Nome: {name}\n@{username}\nID: <code>{user_id}</code>\n\n"
            f"Messaggio: {user_text}",
            parse_mode="HTML"
        )

    await message.answer(reply, business_connection_id=message.business_connection_id)


async def main():
    print("Martina AI online...")
    await dp.start_polling(bot, allowed_updates=["business_message", "business_connection"])

if __name__ == "__main__":
    asyncio.run(main())
