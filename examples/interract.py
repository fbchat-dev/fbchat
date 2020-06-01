import fbchat
import requests

session = fbchat.Session.login("<email>", "<password>")

client = fbchat.Client(session)

thread = session.user
# thread = fbchat.User(session=session, id="0987654321")
# thread = fbchat.Group(session=session, id="1234567890")

# Will send a message to the thread
thread.send_text("<message>")

# Will send the default `like` emoji
thread.send_sticker(fbchat.EmojiSize.LARGE.value)

# Will send the emoji `👍`
thread.send_emoji("👍", size=fbchat.EmojiSize.LARGE)

# Will send the sticker with ID `767334476626295`
thread.send_sticker("767334476626295")

# Will send a message with a mention
thread.send_text(
    text="This is a @mention",
    mentions=[fbchat.Mention(thread.id, offset=10, length=8)],
)

# Will send the image located at `<image path>`
with open("<image path>", "rb") as f:
    files = client.upload([("image_name.png", f, "image/png")])
thread.send_text(text="This is a local image", files=files)

# Will download the image at the URL `<image url>`, and then send it
r = requests.get("<image url>")
files = client.upload([("image_name.png", r.content, "image/png")])
thread.send_files(files)  # Alternative to .send_text


# Only do these actions if the thread is a group
if isinstance(thread, fbchat.Group):
    # Will remove the user with ID `<user id>` from the group
    thread.remove_participant("<user id>")
    # Will add the users with IDs `<1st user id>`, `<2nd user id>` and `<3th user id>` to the group
    thread.add_participants(["<1st user id>", "<2nd user id>", "<3rd user id>"])
    # Will change the title of the group to `<title>`
    thread.set_title("<title>")


# Will change the nickname of the user `<user id>` to `<new nickname>`
thread.set_nickname(fbchat.User(session=session, id="<user id>"), "<new nickname>")

# Will set the typing status of the thread
thread.start_typing()

# Will change the thread color to #0084ff
thread.set_color("#0084ff")

# Will change the thread emoji to `👍`
thread.set_emoji("👍")

message = fbchat.Message(thread=thread, id="<message id>")

# Will react to a message with a 😍 emoji
message.react("😍")
