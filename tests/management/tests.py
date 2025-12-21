from django.core.management.base import OutputWrapper
from django.test import SimpleTestCase


class RecordingStream:
    def __init__(self):
        self.writes = []
        self.flushed = False

    def write(self, s):
        self.writes.append(s)

    def flush(self):
        self.flushed = True


class OutputWrapperTests(SimpleTestCase):
    def test_flush_forwards_to_underlying_stream(self):
        stream = RecordingStream()
        wrapper = OutputWrapper(stream)

        wrapper.write("tick 0...", ending="")
        wrapper.flush()

        self.assertEqual(stream.writes, ["tick 0..."])
        self.assertTrue(stream.flushed)
