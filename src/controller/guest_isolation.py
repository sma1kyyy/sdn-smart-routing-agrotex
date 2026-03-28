#install/remove ONOS flow rules for guest-to-work network isolation

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

import requests
from requests.auth import HTTPBasicAuth


@dataclass(frozen=True)
class Config:
    onos_url: str
    username: str
    password: str
    guest_cidr: str = "10.0.2.0/24"
    work_cidr: str = "10.0.1.0/24"
    priority: int = 50000


class OnosGuestIsolation:
    def __init__(self, config: Config):
        self.cfg = config
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.username, config.password)
        self.session.headers.update({
            "Accept": "application/json"
        })

    def _url(self, path: str) -> str:
        return f"{self.cfg.onos_url.rstrip('/')}{path}"

    def _get_devices(self) -> list[str]:
        response = self.session.get(self._url("/onos/v1/devices"), timeout=10)
        response.raise_for_status()
        data = response.json()
        devices = [d["id"] for d in data.get("devices", []) if d.get("available")]
        if not devices:
            raise RuntimeError("no available ONOS devices found. mininet connected?")
        return devices

    def _drop_flow(self, device_id: str) -> dict:
        return {
            "priority": self.cfg.priority,  # 50000
            "timeout": 0,
            "isPermanent": True,
            "deviceId": device_id,
            "treatment": {"instructions": []},
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},
                    {"type": "IPV4_SRC", "ip": self.cfg.guest_cidr},
                    {"type": "IPV4_DST", "ip": self.cfg.work_cidr}
                ]
            }
        }

    def apply(self) -> None:
        devices = self._get_devices()
        print(f"[INFO] found {len(devices)} active device(s).")

        for dev in devices:
            payload = self._drop_flow(dev)
            response = self.session.post(
                self._url(f"/onos/v1/flows/{dev}"),
                json=payload, 
                timeout=10,
            )
            response.raise_for_status()
            print(f"[OK] drop policy installed on {dev}.")

        print("\n[DONE] guest-to-work isolation policy is active")

    def remove(self) -> None:
        devices = self._get_devices()
        removed = 0

        for dev in devices:
            response = self.session.get(self._url(f"/onos/v1/flows/{dev}"), timeout=10)
            response.raise_for_status()
            flows = response.json().get("flows", [])

            for flow in flows:
                criteria = flow.get("selector", {}).get("criteria", [])
                src_match = any(
                    c.get("type") == "IPV4_SRC" and c.get("ip") == self.cfg.guest_cidr
                    for c in criteria
                )
                dst_match = any(
                    c.get("type") == "IPV4_DST" and c.get("ip") == self.cfg.work_cidr
                    for c in criteria
                )
                if flow.get("priority") == self.cfg.priority and src_match and dst_match:
                    flow_id = flow["id"]
                    delete = self.session.delete(
                        self._url(f"/onos/v1/flows/{dev}/{flow_id}"), timeout=10
                    )
                    delete.raise_for_status()
                    removed += 1
                    print(f"[OK] removed policy flow {flow_id} from {dev}")

        print(f"\n[DONE] removed {removed} isolation flow(s).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ONOS guest network isolation manager")
    parser.add_argument("action", choices=["apply", "remove"], help="Policy action")
    parser.add_argument("--onos-url", default="http://127.0.0.1:8181", help="ONOS base URL")
    parser.add_argument("--user", default="onos", help="ONOS username")
    parser.add_argument("--password", default="rocks", help="ONOS password")
    parser.add_argument("--guest-cidr", default="10.0.2.0/24", help="Guest subnet CIDR")
    parser.add_argument("--work-cidr", default="10.0.1.0/24", help="Work subnet CIDR")
    parser.add_argument(
        "--priority", type=int, default=50000, help="Flow priority for deny rules"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = Config(
        onos_url=args.onos_url,
        username=args.user,
        password=args.password,
        guest_cidr=args.guest_cidr,
        work_cidr=args.work_cidr,
        priority=args.priority,
    )
    policy = OnosGuestIsolation(cfg)

    if args.action == "apply":
        policy.apply()
    elif args.action == "remove":
        policy.remove()


if __name__ == "__main__":
    main()
