from flask import render_template, redirect
from app import app
from app.doyleinfo import DoyleInfo

from app.forms import HistoryForm


doyleInfo=DoyleInfo()

@app.route('/')
@app.route('/index')
@app.route('/executing')
def executing():
    return render_template('executing.html',counts=doyleInfo.getCounts(),status=doyleInfo.getExecution())

@app.route('/queued')
def queued():
    return render_template('queued.html',counts=doyleInfo.getCounts(),status=doyleInfo.getQueued())

@app.route('/select-server', methods=['GET', 'POST'])
def selectServer():
    form = HistoryForm()
    if form.validate_on_submit():
        serverName=form.servername.data
        return redirect('/history/%s' % serverName)
    else:
        return render_template('select-server.html',counts=doyleInfo.getCounts(),form=form)

@app.route('/history/<serverName>')
def history(serverName):
    return render_template('history.html',counts=doyleInfo.getCounts(), servername=serverName, status=doyleInfo.getHistory(serverName))
