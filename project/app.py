import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///brawl_stars.db")
brawler_list = db.execute("SELECT name FROM brawlers")
brawler_list = [value for dictionary in brawler_list for value in dictionary.values()]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def main():
    """Show Account Stats"""
    account_id = session["user_id"]

    acc_username = db.execute("SELECT username FROM user WHERE id = ?", account_id)[0]
    acc_trophies = db.execute("SELECT trophies FROM user WHERE id = ?", account_id)[0]
    acc_kills = db.execute("SELECT SUM(kills) FROM user_brawlers WHERE user_id = ?", account_id)[0]
    acc_deaths = db.execute("SELECT SUM(deaths) FROM user_brawlers WHERE user_id = ?", account_id)[0]
    if acc_deaths["SUM(deaths)"] == 0:
        acc_kd = "N/A - No Deaths"
    else:
        acc_kd = float(acc_kills["SUM(kills)"]) / float(acc_deaths["SUM(deaths)"])
        acc_kd = "{:.2f}".format(acc_kd)
        acc_kd = str(acc_kd) + " Kills Per Death"
    acc_games = db.execute("SELECT SUM(games) FROM user_brawlers WHERE user_id = ?", account_id)[0]
    acc_wins = db.execute("SELECT SUM(wins) FROM user_brawlers WHERE user_id = ?", account_id)[0]
    acc_losses = db.execute("SELECT SUM(losses) FROM user_brawlers WHERE user_id = ?", account_id)[0]
    if acc_games["SUM(games)"] == 0:
        acc_win_rate = "N/A- No Games Played Yet"
    else:
        acc_win_rate = float(acc_wins["SUM(wins)"]) / float(acc_games["SUM(games)"]) * 100
        acc_win_rate = "{:.2f}".format(acc_win_rate)
        acc_win_rate = str(acc_win_rate) + "%"

    return render_template("account.html", username=acc_username, trophies=acc_trophies, kills=acc_kills, deaths=acc_deaths, kd=acc_kd, wins=acc_wins, losses=acc_losses, win_rate=acc_win_rate, games=acc_games)


@app.route("/add_match", methods=["GET", "POST"])
@login_required
def add_match():
    """Add match"""
    add_id = session["user_id"]
    add_brawlers = db.execute(
        "SELECT name FROM brawlers WHERE id IN (SELECT brawler_id FROM user_brawlers WHERE user_id = ?)", add_id)
    add_brawlers_names = []
    for brawler in add_brawlers:
        add_one_brawler = brawler["name"]
        add_brawlers_names.append(add_one_brawler)
    if request.method == "POST":
        add_kills = request.form.get("kills")
        if not add_kills:
            return apology("Missing Kills")
        if not add_kills.isdigit():
            return apology("Kills Are Not An Integer")
        add_kills = int(add_kills)
        add_deaths = request.form.get("deaths")
        if not add_deaths:
            return apology("Missing Deaths")
        if not add_deaths.isdigit():
            return apology("Deaths Are Not An Integer")
        add_deaths = int(add_deaths)
        add_brawler = request.form.get("brawler")
        if add_brawler not in add_brawlers_names:
            return apology("Please Select An Unlocked Brawler")
        add_result = request.form.get("result")
        if not add_result:
            return apology("Missing Result Input")
        add_trophies = request.form.get("trophies")
        if not add_trophies:
            return apology("Missing Trophies")
        if not add_trophies.isdigit():
            return apology("Trophies Are Not An Integer")
        add_trophies = int(add_trophies)

        add_brawler_id = db.execute("SELECT id FROM brawlers WHERE name = ?", add_brawler)
        add_brawler_id = add_brawler_id[0]["id"]

        db.execute("UPDATE user_brawlers SET games = games + 1 WHERE user_id = ? AND brawler_id = ?", add_id, add_brawler_id)
        db.execute("UPDATE user_brawlers SET kills = kills + ? WHERE user_id = ? AND brawler_id = ?", add_kills, add_id, add_brawler_id)
        db.execute("UPDATE user_brawlers SET deaths = deaths + ? WHERE user_id = ? AND brawler_id = ?", add_deaths, add_id, add_brawler_id)

        if add_result == "win":
            db.execute("UPDATE user_brawlers SET wins = wins + 1 WHERE user_id = ? AND brawler_id = ?", add_id, add_brawler_id)
            db.execute("UPDATE user SET trophies = trophies + ? WHERE id = ?", add_trophies, add_id)
        elif add_result == "lose":
            db.execute("UPDATE user_brawlers SET losses = losses + 1 WHERE user_id = ? AND brawler_id = ?", add_id, add_brawler_id)
            db.execute("UPDATE user SET trophies = trophies - ? WHERE id = ?", add_trophies, add_id)
        else:
            return apology("unexpected error")

        return redirect("/")

    else:
        return render_template("add_match.html", selection=add_brawlers_names)


