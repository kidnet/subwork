import subprocess
import shlex
import tempfile
import signal
import os
import time
from distribute import exceptions

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

    def _send_signal(self, pid, sig):
        """
        Send a signal to the process
        """
        os.kill(pid, sig)

    def _terminate(self, pid):
        """
        Terminate the process with SIGTERM
        """
        self._send_signal(pid, signal.SIGTERM)

    def _kill(self, pid):
        """
        Kill the process with SIGKILL
        """
        self._send_signal(pid, signal.SIGKILL)

    def _wait(self, Popen):
        """
        Wait child exit signal
        """
        Popen.wait()

    def _free_child(self, pid, Popen):
        """
        Kill process by pid
        """
        try:
            self._terminate(pid)
            self._kill(pid)
            self._wait(Popen)
        except Exception:
            pass

    def _run(self):
        #Run cmd.
        #Split command string.
        cmd = shlex.split(self._cmd)
        try:
            self._Popen = subprocess.Popen(args=cmd, 
                                          stdout=self._stdout_fd, 
                                          stderr=self._stderr_fd, 
                                          cwd=self._cwd)
            self._pid = self._Popen.pid
            self._start_time = time.time()
            while (self._Popen.poll() == None and 
                    (time.time() - self._start_time) < self._timeout):
                time.sleep(1)
        except (OSError, ValueError), e:
            #raise exceptions.CommandExecutionError("Execute Commonand Filed.", e)
            raise
        except Exception:
            raise
            
        # Child is not exit yet.
        if self._Popen.poll() == None: 
            self._free_child(self._pid, self._Popen)
            #Throw the Exception that run command timeout.
            raise exceptions.CommandExecutionTimeout("Command Execution Timeout %ds." % self._timeout)
        else:
            self._return_code = self._Popen.poll()

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
            elif self._stdout is None or self._stderr is None \
                or self._stdout == self._stderr:
                self._stdout_fd = tempfile.TemporaryFile()
                self._stderr_fd = tempfile.TemporaryFile()
            else:
                self._stdout_fd = self._create_handler(self._stdout)
                self._stderr_fd = self._create_handler(self._stderr)
                self._stdout_fd.write(file_start)
                self._stdout_fd.flush()
                self._stderr_fd.write(file_start)
                self._stderr_fd.flush()

            try:
                self._run()
            except Exception:
                raise

            if self._timestamp:
                end_time = time.strftime("%Y-%m-%d %X", time.localtime())
                file_end = "End Time: " + end_time + "\n"

            self._stdout_fd.write(file_end)
            self._stderr_fd.write(file_end)

            self._stdout_fd.flush()
            self._stderr_fd.flush()

            #Read output content.
            if not self._is_tty:
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
