from datetime import datetime

from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.db import connection

from app.models import User, Entry, Audit


def index(request):
    if request.session.get("user_id"):
        return redirect("entries")
    else:
        return redirect("login")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # WARN: FLAW A07:2021 - Identification and Authentication Failures:
        # We process credential checks infinitely without tracking consecutive bad
        # attempts, leaving the login vulnerable to automated brute-force attacks.

        # FIX: Check if the user account has been locked before verifying credentials

        # existing_user = User.objects.filter(username=username).first()
        # if existing_user and existing_user.failed_attempts >= 3:
        #     return render(
        #         request, "login.html", {"error": "Account locked due to too many failed attempts."}
        #     )

        # WARN: FLAW A02:2021 - Cryptographic Failures:
        # We are checking the plain-text password directly against the database

        user = User.objects.filter(username=username, password_hash=password).first()

        # FIX: Securely verify the password hash.

        # NOTE: You need to uncomment the fix in app/management/commands/seed.py
        # as well, empty the db and reseed it before the fix is applied.

        # user = User.objects.filter(username=username).first()
        # if not (user and check_password(password, user.password_hash)):
        #     user = None

        if user:
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["is_admin"] = user.is_admin

            user.failed_attempts = 0
            user.save()

            return redirect("entries")
        else:
            # FIX: Increment failed try count

            # if existing_user:
            #     existing_user.failed_attempts += 1
            #     existing_user.save()

            return render(
                request, "login.html", {"error": "Invalid username or password"}
            )

    return render(request, "login.html")


def logout(request):
    request.session.flush()
    return redirect("login")


def entries(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    if request.method == "POST":
        start = request.POST.get("start")
        end = request.POST.get("end")
        comment = request.POST.get("comment")

        # WARN: FLAW A03:2021 - Injection:
        # We are using python f-strings to concatenate user input directly into SQL.
        # An attacker can break out of the string using a single quote (') in the
        # comment field.

        cursor = connection.cursor()
        query = f"INSERT INTO app_entry (user_id, start, end, comment) VALUES ({user_id}, '{start}', '{end}', '{comment}')"
        cursor.execute(query)

        # FIX: Use parameterized queries

        # cursor.execute(
        #     "INSERT INTO app_entry (user_id, start, end, comment) VALUES (%s, %s, %s, %s)",
        #     [user_id, start, end, comment],
        # )

        # FIX: Or use the ORM API provided by django

        # Entry.objects.create(user_id=user_id, start=start, end=end, comment=comment)

        return redirect("entries")

    else:
        entries = Entry.objects.filter(user=request.session.get("user_id"))
        return render(request, "entries.html", {"entries": entries})


def admin(request):
    if not request.session["user_id"]:
        return redirect("login")

    # WARN: FLAW A01:2021 - Broken Access Control:
    # We allow any authenticated user to access the admin panel

    # FIX: Restrict access to only admin users

    # if request.session["is_admin"] != True:
    #     request.session.flush()
    #     return redirect("login")

    if request.method == "POST":
        target_user_id = request.POST.get("delete_user_id")

        if target_user_id:
            #  WARN: FLAW A09:2021 - Security Logging and Alerting Failures:
            # The application deletes critical business data silently. If a rogue admin
            # wipes an employee's billable hours, there is no audit trail to hold them accountable.
            Entry.objects.filter(user_id=target_user_id).delete()

            # FIX: Write a deterministic log entry before destroying data

            # admin_username = request.session.get("username")
            # targeted_user = User.objects.filter(id=target_user_id).first()
            # target_name = targeted_user.username if targeted_user else "Unknown User"
            #
            # Audit.objects.create(
            #     action=f"Admin '{admin_username}' permanently wiped all work entries for user '{target_name}' (ID: {target_user_id})."
            # )
            # Entry.objects.filter(user_id=target_user_id).delete()

            # NOTE: In a real production app we would also never just delete these rows,
            # but instead mark them as inactive, so they could be retrieved later on
            # even after being deleted.

        return redirect("admin")

    users_data = []
    all_users = User.objects.all()

    for user in all_users:
        user_entries = Entry.objects.filter(user=user)
        total_hours = 0.0

        for entry in user_entries:
            try:
                start_dt = (
                    datetime.fromisoformat(entry.start)
                    if isinstance(entry.start, str)
                    else entry.start
                )
                end_dt = (
                    datetime.fromisoformat(entry.end)
                    if isinstance(entry.end, str)
                    else entry.end
                )

                if start_dt and end_dt:
                    duration = end_dt - start_dt
                    total_hours += duration.total_seconds() / 3600.0
            except Exception as e:
                print(f"Error calculating duration for entry {entry.id}: {e}")

        users_data.append(
            {
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
                "total_hours": round(total_hours, 2),
            }
        )

    context = {"users": users_data}
    return render(request, "admin.html", context)
