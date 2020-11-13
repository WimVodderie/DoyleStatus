from flask import render_template, redirect
from app import doyleStatusApp
from app.doyleinfo import DoyleInfo

from app.forms import HistoryForm
from app.forms import ChartForm

import datetime


@doyleStatusApp.route("/")
@doyleStatusApp.route("/index")
def index():
    return redirect("/overview")


@doyleStatusApp.route("/overview")
def overview():
    return render_template(
        "overview.html",
        counts=doyleStatusApp.doyleInfo.getCounts(),
        errorMsg=doyleStatusApp.doyleInfo.getErrorMsg(),
        exes=doyleStatusApp.doyleInfo.getExecution(),
        servers=doyleStatusApp.doyleInfo.getServersFailed(),
        queues=doyleStatusApp.doyleInfo.getQueued(),
    )


@doyleStatusApp.route("/executing")
def executing():
    return render_template("executing.html", counts=doyleStatusApp.doyleInfo.getCounts(), errorMsg=doyleStatusApp.doyleInfo.getErrorMsg(), exes=doyleStatusApp.doyleInfo.getExecution())


@doyleStatusApp.route("/queued")
def queued():
    return render_template("queued.html", counts=doyleStatusApp.doyleInfo.getCounts(), errorMsg=doyleStatusApp.doyleInfo.getErrorMsg(), queues=doyleStatusApp.doyleInfo.getQueued())


@doyleStatusApp.route("/servers")
def servers():
    return render_template("servers.html", counts=doyleStatusApp.doyleInfo.getCounts(), errorMsg=doyleStatusApp.doyleInfo.getErrorMsg(), servers=doyleStatusApp.doyleInfo.getServers())


lastServerName = ""
lastServerHistory = {"history": [], "busyPercentage": 0.0}


@doyleStatusApp.route("/history", methods=["GET", "POST"])
def history():

    global lastServerName
    global lastServerHistory

    form = HistoryForm()

    newServerName = lastServerName

    if form.validate_on_submit():
        newServerName = form.servername.data

    if newServerName != lastServerName:
        lastServerHistory = doyleStatusApp.doyleInfo.getHistory(newServerName)
        lastServerName = newServerName

    return render_template("history.html", counts=doyleStatusApp.doyleInfo.getCounts(), servername=lastServerName, status=lastServerHistory, form=form)


@doyleStatusApp.route("/quitquitquit")
def quit():
    doyleStatusApp.shutdown()
    return "Server shutting down"


@doyleStatusApp.route("/cleancleanclean")
def clean():
    doyleStatusApp.doyleInfo.startCleanDatabase()
    return "Cleaning database started"


@doyleStatusApp.route("/backupdb")
def backupDatabase():
    doyleStatusApp.doyleInfo.backupDatabase()
    return "Backing up database"


lastSelectedDate = datetime.date.min
lastCounts = None


@doyleStatusApp.route("/queued-chart", methods=["GET", "POST"])
def queuedChart():

    global lastSelectedDate
    global lastCounts

    form = ChartForm()

    # no entry in form -> use last selected date
    if form.startDate.data == datetime.date.min:
        newDate = lastSelectedDate if lastSelectedDate != datetime.date.min else datetime.date.today()
        form.startDate.data = newDate
    else:
        newDate = form.startDate.data

    # when new date has been selected, get new data
    if newDate != lastSelectedDate:
        lastCounts = doyleStatusApp.doyleInfo.getQueuedChartData(datetime.datetime.combine(form.startDate.data, datetime.time(0)), 24, datetime.timedelta(hours=1))
        lastSelectedDate = newDate

    return render_template("queuedChart.html", date=lastSelectedDate, counts=lastCounts, form=form)
