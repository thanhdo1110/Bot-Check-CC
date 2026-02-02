# Bot CC Checker - Telegram Bot for Card Information Verification

**Version:** 1.0.0  
**Language:** [English](./README.md) | [Vietnamese](./README-VI.md)  
**Author:** CTDOTEAM - Đỗ Thành #1110  
**Last Updated:** February 2026

---

## ⚠️ DISCLAIMER

This project is provided **AS-IS** without any warranties or guarantees. The author and contributors are **NOT RESPONSIBLE** for:

- Any legal consequences or violations arising from the use of this tool
- Data loss, security breaches, or system failures
- Misuse of credit card information or payment processing APIs
- Compliance violations with payment processor terms of service
- Any damages or losses incurred from using this software

**Users are solely responsible** for ensuring their use complies with all applicable laws and regulations.

---

## 📋 Overview

A high-performance Telegram bot for checking credit card information using BIN (Bank Identification Number) lookup and API testing. The bot provides:

- Real-time card information lookup (bank, country, card type)
- BIN verification with multiple API sources
- User management with VIP tiers
- Daily usage limits and cooldown protection
- Admin controls and maintenance mode
- Comprehensive logging and error handling

---

## ✨ Features

### Core Features
- **BIN Lookup**: Fetch bank, country, and card type from 6-8 digit BIN numbers
- **Multi-API Support**: Round-robin API rotation for redundancy (system-api.pro, noxter.dev)
- **Country Information**: Complete country code, name, and flag emoji mappings
- **High Performance**: Async/await architecture with connection pooling
- **User Management**: VIP tiers, daily limits, usage tracking

### Security & Control
- User whitelist management
- Admin-only operations
- Rate limiting and cooldown protection
- Maintenance mode for admin-only access
- Secure environment variable configuration

### Logging & Monitoring
- Comprehensive logging with timestamps
- Usage statistics and analytics
- Error tracking and debugging
- Activity logs for audit trails

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bot-check-cc.git
   cd bot-check-cc
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required
BOT_TOKEN=your_telegram_bot_token_here

# Optional - API Keys
STRIPE_PUBLIC_KEY=pk_live_xxxxx
THUM_CONNECT_SID=your_thum_connect_sid
THUM_USER_ID=your_thum_user_id

# User & Admin Management
ALLOWED_USERS=123456789,987654321
ADMIN_IDS=111111111,222222222
```

See [.env.example](./.env.example) for complete template.

---

## 📁 Project Structure

```
bot-check-cc/
├── bot.py                 # Main Telegram bot implementation
├── config.py             # Configuration management
├── api_client.py         # Stripe & Thum.io API client
├── bin_lookup.py         # BIN lookup with multi-API support
├── database.py           # SQLite database management
├── user_agents.py        # Rotating user agent pool
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── README-VI.md          # Vietnamese documentation
```

---

## 🔍 BIN Lookup Feature

The bot uses intelligent BIN lookup with multiple API sources:

### Supported APIs
1. **system-api.pro** - Primary API source
2. **noxter.dev** - Fallback API source

### Lookup Information
Returns the following card information:

```json
{
  "brand": "VISA",
  "type": "DEBIT",
  "level": "STANDARD",
  "bank": "Bank Name",
  "country_code": "US",
  "country_name": "United States",
  "country_flag": "🇺🇸",
  "prepaid": false
}
```

### API Round-Robin Strategy
- Each request starts from a different API to distribute load
- Automatically falls back to alternate APIs if one fails
- Merges results from multiple APIs for complete information
- Ensures data reliability and redundancy

---

## 🛠️ API Reference

### Key Modules

#### `bin_lookup.py`
Primary BIN lookup functionality with comprehensive country mappings.

**Main Functions:**
- `lookup_bin(bin_number)` - Async BIN lookup with multi-API support
- `format_bin_info(bin_info)` - Format BIN info for display

#### `api_client.py`
Stripe and Thum.io API integration with high-performance async client.

**Key Methods:**
- `check_card_quick(card_number, month, year, cvc)` - Quick card validation

#### `config.py`
Environment-based configuration management.

**Configuration:**
- BOT_TOKEN, API keys, allowed users, admin IDs
- URL endpoints for API services

#### `database.py`
SQLite database for user management and statistics.

**Tables:**
- `users` - User profiles with VIP status and limits
- `settings` - Global bot settings

---

## 🧪 Testing

### Test BIN Lookup API

```bash
# Using curl to test system-api.pro
curl -s "https://system-api.pro/bin/559888"

