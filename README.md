# tbot_proj2
University project, telegram bot for ordering meals.

To setup this project:
1) install packages: \
  pip install python-telegram-bot \
  pip install python-telegram-bot-pagination \
  pip install sqlalchemy \
  pip install python-dotenv
2) create vars.env file at root directory and type in: \
  TELEGRAM_TOKEN = [Bot token] \
  DATABASE = "sqlite:///database//tbot.db" \
  PAYMENT_TOKEN = [Payment api token]
3) change values in config.py. Their meaning is documented to the best of my abilities
4) change localizations/en.py, ru.py to your liking. Change names/used_names.py to suit your needs.
5) put your images in assets/meals, put your meals in ins_meals.py. Run ins_meals.py once.
6) run main.py
