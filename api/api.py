import base64
import html
import hashlib
import os
from json import dumps

import requests
from sanic import Blueprint
from sanic.response import empty, json

MAILGUN_KEY = os.environ.get("MAILGUN_KEY", "")
MAIL_ADDRESSES = os.environ.get("MAIL_ADDRESSES", "")
CAPTCHA_ENABLED = os.environ.get("CAPTCHA_ENABLED", False)

bp = Blueprint("api", url_prefix="/api")


@bp.options("/messages")
async def preflight(_req, _path=""):
    return empty()

@bp.post("/messages")
async def message(req):
    fields = ["feedback", "url", "who", "from", "details"]

    if CAPTCHA_ENABLED:
      captcha = req.json.get("captcha", "")

      res = requests.post(
          f"https://www.google.com/recaptcha/api/siteverify",
          data={"secret": os.environ.get("CAPTCHA_KEY", ""), "response": captcha},
      )
      if res.status_code != 200 or not res.json().get("success"):
          return json(res.json(), status=res.status_code)

    feedback = req.json.get('feedback', '')
    if not feedback in ['+', '-']:
      return json({"message": "Invalid feedback field"}, status=422)

    icon = {'+': '👍', '-': '👎'}[feedback]
    escaped = {k: html.escape(req.json.get(k, '-')) for k in fields}

    ip = req.headers.get("x-real-ip", "")

    # Use more
    accept_language = req.headers.get("accept-language", "")
    accept_encoding = req.headers.get("accept-encoding", "")
    user_agent = req.headers.get("user-agent", "")

    # Remove last IP octet for anoymization
    octets = ip.split(".")
    ip = '.'.join(octets[:-1]) if len(octets) > 1 else octets[0]

    # Remove last IPv6 hextet (if there evel will be any, Vercel doesn't support IPv6 yet)
    hextets = ip.split(":")
    ip = ':'.join(hextets[:-1]) if len(hextets) > 1 else hextets[0]

    user_id = hashlib.sha256(f"{ip}{accept_language}{accept_encoding}{user_agent}".encode('utf-8')).hexdigest()

    body = f"""
    <p>
      Feedback per {escaped['url']}</a>
    </p>
    <dl>
      <dt><strong>Questa pagina ti è stata utile?</strong></dt>
      <dd>{icon}</dd>

      <dt><strong>Sono</strong></dt>
      <dd>{escaped['who']}</dd>

      <dt><strong>Ho trovato questa pagina grazie a</strong></dt>
      <dd>{escaped['from']}</dd>

      <dt><strong>Come possiamo migliorare questa pagina</strong></dt>
      <dd>{escaped['details'][:200]}</dd>

      <dt><strong>User id</strong></dt>
      <dd>{user_id}</dd>
    </dl>
    """

    res = requests.post(
        "https://api.eu.mailgun.net/v3/designers.italia.it/messages",
        auth=("api", MAILGUN_KEY),
        data={
            "from": "no-reply@designers.italia.it",
            "to": MAIL_ADDRESSES,
            "subject": f"{icon} Feedback dal sito designers.italia.it",
            "html": body,
            "h:X-Serialized": base64.b64encode(dumps({k: req.json.get(k, "") for k in fields}).encode('utf-8')),
        },
    )
    if res.status_code != 200:
        try:
          return json(res.json(), status=res.status_code)
        except requests.exceptions.JSONDecodeError:
          return json({"message": res.text}, status=res.status_code)

    return json({"message": "ok"})
