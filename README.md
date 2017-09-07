#Subwork

A subprocess module with "timeout" feture.

- Example
----------
    from subwork import SubWork

    cmd = "/bin/ls /tmp"
    worker = SubWork()
    res = worker.start(cmd, 300, "/tmp/stdout.log", "/tmp/stderr.log")
    print res 
