# MySpeed

Connect Home Assistant to one or more [MySpeed](https://github.com/gnmyt/MySpeed)
instances and expose their speed-test data as entities.

Add the integration **once per instance** — each becomes its own device with
download, upload, ping, jitter, last-test, server and status entities, plus a
**Run speed test** button, a **Pause** switch and a version **Update** entity.

After installing via HACS, restart Home Assistant, then go to
**Settings → Devices & Services → Add Integration → MySpeed** and enter your
instance URL (default port `5216`) and password if one is set.
