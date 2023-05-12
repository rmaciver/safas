"""

"""
from copy import deepcopy
import cv2

from random import random
from time import sleep
from threading import Thread
import multiprocessing as mp
from multiprocessing.pool import ThreadPool
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import Progress
#
def labeler_producer(q_in, cap, x1, x2):
    """ """
    cap.set(cv2.CAP_PROP_POS_FRAMES, x1)
    for frame_idx in range(x1, x2+1):
        result, image = cap.read()
        q_in.put((image, frame_idx))
    q_in.put((None, None))
    print(f"Producer finished")

def labeler_consumer(q_in, q_out, labeler_kwargs): # labeler_kwargs):
    print(f"consumer!")
    while True:
        frame, frame_idx = q_in.get() 
        if not frame_idx: 
            q_in.put((None, None)) 
            return 
        mean = frame.mean()
        q_out.put((frame_idx, mean))

def labeler_monitor(q_out, n_frames, objs): 
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Labeling objects...", total=n_frames+1)
        while (not progress.finished) | (not q_out.empty()):            
            frame_idx, val = q_out.get()
            progress.update(task, advance=1)
            objs[frame_idx] = val
            
def run_labeler(): 
    """ """
    filename = r"C:\Users\rmcma\Desktop\floc-vids\004_reinerstieg_vornafen_26-9-19_01.avi"
    cap = cv2.VideoCapture(filename)
    labeler_kwargs = {"pants": 3, "hair": 7}

    x1 = 50
    x2 = 200
    
    n_frames = x2 - x1
    print(f"Processing {n_frames} frames")
    q_in = Queue(maxsize=50)
    q_out = Queue()

    num_threads = 5

    for i in range(num_threads):
        worker = Thread(target=labeler_consumer, args=(q_in, q_out, labeler_kwargs))
        worker.setDaemon(True)
        worker.start()

    objs = dict()
    m = Thread(target=labeler_monitor, args=(q_out, n_frames, objs))
    m.start()
   
    producer = Thread(target=labeler_producer, args=(q_in, cap, x1, x2))
    producer.start()
    producer.join()
    m.join()

    print('>Labeler done.')

if __name__ == '__main__':
    run_labeler()
