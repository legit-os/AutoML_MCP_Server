import time

print("Starting 8-second task...")
for i in range(8):
    print(f"Running... {i}")
    time.sleep(1)
print("Finished!")
