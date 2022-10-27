# msf_api_flask - WIP
## Instructions
### Install dependancies
* Redis - (https://redis.io/docs/getting-started/installation/)
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
### [SSL](https://werkzeug.palletsprojects.com/en/2.2.x/serving/#ssl)
```python
>>> from werkzeug.serving import make_ssl_devcert
>>> make_ssl_devcert('key', host='localhost')
('/path/to/the/key.crt', '/path/to/the/key.key')
```
```sh
flask --debug run --cert=key.crt --key=key.key
```
### External Requests
Only if you trust your local network.
```sh
--host=0.0.0.0
```

[Todo](todo.md)