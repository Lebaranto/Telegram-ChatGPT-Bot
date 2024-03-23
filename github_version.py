import asyncio
from telethon.sync import TelegramClient, events, utils, Button
import openai

# Replace 'YOUR_API_ID', 'YOUR_API_HASH', 'YOUR_PHONE_NUMBER' on your own values
api_id = ''
api_hash = ''
phone_number = ''

# Your OpenAI API key
openai.api_key = ''

# link to the channel you want to monitor/advertise
channel_link = ''

import asyncio
from telethon.sync import TelegramClient, events
import openai
from telegram.ext import Updater, CommandHandler
from telethon.tl.functions.channels import JoinChannelRequest


bot_token = '' #token for the telegram bot
client = TelegramClient('session_name', api_id, api_hash)
channel_links = []
monitoring_paused = False  
joined_channels = {} 

def start(update, context):
    update.message.reply_text('Hey! Please use commands /addchannel, /removechannel and /pause for controlling your channels.')

def add_channel(update, context):
    new_channel = ' '.join(context.args)
    if new_channel not in channel_links:
        channel_links.append(new_channel)
        update.message.reply_text(f'Channel {new_channel} added!')
    else:
        update.message.reply_text('This channel is already in the list.')

def remove_channel(update, context):
    channel_to_remove = ' '.join(context.args)
    if channel_to_remove in channel_links:
        channel_links.remove(channel_to_remove)
        update.message.reply_text(f'Channel {channel_to_remove} removed!')
    else:
        update.message.reply_text('This channel is not in the list.')

def pause_monitoring(update, context):
    global monitoring_paused
    monitoring_paused = not monitoring_paused
    status = "paused" if monitoring_paused else "resumed"
    update.message.reply_text(f'Channel monitoring {status}.')

# Setting up the Telegram bot
updater = Updater(bot_token, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("addchannel", add_channel, pass_args=True))
dp.add_handler(CommandHandler("removechannel", remove_channel, pass_args=True))
dp.add_handler(CommandHandler("pause", pause_monitoring))

# Telegram userbot functions
async def get_last_post_id(channel):
    messages = await client.get_messages(channel, limit=1)
    return messages[0].id if messages else None

#Here I used russian language for the prompt, but you can use any language you want
async def generate_comment(post_text):
    prompt = (
        f"Дан пост: \"{post_text}\"\n\n"
        "Напишите разумный и уместный комментарий к этому посту, который мог бы написать обычный пользователь. Пиши русским языком.\n\n"
        "Комментарий должен быть вежливым, конструктивным и отражать обычную человеческую реакцию на такой тип контента. Твой лимит: 70 символов."
    )

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=70,
        temperature=0.7  #Regulates the randomness of the response
    )
    return response.choices[0].text.strip()

async def userbot_main():
    async with client:
        await client.start(phone_number)
        print("Connected to Telegram successfully.")

        last_checked_post_ids = {}

        while True:
            if not monitoring_paused:
                for channel_link in channel_links:
                    channel = await client.get_entity(channel_link)

                    if channel_link not in joined_channels:
                        await client(JoinChannelRequest(channel))
                        print(f"Joined to the channel {channel.title}")
                        joined_channels[channel_link] = True

                    last_post_id = await get_last_post_id(channel)

                    if channel.id not in last_checked_post_ids:
                        last_checked_post_ids[channel.id] = last_post_id

                    if last_post_id and last_post_id != last_checked_post_ids.get(channel.id):
                        print(f"New post detected in channel: {channel.title}")
                        last_checked_post_ids[channel.id] = last_post_id

                        message = await client.get_messages(channel, ids=last_post_id)
                        post_text = message.text if message else ""

                        comment = await generate_comment(post_text)
                        await client.send_message(channel.id, comment, comment_to=last_post_id)
                        print("Sent a comment to the channel.")

            await asyncio.sleep(5)

if __name__ == '__main__':
    # Run the userbot and Telegram bot simultaneously
    updater.start_polling()
    asyncio.run(userbot_main())
