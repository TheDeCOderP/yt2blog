# YouTube Transcript API - Proxy Configuration Guide

Since your Ubuntu server is using Apache with a proxy, follow these steps to ensure the Streamlit app uses it correctly.

## Option 1: System-wide Proxy (Recommended)

Set proxy environment variables at the system level so all applications use them.

### 1. Edit `/etc/environment` (system-wide)
```bash
sudo nano /etc/environment
```

Add these lines:
```
http_proxy="http://your-proxy-ip:port"
https_proxy="http://your-proxy-ip:port"
HTTP_PROXY="http://your-proxy-ip:port"
HTTPS_PROXY="http://your-proxy-ip:port"
```

### 2. Apply changes
```bash
source /etc/environment
```

### 3. Verify proxy is set
```bash
echo $http_proxy
echo $HTTP_PROXY
```

### 4. Restart PM2 process
```bash
cd /var/www/yt2blog
./deploy.sh
```

---

## Option 2: PM2 Ecosystem File (Alternative)

Create a PM2 ecosystem file for more control.

### 1. Create `ecosystem.config.js`
```bash
cat > /var/www/yt2blog/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'yt2blog-3030',
    script: 'venv/bin/streamlit',
    args: 'run app.py --server.port=3030 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false',
    interpreter: 'none',
    env: {
      http_proxy: 'http://your-proxy-ip:port',
      https_proxy: 'http://your-proxy-ip:port',
      HTTP_PROXY: 'http://your-proxy-ip:port',
      HTTPS_PROXY: 'http://your-proxy-ip:port'
    }
  }]
};
EOF
```

### 2. Start with ecosystem file
```bash
pm2 start ecosystem.config.js
pm2 save
```

---

## Option 3: .env File (Simple)

Add proxy URL directly to `.env`:

```bash
GEMINI_API_KEY='your-key-here'
PROXY_URL=http://your-proxy-ip:port
```

The app will automatically detect and use it.

---

## Verify It's Working

### 1. Check if proxy is being used
```bash
pm2 logs yt2blog-3030 | grep -i proxy
```

### 2. Test transcript fetch
Try generating a blog from a YouTube video. If it works, the proxy is configured correctly.

### 3. Check environment variables in PM2
```bash
pm2 env yt2blog-3030
```

---

## Troubleshooting

### If still getting "IP blocked" error:

1. **Verify proxy is working:**
   ```bash
   curl -x http://your-proxy-ip:port https://www.youtube.com
   ```

2. **Check PM2 logs:**
   ```bash
   pm2 logs yt2blog-3030 -f
   ```

3. **Restart PM2 with fresh environment:**
   ```bash
   pm2 kill
   source /etc/environment
   cd /var/www/yt2blog
   ./deploy.sh
   ```

4. **Check if proxy requires authentication:**
   If your proxy needs credentials, use format:
   ```
   http://username:password@proxy-ip:port
   ```

---

## Apache Proxy Configuration (Reference)

If you're using Apache as a forward proxy, ensure these modules are enabled:

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_connect
sudo systemctl restart apache2
```

Your Apache VHost should have:
```apache
ProxyRequests On
ProxyVia On
<Proxy *>
    Order allow,deny
    Allow all
</Proxy>
```

---

## Quick Test

Run this to verify the app can fetch transcripts:

```bash
cd /var/www/yt2blog
source venv/bin/activate
python3 << 'EOF'
from app import fetch_transcript_with_proxy
import os

# Test with a known video
vid = "dQw4w9WgXcQ"  # Rick Roll
try:
    data = fetch_transcript_with_proxy(vid)
    print(f"✅ Success! Fetched {len(data)} transcript entries")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

---

## Support

If issues persist:
1. Verify proxy IP and port are correct
2. Check if proxy requires authentication
3. Ensure proxy allows HTTPS connections
4. Try with a different video URL
