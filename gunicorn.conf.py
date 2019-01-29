from prometheus_client import multiprocess

def child_exit(server, worker):
    print("####### Marking %s dead #######", worker.pid)
    multiprocess.mark_process_dead(worker.pid)
