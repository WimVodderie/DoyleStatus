from flask import render_template, redirect
from app import app
from app.doyleinfo import DoyleInfo

from app.forms import HistoryForm

from flask import request


def shutdown_server():
    print("Shutting down the server")
    shutdown_func = request.environ.get("werkzeug.server.shutdown")
    if shutdown_func is None:
        print("Failed to get shutdown function, cannot stop")
    else:
        shutdown_func()


doyleInfo = DoyleInfo()


@app.route("/")
@app.route("/index")
def index():
    return redirect("/overview")


@app.route("/overview")
def overview():
    return render_template("overview.html", counts=doyleInfo.getCounts(), errorMsg=doyleInfo.getErrorMsg(), exes=doyleInfo.getExecution(), servers=doyleInfo.getServersFailed(), queues=doyleInfo.getQueued())


@app.route("/executing")
def executing():
    return render_template("executing.html", counts=doyleInfo.getCounts(), errorMsg=doyleInfo.getErrorMsg(), exes=doyleInfo.getExecution())


@app.route("/queued")
def queued():
    return render_template("queued.html", counts=doyleInfo.getCounts(), errorMsg=doyleInfo.getErrorMsg(), queues=doyleInfo.getQueued())


@app.route("/servers")
def servers():
    return render_template("servers.html", counts=doyleInfo.getCounts(), errorMsg=doyleInfo.getErrorMsg(), servers=doyleInfo.getServers())


@app.route("/select-server", methods=["GET", "POST"])
def selectServer():
    form = HistoryForm()
    if form.validate_on_submit():
        serverName = form.servername.data
        return redirect("/history/%s" % serverName)
    else:
        return render_template("select-server.html", counts=doyleInfo.getCounts(), form=form)


@app.route("/quitquitquit")
def quit():
    doyleInfo.quit()
    shutdown_server()
    return "Server shutting down"


@app.route("/cleancleanclean")
def clean():
    doyleInfo.startCleanDatabase()
    return "Cleaning database started"


@app.route("/history/<serverName>")
def history(serverName):
    return render_template("history.html", counts=doyleInfo.getCounts(), servername=serverName, status=doyleInfo.getHistory(serverName))
