import threading
import queue
import time


class WorkerQueue(threading.Thread):
    """Класс очередей"""
    def __init__(self, func_worker, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.input_queue = queue.Queue()
        self.func_worker = func_worker

    def get_len_queue(self):
        print(f"Длина очереди: {self.input_queue.qsize()}")

    def send_in_queue(self, item):
        self.input_queue.put(item)

    def close(self):
        self.input_queue.join()
        self.input_queue.put("end_work")

    def update_func(self, item):
        """Переопределяется задает новую функцию для обработки элемента очереди"""
        pass

    def processing_element(self, item):
        self.update_func(item)
        self.func_worker(item)
        self.input_queue.task_done()

    def run(self):
        while True:
            if self.input_queue.empty():
                time.sleep(1)
                continue
            item = self.input_queue.get()
            if item == "end_work":
                break
            self.processing_element(item)
        self.input_queue.task_done()
        return


class WorkerQueueSignal(WorkerQueue):
    """Класс очередей для сигналов"""
    def __init__(self, func_worker_dict, *args, **kwargs):
        WorkerQueue.__init__(self, None, *args, **kwargs)
        self.func_worker_dict = func_worker_dict

    def update_func(self, item):
        func_variant = item.get('func_variant')
        if func_variant == 'deal':
            self.func_worker = self.func_worker_dict['deal']
        elif func_variant == 'alert':
            self.func_worker = self.func_worker_dict['alert']
        else:
            self.func_worker = self.func_worker_dict['deal']
