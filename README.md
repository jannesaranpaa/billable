# Billable

A basic billables tracker for the [cybersecurity MOOC project](https://cybersecuritybase.mooc.fi/module-3.1).

## How to run

Assuming you already have `django` installed and ready to go, just run

```shell
python manage.py migrate
python manage.py seed
python manage.py runserver
```

The seed command will provide you with two accounts:
1. admin:admin
2. worker:worker

These can be used to test the security flaws presented. I have not implemented a
way to create accounts any other way, so it is necessary to run the seed command.

### I don't have django installed!?

You may find instructions here at [djangoproject.com](https://www.djangoproject.com/), and I would recommend creating a virtual environment like [venv](https://docs.python.org/3/library/venv.html) or using [uv](https://docs.astral.sh/uv/) so that you don't crowd your local python installation with my packages.

When you have an environment up, you can run `pip -r requirements.txt` to install the
necessary packages, and then follow the earlier instructions.
