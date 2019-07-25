---
name: Bug report
about: Create a report if you're having trouble with `fbchat`

---

## Description of the problem
Example: Logging in fails when the character `%` is in the password. A specific password that fails is `a_password_with_%`

## Code to reproduce
```py
# Example code
from fbchat import Client
client = Client("[REDACTED_USERNAME]", "a_password_with_%")
```

## Traceback
```
Traceback (most recent call last):
  File "<test.py>", line 1, in <module>
  File "[site-packages]/fbchat/client.py", line 78, in __init__
    self.login(email, password, max_tries)
  File "[site-packages]/fbchat/client.py", line 407, in login
    raise FBchatUserError('Login failed. Check email/password. (Failed on URL: {})'.format(login_url))
fbchat.models.FBchatUserError: Login failed. Check email/password. (Failed on URL: https://m.facebook.com/login.php?login_attempt=1)
```

## Environment information
- Python version
- `fbchat` version
- If relevant, output from `$ python -m pip list`

If you have done any research, include that.
Make sure to redact all personal information.
