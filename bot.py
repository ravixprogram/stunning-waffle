import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, ADMIN_ID, WEBHOOK_URL
from database import init_db, save_message, get_stats, get_all_messages

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ========== КЛАВИАТУРЫ ==========

def main_menu_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать анонимно", callback_data="send_anon")],
        [InlineKeyboardButton(text="📋 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return kb

def admin_menu_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📨 Все сообщения", callback_data="all_messages")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ])
    return kb

def cancel_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])
    return kb

def reply_kb(message_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{message_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{message_id}")]
    ])
    return kb

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer(
            '👑 <b>Добро пожаловать в панель управления!</b>'
            'Здесь вы можете управлять анонимными сообщениями, '
            'смотреть статистику и настраивать бота.',
            reply_markup=admin_menu_kb()
        )
    else:
        await message.answer(
            '🎭 <b>Анонимные сообщения</b>'
            'Здесь вы можете отправить <b>полностью анонимное</b> сообщение. '
            'Ваше имя, никнейм и ID останутся в тайне.'
            'Напишите всё, что хотите сказать — без страха и ограничений.',
            reply_markup=main_menu_kb()
        )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        '📖 <b>Как пользоваться ботом:</b>'
        '1. Нажмите «✉️ Написать анонимно»'
        '2. Напишите ваше сообщение'
        '3. Нажмите «Отправить»'
        '<b>Важно:</b>'
        '• Максимум 4000 символов'
        '• Можно отправлять текст, фото, видео, голосовые, стикеры'
        '• Запрещено: спам, угрозы, незаконный контент'
        'Ваши данные <b>никогда</b> не передаются получателю.'
    )

@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    await message.answer(
        '📋 <b>Правила использования:</b>'
        '✅ <b>Разрешено:</b>'
        '• Честные отзывы и конструктивная критика'
        '• Вопросы и предложения'
        '• Поддержка и добрые слова'
        '❌ <b>Запрещено:</b>'
        '• Оскорбления и угрозы'
        '• Спам и флуд'
        '• Незаконный контент'
        '• Попытки деанонимизации'
        'Нарушители будут заблокированы.'
    )

# ========== CALLBACK ОБРАБОТЧИКИ ==========

@dp.callback_query(F.data == "send_anon")
async def send_anon(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '✍️ <b>Напишите ваше анонимное сообщение:</b>'
        'Можно отправить текст, фото, видео, голосовое или стикер.'
        'Ваши данные останутся в полной тайне.',
        reply_markup=cancel_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "rules")
