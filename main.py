import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

import formatters
import store

logger = logging.getLogger(__name__)

MENU, PRODUCT, CART, CHECKOUT = "100 101 102 103".split()


def start(update, context):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=_id)]
        for name, _id in store.get_products().items()
    ]
    keyboard.append([InlineKeyboardButton("Shopping cart", callback_data=CART)])

    context.user_data["menu"] = InlineKeyboardMarkup(keyboard)
    return show_menu(update, context)


def show_menu(update, context):
    update.effective_message.delete()
    update.effective_message.reply_text(
        "Please choose:", reply_markup=context.user_data["menu"]
    )


def handle_menu_choice(update, context):
    query = update.callback_query
    query.answer()

    product = store.get_product(query.data)
    picture = store.get_file_link(product["relationships"]["main_image"]["data"]["id"])
    caption = formatters.make_caption(product)

    keyboard = [
        [
            InlineKeyboardButton(f"{x} kg", callback_data=f"{PRODUCT} {query.data} {x}")
            for x in [1, 5, 10]
        ],
        [InlineKeyboardButton("Menu", callback_data=MENU)],
        [InlineKeyboardButton("Shopping cart", callback_data=CART)],
    ]
    update.effective_message.delete()
    update.effective_message.reply_photo(
        picture, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_to_cart(update, context):
    query = update.callback_query
    query.answer()

    _, prod_id, prod_qty = query.data.split()
    store.add_to_cart(update.effective_user.id, prod_id, prod_qty)


def handle_cart(update, context):
    query = update.callback_query
    query.answer()
    if query.data != CART:
        _, product = query.data.split()
        store.remove_from_cart(update.effective_user.id, product)

    cart = store.get_cart_items(update.effective_user.id)
    content = formatters.make_cart_repr(cart)

    keyboard = [
        [InlineKeyboardButton(f'Remove {p["name"]}', callback_data=f'{CART} {p["id"]}')]
        for p in cart["data"]
    ]
    keyboard.append([InlineKeyboardButton("Menu", callback_data=MENU)])
    keyboard.append([InlineKeyboardButton("Checkout", callback_data=CHECKOUT)])

    update.effective_message.delete()
    update.effective_message.reply_text(
        content, reply_markup=InlineKeyboardMarkup(keyboard)
    )


def handle_checkout(update, context):
    if not (query := update.callback_query):
        name = update.effective_message.chat.first_name
        email = update.effective_message.text

        if not store.find_customer(email):
            store.create_customer(name, email)

        update.effective_message.reply_text("Thank you!")
        return show_menu(update, context)

    query.answer()
    update.effective_message.delete()
    update.effective_message.reply_text("Please enter your email:")


def error(update, context):
    logger.error(f'Update "{update}" caused error "{context.error}"')


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    load_dotenv()

    updater = Updater(os.environ["BOT_TOKEN"])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(show_menu, pattern=MENU))
    dispatcher.add_handler(CallbackQueryHandler(add_to_cart, pattern=PRODUCT))
    dispatcher.add_handler(CallbackQueryHandler(handle_cart, pattern=CART))
    dispatcher.add_handler(CallbackQueryHandler(handle_checkout, pattern=CHECKOUT))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu_choice))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_checkout))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
