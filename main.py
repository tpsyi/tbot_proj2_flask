# import statements
import datetime
import logging
import re
import hashlib
import os

from sqlalchemy import func
from database.tabledef import db_User, Order, Meal
from database import db_util
from telegram import *
from telegram.ext import *

import config
import paginator
import localizations.en as loc_en  # Import english localization
import localizations.ru as loc_ru  # Import russian localization


# logging is not widely used here, but i snatched this anyway.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
bot = Bot(config.TELEGRAM_TOKEN)
datetime = datetime.datetime

# default value for language
lang = loc_en

# initialize updater, dispatcher, setup conversation states
updater = Updater(token=config.TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
LANG_CHOICE, REGISTER, REGISTER_FINAL, CONTACT_CHOICE, CONTACT_TYPE_IN, PASSWORD_CHECK, CHEF_CHECK, CHEF_PASS_CHECK,\
 CHEF_MAIN, CHEF_EDIT_MENU, CHEF_NEW_MEAL, MAIN = range(12)


# yoink, code i borrowed from internet, splits array into smaller arrays with desired overlap
def split_overlap(array, size, overlap):
    result = []
    while True:
        if len(array) <= size:
            result.append(array)
            return result
        else:
            result.append(array[:size])
            array = array[size - overlap:]

def gen_hash_pass(password: str, s_length: int, k_length: int, i_amount: int):
    salt = os.urandom(s_length)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, i_amount, k_length)
    return salt+key

def check_hash_pass(password: str, comp_key_param, s_length: int, k_length: int, i_amount: int):
    c_salt = comp_key_param[:s_length]
    c_key = comp_key_param[s_length:]
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), c_salt, i_amount, k_length)
    return key == c_key


# what happens after '/start'
def start_command(update: Update, context: CallbackContext):
    update.message.reply_text(text='👋')
    reply_keyboard = [['🇬🇧English', '🇷🇺Русский']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("💬❓ ", reply_markup=markup)
    context.user_data['cart'] = []  # Initialize cart for each user
    context.user_data['id'] = update.effective_chat.id  # Write down user id for later
    return LANG_CHOICE


# happens after language was chosen
def language_chosen(update: Update, context: CallbackContext):
    global lang
    response = update.message.text
    if response == "🇬🇧English":
        lang = loc_en
    elif response == "🇷🇺Русский":
        lang = loc_ru

    context.bot.send_message(chat_id=update.effective_chat.id, text=lang.GREETING)
    local_session = db_util.Session()
    if local_session.query(db_User).filter(db_User.id == update.effective_chat.id).all():
        # if user is in database skip to choosing contact phone
        if local_session.query(db_User).filter(db_User.id == update.effective_chat.id).first().is_chef:
            # if user is chef ask which mode to proceed in
            r_keyboard = [[lang.CHEF0, lang.CHEF1]]
            update.message.reply_text(lang.CHEF, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
            local_session.close()
            return CHEF_CHECK
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CONTACT_CHOICE
    else:
        # if user is not in db proceed to registration
        bot.send_message(chat_id=update.effective_chat.id, text=lang.REG)
        r_keyboard = [[KeyboardButton(lang.REG_START, request_contact=True)]]
        update.message.reply_text(lang.REG0, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return REGISTER


# happens after got contact from <start registration> button
def registration(update: Update, context: CallbackContext):
    context.user_data['phone'] = re.sub('\+', '', str(update.message.contact.phone_number))  # strip <+> from number
    bot.send_message(chat_id=update.effective_chat.id, text=lang.REG1)
    return REGISTER_FINAL


# happens after getting correct registration format
def registration_correct(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    context.user_data['tmp'] = update.message.text
    i_name = re.search('[^\s]+(?=[ ])', context.user_data['tmp']).group()  # regex search for name
    i_pass = re.search('(?<=[ ])[^\s]+(?=$)', context.user_data['tmp']).group()  # regex search for password
    if len(i_name) > 32:
        # length requirement check for name
        bot.send_message(chat_id=update.effective_chat.id, text=lang.LONG_NAME)
        local_session.close()
        return REGISTER_FINAL
    if len(i_pass) > 32:
        # length requirement check for password
        bot.send_message(chat_id=update.effective_chat.id, text=lang.LONG_PASS)
        local_session.close()
        return REGISTER_FINAL
    # if both length check are passed add user to the database, hash password
    i_pass = gen_hash_pass(i_pass, config.SALT_LENGTH, config.KEY_LENGTH, config.ITERATION_COUNT)
    local_session.add(db_User(
        id=update.effective_chat.id, phone_number=context.user_data['phone'],
        name=i_name, is_chef=False, password=i_pass, reg_date=func.now())
    )
    local_session.commit()
    # ask for contact phone number input method
    r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
    update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
    local_session.close()
    return CONTACT_CHOICE


# happens after getting incorrect registration format
def registration_incorrect(update: Update, context: CallbackContext):
    bot.send_message(chat_id=update.effective_chat.id, text=lang.UNRECOGNIZED_FORMAT+'\n'+lang.REG)
    return REGISTER_FINAL


# happens after choosing to type in contact phone number
def contact_type(update: Update, context: CallbackContext):
    update.message.reply_text(lang.CONTACT00)
    return CONTACT_TYPE_IN


# happens after getting correctly formatted contact phone number from user
def contact_type_finish(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    context.user_data['contact_phone'] = re.sub('\+', '', str(update.message.text))
    if local_session.query(db_User).filter(db_User.phone_number == context.user_data['contact_phone']).all():
        # if that phone number is in db, ask for password
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return PASSWORD_CHECK
    else:
        # if no such number is in db, ask for contact phone number input method
        bot.send_message(chat_id=update.effective_chat.id, text=lang.PASSWORD0)
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CONTACT_CHOICE


# happens after user chooses to share his own contact
def contact_shared(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    context.user_data['contact_phone'] = re.sub('\+', '', str(update.message.contact.phone_number))
    if local_session.query(db_User).filter(db_User.phone_number == context.user_data['contact_phone']).all() \
            and update.effective_chat.id == local_session.query(db_User)\
            .filter(db_User.phone_number == context.user_data['contact_phone']).first().id:
        # if that phone number is in db, ask for password
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return PASSWORD_CHECK
    else:
        # if no such number is in db, ask for contact phone number input method
        # although this part of code running should indicate that something is really wrong.
        # I'm just going to leave this next line here.
        logging.warning('Suspicious behaviour. ~@line163, in def contact_shared')
        bot.send_message(chat_id=update.effective_chat.id, text=lang.PASSWORD0)
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CONTACT_CHOICE


# happens after getting password esque line from user when in PASSWORD_CHECK
def check_password(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    if update.message.text == lang.PASSWORD_RETURN:
        # Return to selecting contact phone number.
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CONTACT_CHOICE
    if len(update.message.text) > 32:
        # Length check
        bot.send_message(chat_id=update.effective_chat.id, text=lang.LONG_PASS)
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return PASSWORD_CHECK
    # get user with that contact phone number from database
    context.user_data['tmp'] = local_session.query(db_User).\
        filter(db_User.phone_number == context.user_data['contact_phone']).first()
    if check_hash_pass(update.message.text, context.user_data['tmp'].password,
                       config.SALT_LENGTH, config.KEY_LENGTH, config.ITERATION_COUNT):
        # if their password is the one user entered, open main menu
        r_keyboard = [[lang.MAIN0, lang.MAIN1], [lang.MAIN2]]
        update.message.reply_text(lang.MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return MAIN
    else:
        bot.send_message(chat_id=update.effective_chat.id, text=lang.PASSWORD1)
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return PASSWORD_CHECK


# happens after chef-user chooses mode to proceed in
def chef(update: Update, context: CallbackContext):
    # this is written a lil bit differently from other reply keyboard type choices
    if update.message.text == lang.CHEF0:
        # proceed as chef
        bot.send_message(chat_id=update.effective_chat.id, text=lang.CHEF00)
        r_keyboard = [[lang.CHEF01]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        return CHEF_PASS_CHECK
    if update.message.text == lang.CHEF1:
        # proceed as client
        bot.send_message(chat_id=update.effective_chat.id, text=lang.CHEF10)
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        return CONTACT_CHOICE


# happens after getting password-esque message from user when in CHEF_PASS_CHECK state
def chef_check_password(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    if update.message.text == lang.CHEF01:
        # if user changes mind and decides to proceed as client
        r_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
        update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CONTACT_CHOICE
    if len(update.message.text) > 32:
        # length check
        bot.send_message(chat_id=update.effective_chat.id, text=lang.LONG_PASS)
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CHEF_PASS_CHECK
    context.user_data['tmp'] = local_session.query(db_User).filter(db_User.id == update.effective_chat.id).first()
    if check_hash_pass(update.message.text, context.user_data['tmp'].password,
                       config.SALT_LENGTH, config.KEY_LENGTH, config.ITERATION_COUNT):
        # if the entered password is correct proceed to chef's menu
        r_keyboard = [[lang.CHEF_MAIN0, lang.CHEF_MAIN1], [lang.CHEF_MAIN2]]
        update.message.reply_text(lang.CHEF_MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CHEF_MAIN
    else:
        # if the password is wrong
        bot.send_message(chat_id=update.effective_chat.id, text=lang.PASSWORD1)
        r_keyboard = [[lang.PASSWORD_RETURN]]
        update.message.reply_text(lang.PASSWORD, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
        local_session.close()
        return CHEF_PASS_CHECK


# function to make a description for order from database
def textify_order(order_id):
    local_session = db_util.Session()
    i = local_session.query(Order).filter(Order.id == order_id).first()
    reply_text = lang.CHEF_ORDER_LIST_CONTENT.format(id=i.id, user_id=i.user_id,
                                                     phone=i.contact_phone_number, content=i.content,
                                                     date=i.ins_date, status=i.status)
    local_session.close()
    return reply_text


# happens after chef presses get orders button
def chef_list_orders(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    db_q_p_orders = local_session.query(Order).filter(Order.status == "pending")
    if db_q_p_orders.all():
        # if there are pending orders in db, send them using pages from paginator
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_p_orders.all()),
            data_pattern='chef_orders#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.ACCEPT, callback_data='accept_order#{}#{} '.format(1, db_q_p_orders.first().id)),
            InlineKeyboardButton(lang.REJECT, callback_data='reject_order#{}#{}'.format(1, db_q_p_orders.first().id))
        )
        bot.send_photo(chat_id=update.effective_chat.id,
                       photo=open(str(db_q_p_orders.first().meal.img), 'rb'),
                       caption=textify_order(db_q_p_orders.first().id), reply_markup=r_pag.markup)
    else:
        # else notify chef there are no orders
        bot.send_message(chat_id=update.effective_chat.id, text=lang.CHEF_MAIN00)
    r_keyboard = [[lang.CHEF_MAIN0, lang.CHEF_MAIN1], [lang.CHEF_MAIN2]]
    update.message.reply_text(lang.CHEF_MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
    local_session.close()
    return CHEF_MAIN


# happens after chef presses get accepted orders button
def chef_list_accepted_orders(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    db_q_a_orders = local_session.query(Order).filter(Order.status == "accepted")
    if db_q_a_orders.all():
        # if there are accepted orders in db, send them using pages from paginator
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_a_orders.all()),
            data_pattern='chef_a_orders#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.READY_TO_DELIVER,
                                 callback_data='rtd_order#{}#{}'.format(1, db_q_a_orders.first().id)),
            InlineKeyboardButton(lang.REJECT,
                                 callback_data='reject_order#{}#{}'.format(1, db_q_a_orders.first().id))
        )
        bot.send_photo(chat_id=update.effective_chat.id,
                       photo=open(str(db_q_a_orders.first().meal.img), 'rb'),
                       caption=textify_order(db_q_a_orders.first().id), reply_markup=r_pag.markup)
    else:
        # else notify chef there are no orders and return to main menu
        bot.send_message(chat_id=update.effective_chat.id, text=lang.CHEF_MAIN00)
    r_keyboard = [[lang.CHEF_MAIN0, lang.CHEF_MAIN1], [lang.CHEF_MAIN2]]
    update.message.reply_text(lang.CHEF_MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
    local_session.close()
    return CHEF_MAIN


# happens after chef presses edit menu button
def chef_edit_menu(update: Update, context: CallbackContext):
    r_keyboard = [[lang.CHEF_MAIN21, lang.CHEF_MAIN22], [lang.CHEF_MAIN23]]
    r_markup = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)
    update.message.reply_text(lang.CHEF_MAIN20, reply_markup=r_markup)
    return CHEF_EDIT_MENU


# happens after chef presses add meal button
def chef_add_meal(update: Update, context: CallbackContext):
    context.user_data['nm_name'] = ""  # Initialize necessary values to add a meal for user
    context.user_data['nm_cost'] = ""
    r_keyboard = [[lang.CHEF_MAIN211]]
    r_markup = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)
    update.message.reply_text(lang.CHEF_MAIN210, reply_markup=r_markup)
    return CHEF_NEW_MEAL


# happens after getting correct input from chef to add a meal
def chef_add_meal_process(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    if update.message.text == lang.CHEF_MAIN211:
        r_keyboard = [[lang.CHEF_MAIN21, lang.CHEF_MAIN22], [lang.CHEF_MAIN23]]
        r_markup = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)
        update.message.reply_text(lang.CHEF_MAIN20, reply_markup=r_markup)
        local_session.close()
        return CHEF_EDIT_MENU
    context.user_data['tmp'] = update.message.text
    if update.message.photo:
        context.user_data['nm_photo'] = update.message.photo
        update.message.reply_text(lang.CHEF_MAIN212)
    elif re.search("[0-9.]+", context.user_data['tmp']):
        context.user_data['nm_cost'] = re.search("[0-9.]+", context.user_data['tmp']).group()
        update.message.reply_text(lang.CHEF_MAIN214.format(context.user_data['nm_cost']))
    elif re.search("[0-9\s]*[A-Za-z,!@#$%^&*();'/\":\s]+[0-9\s]*", context.user_data['tmp']):
        context.user_data['nm_name'] = re.search("[0-9\s]*[A-Za-z,!@#$%^&*();'/\":\s]+[0-9\s]*",
                                                 context.user_data['tmp']).group()
        update.message.reply_text(lang.CHEF_MAIN213.format(context.user_data['nm_name']))

    if context.user_data['nm_photo'] and context.user_data['nm_name'] and context.user_data['nm_cost']:
        # if everything is set and done download file, add meal to the database
        file_id = context.user_data['nm_photo'][2].file_id
        img = 'assets/meals/'+context.user_data['nm_name']+'.jpg'
        new_File = bot.getFile(file_id)
        new_File.download(img)
        local_session.add(Meal(img=img, name=context.user_data['nm_name'], cost=float(context.user_data['nm_cost'])))
        local_session.commit()
        r_keyboard = [[lang.CHEF_MAIN21, lang.CHEF_MAIN22], [lang.CHEF_MAIN23]]
        r_markup = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)
        update.message.reply_text(lang.CHEF_MAIN20, reply_markup=r_markup)
        local_session.close()
        return CHEF_EDIT_MENU


# happens after chef presses view meals button
def chef_view_meals(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    db_q_meal_types = local_session.query(Meal)
    if db_q_meal_types.all():
        # if there are meals in db, send them using pages from paginator
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_meal_types.all()),
            data_pattern='chef_v_meals#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.REMOVE,
                                 callback_data='remove_meal#{}#{}'.format(1, db_q_meal_types.first().id))
        )
        bot.send_photo(chat_id=update.effective_chat.id,
                       photo=open(str(db_q_meal_types.first().img), 'rb'),
                       caption=lang.MEAL.format(id=db_q_meal_types.first().id, name=db_q_meal_types.first().name,
                                                cost=db_q_meal_types.first().cost), reply_markup=r_pag.markup)
    else:
        # else notify chef there are no meals and return to main menu
        bot.send_message(chat_id=update.effective_chat.id, text=lang.NO_MEALS)
    r_keyboard = [[lang.CHEF_MAIN21, lang.CHEF_MAIN22], [lang.CHEF_MAIN23]]
    r_markup = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)
    update.message.reply_text(lang.CHEF_MAIN20, reply_markup=r_markup)
    local_session.close()
    return CHEF_EDIT_MENU


# happens after chef presses go back button
def chef_return_to_main(update: Update, context: CallbackContext):
    r_keyboard = [[lang.CHEF_MAIN0, lang.CHEF_MAIN1], [lang.CHEF_MAIN2]]
    update.message.reply_text(lang.CHEF_MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
    return CHEF_MAIN


# happens after client asks for (meal) menu
def menu(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    db_q_meal_types = local_session.query(Meal)
    if db_q_meal_types.all():
        # if there are meals in db, send them using pages from paginator
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_meal_types.all()),
            data_pattern='user_v_meals#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.MAIN00,
                                 callback_data='add_cart#{}#{}'.format(1, db_q_meal_types.first().id))
        )
        bot.send_photo(chat_id=update.effective_chat.id,
                       photo=open(str(db_q_meal_types.first().img), 'rb'),
                       caption=lang.MEAL.format(id=db_q_meal_types.first().id, name=db_q_meal_types.first().name,
                                                cost=db_q_meal_types.first().cost), reply_markup=r_pag.markup)
    else:
        # else notify user there are no meals
        bot.send_message(chat_id=update.effective_chat.id, text=lang.NO_MEALS)
    # return to main menu
    r_keyboard = [[lang.MAIN0, lang.MAIN1], [lang.MAIN2]]
    update.message.reply_text(lang.MAIN, reply_markup=ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True))
    local_session.close()
    return MAIN


# happens after client presses cart button
def def_cart(update: Update, context: CallbackContext):
    if not context.user_data['cart']:
        # if cart is empty return to main menu
        bot.send_message(chat_id=update.effective_chat.id, text=lang.CART0)
        reply_keyboard = [[lang.MAIN0, lang.MAIN1], [lang.MAIN2]]
        update.message.reply_text(lang.MAIN, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return MAIN
    r_text = ""
    r_t_cost = 0
    # count total price, generate message with detailed breakdown of prices for meals in cart
    for item in context.user_data['cart']:
        r_t_cost += item.cost
        r_text += item.name+" "+str(item.cost)+config.CURRENCY+"\n"
    # define payload with user id after # e.g. cart_confirm_payload#70707070, send message describing cart content,
    # add a button to cancel order, generate invoice to pay for the order.
    payload = "cart_confirm_payload#"+str(context.user_data['id'])
    r_keyboard = [[InlineKeyboardButton(text=lang.CART2, callback_data="cart#cancel")]]
    r_markup = InlineKeyboardMarkup(r_keyboard)
    bot.send_message(chat_id=update.effective_chat.id,
                     text=lang.CART+"\n"+r_text+"\n"+lang.CART_TC+str(r_t_cost)+config.CURRENCY,
                     reply_markup=r_markup)
    bot.send_invoice(chat_id=update.effective_chat.id,
                     title=lang.PAYMENT0,
                     description=lang.PAYMENT01,
                     payload=payload,
                     prices=[LabeledPrice("Order", int(r_t_cost) * config.CUR_DEC)],
                     currency=config.CURRENCY,
                     provider_token=config.PAYMENT_TOKEN)
    reply_keyboard = [[lang.MAIN0, lang.MAIN1], [lang.MAIN2]]
    update.message.reply_text(lang.MAIN, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MAIN


# happens after user presses order status button
def order_status(update: Update, context: CallbackContext):
    local_session = db_util.Session()
    db_q_u_orders = local_session.query(Order).filter(Order.user_id == update.effective_chat.id)
    if db_q_u_orders.all():
        # if there are orders of that user in db, send info about them in pages
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_u_orders.all()),
            data_pattern='user_orders#{page}'
        )
        bot.send_photo(chat_id=update.effective_chat.id,
                       photo=open(str(db_q_u_orders.first().meal.img), 'rb'),
                       caption=textify_order(db_q_u_orders.first().id), reply_markup=r_pag.markup)
    else:
        bot.send_message(chat_id=update.effective_chat.id, text=lang.MAIN20)
    reply_keyboard = [[lang.MAIN0, lang.MAIN1], [lang.MAIN2]]
    update.message.reply_text(lang.MAIN, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    local_session.close()
    return MAIN


# happens after user presses inline button
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    q_data = query.data
    local_session = db_util.Session()

    if q_data.find("cart#") != -1:
        # if pressed button callback data begins with <cart#>, take substring of q_data after "#"
        choice = q_data.split("#")[1]
        if choice == "cancel" and context.user_data['cart']:
            # if substring is <cancel> clear the cart
            context.user_data['cart'].clear()
            bot.send_message(chat_id=update.effective_chat.id, text=lang.CART20)

    if q_data.find("chef_orders#") != -1:
        # if pressed button callback data begins with <chef_orders#>,
        # get page number (as this callback data is sent from paginator class), switch page to that number,
        # update displayed order, update photo
        db_q_p_orders = local_session.query(Order).filter(Order.status == "pending").all()
        new_page = int(q_data.split('#')[1])
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_p_orders),
            current_page=new_page,
            data_pattern='chef_orders#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.ACCEPT, callback_data='accept_order#{}#{}'.
                                 format(new_page, db_q_p_orders[new_page-1].id)),
            InlineKeyboardButton(lang.REJECT, callback_data='reject_order#{}#{}'.
                                 format(new_page, db_q_p_orders[new_page-1].id))
        )
        query.edit_message_media(
            media=InputMediaPhoto(open(str(db_q_p_orders[new_page-1].meal.img), 'rb'))
        )
        query.edit_message_caption(
            caption=textify_order(db_q_p_orders[new_page-1].id),
            reply_markup=r_pag.markup
        )

    if q_data.find("chef_a_orders#") != -1:
        # if pressed button callback data begins with <chef_a_orders#>,
        # get page number (as this callback data is sent from paginator class), switch page to that number,
        # update displayed order, update photo
        db_q_a_orders = local_session.query(Order).filter(Order.status == "accepted").all()
        new_page = int(q_data.split('#')[1])
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_a_orders),
            current_page=new_page,
            data_pattern='chef_a_orders#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.READY_TO_DELIVER, callback_data='rtd_order#{}#{}'.
                                 format(new_page, db_q_a_orders[new_page-1].id)),
            InlineKeyboardButton(lang.REJECT, callback_data='reject_order#{}#{}'.
                                 format(new_page,  db_q_a_orders[new_page-1].id))
        )
        query.edit_message_media(
            media=InputMediaPhoto(open(str(db_q_a_orders[new_page-1].meal.img), 'rb')))
        query.edit_message_caption(
            caption=textify_order(db_q_a_orders[new_page-1].id),
            reply_markup=r_pag.markup
        )

    if q_data.find("user_orders#") != -1:
        # if pressed button callback data begins with <user_orders#>,
        # get page number (as this callback data is sent from paginator class), switch page to that number,
        # update displayed order, update photo
        db_q_u_orders = local_session.query(Order).filter(Order.user_id == update.effective_chat.id).all()
        new_page = int(q_data.split('#')[1])
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_u_orders),
            current_page=new_page,
            data_pattern='user_orders#{page}'
        )
        query.edit_message_media(
            media=InputMediaPhoto(open(str(db_q_u_orders[new_page-1].meal.img), 'rb'))
        )
        query.edit_message_caption(
            caption=textify_order(db_q_u_orders[new_page-1].id),
            reply_markup=r_pag.markup
        )

    if q_data.find("chef_v_meals#") != -1:
        # if pressed button callback data begins with <chef_v_meals#>,
        # get page number (as this callback data is sent from paginator class), switch page to that number,
        # update displayed meal

        db_q_meal_types = local_session.query(Meal)
        new_page = int(q_data.split('#')[1])
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_meal_types.all()),
            current_page=new_page,
            data_pattern='chef_v_meals#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.REMOVE, callback_data='remove_meal#{}#{}'.
                                 format(new_page, db_q_meal_types[new_page - 1].id))
        )
        query.edit_message_media(
            media=InputMediaPhoto(open(str(db_q_meal_types[new_page - 1].img), 'rb')))
        query.edit_message_caption(
            caption=lang.MEAL.format(id=db_q_meal_types[new_page - 1].id, name=db_q_meal_types[new_page - 1].name,
                                        cost=db_q_meal_types[new_page - 1].cost),
            reply_markup=r_pag.markup
        )

    if q_data.find("user_v_meals#") != -1:
        # if pressed button callback data begins with <chef_v_meals#>,
        # get page number (as this callback data is sent from paginator class), switch page to that number,
        # update displayed meal

        db_q_meal_types = local_session.query(Meal)
        new_page = int(q_data.split('#')[1])
        r_pag = paginator.MyPaginator(
            page_count=len(db_q_meal_types.all()),
            current_page=new_page,
            data_pattern='user_v_meals#{page}'
        )
        r_pag.add_before(
            InlineKeyboardButton(lang.MAIN00, callback_data='add_cart#{}#{}'.
                                 format(new_page, db_q_meal_types[new_page - 1].id))
        )
        query.edit_message_media(
            media=InputMediaPhoto(open(str(db_q_meal_types[new_page - 1].img), 'rb')))
        query.edit_message_caption(
            caption=lang.MEAL.format(id=db_q_meal_types[new_page - 1].id, name=db_q_meal_types[new_page - 1].name,
                                        cost=db_q_meal_types[new_page - 1].cost),
            reply_markup=r_pag.markup
        )

    if q_data.find("add_cart#") != -1:
        # if pressed button callback data begins with <add_cart#>,
        # add meal to cart
        choice = q_data.split('#')[2]
        bot.send_message(chat_id=update.effective_chat.id, text=local_session.query(Meal).
                         filter(Meal.id == int(choice)).first().name + lang.CART_ADD)
        context.user_data['cart'].append(local_session.query(Meal).filter(Meal.id == int(choice)).first())

    if q_data.find("remove_meal#") != -1:
        id = int(q_data.split('#')[2])
        db_q_id = local_session.query(Meal).filter(Meal.id == id)
        bot.send_message(chat_id=context.user_data['id'],
                         text=lang.REMOVE + " meal#" + str(db_q_id.first().id))
        local_session.delete(db_q_id.first())
        local_session.commit()
    if q_data.find("accept_order#") != -1:
        # if pressed button callback data begins with <accept_order#>,
        # get substring after "#", find order with that substring as id, change its status to accepted, notify user
        id = int(q_data.split('#')[2])
        db_q_id = local_session.query(Order).filter(Order.id == id)
        db_q_id.first().status = 'accepted'
        local_session.commit()
        bot.send_message(chat_id=context.user_data['id'],
                         text=lang.ACCEPT + " order#" + str(db_q_id.first().id))
        bot.send_message(chat_id=db_q_id.first().user_id,
                         text=lang.NOTIFICATION_ACCEPT.format(id=str(db_q_id.first().id)))
    if q_data.find("reject_order#") != -1:
        # if pressed button callback data begins with <reject_order#>,
        # get substring after "#", find order with that substring as id,
        # delete that order, notify user, log it into file
        id = int(q_data.split('#')[2])
        db_q_id = local_session.query(Order).filter(Order.id == id)
        bot.send_message(chat_id=context.user_data['id'],
                         text=lang.REJECT+" order#"+str(db_q_id.first().id))
        bot.send_message(chat_id=db_q_id.first().user_id,
                         text=lang.NOTIFICATION_REJECT.format(id=str(db_q_id.first().id)))
        orders_log = open(config.ORDERS_LOG, "a+")
        orders_log.write("REJECTED > "+"USER_ID={0}|CONTACT_PHONE={1}|CONTENT='{2}'|DATE='{3}'".format(
            db_q_id.first().user_id, db_q_id.first().contact_phone_number,
            db_q_id.first().content, db_q_id.first().ins_date)+"\n")
        orders_log.close()
        local_session.delete(db_q_id.first())
        local_session.commit()
    if q_data.find("rtd_order#") != -1:
        # if pressed button callback data begins with <rtd_order#>,
        # get substring after "#", find order with that substring as id,
        # delete that order, notify user, log it into file
        id = int(q_data.split('#')[2])
        db_q_id = local_session.query(Order).filter(Order.id == id)
        bot.send_message(chat_id=context.user_data['id'], text=lang.READY_TO_DELIVER+" order#"+str(db_q_id.first().id))
        bot.send_message(chat_id=db_q_id.first().user_id, text=lang.NOTIFICATION_RTD.format(id=str(db_q_id.first().id)))
        orders_log = open(config.ORDERS_LOG, "a+")
        orders_log.write("COMPLETED > " + "USER_ID={0}|CONTACT_PHONE={1}|CONTENT='{2}'|DATE='{3}'".format(
            db_q_id.first().user_id, db_q_id.first().contact_phone_number,
            db_q_id.first().content, db_q_id.first().ins_date) + "\n")
        orders_log.close()
        local_session.delete(db_q_id.first())
        local_session.commit()
    local_session.close()


