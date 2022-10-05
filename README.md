# msf_api_flask - WIP
## Instructions
### Clone
```sh
git clone https://github.com/nadavcoh/msf_api_flask.git
cd msf_api_flask
```
### venv - Windows
```bat
py -3 -m venv venv
venv\Scripts\activate
```
### venv - Linux/Mac
```sh
python3 -m venv venv
. venv/bin/activate
```
### Requerments
```sh
pip install -r requirements.txt
```
### Configure
Rename `instance/config_example.py` to `instence/config.py` and add your app details.
### Initialize
```sh
flask init-db
```
### Run
```
flask --debug run --cert=adhoc
```

[Todo](todo.md)