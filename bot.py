import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import requests
import json
import os

# Your JSONBin.io credentials
BIN_ID = '66978ffdacd3cb34a867556e'  # Replace with your bin ID
SECRET_KEY = '$2a$10$XHj0.DGTDEqhbEY4RFKZau7LXkRq5jM15dAsXJnK4eU3P9hkaXpGi'  # Replace with your secret key
BIN_URL = f'https://api.jsonbin.io/v3/b/{BIN_ID}'

# Telegram Bot Token
TOKEN = "7446815124:AAH3UirI0n-kFJtaHI4_gndjyB9IkGnODoI"
bot = Bot(token=TOKEN)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Function to get orders from JSONBin.io
def get_orders():
    headers = {'X-Master-Key': SECRET_KEY}
    response = requests.get(BIN_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['record']['orders'] if 'record' in data and 'orders' in data['record'] else []
    else:
        logging.error(f"Error fetching orders: {response.status_code} {response.text}")
        return []

# Function to save orders to JSONBin.io
def save_orders(orders):
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': SECRET_KEY
    }
    response = requests.put(BIN_URL, headers=headers, data=json.dumps({'orders': orders}))
    if response.status_code != 200:
        logging.error(f"Error saving orders: {response.status_code} {response.text}")

# Command to add an order
def add_order(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 3:
            update.message.reply_text('Usage: /add <date> <kol> <sum>, <kol> <sum>, ...')
            return

        date = args[0]
        orders_input = ' '.join(args[1:])
        new_orders = [{'date': date, 'kol': int(kol), 'sum': float(sum)} for kol, sum in (item.split() for item in orders_input.split(','))]
        
        orders = get_orders()
        orders.extend(new_orders)
        save_orders(orders)

        update.message.reply_text(f"Orders for {date} added successfully.")
    except Exception as e:
        logging.error(f"Error in add_order: {e}")
        update.message.reply_text(f"Error: {e}")

# Command to list orders
def list_orders(update: Update, context: CallbackContext):
    try:
        args = context.args
        start_date = args[0] if len(args) > 0 else "11.07"
        end_date = args[1] if len(args) > 1 else "28.07"
        
        orders = get_orders()
        filtered_orders = [order for order in orders if start_date <= order['date'] <= end_date]
        
        if not filtered_orders:
            update.message.reply_text("No orders found in the specified date range.")
            return
        
        summary = "Orders Summary:\n"
        for order in filtered_orders:
            summary += f"{order['date']}: {order['kol']} items, total {order['sum']}\n"
        
        update.message.reply_text(summary)
    except Exception as e:
        logging.error(f"Error in list_orders: {e}")
        update.message.reply_text(f"Error: {e}")

# Command to restart the bot
def restart(update: Update, context: CallbackContext):
    try:
        update.message.reply_text("Restarting bot...")
        os.system('pm2 restart bot')
    except Exception as e:
        logging.error(f"Error in restart: {e}")
        update.message.reply_text(f"Error: {e}")

# Default handler
def handle_message(update: Update, context: CallbackContext):
    update.message.reply_text('Usage:\n- To add orders: /add <date> <kol> <sum>, <kol> <sum>, ...\nExample: /add 06.07 1 1000, 3 1000\n- To list orders: /list <start_date> <end_date> (defaults to 11.07 28.07)\n- To restart bot: /restart')

def main():
    try:
        # Initialize the Updater and Dispatcher
        updater = Updater(TOKEN)
        dp = updater.dispatcher

        # Add command handlers
        dp.add_handler(CommandHandler("add", add_order))
        dp.add_handler(CommandHandler("list", list_orders))
        dp.add_handler(CommandHandler("restart", restart))

        # Add message handler for default response
        dp.add_handler(MessageHandler(filters.Filters.text & ~filters.Filters.command, handle_message))

        # Start the Bot
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == '__main__':
    main()
