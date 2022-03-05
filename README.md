# siren-notifier

Siren-notifier is a Python project to warn people of danger by calling in a telegram to specified users.

Due to the fact that there is no single common source for the notification of citizens about the siren - you are invited to change the base event that will trigger a call to the specified usernames.

In my case, the trigger event is a message with a photo about turning on / off the air raid alarm in the channel of [the Khmelnytsky city council](https://t.me/khm_gov_ua).

## Installation

To run this project clone it and install specified requirements using the package manager [pip](https://pip.pypa.io/en/stable/) in the next way:

```bash
pip install -r requirements.txt
```

Also you need to make some changes in the session.conf file. Specify `api_id` and `api_hash` from https://my.telegram.org/apps. `session_name` could be any string, for example you can provide your own username.

## Usage

```bash
python run.py --dial_usernames @username_1 @username_2 --url_to_channel https://t.me/khm_gov_ua
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)