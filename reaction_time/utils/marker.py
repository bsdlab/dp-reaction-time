import serial
from pylsl import StreamInfo, StreamOutlet

from reaction_time.utils.clock import sleep_s
from reaction_time.utils.logging import logger


class MarkerWriter(object):

    """Class for interacting with the virtual serial
    port provided by the BV TriggerBox and an LSL marker stream
    """

    def __init__(self, serial_nr: str, pulsewidth: float = 0.01):
        """Open the port at the given serial_nr

        Parameters
        ----------

        serial_nr : str
            Serial number of the trigger box as can be read under windows hw manager
        pulsewidth : float
            Seconds to sleep between base and final write to the PPort

        """
        try:
            self.port = serial.Serial(serial_nr)
        except (
            serial.SerialException
        ):  # if trigger box is not available at given serial_nr
            logger.debug(
                f"Starting DUMMY as connection with {serial_nr=} failed"
            )
            self.create_dummy(serial_nr)

        self.pulsewidth = pulsewidth

        self.stream_info = StreamInfo(
            name="StroopParadigmMarkerStream",
            type="Markers",
            channel_count=1,
            nominal_srate=0,  # irregular stream
            channel_format="int32",
            source_id="myStroopParadigmMarkerStream",
        )
        self.stream_outlet = StreamOutlet(self.stream_info)
        self.logger: logger | None = None

    def write(self, data):
        """

        Parameters
        ----------

        data:  list of int(s), byte or bytearray
            data to be written to the port

        Returns
        -------
        byteswritten : int
            number of bytes written

        """
        # Send to LSL Outlet
        self.stream_outlet.push_sample(data)
        if self.logger:
            self.logger.info(f"Pushing sample {data}")

        # Set a base value as trigger will only emit once change from base is written
        self.port.write([0])
        sleep_s(self.pulsewidth)
        ret = self.port.write(data)

        return ret

    def __del__(self):
        """Destructor to close the port"""
        print("Closing serial port connection")
        if self.port is not None:
            self.port.close()

    def create_dummy(self, serial_nr: str):
        """Initialize a dummy version - used for testing"""
        print(
            "-" * 80
            + "\n\nInitializing DUMMY VPPORT\nSetup for regular VPPORT at"
            + f" at {serial_nr} failed \n No device present?\n"
            + "-" * 80
        )

        self.port = None
        self.write = self.dummy_write

    def dummy_write(self, data):
        """Overwriting the write to pp"""
        print(f"PPort would write data: {data}")
