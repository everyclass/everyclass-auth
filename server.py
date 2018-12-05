# import multiprocessing
from everyclass.auth import create_app


app = create_app()

if __name__ == '__main__':
    # process_handle_queue = multiprocessing.Process(target=start_register_queue)
    # process_handle_queue.start()
    app.run(host='0.0.0.0')


