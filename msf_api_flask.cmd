start redis.cmd
call venv\Scripts\activate
start cmd
flask --debug run --cert=key.crt --key=key.key --host=0.0.0.0
pause