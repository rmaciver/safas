"""

threading module.
 
based on QT5 thread class, can be used with or without a GUI

Make a ThreadQueue object, then add functions to be executed
 
"""

import traceback
import sys

import random
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class QueueThreads(QThreadPool): 
    """
    general threadpool for the main GUI and other components
    """
    def __init__(self):
        super(QueueThreads, self).__init__()   
        
    def add_to_queue(self, 
                     function=None,
                     signal=None,
                     slot=None, 
                     **kwargs):
        
        # signal passed as a string
        worker = Worker(function=function, signal=signal, slot=slot, **kwargs)
     
        worker.signals.result.connect(self.print_output)
        #worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)   
        
        # not every function added to queue requires signal/slot
        if slot != None: 
            sig = getattr(worker.signals, signal)
            sig.connect(slot)
        
        self.start(worker)

    def print_output(self, s):
        """ """ 
    
    def thread_complete(self):
        """  """ 
        
    def progress_fn(self, n):
        """ """

class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """
    def __init__(self, 
                 function=None, 
                 signal=None,
                 slot=None,
                 **kwargs):
        
        super(Worker, self).__init__()

        self.function = function
        self.kwargs = kwargs
        
        self.signals = WorkerSignals()        
        self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs['imgtime_callback'] = self.signals.imgtime
        self.kwargs['result_callback'] = self.signals.result
        self.kwargs['obj_callback'] = self.signals.obj
        self.kwargs['imgtimen_callback'] = self.signals.imgtimen
        self.kwargs['val_callback'] = self.signals.val
        
    @pyqtSlot()
    def run(self):
        """ Initialise runner function with passed args, kwargs.
            The current use doesnt implement this part very well, aside
            from the result = self.function(**self.kwargs) part
        """
        try:
            result = self.function(**self.kwargs)
            
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
            
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Use class (w/o __init__) to ensure the signals are bound objects
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)    
    imgtime = pyqtSignal((object, str))
    imgtimen = pyqtSignal((object, float, int))
    imgtimed = pyqtSignal((object, str, int))
    obj = pyqtSignal(object)
    val = pyqtSignal(int)



