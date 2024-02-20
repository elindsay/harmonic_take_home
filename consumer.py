class Consumer:
    def __init__(self, name):
        self.name = name
 
    def receive(self, message):
        print(f"{self.name}"+"received message:"
              +f"{message}")

