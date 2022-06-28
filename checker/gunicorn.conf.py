import multiprocessing

worker_class = "uvicorn.workers.UvicornWorker"
workers = min(16, multiprocessing.cpu_count())
bind = "0.0.0.0:8000"
timeout = 90
