from lnst.Controller.Task import ctl
from lnst.RecipeCommon.ModuleWrap import ping, ping6
from Testlib import Testlib
import logging

# ------
# SETUP
# ------

tl = Testlib(ctl)

# hosts
host1 = ctl.get_host("host1")
host2 = ctl.get_host("host2")

# guest machines
guest1 = ctl.get_host("guest1")

guest1.sync_resources(modules=["IcmpPing", "Icmp6Ping"])

# ------
# TESTS
# ------

ipv = ctl.get_alias("ipv")
mtu = ctl.get_alias("mtu")
turn_off_sriov = ctl.get_alias("turn_off_sriov")
skip_tc_verify = ctl.get_alias("skip_tc_verify")

g1_nic = guest1.get_interface("if1")
try:
    h2_nic = host2.get_interface("if1")
except KeyError:
    h2_nic = host2.get_device("int0")

vxlan_port = ctl.get_alias("vxlan_port")
vxlan_dev = "vxlan_sys_%s" % vxlan_port


def do_pings():
    ping_opts = {"count": 10, "interval": 0.2}
    if ipv in ['ipv4', 'both']:
        ping((guest1, g1_nic, 0, {"scope": 0}),
             (host2, h2_nic, 0, {"scope": 0}),
             options=ping_opts, expect="pass")
        if not skip_tc_verify:
            verify_tc_rules('ip')

    if ipv in ['ipv6', 'both']:
        ping6((guest1, g1_nic, 1, {"scope": 0}),
              (host2, h2_nic, 1, {"scope": 0}),
              options=ping_opts, expect="pass")
        if not skip_tc_verify:
            verify_tc_rules('ipv6')


def verify_tc_rules(proto):
    g1_mac = g1_nic.get_hwaddr()
    h2_mac = h2_nic.get_hwaddr()

    # encap rule
    m = tl.find_tc_rule(host1, 'tap1', g1_mac, h2_mac, proto, 'tunnel_key set')
    desc = "TC rule %s tunnel_key set" % proto
    if m:
        tl.custom(host1, desc)
    else:
        tl.custom(host1, desc, 'ERROR: cannot find tc rule')

    # decap rule
    m = tl.find_tc_rule(host1, vxlan_dev, h2_mac, g1_mac, proto, 'tunnel_key unset')
    desc = "TC rule %s tunnel_key unset" % proto
    if m:
        tl.custom(host1, desc)
    else:
        tl.custom(host1, desc, 'ERROR: cannot find tc rule')


# sleep a second before testing.
ctl.wait(3)
do_pings()
