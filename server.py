import multiprocessing
from everyclass.auth import create_app
from everyclass.auth.handle_register_queue import start_register_queue

app = create_app()

if __name__ == '__main__':
    process_handle_queue = multiprocessing.Process(target=start_register_queue)
    process_handle_queue.start()
    app.run(host='0.0.0.0', debug=True)


