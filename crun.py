#!/usr/bin/env python
# 
# NAME
#
#        crun
#
# DESCRIPTION
#
#        'crun' is functor family of scripts for running command line
#        apps on a cluster.
#
# HISTORY
#
# 25 January 2012
# o Initial design and coding.
#

# System imports
import systemMisc as misc
import sys

class crun(object):
    """
        This family of functor classes provides a unified interface
        to running shell-commands in several contexts:
        
            - locally on the underlying OS
            - remote host via ssh 
            - remote cluster via scheduler 

        If the baseclass is "run", no cluster scheduling is performed
        and a straightforward remote exec via ssh is executed.
        
        If a scheduler subclass is "run", the shell command is scheduled
        and executed on the cluster.
        
        If the parent caller does not need to explicitly wait on the child,
        the crun.detach() method will decouple the child completely. The
        parent would then need some child- or operation-specific 
        mechanism to determine if the child has finished executing.
        
        By default, the child will not detach and the parent will wait/block
        on the call.
    """    
        
    def __init__(self, **kwargs):
        self._b_schedulerSet    = False
        self._b_runCmd          = True          # Debugging flag
                                                #+ will only execute command
                                                #+ if flag is true
        self._b_sshDo           = False
        self._b_singleQuoteCmd  = False         # If True, force enclose of
                                                #+ strcmd with single quotes
        self._b_detach          = False         # If True, detach process from
                                                #+ shell
        self._b_echoCmd         = False
        self._b_echoStdOut      = False
        self._b_echoStdErr      = False
        self._b_devnull         = False
        self._str_remoteHost    = ""
        self._str_remoteUser    = ""
        self._str_remotePasswd  = ""

        self._str_scheduleCmd   = ""
        self._str_scheduleArgs  = ""
        self._str_stdout        = ""
        self._str_stderr        = ""
        self._exitCode          = 0

        self._str_cmdPrefix     = ""
        
        for key, value in kwargs.iteritems():
            if key == "remoteHost":
                self._b_sshDo           = True     
                self._str_remoteHost    = value
            if key == "remoteUser":     self._str_remoteUser    = value
            if key == "remotePasswd":   self._str_remotePasswd  = value
            if key == 'cmdPrefix':      self._str_cmdPrefix     = value
        
    
    def __call__(self, str_cmd, **kwargs):
        str_prefix              = self._str_scheduleCmd + " " + \
                                  self._str_scheduleArgs
        if self._b_singleQuoteCmd:
            str_shellCmd        = str_prefix + (" '%s'" % str_cmd)
        else:
            str_shellCmd        = str_prefix + str_cmd
        if self._b_devnull:
            str_suffix       = ">/dev/null 2>&1 "
        else: str_suffix     = ''
        if self._b_detach:   str_embeddedDetach = "&"
        else:                str_embeddedDetach = ""
        str_shellCmd            = '%s %s %s %s' % ( self._str_cmdPrefix,
                                                    str_shellCmd,
                                                    str_suffix,
                                                    str_embeddedDetach)
        if self._b_sshDo and len(self._str_remoteHost):
           str_shellCmd         = 'ssh %s@%s  "%s"' % (self._str_remoteUser,
                                                    self._str_remoteHost,
                                                    str_shellCmd)
        
        ret                     = 0
        if self._b_detach and self._b_schedulerSet: str_shellCmd += " &"

        if self._b_echoCmd: sys.stdout.write('%s\n' % str_shellCmd)
        if self._b_runCmd:
