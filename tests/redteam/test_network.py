"""No tool has an arbitrary network route (decision 0023; SPEC.md Section 3).

``bwrap --unshare-all`` gives the tool a fresh network namespace with only a
down loopback, and ``--cap-drop ALL`` removes CAP_NET_ADMIN/RAW, so nothing can
bring an interface up or open a raw socket. The only reachable endpoint is the
fixture Unix socket, mounted by path; any other Unix socket path is simply not
in the mount namespace.
"""
from __future__ import annotations

import socket as _s

from conftest import attempt_snippet, requires_sandbox, run_probe, skip_if_root

pytestmark = [requires_sandbox, skip_if_root]


def test_no_tcp_udp_or_raw_route_exists(trial):
    port = trial.listen_tcp()  # a real listener on the host loopback, unreachable from the net ns
    code = attempt_snippet() + f"""
import socket
def tcp(host, port):
    def f():
        s = socket.socket(); s.settimeout(2); s.connect((host, port)); s.close(); return "connected"
    return f
def udp(host, port):
    def f():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"x", (host, port))   # may 'succeed' into the void; then try to read
        s.settimeout(1); s.recvfrom(16); return "roundtrip"
    return f
attempt("tcp_loopback", tcp("127.0.0.1", {port}))
attempt("tcp_external", tcp("192.0.2.1", 9))     # TEST-NET-1, routed nowhere even unsandboxed
attempt("tcp_public_dns", tcp("8.8.8.8", 53))
attempt("udp_external", udp("192.0.2.1", 9))
attempt("ip6_loopback", tcp("::1", {port}))
def raw():
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW); s.close(); return "opened"
attempt("raw_packet_socket", raw)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    for name in ("tcp_loopback", "tcp_external", "tcp_public_dns", "ip6_loopback", "raw_packet_socket"):
        assert r[name][0] == "denied", (name, r[name])
    # UDP sendto to a dead net can "send"; the point is no datagram ever returns.
    assert r["udp_external"][0] == "denied", r["udp_external"]


def test_cannot_reach_a_foreign_unix_socket(trial):
    foreign = trial.listen_unix(trial.outside, "foreign.sock")  # outside every mount
    code = attempt_snippet() + f"""
import socket, os
def unix(path):
    def f():
        s = socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(path); s.close(); return "connected"
    return f
attempt("foreign_rel", unix({foreign!r}))
attempt("foreign_abs", unix({str(trial.outside / "foreign.sock")!r}))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["foreign_rel"][0] == "denied", r["foreign_rel"]
    assert r["foreign_abs"][0] == "denied", r["foreign_abs"]


def test_cannot_bring_the_loopback_interface_up(trial):
    """Even if a route to 127.0.0.1 would help, CAP_NET_ADMIN is dropped, so the
    tool cannot configure the interface (ioctl SIOCSIFFLAGS -> EPERM/EACCES)."""
    code = attempt_snippet() + r"""
import socket, struct, fcntl, os
SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914
IFF_UP = 0x1
def bring_up():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ifr = struct.pack("16sh", b"lo", 0)
    cur = fcntl.ioctl(s, SIOCGIFFLAGS, ifr)
    flags = struct.unpack("16sh", cur)[1] | IFF_UP
    fcntl.ioctl(s, SIOCSIFFLAGS, struct.pack("16sh", b"lo", flags))
    return "configured"
attempt("loopback_up", bring_up)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["loopback_up"][0] == "denied", r["loopback_up"]


def test_io_uring_cannot_reach_a_host_file_or_foreign_socket(trial):
    """io_uring SQEs are not seccomp-filtered, but they still run inside the mount
    and network namespaces: an unmounted path does not exist and there is no
    route, so io_uring buys no escape. (If io_uring is unavailable, that is also
    fine — the point is it never succeeds.)"""
    foreign = trial.listen_unix(trial.outside, "foreign2.sock")
    code = attempt_snippet() + f"""
import ctypes, os, struct
libc = ctypes.CDLL(None, use_errno=True)
NR_io_uring_setup = 425
def setup():
    class Params(ctypes.Structure):
        _fields_ = [("x", ctypes.c_uint32 * 30)]
    p = Params()
    ctypes.set_errno(0)
    fd = libc.syscall(ctypes.c_long(NR_io_uring_setup), 8, ctypes.byref(p))
    if fd < 0:
        raise OSError(ctypes.get_errno(), "io_uring_setup unavailable")
    os.close(fd)
    return "io_uring_available"
attempt("io_uring_setup", setup)
# Regardless of io_uring, the host path simply is not present in the mount ns:
attempt("open_host_file", lambda: open("/etc/passwd").read(8))
attempt("stat_foreign_sock", lambda: os.stat({str(trial.outside / "foreign2.sock")!r}))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    # Whether or not io_uring is available, the host file and foreign socket are unreachable.
    assert r["open_host_file"][0] == "denied", r["open_host_file"]
    assert r["stat_foreign_sock"][0] == "denied", r["stat_foreign_sock"]