# handle precheckout callback
def precheckout_callback(update: Update, context: CallbackContext) -> None:
    local_session = db_util.Session()
    q_invoice = update.pre_checkout_query
    context.user_data['last_q_invoice'] = q_invoice
    if q_invoice.invoice_payload.find("cart_confirm_payload#") != -1 \
            and q_invoice.invoice_payload.split('#')[1] == str(context.user_data['id']):
        # if payload is <cart_confirm_payload#[user_id]>, check length of user's cart, count number of user's orders
        # already in db, compare their sum to MAX_ORDERS. If it is not greater add those orders in db with pending
        # status, notify the payer, 'ok' the invoice and clear the cart; else notify the user and reject the payment
        payload_id = int(q_invoice.invoice_payload.partition('#')[2])
        n_ord_db = len(
            local_session.query(Order).filter(Order.contact_phone_number == context.user_data['contact_phone']).all())
        if len(context.user_data['cart']) + n_ord_db <= config.MAX_ORDERS:
            q_invoice.answer(ok=True)
        else:
            bot.send_message(chat_id=payload_id,
                             text=lang.CART_TMO.format(n_ord_db=n_ord_db, n_av_db=config.MAX_ORDERS - n_ord_db))
            context.user_data['cart'].clear()
            q_invoice.answer(ok=False, error_message="Too many orders.")
    local_session.close()


