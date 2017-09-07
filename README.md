#Subwork

A subprocess module with "timeout" feture.

- Example
This is a example.
    from subwork import SubWork

    cmd = "/bin/ls /tmp"
    worker = SubWork()
    res = worker.start(cmd, 300, "/tmp/stdout.log", "/tmp/stderr.log")
    print res 
