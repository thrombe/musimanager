
def try_commit_changes():
    import subprocess
    import opts
    dir = opts.musimanager_directory

    # check if the dir has a git repo
    commands = f"""
    cd {dir}
    git log
    """
    out = subprocess.run(
        [commands, ],
        shell=True,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        stderr=subprocess.STDOUT # mutes output
    )
    out  = str(out.stdout)

    #if no git repo, make one
    if out.startswith("fatal: not a git repository"):
        commands = f"""
        cd {dir}
        git init .
        git commit --allow-empty -m "initial commit"
        """
        out = subprocess.check_output(
            [commands, ],
            shell=True,
            stderr=subprocess.STDOUT # mutes output
        )

    try:
        # get the timestamp of the latest commit
        commands = f"""
        cd {dir}
        git log | grep Date | head -n1
        """
        out = subprocess.check_output(
            [commands, ],
            shell=True,
            # stderr=subprocess.STDOUT # mutes output
        )
        out = str(out).split()

        # parse the time into timestamp
        import datetime
        import time
        dt = datetime.datetime.strptime(f'{out[1]} {out[2]} {out[3]} {out[4]} {out[5]}', '%c')
        secs = time.time() - dt.timestamp()
        day = 60*60*24

        # if enough time has passes, commit changes of the 2 files
        if secs > day:
            print("commiting mutracker changes changes")
            commands = f"""
            cd {dir}
            git add opts.toml
            git add musitracker.json
            git commit -m "{str(datetime.date.today()).replace("-", "/")}"
            """
            subprocess.check_output(
                [commands, ],
                shell=True,
            )
    except:
        raise Exception("failed git commands")
