# main.py
from schedule.manager import start as start_manager

if __name__ == "__main__":
    start_manager()


"""
In the Future...

from multiprocessing import Process
from schedule.manager import start as start_manager
from machine.schedule_monitor import start as start_monitor

if __name__ == "__main__":
    p1 = Process(target=start_manager)
    p2 = Process(target=start_monitor)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


Or...

Use Docker Compose with each module as a container
or
Supervisor, Systemd, or PM2 to manage Python scripts as services

"""