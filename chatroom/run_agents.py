from multiprocessing import Process
from client_ws import run_agent

ROOM = "test"
AGENTS = ['A','B','C']

if __name__ == "__main__":
    agents = []

    for aid in AGENTS:
        print(f'Starting Client {aid} added...')
        p = Process(target=run_agent, args=(aid,))
        p.start()
        agents.append(p)

    for p in agents:
        p.join()