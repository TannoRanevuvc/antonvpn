"""Custom AntonVPN subscription page — replaces remnawave/subscription-page container."""
import re
from datetime import datetime, timezone

import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from config import settings

router = APIRouter()

# User-agents of VPN clients that expect raw subscription data
_VPN_CLIENT_RE = re.compile(
    r"clash|v2ray|shadowrocket|quantumult|surge|hiddify|sing.?box|"
    r"streisand|stash|loon|nekobox|nekoray|karing|flclash|mihomo|xray",
    re.I,
)

_REMNAWAVE_INTERNAL = settings.REMNAWAVE_PANEL_URL.rstrip("/")
_TOKEN = settings.REMNAWAVE_TOKEN


async def _remnawave_get(path: str) -> dict | None:
    url = f"{_REMNAWAVE_INTERNAL}{path}"
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(url, headers={"Authorization": f"Bearer {_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=10))
            if resp.status == 200:
                data = await resp.json()
                return data.get("response") if isinstance(data.get("response"), dict) else data
    except Exception:
        pass
    return None


async def _proxy_raw_sub(short_uuid: str) -> Response:
    url = f"{_REMNAWAVE_INTERNAL}/api/sub/{short_uuid}"
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(url, headers={"Authorization": f"Bearer {_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=10))
            content = await resp.read()
            ct = resp.headers.get("content-type", "text/plain; charset=utf-8")
            headers = {}
            for h in ("subscription-userinfo", "profile-update-interval", "content-disposition"):
                if h in resp.headers:
                    headers[h] = resp.headers[h]
            return Response(content=content, media_type=ct, headers=headers)
    except Exception:
        return Response(content=b"", status_code=502)


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return iso[:10]


def _days_left(iso: str | None) -> int:
    if not iso:
        return 0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = dt - datetime.now(timezone.utc)
        return max(0, delta.days)
    except Exception:
        return 0


@router.get("/sub/{short_uuid}")
async def subscription_page(short_uuid: str, request: Request) -> Response:
    ua = request.headers.get("user-agent", "")

    if _VPN_CLIENT_RE.search(ua):
        return await _proxy_raw_sub(short_uuid)

    # Fetch subscription info
    info = await _remnawave_get(f"/api/users/by-short-uuid/{short_uuid}")

    if not info:
        return HTMLResponse(content=_render_error("Подписка не найдена"), status_code=404)

    status = info.get("status", "UNKNOWN")
    expire_iso = info.get("expireAt")
    expire_str = _fmt_date(expire_iso)
    days = _days_left(expire_iso)
    is_active = status == "ACTIVE"

    # Build the clean sub-page URL (browser-facing)
    from urllib.parse import urlparse
    parsed = urlparse(settings.ADMIN_PUBLIC_BASE_URL)
    public_base = f"{parsed.scheme}://{parsed.netloc}"
    sub_url = f"{public_base}/sub/{short_uuid}"

    return HTMLResponse(content=_render_page(sub_url, expire_str, days, is_active))


def _render_error(msg: str) -> str:
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<title>AntonVPN</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;background:#0d1117;color:#fff;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;}}
.box{{text-align:center;}}.icon{{font-size:48px;}}.msg{{color:#8b949e;margin-top:8px;}}</style></head>
<body><div class="box"><div class="icon">🔒</div><h2>AntonVPN</h2><p class="msg">{msg}</p></div></body></html>"""


def _render_page(sub_url: str, expire_str: str, days: int, is_active: bool) -> str:
    status_color = "#2ea043" if is_active else "#f85149"
    status_text = "Активна" if is_active else "Неактивна"
    days_text = f"{days} дн." if days > 0 else "Истекла"
    days_color = "#2ea043" if days > 7 else ("#e3b341" if days > 0 else "#f85149")

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AntonVPN — Подписка</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --bg:#0d1117;--card:#161b22;--border:#30363d;--blue:#2188ff;
    --text:#e6edf3;--muted:#8b949e;--green:#2ea043;--yellow:#e3b341;
  }}
  body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh;padding:16px}}
  .wrap{{max-width:480px;margin:0 auto;padding-bottom:32px}}
  .header{{display:flex;align-items:center;gap:12px;padding:24px 0 20px}}
  .logo-icon{{width:44px;height:44px;background:linear-gradient(135deg,#2188ff,#0969da);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0}}
  .logo-name{{font-size:20px;font-weight:700;color:var(--text)}}
  .logo-sub{{font-size:12px;color:var(--muted);margin-top:2px}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:12px}}
  .card-title{{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:14px}}
  .status-row{{display:flex;justify-content:space-between;align-items:center}}
  .badge{{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}}
  .badge-active{{background:rgba(46,160,67,.15);color:{status_color};border:1px solid rgba(46,160,67,.3)}}
  .badge-inactive{{background:rgba(248,81,73,.15);color:#f85149;border:1px solid rgba(248,81,73,.3)}}
  .meta-row{{display:flex;gap:24px;margin-top:14px}}
  .meta-item label{{display:block;font-size:11px;color:var(--muted);margin-bottom:4px}}
  .meta-item span{{font-size:15px;font-weight:600}}
  .url-box{{background:#0d1117;border:1px solid var(--border);border-radius:8px;padding:12px;font-family:"SF Mono",Consolas,monospace;font-size:12px;color:var(--muted);word-break:break-all;line-height:1.5;margin-bottom:12px;cursor:pointer;transition:border-color .2s}}
  .url-box:hover{{border-color:var(--blue)}}
  .btn{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:12px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;text-decoration:none;transition:opacity .15s}}
  .btn:hover{{opacity:.85}}
  .btn-primary{{background:var(--blue);color:#fff;margin-bottom:8px}}
  .btn-outline{{background:transparent;border:1px solid var(--border);color:var(--text);margin-bottom:8px}}
  .qr-wrap{{display:flex;justify-content:center;padding:8px 0 4px}}
  .qr-wrap canvas,.qr-wrap img{{border-radius:8px}}
  .clients{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
  .client-btn{{display:flex;align-items:center;gap:10px;padding:12px;background:#0d1117;border:1px solid var(--border);border-radius:8px;text-decoration:none;color:var(--text);transition:border-color .2s;font-size:13px;font-weight:500}}
  .client-btn:hover{{border-color:var(--blue)}}
  .client-icon{{font-size:20px;flex-shrink:0}}
  .client-info small{{display:block;color:var(--muted);font-size:11px;margin-top:1px}}
  .platform-tabs{{display:flex;gap:4px;margin-bottom:12px;background:#0d1117;border-radius:8px;padding:4px}}
  .tab{{flex:1;padding:7px;text-align:center;font-size:12px;font-weight:600;border-radius:6px;cursor:pointer;color:var(--muted);border:none;background:transparent;transition:all .15s}}
  .tab.active{{background:var(--card);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.4)}}
  .platform-content{{display:none}}.platform-content.active{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
  .divider{{height:1px;background:var(--border);margin:4px 0 16px}}
  .copied-toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#2ea043;color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:600;opacity:0;pointer-events:none;transition:opacity .2s}}
  .copied-toast.show{{opacity:1}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo-icon">🔒</div>
    <div>
      <div class="logo-name">AntonVPN</div>
      <div class="logo-sub">Ваша подписка</div>
    </div>
  </div>

  <!-- Status card -->
  <div class="card">
    <div class="card-title">Статус подписки</div>
    <div class="status-row">
      <span class="badge {'badge-active' if is_active else 'badge-inactive'}">{status_text}</span>
    </div>
    <div class="meta-row">
      <div class="meta-item">
        <label>Действует до</label>
        <span>{expire_str}</span>
      </div>
      <div class="meta-item">
        <label>Осталось</label>
        <span style="color:{days_color}">{days_text}</span>
      </div>
    </div>
  </div>

  <!-- QR & copy card -->
  <div class="card">
    <div class="card-title">Ссылка подписки</div>
    <div class="qr-wrap" id="qr"></div>
    <div style="margin-top:12px"></div>
    <div class="url-box" onclick="copyUrl()" title="Нажмите, чтобы скопировать">{sub_url}</div>
    <button class="btn btn-primary" onclick="copyUrl()">
      <span>📋</span> Скопировать ссылку
    </button>
  </div>

  <!-- Download card -->
  <div class="card">
    <div class="card-title">Скачать клиент</div>
    <div class="platform-tabs">
      <button class="tab active" onclick="setTab('android',this)">Android</button>
      <button class="tab" onclick="setTab('ios',this)">iOS</button>
      <button class="tab" onclick="setTab('windows',this)">Windows</button>
      <button class="tab" onclick="setTab('mac',this)">macOS</button>
    </div>

    <div id="tab-android" class="platform-content active">
      <a class="client-btn" href="https://play.google.com/store/apps/details?id=com.hiddify.app" target="_blank">
        <span class="client-icon">🛡️</span>
        <div class="client-info">Hiddify<small>Рекомендуем</small></div>
      </a>
      <a class="client-btn" href="https://play.google.com/store/apps/details?id=com.v2ray.ang" target="_blank">
        <span class="client-icon">📱</span>
        <div class="client-info">v2rayNG<small>Популярный</small></div>
      </a>
    </div>

    <div id="tab-ios" class="platform-content">
      <a class="client-btn" href="https://apps.apple.com/app/streisand/id6450534064" target="_blank">
        <span class="client-icon">🛡️</span>
        <div class="client-info">Streisand<small>Бесплатный</small></div>
      </a>
      <a class="client-btn" href="https://apps.apple.com/app/shadowrocket/id932747118" target="_blank">
        <span class="client-icon">🚀</span>
        <div class="client-info">Shadowrocket<small>$2.99</small></div>
      </a>
    </div>

    <div id="tab-windows" class="platform-content">
      <a class="client-btn" href="https://github.com/hiddify/hiddify-app/releases/latest" target="_blank">
        <span class="client-icon">🛡️</span>
        <div class="client-info">Hiddify<small>Рекомендуем</small></div>
      </a>
      <a class="client-btn" href="https://github.com/MatsuriDayo/nekoray/releases/latest" target="_blank">
        <span class="client-icon">🐱</span>
        <div class="client-info">NekoRay<small>Продвинутый</small></div>
      </a>
    </div>

    <div id="tab-mac" class="platform-content">
      <a class="client-btn" href="https://github.com/hiddify/hiddify-app/releases/latest" target="_blank">
        <span class="client-icon">🛡️</span>
        <div class="client-info">Hiddify<small>Рекомендуем</small></div>
      </a>
      <a class="client-btn" href="https://apps.apple.com/app/streisand/id6450534064" target="_blank">
        <span class="client-icon">🛡️</span>
        <div class="client-info">Streisand<small>Бесплатный</small></div>
      </a>
    </div>
  </div>

  <!-- How to connect -->
  <div class="card">
    <div class="card-title">Как подключиться</div>
    <ol style="padding-left:18px;color:var(--muted);font-size:14px;line-height:1.9">
      <li>Скачайте VPN-клиент для вашего устройства</li>
      <li>Скопируйте ссылку подписки выше</li>
      <li>Откройте клиент → «Добавить подписку» → вставьте ссылку</li>
      <li>Выберите сервер и нажмите «Подключить»</li>
    </ol>
  </div>
</div>

<div class="copied-toast" id="toast">✓ Скопировано</div>

<script>
const SUB_URL = {repr(sub_url)};

// QR code
new QRCode(document.getElementById("qr"), {{
  text: SUB_URL,
  width: 180,
  height: 180,
  colorDark: "#ffffff",
  colorLight: "#161b22",
  correctLevel: QRCode.CorrectLevel.M
}});

// Detect platform
const ua = navigator.userAgent.toLowerCase();
if (/iphone|ipad|ipod/.test(ua)) setTab('ios', document.querySelector('.tab:nth-child(2)'));
else if (/macintosh/.test(ua)) setTab('mac', document.querySelector('.tab:nth-child(4)'));
else if (/windows/.test(ua)) setTab('windows', document.querySelector('.tab:nth-child(3)'));

function copyUrl() {{
  navigator.clipboard.writeText(SUB_URL).then(() => {{
    const t = document.getElementById('toast');
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
  }});
}}

function setTab(name, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.platform-content').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}}
</script>
</body>
</html>"""
