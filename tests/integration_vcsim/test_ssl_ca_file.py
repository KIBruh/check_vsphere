import pytest


pytestmark = pytest.mark.integration


def test_about_with_ssl_ca_file(run_cli, vcsim_server_with_tls, temp_ca_cert):
    """Connecting with trust and valid CA should succeed."""
    result = run_cli(
        [
            "about",
            "-s", vcsim_server_with_tls["host"],
            "-o", str(vcsim_server_with_tls["port"]),
            "-u", "user",
            "-p", "pass",
        ],
        env={"SSL_CA_FILE": temp_ca_cert},
        disable_ssl=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "govmomi simulator" in result.stdout


def test_about_with_ssl_ca_path(run_cli, vcsim_server_with_tls, temp_ca_cert):
    """Connecting with CA path should succeed - copy to openssl hashed name."""
    import tempfile
    import shutil
    import subprocess
    dir_path = tempfile.mkdtemp()

    hash_name = subprocess.run(
        ["openssl", "x509", "-hash", "-noout", "-in", temp_ca_cert],
        capture_output=True, text=True
    ).stdout.strip()
    dest = shutil.copy(temp_ca_cert, f"{dir_path}/{hash_name}.0")

    try:
        result = run_cli(
            [
                "about",
                "-s", vcsim_server_with_tls["host"],
                "-o", str(vcsim_server_with_tls["port"]),
                "-u", "user",
                "-p", "pass",
            ],
            env={"SSL_CA_PATH": dir_path},
            disable_ssl=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK:" in result.stdout
        assert "govmomi simulator" in result.stdout
    finally:
        shutil.rmtree(dir_path)


def test_about_without_ca_fails_with_tls(run_cli, vcsim_server_with_tls):
    """Connecting without trust should fail with self-signed cert."""
    result = run_cli(
        [
            "about",
            "-s", vcsim_server_with_tls["host"],
            "-o", str(vcsim_server_with_tls["port"]),
            "-u", "user",
            "-p", "pass",
        ],
        disable_ssl=False,
    )

    assert result.returncode in (2, 3), result.stdout + result.stderr
    assert "ERROR" in result.stdout or "UNKNOWN" in result.stdout


def test_about_without_ssl_verification_still_works(run_cli, vcsim_server_with_tls):
    """Using -nossl should bypass SSL verification."""
    result = run_cli(
        [
            "about",
            "-s", vcsim_server_with_tls["host"],
            "-o", str(vcsim_server_with_tls["port"]),
            "-u", "user",
            "-p", "pass",
        ],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout