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


@doyleStatusApp.route("/select-server", methods=["GET", "POST"])
def selectServer():
    form = HistoryForm()
    if form.validate_on_submit():
        serverName = form.servername.data
        return redirect("/history/%s" % serverName)
    else:
        return render_template("select-server.html", counts=doyleStatusApp.doyleInfo.getCounts(), form=form)


@doyleStatusApp.route("/history/<serverName>")
def history(serverName):
    return render_template("history.html", counts=doyleStatusApp.doyleInfo.getCounts(), servername=serverName, status=doyleStatusApp.doyleInfo.getHistory(serverName))


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


@doyleStatusApp.route("/queued-chart", methods=["GET", "POST"])
def queuedChart():
    form = ChartForm()
    baseDate = datetime.datetime.combine(datetime.date.today(),datetime.time(0))
    if form.validate_on_submit():
        # form returns a date object which we need to convert to datetime
        baseDate = datetime.datetime.combine(form.startDate.data,datetime.time(0))
    return render_template('queuedChart.html', baseDate=baseDate, form=form, counts=doyleStatusApp.doyleInfo.getQueuedChartData(baseDate,24,datetime.timedelta(hours=1)))
