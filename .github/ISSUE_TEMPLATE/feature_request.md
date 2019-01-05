---
name: Feature request
about: Suggest a feature that you'd like to see implemented

---

## Description
Example: There's no way to send messages to groups

## Research (if applicable)
Example: I've found the URL `https://facebook.com/send_message.php`, to which you can send a POST requests with the following JSON:
```json
{
   "text": message_content,
   "fbid": group_id,
   "some_variable": ?
}
```
But I don't know how what `some_variable` does, and it doesn't work without it. I've found some examples of `some_variable` to be: `MTIzNDU2Nzg5MA`, `MTIzNDU2Nzg5MQ` and `MTIzNDU2Nzg5Mg`
