# feedback.designers.italia.it

Backend for the feedback form of https://designers.italia.it

## `POST /api/messages`

Sends an email to `MAIL_ADDRESSES` (env variable with comma separated list of email addresses) containing
the formatted payload.

The raw payload is also base64 encoded in the `X-Serialized` email header.

### Payload

```json
{
    "feedback": "+",
    "url": "https://designers.italia.it/home",
    "who": "progettista",
    "from": "motore-di-ricerca",
    "details": "potentially long text\nwith details\n",
    "captcha": "captcha-challenge-string"
  }
```

Where:
* `feedback`: is the feedback for the page and can be either `+` or `-`
* `url`: is the page the feedback is about
* `who`: is the type of user
* `from`: is where the user found this page
* `details`: are the additional details the user wrote to the form
* `captcha`: is the CAPTCHA challenge string from reCAPTCHA, if CAPTCHA is enable with the `CAPTCHA_ENABLED` environment variable at build time

### Response

#### Success

HTTP code 200

```json
{ "message": "ok" }
```

#### CAPTCHA verification failed (if CAPTCHA is enabled)

HTTP code 400

```json
{ "message": "Captcha verification failed" }
```

#### Other errors

HTTP code < 200 or HTTP code > 400

```json
{ "message": "Error details" }
```
