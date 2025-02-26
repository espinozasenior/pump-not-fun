# 🤖 Telegram Bot Template

A clean and scalable Telegram bot template using [Pyrotgfork](https://github.com/TelegramPlayGround/Pyrogram) (a forked version of [Pyrogram](https://github.com/pyrogram/pyrogram)) with multi-language support and SQLite database.

Personal purpose to take advantage from telegram token finder channels and make my due diligences to buy and sell in Solana.

## ✨ Features

- 🌐 Multi-language support with easy switching
- 💾 SQLite database with SQLAlchemy ORM
- 📅 Task scheduling with APScheduler
- 📁 Clean and organized folder structure
- ⚙️ Environment variables management
- ⚡️ **[Astral(uv)](https://github.com/astral-sh/uv)** - extremely fast Python package and project manager
- 🎯 Decorator-based user handling
- 💬 Catch messages from selected telegram chats (groups, channels, etc)
- 🔍 Message handler to find pump fun token
- ~~🛍️ Buy and Sell token as specific PNL~~
- ~~Twitter(X) API integration to make due diligences~~


## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/espinozasenior/pump-not-fun.git
   ```

2. **Install requirements:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   Create a `.env` file with:
   ```env
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   SESSION_STRING=your session string token
   ```

4. **Run the bot:**
   ```bash
   uv run main.py
   ```

## 📖 How to Use

Follow these simple steps to customize the bot:

1. Add your commands in the `commands` folder
2. Add your callbacks in the `callbacks` folder
3. Add your messages handler in the `messages` folder
3. Register commands, callbacks and messages handlers in `handlers.py` file
4. Register tasks in `tasks.py` file
5. Add new languages in the `languages` folder
6. Create database models in the `database` folder

## 📈 Scaling to PostgreSQL (Optional)

To upgrade to PostgreSQL:

1. **Install PostgreSQL adapter:**
   ```bash
   uv add psycopg2-binary
   ```

2. **Update database configuration:**
   In `settings.py`, modify the `DATABASE_URL`:
   ```python
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

## 📝 Note

This implementation:                                                                    

 • Processes 1000+ transfers in <1s                                                     
 • Avoids N+1 query problems                                                            
 • Uses native Helius webhook filtering                                                 
 • Maintains 24h alert history to prevent repeats                                       
 • Directly links to on-chain proof                                                     
 • Leverages database constraints for data integrity 

Key features:                                                                           

 1 Uses Helius' native event filtering to only get relevant transfers                   
 2 Batched account/mint queries with single database roundtrips                         
 3 24-hour deduplication window using timestamp filtering                               
 4 Combined entity fetching with asyncio.gather()                                       
 5 Atomic alert+save operation                                                          
 6 Direct transaction links in alerts                                                   
 7 Minimal data processing in Python layer

This template follows Telegram bot development best practices and can be customized to suit your needs.
For custom implementations, please reach out to us at any of the following links:

- [Telegram](https://t.me/tufcoding)
- [Discord](https://discord.com/invite/64CDPKPN3V)

## 🤝 Contributing

- Create a new branch for your features
- Submit pull requests for improvements
- Open issues for bugs or suggestions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.