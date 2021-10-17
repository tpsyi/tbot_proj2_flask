import config
import names.used_names as names

GREETING = "Welcome to the official "+names.ORG_NAME+" bot. 🤖"
REG_START = '✅Start Registration'
REG = '❕Before proceeding we need to add you to the system.📘'
REG0 = 'Please share your number📱 to register.'
REG1 = 'Please enter your name🪦 and your desired password🔐 in this format:\n' \
      '[name] [password]\n' \
      'Keep in mind that your name and password should be no longer than 32 characters long📏'
LONG_NAME = '❗️Name is too long.'
LONG_PASS = '❗️Password is too long.'
UNRECOGNIZED_FORMAT = '❔Unrecognized Format.'
CONTACT = "You need to specify phone number📞 which we should contact about your order.🍽\n" \
          "You can type it in or share contact."
CONTACT0 = '📇Type phone number'
CONTACT1 = '📱Share phone number'
CONTACT00 = 'Please, type in the phone number in format +xxxxxxxxxxxx'
PASSWORD_RETURN = '↪️Return to selecting contact phone number.'
PASSWORD = 'Enter the password🔑 associated with that phone number.'
PASSWORD0 = '❕That phone number is not registered within our database.\n Please enter a different phone number.'
PASSWORD1 = '❗️Wrong password.\n'
CHEF = 'ℹ️You have an access to chef tools. Do you want to proceed as chef🧂?'
CHEF0 = '🧂Proceed as chef'
CHEF1 = '🦀Proceed as client'
CHEF00 = 'You logged on as chef🧂'
CHEF10 = 'You chose to proceed as client🦀'
CHEF01 = '🤚Proceed as client.'
CHEF_MAIN = 'ℹ️Use button menu to navigate.'
CHEF_MAIN0 = '❔Get list of orders.'
CHEF_MAIN00 = '💤No orders! Enjoy your rest.'
CHEF_MAIN1 = '✔️Accepted orders'
CHEF_MAIN2 = '📝Edit Menu'
CHEF_MAIN20 = "You can edit📝 menu now. Use button menu to add➕ a meal or view👁 meals that are being served."
CHEF_MAIN21 = '➕Add a meal'
CHEF_MAIN210 = "You are about to add a new meal🍽 to the system. You should send an image🖼 for the meal, name🔤 and cost💵"
CHEF_MAIN211 = "↪Go back"
CHEF_MAIN212 = "🖼Photo successfully added.✅"
CHEF_MAIN213 = "🔤Name updated to {}."
CHEF_MAIN214 = "💵Cost updated to {}."
CHEF_MAIN22 = '👁View meals'
CHEF_MAIN23 = '↪Go back'
MEAL = '🆔️: {id}, \nℹName: {name}, \n💵Cost: {cost}'
NO_MEALS = "⚠️No meals in the database!"
NOTIFICATION_ACCEPT = '✅Your order id#{id} has been accepted.'
NOTIFICATION_REJECT = '❌Your order id#{id} has been rejected.'
NOTIFICATION_RTD = '🆗️Your order id#{id} is ready for delivery.'
CHEF_ORDER_LIST = 'Here are the pending⏳ orders:'
CHEF_ORDER_LIST_CONTENT = '🍽Meal: {content},\nOrder ID: {id}, 👤User ID: {user_id},\n📞Phone number to contact: {phone},\n' \
                          '🗓Date: {date},\n#️⃣Status: {status}'
STOP = '⛔️Stop'
MAIN = 'ℹ️Use button menu to navigate'
MAIN0 = '🖼Menu'
MAIN00 = '➕Add to cart'
MAIN1 = '🛒Cart'
MAIN2 = '⏳Order status'
MAIN20 = "0️⃣No orders!"
CART = 'Your Cart 🛒: '
CART0 = '📉Your Cart is empty. To order press '+MAIN0
CART_ADD = ' was added to your basket.📥'
CART1 = '✅Confirm order'
CART10 = "▶️Your order is being processed. To check it's status press "+MAIN2
CART2 = '📛Cancel order'
CART20 = 'ℹ️Your order has been cancelled.'
CART_TC = "Total cost : "
CART_TMO = '🙇‍♂️Sorry, but with this action number of orders associated with that phone number in database' \
           ' would be over allowed '+str(config.MAX_ORDERS)+'. ℹ️There are {n_ord_db} orders in the database.' \
           ' You can order {n_av_db} more meals.'
ACCEPT = '✅Accept'
REJECT = '❌Reject'
READY_TO_DELIVER = '🟢Ready for delivery.'
REMOVE = '➖Remove'
CLEAR = '🧹Clear'
PAYMENT0 = 'ℹ️Your order'
PAYMENT01 = '"Detailed breakdown can be found above☝ this invoice."'
PAYMENT_TY = '🤝Thank you for your order!'