# happens after successful payment
def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    local_session = db_util.Session()
    update.message.reply_text(lang.PAYMENT_TY)
    q_invoice = context.user_data['last_q_invoice']
    if q_invoice.invoice_payload.find("cart_confirm_payload#") != -1 \
            and q_invoice.invoice_payload.split('#')[1] == str(context.user_data['id']):
        # if payload is <cart_confirm_payload#[user_id]>, check length of user's cart, count number of user's orders
        # already in db, compare their sum to MAX_ORDERS. If it is not greater add those orders in db with pending
        # status, notify the payer, 'ok' the invoice and clear the cart; else notify the user and reject the payment
        payload_id = int(q_invoice.invoice_payload.partition('#')[2])
        for item in context.user_data['cart']:
            local_session.add(
                Order(user_id=payload_id, contact_phone_number=context.user_data['contact_phone'],
                      content=item.name, status='pending', ins_date=func.now()))
        local_session.commit()
        bot.send_message(chat_id=payload_id, text=lang.CART10)
        context.user_data['cart'].clear()
    local_session.close()


# haven't quite figured out how to restart bot, ignore this please
def stop_bot(update: Update, context: CallbackContext):
    reply_keyboard = [[lang.CONTACT0, KeyboardButton(lang.CONTACT1, request_contact=True)], [lang.STOP]]
    update.message.reply_text(lang.CONTACT, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CONTACT_CHOICE


# main function
def main():
    # define conversation handler which handles conversation states and message/command handlers, allow reentry to
    # restart conversation when </start> is typed at any time
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        allow_reentry=True,
        states={
            LANG_CHOICE: [MessageHandler(Filters.regex('^(🇬🇧English|🇷🇺Русский)$'), language_chosen)],
            REGISTER: [MessageHandler(Filters.contact, registration)],
            REGISTER_FINAL: [MessageHandler(Filters.regex('[^\s]+ [^\s]+(?=$)'), registration_correct),
                             MessageHandler(~Filters.regex('[^\s]+ [^\s]+(?=$)'), registration_incorrect)],
            CONTACT_CHOICE: [MessageHandler(
                Filters.regex('^(' + loc_en.CONTACT0 + '|' + loc_ru.CONTACT0 + ')$') & ~Filters.contact, contact_type),
                         # if first button pressed proceed to typing
                         MessageHandler(Filters.contact, contact_shared),
                         # if second button pressed (and contact shared) assign user_phone_number
                         MessageHandler(
                             ~Filters.contact & ~Filters.regex('^(' + loc_en.CONTACT0 + '|' + loc_ru.CONTACT0 + ')$'),
                             language_chosen)],
            CONTACT_TYPE_IN: [MessageHandler(Filters.regex('^[+][0-9]{8}[0-9]+$'), contact_type_finish),
                              MessageHandler(~Filters.regex('^[+][0-9]{8}[0-9]+$'), contact_type)],
            PASSWORD_CHECK: [MessageHandler(Filters.regex('[^\s]+'), check_password)],
            CHEF_CHECK: [MessageHandler(Filters.regex('^(' + loc_en.CHEF0 + '|' + loc_ru.CHEF0 + ')$'), chef),
                         MessageHandler(Filters.regex('^(' + loc_en.CHEF1 + '|' + loc_ru.CHEF1 + ')$'), chef)],
            CHEF_PASS_CHECK: [MessageHandler(Filters.regex('[^\s]+'), chef_check_password)],
            CHEF_MAIN: [MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN0 + '|' + loc_ru.CHEF_MAIN0 + ')$'),
                                       chef_list_orders),
                        MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN1 + '|' + loc_ru.CHEF_MAIN1 + ')$'),
                                       chef_list_accepted_orders),
                        MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN2 + '|' + loc_ru.CHEF_MAIN2 + ')$'),
                                       chef_edit_menu)],
            CHEF_EDIT_MENU: [MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN21 + '|' + loc_ru.CHEF_MAIN21 + ')$'),
                                       chef_add_meal),
                             MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN22 + '|' + loc_ru.CHEF_MAIN22 + ')$'),
                                            chef_view_meals),
                             MessageHandler(Filters.regex('^(' + loc_en.CHEF_MAIN23 + '|' + loc_ru.CHEF_MAIN23 + ')$'),
                                            chef_return_to_main)],
            CHEF_NEW_MEAL: [MessageHandler(Filters.regex('[^\s]+'), chef_add_meal_process),
                            MessageHandler(Filters.photo, chef_add_meal_process),],
            MAIN: [MessageHandler(Filters.regex('^(' + loc_en.MAIN0 + '|' + loc_ru.MAIN0 + ')$'), menu),
                   MessageHandler(Filters.regex('^(' + loc_en.MAIN1 + '|' + loc_ru.MAIN1 + ')$'), def_cart),
                   MessageHandler(Filters.regex('^('+loc_en.MAIN2+'|'+loc_ru.MAIN2+')$'), order_status),
                   ]
        },
        fallbacks=[MessageHandler(Filters.regex('^(' + loc_en.STOP + '|' + loc_ru.STOP + ')$'), stop_bot),
                   CommandHandler('stop', stop_bot)],
    )

    # connect other handlers, start polling
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))


def insert_meals() -> None:
    import ins_meals
    ins_meals.insert()
def start():
    updater.start_polling()
def stop():
    updater.stop()


# run
if __name__ == '__main__':
    main()
    start()
    insert_meals()
