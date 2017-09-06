import subprocess
import shlex
import tempfile
import os
import time

class SubWork(object):
    """
    add timeout support!
    if timeout, we SIGTERM to child process, and not to cause zombie process
    safe!
    """
    def __init__(self): 
        """
        default None
        """
        self._Popen = None
        self._pid = None
        self._return_code = None
        self._cwd = None
        self._start_time = None

    def _run(self):
        #Run cmd.
        #Split command string.
        cmd = shlex.split(self._cmd)
        self._Popen = subprocess.Popen(args=cmd, 
                                       stdout=self._stdout_fd, 
                                       stderr=self._stderr_fd, 
                                       cwd=self._cwd)
        self._pid = self._Popen.pid
        self._start_time = time.time()

        while (self._Popen.poll() == None and 
                (time.time() - self._start_time) < self._timeout):
            time.sleep(1)
            
        _r_code = self._Popen.poll()

        # If child process has not exited yet, terminate it.
        if self._Popen.poll() == None: 
            self._Popen.terminate()
            _r_code = 254

        # Wait for the child process to exit.
        time.sleep(1)

        # If child process has not been terminated yet, kill it. 
        if self._Popen.poll() == None:
            self._Popen.kill()
            _r_code = 255

        self._return_code = _r_code

    def start(self,
              cmd, 
              timeout=5*60*60,
              stdin=None,
              stdout=None,
              stderr=None,
              tty=False,
              timestamp=False):

        self._cmd = cmd
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._timeout = timeout
        self._is_tty = tty
        self._timestamp = timestamp

        #Init output.
        info = None
        err = None

        if self._timestamp:
            start_time = time.strftime("%Y-%m-%d %X", time.localtime())
            file_start = "Start Time: " + start_time + "\n"
        else:
            file_start = ""
            file_end = ""

        try:
            #Init the file handle of output.
            if self._is_tty:
                self._stdout_fd = None
                self._stderr_fd = None

            elif (self._stdout is None or 
                self._stderr is None or 
                self._stdout == self._stderr):

                self._stdout_fd = tempfile.TemporaryFile()
                self._stderr_fd = tempfile.TemporaryFile()

            else:
                self._stdout_fd = self._create_handler(self._stdout)
                self._stderr_fd = self._create_handler(self._stderr)
                self._stdout_fd.write(file_start)
                self._stdout_fd.flush()
                self._stderr_fd.write(file_start)
                self._stderr_fd.flush()

            self._run()

            if self._timestamp:
                end_time = time.strftime("%Y-%m-%d %X", time.localtime())
                file_end = "End Time: " + end_time + "\n"

            #Write and Read output content.
            if not self._is_tty:
                self._stdout_fd.write(file_end)
                self._stderr_fd.write(file_end)

                self._stdout_fd.flush()
                self._stderr_fd.flush()

                self._stdout_fd.seek(0)
                self._stderr_fd.seek(0)
                info = file_start + self._stdout_fd.read() + file_end
                err = file_start + self._stderr_fd.read() + file_end
        finally:
            #Close file handle.
            if not self._is_tty:
                self._stdout_fd.close()
                self._stderr_fd.close()

        return {"code":self._return_code,
                "stdout":info,
                "stderr":err
                }

    #Create file handle.
    def _create_handler(self, filename):
        if isinstance(filename, file):
            return filename
        elif isinstance(filename, basestring):
            path = os.path.dirname(filename)
            timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
            
            if not os.path.exists(path):
                os.makedirs(path)
            elif os.path.exists(filename) and not os.path.isfile(filename):
                backup_name = filename + timestamp
                os.rename(filename, backup_name)

            fd = open(filename, 'a+b')
            return fd
        else:
            raise "The type of \'filename\' must be \'file\' or \'basestring\'"
