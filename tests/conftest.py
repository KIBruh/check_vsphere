import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests that require vcsim and govc",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return

    skip_marker = pytest.mark.skip(
        reason="use --run-integration to run integration tests"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(host, port, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.1)

    raise RuntimeError("vcsim did not become ready in time")


@pytest.fixture
def vcsim_server():
    vcsim = shutil.which("vcsim")
    if not vcsim:
        pytest.skip("vcsim binary not found in PATH")

    host = "127.0.0.2"
    port = _find_free_port()

    proc = subprocess.Popen(
        [vcsim, "-l", f"{host}:{port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_port(host, port)
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        raise

    yield {"host": host, "port": port}

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _get_vcsim_cert(host, port):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
            return cert_pem


def _generate_tls_cert(host, port):
    """Generate self-signed TLS certificate for host."""
    key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False)
    cert_file = tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False)

    subprocess.run(
        [
            "openssl", "req", "-new", "-x509",
            "-keyout", key_file.name,
            "-out", cert_file.name,
            "-days", "365",
            "-subj", f"/CN={host}",
            "-addext", f"subjectAltName=IP:{host}",
            "-nodes",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    key_file.close()
    cert_file.close()

    return key_file.name, cert_file.name


@pytest.fixture
def vcsim_server_with_tls():
    """vcsim server with TLS enabled and valid certificate."""
    vcsim = shutil.which("vcsim")
    if not vcsim:
        pytest.skip("vcsim binary not found in PATH")

    host = "127.0.0.2"
    port = _find_free_port()

    key_file, cert_file = _generate_tls_cert(host, port)

    proc = subprocess.Popen(
        [vcsim, "-l", f"{host}:{port}", "-tlscert", cert_file, "-tlskey", key_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_port(host, port)
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        raise

    yield {"host": host, "port": port, "proc": proc, "cert_file": cert_file, "key_file": key_file}

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    os.unlink(key_file)
    os.unlink(cert_file)


@pytest.fixture
def temp_ca_cert(vcsim_server_with_tls):
    """Return the generated certificate file as CA."""
    yield vcsim_server_with_tls["cert_file"]


@pytest.fixture
def cli_connection_args(vcsim_server):
    return [
        "-nossl",
        "-s",
        vcsim_server["host"],
        "-o",
        str(vcsim_server["port"]),
        "-u",
        "user",
        "-p",
        "pass",
    ]


@pytest.fixture
def run_cli():
    def _run(args, timeout=30, env=None, disable_ssl=True):
        args = list(args)
        if disable_ssl and "-nossl" not in args:
            args.insert(1, "-nossl")
        cmd = [sys.executable, "-m", "checkvsphere.cli"] + args
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        return subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=merged_env,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    return _run


@pytest.fixture
def run_govc(vcsim_server):
    govc = shutil.which("govc")
    if not govc:
        pytest.skip("govc binary not found in PATH")

    base_env = {
        "GOVC_URL": f"https://user:pass@{vcsim_server['host']}:{vcsim_server['port']}/sdk",
        "GOVC_INSECURE": "1",
    }

    def _run(args, timeout=30):
        merged_env = os.environ.copy()
        merged_env.update(base_env)

        return subprocess.run(
            [govc] + list(args),
            cwd=str(REPO_ROOT),
            env=merged_env,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    return _run
