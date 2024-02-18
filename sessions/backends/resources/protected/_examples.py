EXAMPLES = {
    "dict": """
import time
import random
from pypools import ProtectedResource
from concurrent.futures import ThreadPoolExecutor, as_completed
    protected_dict = ProtectedResource({"a": 1, "b": 2, "c": 3})
def update_dict(dct):
    with dct:
        length = len(dct)
        if random.choice([True, False]):
            time.sleep(random.uniform(0, 1))
        dct[current_thread().ident] = length
        return length
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(update_dict, protected_dict) for _ in range(10)]
    for i, future in enumerate(as_completed(futures)):
        assert future.result() == i
    """
}

def example(T):
    return EXAMPLES[T]
