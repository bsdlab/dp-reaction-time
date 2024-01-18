from dareplane_utils.default_server.server import DefaultServer
from fire import Fire

from reaction_time.main import run_one_block_reaction_time
from reaction_time.utils.logging import logger


def main(port: int = 8080, ip: str = "127.0.0.1", loglevel: int = 30):
    # Implement primary commands here

    logger.setLevel(loglevel)

    pcommand_map = {"RUN": run_one_block_reaction_time}

    logger.debug("Pcommands setup")

    server = DefaultServer(
        port,
        ip=ip,
        pcommand_map=pcommand_map,
        name="reaction_time",
        logger=logger,
    )

    # initialize to start the socket
    server.init_server()
    # start processing of the server
    server.start_listening()

    return 0


if __name__ == "__main__":
    Fire(main)
