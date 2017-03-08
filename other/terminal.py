from console import Commander

if __name__ == '__main__':
    class TestCmd(Command):
        def do_echo(self, *args):
            '''echo - Just echos all arguments'''
            return ' '.join(args)

        def do_raise(self, *args):
            raise Exception('Some Error')


    c = Commander('Test', cmd_cb=TestCmd())

    # Test async output -  e.g. comming from different thread
    import time

    def run():
        while True:
            time.sleep(1)
            c.output('Tick', 'green')


    t = Thread(target=run)
    t.daemon = True
    t.start()

    # start main loop
    c.loop()