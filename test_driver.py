from main import *
import time

# ===== Singleton process w/multi subscribers =====
test_in_progress_event = threading.Event()
test_in_progress_lock = threading.Lock()

def start_test(ctx):
    ctx.send_subscribe(ctx.publisher.address, ["test-status", "device-info"])
    with test_in_progress_lock:
        if test_in_progress_event.is_set():
            ctx.send("Test Already in Progress")
            return
        else:
            test_in_progress_event.set()
            ctx.send("Test Started")
    ctx.publish("test-status", {
        "stage-1": "not started",
        "stage-2": "not started"
    }, "start")
    time.sleep(0.1)
    ctx.publish("test-status", {
        "stage-1": "started",
        "stage-2": "not started"
    })
    ctx.publish("device-info", {
        "light": "yes",
        "air": "no"
    })
    time.sleep(1)
    ctx.publish("test-status", {
        "stage-1": "test-finish-success",
        "stage-2": "started",
    })
    time.sleep(1)
    ctx.publish("test-status", {
        "stage-1": "test-finish-success",
        "stage-2": "test-finish-failure",
    }, "end")
    with test_in_progress_lock:
        test_in_progress_event.clear()

router = SeaZMQServer({
    "router": "tcp://127.0.0.1:8000",
    "publisher": "tcp://127.0.0.1:8001",
    "commands": {
        "start-test": start_test,
    }
})

dealer = SeaZMQClient({"conn": "tcp://127.0.0.1:8000"})
client_1 = dealer.send({"command": "start-test"})
# unwrapped for easier print viewing.
client_1.response_event.wait()
print("client_1", client_1.get_response())

client_1.stream_event.wait()
print("client_1", client_1.get_stream())
client_1.stream_event.wait()
print("client_1", client_1.get_stream())

time.sleep(5)
client_2 = dealer.send({"command": "start-test"})

client_2.response_event.wait()
print("client_2", client_2.get_response())

client_2.stream_event.wait()
print("client_2", client_2.get_stream())
client_3 = dealer.send({"command": "start-test"})
client_1.stream_event.wait()
print("client_1", client_1.get_stream())

client_2.stream_event.wait()
print("client_2", client_2.get_stream())

client_1.stream_event.wait()
print("client_1", client_1.get_stream())
client_2.stream_event.wait()
print("client_2", client_2.get_stream())
client_1.stream_event.wait()
print("client_1", client_1.get_stream())
print("Done")
client_3.stream_event.wait()
print("client_3", client_3.get_stream())
client_1.close()
client_2.close()
client_3.close()
dealer.stop_threads()
router.stop_threads()