async def show_rules(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '📋 <b>Правила использования:</b>'
        '✅ <b>Разрешено:</b>'
        '• Честные отзывы и конструктивная критика'
        '• Вопросы и предложения'
        '• Поддержка и добрые слова'
        '❌ <b>Запрещено:</b>'
        '• Оскорбления и угрозы'
        '• Спам и флуд'
        '• Незаконный контент'
        '• Попытки деанонимизации'
        'Нарушители будут заблокированы.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "help")
async def show_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '📖 <b>Как пользоваться ботом:</b>'
        '1. Нажмите «✉️ Написать анонимно»'
        '2. Напишите ваше сообщение'
        '3. Нажмите «Отправить»'
        '<b>Важно:</b>'
        '• Максимум 4000 символов'
        '• Можно отправлять текст, фото, видео, голосовые, стикеры'
        '• Запрещено: спам, угрозы, незаконный контент'
        'Ваши данные <b>никогда</b> не передаются получателю.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '🎭 <b>Анонимные сообщения</b>'
        'Здесь вы можете отправить <b>полностью анонимное</b> сообщение. '
        'Ваше имя, никнейм и ID останутся в тайне.'
        'Напишите всё, что хотите сказать — без страха и ограничений.',
        reply_markup=main_menu_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '❌ <b>Действие отменено</b>'
        'Ваше сообщение не было отправлено.',
        reply_markup=main_menu_kb()
    )
    await callback.answer("Отменено")

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    if len(message.text) > 4000:
        await message.answer(
            '⚠️ <b>Сообщение слишком длинное!</b>'
            'Максимальная длина — 4000 символов.'
        )
        return

    msg_id = await save_message(
        user_id=user_id,
        content_type="text",
        text=message.text,
        file_id=None
    )

    await message.answer(
        '✅ <b>Сообщение отправлено анонимно!</b>'
        'Ваше сообщение доставлено получателю. '
        'Ваши данные остались в полной тайне.',
        reply_markup=main_menu_kb()
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f'🎭 <b>Новое анонимное сообщение!</b>'
            f'📨 <b>Текст:</b>{message.text}'
            f'🆔 <b>ID сообщения:</b> <code>{msg_id}</code>'
            f'📅 <b>Время:</b> {message.date.strftime("%d.%m.%Y %H:%M")}',
            reply_markup=reply_kb(msg_id)
        )
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    photo = message.photo[-1]
    caption = message.caption or ""

    msg_id = await save_message(
        user_id=user_id,
        content_type="photo",
        text=caption,
        file_id=photo.file_id
    )

    await message.answer(
        '✅ <b>Фото отправлено анонимно!</b>',
        reply_markup=main_menu_kb()
    )

    try:
        await bot.send_photo(
            ADMIN_ID,
            photo=photo.file_id,
            caption=f'🎭 <b>Анонимное фото</b>'
                  f'📝 <b>Подпись:</b> {caption or "нет"}'
                  f'🆔 <b>ID:</b> <code>{msg_id}</code>',
            reply_markup=reply_kb(msg_id)
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")

@dp.message(F.video)
async def handle_video(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    video = message.video
    caption = message.caption or ""

    msg_id = await save_message(
        user_id=user_id,
        content_type="video",
        text=caption,
        file_id=video.file_id
    )

    await message.answer(
        '✅ <b>Видео отправлено анонимно!</b>',
        reply_markup=main_menu_kb()
    )

    try:
        await bot.send_video(
            ADMIN_ID,
            video=video.file_id,
            caption=f'🎭 <b>Анонимное видео</b>'
                  f'📝 <b>Подпись:</b> {caption or "нет"}'
                  f'🆔 <b>ID:</b> <code>{msg_id}</code>',
            reply_markup=reply_kb(msg_id)
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    voice = message.voice

    msg_id = await save_message(
        user_id=user_id,
        content_type="voice",
        text=None,
        file_id=voice.file_id
    )

    await message.answer(
        '✅ <b>Голосовое сообщение отправлено анонимно!</b>',
        reply_markup=main_menu_kb()
    )

    try:
        await bot.send_voice(
            ADMIN_ID,
            voice=voice.file_id,
            caption=f'🎭 <b>Анонимное голосовое</b>'
                  f'🆔 <b>ID:</b> <code>{msg_id}</code>',
            reply_markup=reply_kb(msg_id)
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")

@dp.message(F.sticker)
async def handle_sticker(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    sticker = message.sticker

    msg_id = await save_message(
        user_id=user_id,
        content_type="sticker",
        text=None,
        file_id=sticker.file_id
    )

    await message.answer(
        '✅ <b>Стикер отправлен анонимно!</b>',
        reply_markup=main_menu_kb()
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f'🎭 <b>Анонимный стикер</b>'
            f'🆔 <b>ID:</b> <code>{msg_id}</code>',
            reply_markup=reply_kb(msg_id)
        )
        await bot.send_sticker(ADMIN_ID, sticker=sticker.file_id)
    except Exception as e:
        logging.error(f"Ошибка: {e}")

# ========== АДМИН-ПАНЕЛЬ ==========

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return

    stats = await get_stats()

    await callback.message.edit_text(
        f'📊 <b>Статистика бота</b>'
        f'📨 Всего сообщений: <b>{stats["total"]}</b>'
        f'📝 Текстовых: <b>{stats["text"]}</b>'
        f'📷 Фото: <b>{stats["photo"]}</b>'
        f'🎥 Видео: <b>{stats["video"]}</b>'
        f'🎤 Голосовых: <b>{stats["voice"]}</b>'
        f'😊 Стикеров: <b>{stats["sticker"]}</b>'
        f'👥 Уникальных отправителей: <b>{stats["unique_senders"]}</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "all_messages")
async def show_all_messages(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return

    messages = await get_all_messages(limit=10)

    if not messages:
        text = '📭 <b>Сообщений пока нет</b>'
    else:
        text = '📨 <b>Последние сообщения:</b>'
        for msg in messages:
            text += f'🆔 <code>{msg["id"]}</code> | {msg["type"]} | {msg["date"]}'
            if msg['text']:
                preview = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
                text += f'   └ {preview}'
            text += ''

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="all_messages")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_admin")
async def back_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        '👑 <b>Панель управления</b>'
        'Выберите действие:',
        reply_markup=admin_menu_kb()
    )
    await callback.answer()

# ========== ОТВЕТЫ И УДАЛЕНИЕ ==========

@dp.callback_query(F.data.startswith("reply_"))
async def reply_to_message(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return

    msg_id = int(callback.data.split("_")[1])

    await callback.message.edit_text(
        f'💬 <b>Ответ на сообщение #{msg_id}</b>'
        f'Напишите ваш ответ. Он будет отправлен анонимно отправителю.',
        reply_markup=cancel_kb()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_message(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return

    msg_id = int(callback.data.split("_")[1])

    await callback.message.edit_text(
        f'🗑 <b>Сообщение #{msg_id} удалено</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ])
    )
    await callback.answer("Удалено")

# ========== WEB SERVER (для Render) ==========

async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# ========== ЗАПУСК ==========

async def main():
    await init_db()

    # Запускаем веб-сервер для keep-alive
    asyncio.create_task(start_web_server())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
