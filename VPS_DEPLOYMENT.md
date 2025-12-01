# VPS Deployment Guide

## Prerequisites

- Ubuntu 20.04+ VPS
- SSH access with sudo privileges
- Python 3.8+
- Git

## Quick Deployment (Recommended)

### Option 1: Automated Script

```bash
# 1. Clone repository
git clone https://github.com/Lakodros-dev/HR-tracker.git
cd HR-tracker

# 2. Make deploy script executable
chmod +x deploy.sh

# 3. Run deployment
sudo ./deploy.sh

# 4. Configure environment
sudo nano /home/ubuntu/HR-tracker/.env
# Add your BOT_TOKEN, ADMIN_ID, etc.

# 5. Restart bot
sudo systemctl restart hr-tracker-bot
```

### Option 2: Manual Deployment

```bash
# 1. System dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# 2. Clone repository
git clone https://github.com/Lakodros-dev/HR-tracker.git
cd HR-tracker

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env
# Fill in: BOT_TOKEN, ADMIN_ID, etc.

# 6. Test bot
python bot.py
# Press Ctrl+C to stop

# 7. Setup systemd service
sudo cp hr-tracker-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hr-tracker-bot
sudo systemctl start hr-tracker-bot

# 8. Check status
sudo systemctl status hr-tracker-bot
```

## Environment Variables

Required variables in `.env`:

```bash
# Telegram Bot Token (from @BotFather)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Admin ID (your Telegram user ID)
# For single admin: ADMIN_ID=123456789
# For multiple admins: ADMIN_ID=123456789,987654321
ADMIN_ID=your_telegram_id

# Office Location (optional, can be configured via bot)
OFFICE_LATITUDE=41.2995
OFFICE_LONGITUDE=69.2401
ALLOWED_DISTANCE=100

# Mini App URL (if using office map feature)
MINI_APP_URL=https://your-mini-app-url.com/

# Backend URL (for settings sync)
BACKEND_URL=https://your-backend-url.com
```

## Service Management

```bash
# Start bot
sudo systemctl start hr-tracker-bot

# Stop bot
sudo systemctl stop hr-tracker-bot

# Restart bot
sudo systemctl restart hr-tracker-bot

# Check status
sudo systemctl status hr-tracker-bot

# View logs (realtime)
sudo journalctl -u hr-tracker-bot -f

# View logs (last 100 lines)
sudo journalctl -u hr-tracker-bot -n 100
```

## Updating Bot

```bash
cd /home/ubuntu/HR-tracker

# Stop bot
sudo systemctl stop hr-tracker-bot

# Pull latest changes
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart bot
sudo systemctl start hr-tracker-bot
```

## Troubleshooting

### Bot not starting

```bash
# Check service status
sudo systemctl status hr-tracker-bot

# Check logs
sudo journalctl -u hr-tracker-bot -n 50

# Common issues:
# 1. Invalid BOT_TOKEN - check .env file
# 2. Missing dependencies - run: pip install -r requirements.txt
# 3. Permission issues - check file ownership
```

### Database issues

```bash
# Check database file exists
ls -lh /home/ubuntu/HR-tracker/attendance.db

# If corrupted, restore from backup
cp /home/ubuntu/HR-tracker/attendance.db.backup /home/ubuntu/HR-tracker/attendance.db
```

### Permission issues

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/HR-tracker
```

## Backup & Maintenance

### Manual Backup

```bash
# Backup database
cp /home/ubuntu/HR-tracker/attendance.db \
   /home/ubuntu/HR-tracker/backups/attendance-$(date +%Y%m%d).db

# Backup .env
cp /home/ubuntu/HR-tracker/.env \
   /home/ubuntu/HR-tracker/backups/env-$(date +%Y%m%d).backup
```

### Automated Backup (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at midnight
0 0 * * * cp /home/ubuntu/HR-tracker/attendance.db /home/ubuntu/HR-tracker/backups/attendance-$(date +\%Y\%m\%d).db

# Add weekly cleanup (keep last 30 days)
0 1 * * 0 find /home/ubuntu/HR-tracker/backups -name "attendance-*.db" -mtime +30 -delete
```

## Security Recommendations

1. **Never commit .env to Git**
2. **Use strong bot token** (get from @BotFather)
3. **Restrict SSH access** (use SSH keys, disable password login)
4. **Enable firewall** (allow only SSH and required ports)
5. **Regular backups** (setup automated backups)
6. **Keep system updated** (`sudo apt-get update && sudo apt-get upgrade`)

## Monitoring

### Check bot is running

```bash
# Process check
ps aux | grep "python bot.py"

# Service check
systemctl is-active hr-tracker-bot
```

### Disk space

```bash
# Check disk usage
df -h

# Check database size
du -h /home/ubuntu/HR-tracker/attendance.db
```

### Memory usage

```bash
# Check memory
free -h

# Check bot memory
ps aux | grep "python bot.py" | awk '{print $6}'
```

## Support

For issues, check:
1. Bot logs: `sudo journalctl -u hr-tracker-bot -f`
2. System logs: `sudo tail -f /var/log/syslog`
3. Database integrity: `sqlite3 attendance.db "PRAGMA integrity_check;"`

## Done! 🎉

Your bot should now be running on VPS. Test it by sending `/start` to your bot on Telegram.
