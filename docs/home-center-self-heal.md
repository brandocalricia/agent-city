# Home center self-heal

The Home line "{active} active · {errors} error" takes `errors` from
`topology.errorProvider`. That field is the provider whose newest call
status is outside 200-399. Idle traffic is "0 active" and is not an error.

A disabled connection must not set it. The metrics query keeps
`pc.is_active = 1`. `tools/home_error_heal.py` writes that filter back
into the running bundle when an upgrade drops it, and it records a heal
attempt when the center has shown an error for more than 2 minutes.
`tools/minute_heal.sh` runs this check at least every 60 seconds.

`tests/test_home_error_heal.py` fails if an error older than 2 minutes
has no heal attempt inside 60 seconds.
