
from pebble.concurrent.process import (
    get_start_method, ProcessFuture, Pipe, launch_process, 
    _function_handler, launch_thread, _worker_handler)


def run_in_process(function, timeout=None, *args, **kwargs):
    # Extracted from pebble https://github.com/noxdafox/pebble/blob/master/pebble/concurrent/process.py

    #_register_function(function)  # wouldn't work for lambda's
    assert get_start_method() == 'fork'

    future = ProcessFuture()
    reader, writer = Pipe(duplex=False)
    name = function.__name__
    worker = launch_process(name, _function_handler, function, args, kwargs, writer)
    writer.close()
    future.set_running_or_notify_cancel()
    launch_thread(name, _worker_handler, future, worker, reader, timeout)
    return future
