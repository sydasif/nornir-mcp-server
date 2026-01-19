"""Resource registrations for the Nornir MCP server.

Drop your own resource functions in this file. Any callable whose name
starts with "resource_" will be automatically registered when
`register_resources(mcp, nr_mgr)` is called from `server.py`.

Registration rules:
- If the function takes no parameters it will be called with no args.
- If it accepts a single parameter, it will be passed the `nr_mgr`
  (instance of NornirManager) so it can access `nr_mgr.nr` or other
  helpers.
- If a function name is `resource_foo_bar` and no explicit URI is
  provided in RESOURCE_MAP, the URI will default to
  `resource://user/foo/bar`.

Pre-registered resources:
- resource://inventory/hosts -> list of inventory hosts
- resource://inventory/groups -> list of inventory groups
- resource://cisco_ios_commands -> parsed JSON from resources/cisco_ios_commands.json
"""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

from .application import get_nr

# We import get_nr inside the functions to avoid circular import issues

# Map of local function name -> resource URI(s). Use this to control
# explicit URIs for functions in this module. Values may be a string or
# a list of strings. Template URIs (with '{...}') are supported and
# will be registered as separate resource patterns.
RESOURCE_MAP: dict[str, object] = {
    "resource_hosts": [
        "resource://inventory/hosts",
        "resource://inventory/hosts/{keyword}",
    ],
    "resource_groups": [
        "resource://inventory/groups",
        "resource://inventory/groups/{keyword}",
    ],
    "resource_cisco_ios_commands": "resource://cisco_ios_commands",
}


def _sanitize_dict(d: dict, remove_keys=None):
    """Remove sensitive keys recursively from a dict in-place and return it."""
    if remove_keys is None:
        remove_keys = {"username", "password", "secret"}
    if not isinstance(d, dict):
        return d
    for key in list(d.keys()):
        if key in remove_keys:
            d.pop(key, None)
            continue
        val = d.get(key)
        if isinstance(val, dict):
            _sanitize_dict(val, remove_keys)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    _sanitize_dict(item, remove_keys)
    return d


def resource_hosts():
    """Return a list of hosts from the Nornir inventory."""
    # Get the Nornir instance
    nr = get_nr()

    # Get hosts and sanitize to remove sensitive information
    hosts = []
    for name, host_obj in nr.inventory.hosts.items():
        safe_data = dict(host_obj.data or {})
        _sanitize_dict(safe_data)
        hostname = host_obj.hostname
        platform = host_obj.platform
        groups = [g.name for g in host_obj.groups]

        hosts.append(
            {
                "name": name,
                "hostname": hostname,
                "platform": platform,
                "groups": groups,
                "data": safe_data,
            }
        )

    return hosts


def resource_groups():
    """Return a list of inventory group names."""
    nr = get_nr()
    groups = {}

    # Add group information
    for gname, gobj in nr.inventory.groups.items():
        safe_attrs = dict(gobj.data or {})
        _sanitize_dict(safe_attrs)
        groups[gname] = {"data": safe_attrs}

    # Count members for each group
    for hname, hobj in nr.inventory.hosts.items():
        for group in hobj.groups:
            if group.name in groups:
                if "members" not in groups[group.name]:
                    groups[group.name]["members"] = []
                groups[group.name]["members"].append(hname)
                if "member_count" not in groups[group.name]:
                    groups[group.name]["member_count"] = 0
                groups[group.name]["member_count"] += 1

    return groups


def _load_json_resource(filename: str):
    p = Path(__file__).resolve().parent / "resources" / filename
    if not p.exists():
        # try workspace sibling (in case this file is in a package)
        p = Path.cwd() / "resources" / filename
    if not p.exists():
        raise FileNotFoundError(f"Resource file not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)




def resource_cisco_ios_commands():
    """Return parsed JSON from resources/cisco_ios_commands.json"""
    try:
        return _load_json_resource("cisco_ios_commands.json")
    except FileNotFoundError:
        return {"error": "Cisco IOS commands resource file not found"}


def register_resources(mcp) -> None:
    """Register resource_* callables in this module with the given MCP."""
    import sys

    mod = sys.modules[__name__]

    for name, obj in list(vars(mod).items()):
        if not name.startswith("resource_"):
            continue
        if not callable(obj):
            continue
        # Determine URIs (allow single string or list)
        uri_spec = RESOURCE_MAP.get(name)
        if uri_spec is None:
            rest = name[len("resource_") :]
            uri_list = ["resource://user/" + rest.replace("_", "/")]
        elif isinstance(uri_spec, (list, tuple)):
            uri_list = list(uri_spec)
        else:
            uri_list = [uri_spec]

        # Inspect original signature to decide whether to inject nr_mgr
        sig = inspect.signature(obj)
        param_names = [p.name for p in sig.parameters.values()]

        for uri in uri_list:
            # Determine template parameter names in URI (e.g. {keyword})
            template_params = re.findall(r"{([^}]+)}", str(uri))

            # We must create a wrapper whose signature EXACTLY matches the
            # template parameter names (or empty). MCP validates parameter
            # names against the function signature.

            # Decide whether to inject nr_mgr into underlying function
            needs_inject = False
            first_param = param_names[0] if param_names else None
            if first_param in ("nr_mgr", "nr", "manager"):
                needs_inject = True

            # Build a wrapper function dynamically with explicit parameter names
            # so MCP's decorator accepts it.
            func_name = obj.__name__
            if template_params:
                params_sig = ", ".join(f"{p}=None" for p in template_params)
            else:
                params_sig = ""

            # Build wrapper source. It will call the original function (injecting
            # nr_mgr if requested) and optionally apply a keyword filter when
            # template param 'keyword' is present.
            wrapper_src = [f"def {func_name}({params_sig}):"]
            # call underlying function
            if needs_inject:
                wrapper_src.append("    _res = _orig_func(get_nr())")
            else:
                wrapper_src.append("    _res = _orig_func()")

            # optional keyword filtering support
            if "keyword" in template_params:
                wrapper_src.append(
                    "    if keyword:\n        try:\n            k = str(keyword).lower()\n            # Filter list/dict-of-hosts by matching name/hostname/platform/groups/data values\n            if isinstance(_res, list):\n                out = []\n                for item in _res:\n                    text = ' '.join([str(item.get('name','') or ''), str(item.get('hostname','') or ''), str(item.get('platform','') or ''), ' '.join(item.get('groups',[]))])\n                    # include data values\n                    data_vals = []\n                    if isinstance(item.get('data'), dict):\n                        for v in item.get('data').values():\n                            data_vals.append(str(v))\n                    text = text + ' ' + ' '.join(data_vals)\n                    if k in text.lower():\n                        out.append(item)\n                _res = out\n            elif isinstance(_res, dict):\n                # filter dict keys and nested values\n                out = {}\n                for key, val in _res.items():\n                    joined = key + ' ' + json.dumps(val)\n                    if k in joined.lower():\n                        out[key] = val\n                _res = out\n        except Exception:\n            pass"
                )

            wrapper_src.append("    return _res")

            wrapper_code = "\n".join(wrapper_src)

            # Prepare exec environment - remove the problematic import
            env = {"_orig_func": obj, "_sanitize_dict": _sanitize_dict, "json": json}
            try:
                exec(wrapper_code, env)
                wrapped = env[func_name]
                # register with MCP
                mcp.resource(uri)(wrapped)
            except Exception:
                import traceback

                print(f"Failed to register resource '{name}' as '{uri}':")
                traceback.print_exc()