#            ret, self._str_stdout = misc.system_procRet(str_shellCmd)
            self._str_stdout, self._str_stderr, self._exitCode    = \
                    misc.shell(str_shellCmd, **kwargs)
        if self._b_echoStdOut: sys.stdout.write(self._str_stdout)
        return self._str_stdout, self._str_stderr, self._exitCode
    
    def scheduleCmd(self, *args):
        if len(args):
            self._str_scheduleCmd = args[0]
        else:
            return self._str_scheduleCmd

    def scheduleArgs(self, *args):
        if len(args):
            self._str_scheduleArgs = args[0]
        else:
            return self._str_scheduleArgs

    def echo(self, *args):
        self._b_echoCmd         = True
        if len(args):
            self._b_echoCmd     = args[0]

    def echoStdOut(self, *args):
        self._b_echoStdOut      = True
        if len(args):
            self._b_echoStdOut  = args[0]
            
    def stdout(self):
        return self._str_stdout
            
    def stderr(self):
        return self._str_stderr
        
    def exitCode(self):
        return self._exitCode

    def echoStdErr(self, *args):
        self._b_echoStdErr      = True
        if len(args):
            self._b_echoStdErr  = args[0]
            
    def detach(self, *args):
        self._b_detach          = True
        if len(args):
            self._b_detach      = args[0]

    def devnull(self, *args):
        if len(args):
            self._b_sshDo       = args[0]
        else:
            return self._b_devnull
    
    def ssh(self, *args):
        self._b_sshDo           = True
        if len(args):
            self._b_sshDo       = args[0]

    def dontRun(self, *args):
        self._b_runCmd          = False
        if len(args):
            self._b_runCmd      = args[0]

    def remoteLogin_set(self, str_remoteUser, str_remoteHost, **kwargs):
        self.ssh()
        self._str_remoteUser    = str_remoteUser
        self._str_remoteHost    = str_remoteHost
        for key, value in kwargs.iteritems():
            if key == "passwd": self._str_remotePasswd = value

class crun_mosix(crun):

    def priority(self, *args):
        if len(args):
            self._priority      = args[0]
        else:
            return self._priority

    def scheduleHostOnly(self, *args):
        if len(args):
            self._str_scheduleHostOnly = args[0]
            self._b_scheduleOnHostOnly = True
        else:
            return self._str_scheduleHostOnly

    def scheduleArgs(self, *args):
        if len(args):
            self._str_scheduleArgs      = args[0]
        else:
            self._str_scheduleArgs     += "-q%d " % self._priority 
            if self._b_scheduleOnHostOnly:
                self._str_scheduleArgs += "-r%s " % self._str_scheduleHostOnly
            else:
                self._str_scheduleArgs += "-b " % self._priority
        return self._str_scheduleArgs
    
    def __init__(self, **kwargs):
        self._b_schedulerSet            = True
        self._b_scheduleOnHostOnly      = False
        self._str_scheduleHostOnly      = ''
        crun.__init__(self, **kwargs)

        self._priority          = 50
        self._str_scheduleCmd   = 'mosbatch'
        self._str_scheduleArgs  = ''
        
    def __call__(self, str_cmd, **kwargs):
        self.scheduleArgs()
        return crun.__call__(self, str_cmd, **kwargs)

class crun_mosixbash(crun):
    def __init__(self, **kwargs):
        self._b_schedulerSet     = True
        crun.__init__(self, **kwargs)
        self._str_scheduleCmd   = 'mosix_run.bash'
        self._str_scheduleArgs  = '-c'
        self._b_singleQuoteCmd  = True
        
    def __call__(self, str_cmd):
        return crun.__call__(self, str_cmd)


if __name__ == '__main__':

    # Create the crun instance
    #shell       = crun()
    #shell       = crun_mosix(remoteUser="rudolphpienaar", remoteHost="rc-twice")
    shell       = crun(remoteUser="rudolphpienaar", remoteHost="rc-drno")

    # Grab the command line args defining the app and args that need to be 
    # scheduled
    str_cmd     = ""
    for arg in sys.argv[1:len(sys.argv)]:
        str_cmd = str_cmd + " " + arg
    
    # Set some parameters for this shell
    shell.echo()
    shell.echoStdOut()
    shell.detach()
    # shell.dontRun()

    # And now run it!
    misc.tic()
    shell(str_cmd)
    print "Elapsed time = %f seconds" % misc.toc()
    
    
