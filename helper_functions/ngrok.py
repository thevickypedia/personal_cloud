import os
from logging import INFO, basicConfig, getLogger
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, gethostbyname, socket
from subprocess import check_output

from pyngrok.conf import get_default
from pyngrok.exception import PyngrokError
from pyngrok.ngrok import connect, kill, set_auth_token

basicConfig(format="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
            level=INFO)
getLogger(name='pyngrok').propagate = False  # disable module level logging
logger = getLogger(Path(__file__).stem)

host = gethostbyname('localhost')
port = int(os.environ.get('port', 4443))


def writer(url) -> None:
    """Writes the received url into a file named `url`.

    Notes:
        - This is to support `Jarvis <https://github.com/thevickypedia/Jarvis>`__
        - Jarvis scans the url file to fetch the public_url and sends it to the end user.

    Args:
        url: Public URL generated by Ngrok.
    """
    if 'url' in os.listdir():
        os.remove('url')
    with open('url', 'w') as url_file:
        url_file.write(url)


def checker() -> str:
    """Checks for an existing instance of ``ngrok.py`` running.

    Returns:
        str:
        Returns the process ID if an existing instance is actively running.
    """
    pid_check = check_output("ps -ef | grep ngrok", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if 'site-packages/pyngrok/bin/ngrok' in id_:
            return id_.split()[1]


def tunnel() -> None:
    """Creates an HTTP socket and uses `pyngrok` module to bind the socket.

    Once the socket is bound, the listener is activated and runs in a forever loop accepting connections.

    See Also:
        Run the following code to setup.

        .. code-block:: python
            :emphasize-lines: 4,7,10

            from pyngrok.conf import PyngrokConfig, get_default
            from pyngrok.ngrok import set_auth_token

            # Sets auth token only during run time without modifying global config.
            PyngrokConfig.auth_token = '<NGROK_AUTH_TOKEN>'

            # Uses auth token from the specified file without modifying global config.
            get_default().config_path = "/path/to/config.yml"

            # Changes auth token at $HOME/.ngrok2/ngrok.yml
            set_auth_token('<NGROK_AUTH_TOKEN>')
    """
    sock = socket(AF_INET, SOCK_STREAM)

    # # Uncomment bind to create a whole new connection to the port
    # server_address = (host, port)  # Bind a local socket to the port
    # sock.bind(server_address)  # Bind only accepts tuples

    sock.listen(1)

    if os.path.isfile('ngrok.yml'):
        get_default().config_path = 'ngrok.yml'

    if auth_token := os.environ.get('ngrok_auth'):
        set_auth_token(auth_token)

    try:
        endpoint = connect(port, "http", options={"remote_addr": f"{host}:{port}"})  # Open a ngrok tunnel to the socket
        public_url = endpoint.public_url.replace('http', 'https')
        writer(public_url)
    except PyngrokError as err:
        logger.error(err)
        writer(err)
        return

    logger.info(f'Hosting to the public URL: {public_url}')

    connection = None
    while True:
        try:
            # Wait for a connection
            logger.info("Waiting for a connection")
            connection, client_address = sock.accept()
            logger.info(f"Connection established from {client_address}")
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            if connection:
                connection.close()
            break

    kill(pyngrok_config=None)  # uses default config when None is passed
    sock.close()


if __name__ == '__main__':
    tunnel()
