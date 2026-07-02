LINK: [https://github.com/jannesaranpaa/billable](https://github.com/jannesaranpaa/billable)
Installation is done with the django `manage.py`-script. You may run
```shell
python manage.py migrate
python manage.py seed
python manage.py runserver
```
to start the app. The seed command inserts two users:

1. admin:admin
2. worker:worker

The app has now other ways of adding users, so you have to use the seed command.

The admin user is a privileged user, while the worker is an unprivileged one.

I followed the [2021 OWASP top ten list](https://owasp.org/Top10/2021/).

FLAW 1:
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L28](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L28)

Flaw A07:2021 - Identification and Authentication Failures. The application
processes credential checks indefinitely, without tracking the bad attempts
made. This leaves the login system vulnerable to automated brute force attacks.
A dictionary attack similar to the one used earlier on this course could break
in to both of the seeded accounts almost instantly. Partly this is because of
the poor passwords of the seeded accounts, but a system should never rely on
passwords being hard to guess.

This flaw can be fixed by storing a counter of consecutive failed login attempts
for a user, and checking if there have been too many when trying to log in,
essentially locking the account. In a production app we should combine this
with rate limiting, and DDOS protection on the server infrastructure, so
that a botnet dictionary attack would not bring the service down.

In this demo application there is no way to unlock the account besides of
manipulating the database directly. A real application would have
a tool for the administrators to unlock an account, and that should trigger
a forced password change.

![Flaw 1 - before the fix a user can try to login as many times as they want](/screenshots/flaw-1-before.png)
![Flaw 1 - after the fix the account will be locked after 3 failed
attempts](/screenshots/flaw-1-after.png)

FLAW 2:
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L37](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L37)
and
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/management/commands/seed.py#L16](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/management/commands/seed.py#L16)

Flaw A02:2021 - Cryptographic Failures. The application stores the plain-text
password directly in the database, and checks for that plain-text password
against the database. This way any malicious access to the database would leak
all the passwords stored in the application, alongside the user account names.
While it is bad practice to use the same username and password combination on
multiple sites, it is very common. This flaw could endanger the users'
information across many services, potentially endangering even human lives.

This flaw can be fixed by using the `check_password` and `make_passwords`
functions provided by django. When storing user passwords we create secure
hashes and never store the plaintext password on the server, and when the user
types in the password, we hash it and check against the hash in the database.
This way a leaked database would only contain hashes of salted passwords,
that could not be reverted to the plaintext passwords.

Note that the fix requires modifying both the seed script and the views of the
application, and you will have to empty the database and reseed it for the fix
to be applied.

It would also be paramount to not store the secret key used by the encryption
functions in the repository, as we now do in [https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/settings.py#L23](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/settings.py#L23). Instead we should
generate a new key per installation, and store that in a protected .env file,
that would never leave the server in question.

![Flaw 2 - before the fix we have plaintext passwords in the
database](/screenshots/flaw-2-before.png)
![Flaw 2 - after the fix the passwords are hashed](/screenshots/flaw-2-after.png)

FLAW 3:
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L92](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L92)

Flaw A03:2021 - Injection. The application uses [f-strings](https://docs.python.org/3/tutorial/inputoutput.html#tut-f-strings) to inject user input directly into an sql-query with no escaping of the input.
This allows the user to break out of the query simply by inserting one quote
character (') into their input, and after that they can run arbitrary sql
queries. For example with the following comment: `Injection! ' || (SELECT password_hash FROM app_user WHERE username='admin') || '` the user can select the admin password and see it in the
outputted comment.

In the screenshot the password is not hashed, since I'm running with all the
flaws in the code. This flaw alone wouldn't leave the passwords in the database
as plaintext like this.

There is only one screenshot for this flaw, and it includes the results of
running this query without the fixes, and with the fixes as well.

This can be fixed by either using parameterized queries via the sqlite API,
or with an ORM like the one django uses. Both solutions are provided in the
source code. Either fix will escape the inputs that are inserted into the
query, so that they can't run any sql code.

With these solutions we are placing lots of trust in the APIs we are using to
escape user input, but the amount of edge cases and potential attacks are so
many, that we shouldn't try to write an escaper ourselves. Instead, we should
rely on well known and vetted solutions, which are frequently verified by
experts.

![Flaw 3 - Image showcasing results of the flaw](/screenshots/flaw-3-before.png)
![Flaw 3 - Image showcasing results of the fix](/screenshots/flaw-3-after.png)

FLAW 4:
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L122](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L122)

Flaw A01:2021 - Broken Access Control. The application allows any authenticated
account to access the admin panel. The app hides the navigation link for
the admin panel for non-admin users, but it doesn't prevent the users from
manually navigating to
[http://127.0.0.1:1234/admin/](http://127.0.0.1:1234/admin/). (Note that the
port might be different for you!)
This allows any non-admin user to see sensitive information, and potentially to
execute dangerous actions.

The fix is to check if the user is an admin before serving the page, and
redirecting them to login and flushing their session if they are not. The
fact that the user tried to access the admin panel should also be logged, but
that is not implemented for this demo.

The screenshot after the fix is of the terminal the server is running at,
because the browser window wouldn't show any difference from a normal access
at the login page. From the server output we can see that the user was in fact
redirected to the login. The before screenshot shows that the account is 'worker',
but we are still in the admin panel.

![Flaw 4 - Before the fix the worker account can navigate to the admin
panel](/screenshots/flaw-4-before.png)
![Flaw 4 - After the fix the user is redirected to
login](/screenshots/flaw-4-after.png)
![Flaw 4 - Network requests after the flaw - a](/screenshots/flaw-4-response_a.png)
![Flaw 4 - Network requests after the flaw - b](/screenshots/flaw-4-response_b.png)
![Flaw 4 - Server terminal output](/screenshots/flaw-4-after-server.png)

FLAW 5:
[https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L133](https://github.com/jannesaranpaa/billable/blob/c1e2492bf099064c75e9780552713ccd74948fe4/app/views.py#L133)

Flaw A09:2021 - Security Logging and Alerting Failures. The application doesn't
hold a log of dangerous actions, such as wiping a users hours. In the admin panel
there is an option where an admin can wipe all the entries for a user. This action
is not logged anywhere, and the data is permanently gone. A single compromised
admin user could cause significant harm to the company running this service.

The fix is to implement an audit log, which tracks dangerous actions such as these
in the database. That way it is possible to identify who deleted the information.
It would also be important to not actually remove the data, but to soft delete it
via a flag in the database table so that it could be retrieved, but that is not
implemented in this demo. This fix would however enable the company to find the
person responsible for the data loss, and seeking compensation from them.

The screenshots are from the database, since there is no frontend for the audit
log implemented. The screenshots show that first there was data in the entry
table, but it has been wiped between the queries. The before screenshot shows that
the audit log retains no information about what happened. The after screenshot
shows that now there is an audit log, and we can see that admin deleted all of 
their own hours. If this action needed to be investigated by the company, they
would now know who to start asking questions.

In a production application the audit log would have a frontend, and the
entities would contain all the necessary information to retain the earlier
state.

![Flaw 5 - Before the fix there is no audit log](/screenshots/flaw-5-before.png)
![Flaw 5 - After the fix the audit log shows who did and
what](/screenshots/flaw-5-after.png)

