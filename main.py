import logging
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

import store
import formatters


logger = logging.getLogger(__name__)

CHOICE, PRODUCT, CART, CHECKOUT = "101 102 103 104".split()


def start(update, context):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=_id)]
        for name, _id in context.bot_data["products"].items()
    ]
    keyboard.append([InlineKeyboardButton("Shopping cart", callback_data=CART)])
    context.user_data["menu"] = InlineKeyboardMarkup(keyboard)

    update.effective_message.reply_text(
        "Please choose:", reply_markup=context.user_data["menu"]
    )
    db = context.bot_data["db"]
    db.set(update.effective_user.id, CHOICE)


def handle_users_reply(update, context):
    state_handlers = {
        CHOICE: handle_menu_choice,
        PRODUCT: handle_product_card,
        CART: handle_cart,
        CHECKOUT: handle_checkout,
    }
    db = context.bot_data["db"]
    user_state = db.get(update.effective_user.id).decode()
    handler = state_handlers[user_state]
    next_state = handler(update, context)
    db.set(update.effective_user.id, next_state)


def handle_menu_choice(update, context):
    query = update.callback_query
    query.answer()

    if query.data == CART:
        return handle_cart(update, context)

    product = store.get_product(query.data)
    picture = store.get_file_link(product["relationships"]["main_image"]["data"]["id"])
    caption = formatters.make_caption(product)

    keyboard = [
        [
            InlineKeyboardButton(f"{x} kg", callback_data=f"{query.data} {x}")
            for x in [1, 5, 10]
        ],
        [InlineKeyboardButton("Menu", callback_data=CHOICE)],
        [InlineKeyboardButton("Shopping cart", callback_data=CART)],
    ]
    update.effective_message.delete()
    update.effective_message.reply_photo(
        picture, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PRODUCT


def handle_product_card(update, context):
    query = update.callback_query
    query.answer()

    if query.data == CHOICE:
        update.effective_message.delete()
        update.effective_message.reply_text(
            "Please choose:", reply_markup=context.user_data["menu"]
        )
        return CHOICE
    if query.data == CART:
        return handle_cart(update, context)

    prod_id, prod_qty = query.data.split()
    store.add_to_cart(update.effective_user.id, prod_id, prod_qty)
    return PRODUCT


def handle_cart(update, context):
    query = update.callback_query
    query.answer()

    if query.data == CHOICE:
        return handle_product_card(update, context)
    if query.data == CHECKOUT:
        update.effective_message.delete()
        update.effective_message.reply_text("Please enter your email:")
        return CHECKOUT
    if query.data != CART:
        store.remove_from_cart(update.effective_user.id, query.data)

    cart = store.get_cart_items(update.effective_user.id)
    content = formatters.make_cart_repr(cart)

    keyboard = [
        [InlineKeyboardButton(f'Remove {p["name"]}', callback_data=p["id"])]
        for p in cart["data"]
    ]
    keyboard.append([InlineKeyboardButton("Menu", callback_data=CHOICE)])
    keyboard.append([InlineKeyboardButton("Checkout", callback_data=CHECKOUT)])

    update.effective_message.delete()
    update.effective_message.reply_text(
        content, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CART


def handle_checkout(update, context):
    name = update.effective_message.chat.first_name
    email = update.effective_message.text

    if not store.find_customer(email):
        store.create_customer(name, email)

    update.effective_message.reply_text(
        "Thank You!", reply_markup=context.user_data["menu"]
    )
    return CHOICE


def error(update, context):
    logger.error(f'Update "{update}" caused error "{context.error}"')


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    load_dotenv()

    updater = Updater(os.environ["TELEGRAM_TOKEN"])
    dispatcher = updater.dispatcher

    dispatcher.bot_data["db"] = redis.Redis(
        host=os.environ["REDIS_ENDPOINT"],
        port=os.environ["REDIS_PORT"],
        password=os.environ["REDIS_PASSWORD"],
    )
    dispatcher.bot_data["products"] = store.get_products()

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
