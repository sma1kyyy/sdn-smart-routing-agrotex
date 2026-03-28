#mininet topology for AgroTex office SDN lab (security scenario)

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController


class AgroTexTopology:
    """builds and runs a topology with work/guest segments and gateway host"""

    def __init__(self, controller_ip: str = "127.0.0.1", controller_port: int = 6653):
        self.controller_ip = controller_ip
        self.controller_port = controller_port

    def build(self) -> Mininet:
        net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, autoSetMacs=True)

        # SDN controller (ONOS)
        net.addController(
            "c0",
            controller=RemoteController,
            ip=self.controller_ip,
            port=self.controller_port,
        )

        # switches
        s1 = net.addSwitch("s1", protocols="OpenFlow13")  # work VLAN/segment
        s2 = net.addSwitch("s2", protocols="OpenFlow13")  # guest VLAN/segment
        s3 = net.addSwitch("s3", protocols="OpenFlow13")  # border/gateway segment

        # hosts: work network 10.0.1.0/24
        h1 = net.addHost("h1", ip="10.0.1.11/24")
        h2 = net.addHost("h2", ip="10.0.1.12/24")

        # hosts: guest network 10.0.2.0/24
        h3 = net.addHost("h3", ip="10.0.2.11/24")
        h4 = net.addHost("h4", ip="10.0.2.12/24")

        # mock internet gateway ("external" service endpoint)
        hgw = net.addHost("hgw", ip="10.0.2.254/24")

        # access links
        net.addLink(h1, s1, bw=100)
        net.addLink(h2, s1, bw=100)
        net.addLink(h3, s2, bw=100)
        net.addLink(h4, s2, bw=100)
        net.addLink(hgw, s3, bw=100)

        # trunk/uplink links
        net.addLink(s1, s3, bw=1000, delay="1ms")
        net.addLink(s2, s3, bw=1000, delay="1ms")

        return net

    def run(self) -> None:
        net = self.build()
        net.start()

        print("\n[INFO] topology started.")
        print("[INFO] work hosts: h1(10.0.1.11), h2(10.0.1.12)")
        print("[INFO] guest hosts: h3(10.0.2.11), h4(10.0.2.12)")
        print("[INFO] gateway host: hgw(10.0.2.254)\n")
        print("[INFO] example checks in Mininet CLI:")
        print("  mininet> pingall")
        print("  mininet> h3 ping -c 3 hgw")
        print("  mininet> h3 ping -c 3 h1  # should fail after isolation rules")

        CLI(net)
        net.stop()


def main() -> None:
    topo = AgroTexTopology()
    topo.run()


if __name__ == "__main__":
    setLogLevel("info")
    main()