@app.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    """Get Stats"""
    if request.method == "POST":
        topics = ["games", "wins", "losses", "kills", "deaths"]
        tails = ["Top", "Bottom"]
        stats_id = session["user_id"]
        stats_brawlers_amount = db.execute("SELECT COUNT(brawler_id) FROM user_brawlers WHERE user_id = ?", stats_id)
        stats_topic = request.form.get("topic")
        if stats_topic not in topics:
            return apology("Please Select An Offered Topic")
        stats_tail = request.form.get("tail")
        if stats_tail not in tails:
            return apology("Please Select An Offered Tail")
        stats_amount = request.form.get("amount")
        if not stats_amount:
            return apology("Please Input How Many Brawlers Desired")
        stats_amount = int(stats_amount)
        if stats_amount > stats_brawlers_amount[0]["COUNT(brawler_id)"]:
            return apology("Player Has Less Unlocked Brawlers")

        if stats_topic == "games":
            if stats_tail == "Top":
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY games DESC LIMIT ?", stats_id, stats_amount)
            else:
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY games ASC LIMIT ?", stats_id, stats_amount)
        elif stats_topic == "wins":
            if stats_tail == "Top":
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY wins DESC LIMIT ?", stats_id, stats_amount)
            else:
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY wins ASC LIMIT ?", stats_id, stats_amount)
        elif stats_topic == "losses":
            if stats_tail == "Top":
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY losses DESC LIMIT ?", stats_id, stats_amount)
            else:
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY losses ASC LIMIT ?", stats_id, stats_amount)
        elif stats_topic == "kills":
            if stats_tail == "Top":
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY kills DESC LIMIT ?", stats_id, stats_amount)
            else:
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY kills ASC LIMIT ?", stats_id, stats_amount)
        elif stats_topic == "deaths":
            if stats_tail == "Top":
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY deaths DESC LIMIT ?", stats_id, stats_amount)
            else:
                stats_list = db.execute("SELECT name FROM brawlers JOIN user_brawlers ON brawlers.id = user_brawlers.brawler_id WHERE user_id = ? ORDER BY deaths ASC LIMIT ?", stats_id, stats_amount)
        else:
            return apology("unexpected error")

        return render_template("stats_results.html", list=stats_list, tail=stats_tail, amount=stats_amount, topic=stats_topic)

    else:
        return render_template("stats.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM user WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash_pass"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search Player"""
    if request.method == "POST":
        search_name = request.form.get("username")
        if not search_name:
            return apology("Please Input A Username")
        search_id = db.execute("SELECT id FROM user WHERE username = ?", search_name)
        if not search_id:
            return apology("Invalid Username")
        search_id = search_id[0]["id"]
        search_username = db.execute("SELECT username FROM user WHERE id = ?", search_id)[0]
        search_trophies = db.execute("SELECT trophies FROM user WHERE id = ?", search_id)[0]
        search_kills = db.execute("SELECT SUM(kills) FROM user_brawlers WHERE user_id = ?", search_id)[0]
        search_deaths = db.execute("SELECT SUM(deaths) FROM user_brawlers WHERE user_id = ?", search_id)[0]
        if search_deaths["SUM(deaths)"] == 0:
            search_kd = "N/A - No Deaths"
        else:
                search_kd = float(search_kills["SUM(kills)"]) / float(search_deaths["SUM(deaths)"])
                search_kd = "{:.2f}".format(search_kd)
                search_kd = str(search_kd) + " Kills Per Death"
        search_games = db.execute("SELECT SUM(games) FROM user_brawlers WHERE user_id = ?", search_id)[0]
        search_wins = db.execute("SELECT SUM(wins) FROM user_brawlers WHERE user_id = ?", search_id)[0]
        search_losses = db.execute("SELECT SUM(losses) FROM user_brawlers WHERE user_id = ?", search_id)[0]
        if search_games["SUM(games)"] == 0:
            search_win_rate = "N/A- No Games Played Yet"
        else:
            search_win_rate = float(search_wins["SUM(wins)"]) / float(search_games["SUM(games)"]) * 100
            search_win_rate = "{:.2f}".format(search_win_rate)
            search_win_rate = str(search_win_rate) + "%"
        return render_template("searched.html", username=search_username, trophies=search_trophies, kills=search_kills, deaths=search_deaths, kd=search_kd, wins=search_wins, losses=search_losses, win_rate=search_win_rate, games=search_games)

    else:
        return render_template("search.html")


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    """Create user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("Please Input A Username")
        password1 = request.form.get("password")
        if not password1:
            return apology("Please Input A Password")
        password2 = request.form.get("confirmation")
        if not password2:
            return apology("Please Confirm Password")
        if password1 != password2:
            return apology("Passwords Do Not Match")

        user_match = db.execute("SELECT username FROM user WHERE username = ?", username)
        if len(user_match) != 0:
            return apology("Username is taken")

        create_trophies = (request.form.get("trophies"))
        if not create_trophies:
            return apology("Missing Trophies")
        if not create_trophies.isdigit():
            return apology("Trophies Are Not An Integer")
        create_trophies = int(create_trophies)

        for brawler in request.form.getlist("brawler"):
            if brawler not in brawler_list:
                return apology("Selected Brawler Not In List")

        secure_password = generate_password_hash(password1)
        db.execute("INSERT INTO user(username, hash_pass, trophies) VALUES(?, ?, ?)", username, secure_password, create_trophies)
        current_user = db.execute("SELECT id FROM user WHERE username = ?", username)
        session["user_id"] = current_user[0]['id']

        for brawler in request.form.getlist("brawler"):
            current_brawler = db.execute("SELECT id FROM brawlers WHERE name = ?", brawler)
            current_brawler = current_brawler[0]['id']
            db.execute("INSERT INTO user_brawlers(user_id, brawler_id) VALUES(?, ?)", current_user[0]['id'], current_brawler)

        return redirect("/")
    else:
        return render_template("create_user.html", brawlers=brawler_list)


@app.route("/leaderboards", methods=["GET", "POST"])
@login_required
def leaderboards():
    """Show Leaderboards"""
    lead_trophies = db.execute("SELECT username, trophies FROM user ORDER BY trophies DESC LIMIT 10")
    lead_games = db.execute("SELECT user.username, SUM(user_brawlers.games) as total_games FROM user JOIN user_brawlers ON user.id = user_brawlers.user_id GROUP BY user_id ORDER BY total_games DESC LIMIT 10")
    lead_wins = db.execute("SELECT user.username, SUM(user_brawlers.wins) as total_wins FROM user JOIN user_brawlers ON user.id = user_brawlers.user_id GROUP BY user_id ORDER BY total_wins DESC LIMIT 10")
    lead_kills = db.execute("SELECT user.username, SUM(user_brawlers.kills) as total_kills FROM user JOIN user_brawlers ON user.id = user_brawlers.user_id GROUP BY user_id ORDER BY total_kills DESC LIMIT 10")

    return render_template("leaderboards.html", trophies=lead_trophies, games=lead_games, wins=lead_wins, kills=lead_kills)


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update user"""
    update_id = session["user_id"]
    update_unlocked_brawlers = db.execute("SELECT name FROM brawlers WHERE id IN (SELECT brawler_id FROM user_brawlers WHERE user_id = ?)", update_id)
    update_unlocked_brawlers = [value for dictionary in update_unlocked_brawlers for value in dictionary.values()]
    update_locked_brawlers = []
    for brawler in brawler_list:
        new_brawler = brawler
        if new_brawler not in update_unlocked_brawlers:
            update_locked_brawlers.append(new_brawler)
    if request.method == "POST":
        update_username = request.form.get("username")
        if update_username:
            update_match = db.execute("SELECT username FROM user WHERE username = ?", update_username)
            if len(update_match) != 0:
                return apology("Username is taken")
            db.execute("UPDATE user SET username = ? WHERE id = ?", update_username, update_id)

        update_password1 = request.form.get("password")
        if update_password1:
            update_password2 = request.form.get("confirmation")
            if not update_password2:
                return apology("Please Confirm Password")
            if update_password1 != update_password2:
                return apology("Passwords Do Not Match")
            update_secure_password = generate_password_hash(update_password1)
            db.execute("UPDATE user SET hash_pass = ? WHERE id = ?", update_secure_password, update_id)

        update_change_trophies = request.form.get("trophies")
        if update_change_trophies:
            if not update_change_trophies.isdigit():
                return apology("Trophies Are Not An Integer")
            update_change_trophies = int(update_change_trophies)
            db.execute("UPDATE user SET trophies = ? WHERE id = ?", update_change_trophies, update_id)

        for brawler in request.form.getlist("brawler"):
            if brawler not in update_locked_brawlers:
                return apology("Please Only Select Currently Locked Brawlers")

        for brawler in request.form.getlist("brawler"):
            current_brawler = db.execute("SELECT id FROM brawlers WHERE name = ?", brawler)
            current_brawler = current_brawler[0]['id']
            db.execute("INSERT INTO user_brawlers(user_id, brawler_id) VALUES(?, ?)", update_id, current_brawler)

        return redirect("/")
    else:
        return render_template("update.html", brawlers=update_locked_brawlers)
