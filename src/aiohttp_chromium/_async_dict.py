from collections import UserDict
from asyncio import Event


class async_dict(UserDict):
    """MutableMapping with waitable get and pop.

    aka "class AsyncDict"

    based on "class AsyncDictionary" from
    https://github.com/groove-x/trio-util/blob/cd8f273f62dbb301b504a3b7778bdd3069fecb6f/src/trio_util/_async_dictionary.py

    see also

    https://github.com/groove-x/trio-util/issues/4
    AsyncDict vs. cancellation
    AsyncDictionary has been removed from the package

    https://github.com/python-trio/trio/issues/467
    Add "one obvious way" for implementing the common multiplexed request/response pattern

    https://github.com/shmocz/pyra2yr/blob/main/pyra2yr/async_container.py

    https://github.com/f3at/feat/blob/15da93fc9d6ec8154f52a9172824e25821195ef8/src/feat/common/container.py#L744
    """

    _pending = {}  # key: Event

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __getitem__(self, key):
        """Return value of given key, blocking until populated."""
        try:
            return super().__getitem__(key)
        except KeyError:
            pass
        try:
            event = self._pending[key]
        except KeyError:
            event = Event()
            self._pending[key] = event
        await event.wait()
        return super().__getitem__(key)

    async def pop(self, key):
        """Remove key and return its value, blocking until populated."""
        value = await self.get(key)
        super().__delitem__(key)
        return value

    def is_waiting(self, key) -> bool:
        """Return True if there is a task waiting for key."""
        return key in self._pending

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key in self._pending:
            self._pending.pop(key).set()
