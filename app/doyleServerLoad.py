"""
Keep track of doyle server load as a percentage per day

- store in a table in the db
    server
    day
    used seconds that day
    last update time

- when server session usage is reported
    get entry for session start
    if entry exists
        # check if current session on server is
        if last update time < session start
            seconds = session start - session end
        else
            session = (session end - last update time)

        used secsond += seconds
        last update time = session end
TODO:
day overflow
new entry


                lut
                    x
    x               ---------------x
    ss                             se

                                lut
                                    x
    x                               --------x
    ss                                      se

                                        lut
                                            x
                                                                x-----------x
                                                                ss          se
"""