# Using curl to test noxter.dev
curl -s "https://noxter.dev/gate/bin?bin=559888"
```

### Manual Testing

```python
import asyncio
from bin_lookup import lookup_bin

async def test():
    result = await lookup_bin("559888")
    print(result)

asyncio.run(test())
```

---

## 📊 Usage Statistics

The bot tracks:
- Total checks per user
- Daily usage with automatic resets
- VIP expiration dates
- User roles and permissions

Access via `/stats` command (admin only).

---

## 🔐 Security Considerations

- **Never commit .env files** - Use .env.example as template
- **Protect Bot Token** - Keep your BOT_TOKEN confidential
- **Whitelist Users** - Use ALLOWED_USERS and ADMIN_IDS
- **Rate Limiting** - Built-in cooldown protection
- **Input Validation** - Strict BIN format validation
- **API Keys** - Store sensitive keys in environment variables

---

## 🐛 Troubleshooting

### Bot Won't Start
```bash
# Check Python version
python --version  # Requires 3.8+

# Verify dependencies
pip list | grep -E "aiogram|aiohttp|python-dotenv"

# Check .env file exists
test -f .env && echo "OK" || echo "Missing .env"
```

### BIN Lookup Fails
- Check internet connection
- Verify API endpoints are accessible:
  ```bash
  curl -s "https://system-api.pro/bin/559888" -o /dev/null -w "%{http_code}\n"
  curl -s "https://noxter.dev/gate/bin?bin=559888" -o /dev/null -w "%{http_code}\n"
  ```
- APIs may have rate limits or geographic restrictions

### Database Lock Error
```bash
# Remove corrupted database
rm -f bot_users.db
# Bot will recreate on next run
```

---

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:

- **aiogram** (>=3.0.0) - Telegram Bot API framework
- **aiohttp** (>=3.9.0) - Async HTTP client library
- **python-dotenv** (>=1.0.0) - Environment variable management

---

## 📝 License & Attribution

**Copyright © CTDOTEAM - Đỗ Thành #1110**

This project is provided for educational and authorized testing purposes only. Users must comply with:
- Telegram Bot API Terms of Service
- Payment processor API terms (Stripe, etc.)
- Local and international regulations
- Responsible disclosure practices

---

## 🤝 Contributing

### Code Standards
- Follow PEP 8 style guide
- Use type hints where applicable
- Add docstrings to functions
- Include error handling
- Test before submitting changes

### Reporting Issues
Please report bugs or feature requests via GitHub Issues.

---

## 📞 Support

For questions, issues, or inquiries:
- Check documentation (README.md, README-VI.md)
- Review troubleshooting section
- Open a GitHub issue
- Contact: CTDOTEAM - Đỗ Thành #1110

---

## 🔄 Updates & Maintenance

- Regular updates for API compatibility
- Security patches as needed
- Dependency updates and version bumps
- Performance optimizations

---

## 📚 References

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram Documentation](https://docs.aiogram.dev/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [BIN Database](https://en.wikipedia.org/wiki/Payment_card_number)

---

**Last Updated:** February 2026  
**Status:** Active  
**Python Version:** 3.8+

---

*This README serves as the primary English documentation. See [README-VI.md](./README-VI.md) for Vietnamese version.*
