"""

"""
from copy import deepcopy
import cv2

from threading import Thread
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from rich.progress import Progress

import logging
log = logging.getLogger("rich")

# TODO: get relative import of prints from safas
def print_process(
    color, process_name, *args, error=False, warning=False, exception=False, **kwargs
    ):
    msg = " ".join([str(arg) for arg in args])  # Concatenate all incoming strings or objects
    rich_msg = f"[{color}]{process_name}[/{color}] | {msg}"
    
    if error:
        log.error(rich_msg)
    elif warning:
        log.warning(rich_msg)
    elif exception:
        log.exception(rich_msg)
    else:
        log.info(rich_msg)

def print(*args, **kwargs):
    print_process("bright_yellow", "labeler", *args, **kwargs)

def _producer(q_in, cap, x1, x2):
    """ """
    cap.set(cv2.CAP_PROP_POS_FRAMES, x1)
    for frame_idx in range(x1, x2+1):
        result, image = cap.read()
        q_in.put((image, frame_idx))
    q_in.put((None, None))

def _consumer(q_in, q_out, labeler_func, labeler_kwargs):    
    """
    """
    while True:
        frame, frame_idx = q_in.get() 
        if not frame_idx: 
            q_in.put((None, None)) 
            return   
        objs_f = labeler_func(frame, frame_idx=frame_idx, **labeler_kwargs)
        q_out.put((frame_idx, objs_f))

def _monitor(q_out, n_frames, objs): 
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Labeling objects...", total=n_frames+1)
        i = 0
        while (not progress.finished) | (not q_out.empty()):            
            frame_idx, objs_f = q_out.get()
            progress.update(task, advance=1)
            objs[frame_idx] = objs_f
    
def run_labeler(cap, x1, x2, n_threads, labeler_func, labeler_kwargs): 
    """ """   
    n_frames = x2 - x1
    q_in = Queue(maxsize=100)
    q_out = Queue()

    for i in range(n_threads):
        worker = Thread(target=_consumer, args=(q_in, q_out, labeler_func, labeler_kwargs))
        worker.setDaemon(True)
        worker.start()

    objs = dict()
    mon = Thread(target=_monitor, args=(q_out, n_frames, objs))
    mon.start()
   
    producer = Thread(target=_producer, args=(q_in, cap, x1, x2))
    producer.start()
    
    producer.join()
    mon.join()

    print('Labeler done')
    return objs
