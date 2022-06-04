import multiprocessing

worker_class = "uvicorn.workers.UvicornWorker"
workers = min(4, multiprocessing.cpu_count())
bind = "0.0.0.0:8010"
timeout = 90
