start redis.cmd
start cmd
call venv\Scripts\activate
flask --debug run --cert=key.crt --key=key.key --host=0.0.0.0
pause