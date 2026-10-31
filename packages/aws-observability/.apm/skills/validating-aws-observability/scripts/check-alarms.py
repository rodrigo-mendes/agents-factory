#!/usr/bin/env python3
"""check-alarms.py - Alarms pillar, read-only (it never changes an alarm state; see trigger-alarm-test.py).
Detail: ../blueprints/pillar-alarms.md
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: check-alarms.py (--alarm-prefix PREFIX | --alarm-names A,B) [options]

Read-only. Describes the alarms with --alarm-types MetricAlarm CompositeAlarm (without it only metric
alarms are returned) and asserts per alarm: ActionsEnabled is true, AlarmActions is not empty, and the
state. For every SNS topic in AlarmActions it reads list-subscriptions-by-topic and fails on a topic
without subscriptions or with a PendingConfirmation subscription. Subscriber endpoints are never printed.

State rules: OK passes; ALARM fails; INSUFFICIENT_DATA is a WARN (the alarm just started, the metric is
not available or there is not enough data) unless --fail-on-insufficient-data is given.

Options:
  --alarm-prefix P            select alarms by name prefix (cannot be combined with --alarm-names)
  --alarm-names A,B           select alarms by exact name, comma separated (at most 100)
  --fail-on-insufficient-data treat INSUFFICIENT_DATA as FAIL
"""


def all_alarms(resp):
    """Metric and composite alarms of a describe-alarms response, each tagged with its kind."""
    out = []
    for a in oc.items(oc.get(resp, "MetricAlarms")):
        out.append(dict(a, kind="metric"))
    for a in oc.items(oc.get(resp, "CompositeAlarms")):
        out.append(dict(a, kind="composite"))
    return out


def main():
    c = oc.Ctx(__file__)
    prefix = ""
    names = ""
    fail_insuff = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--alarm-prefix":
            prefix = c.need_value(args, i)
            i += 2
        elif a == "--alarm-names":
            names = c.need_value(args, i)
            i += 2
        elif a == "--fail-on-insufficient-data":
            fail_insuff = True
            i += 1
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not prefix and not names:
        c.usage_err("give --alarm-prefix or --alarm-names")
    if prefix and names:
        c.usage_err("--alarm-prefix and --alarm-names cannot be combined")

    narr = []
    if prefix:
        sel = ["--alarm-name-prefix", prefix]
    else:
        narr = oc.split_csv(names)
        if len(narr) > 100:
            c.usage_err("--alarm-names takes at most 100 names")
        sel = ["--alarm-names"] + narr

    c.init_env()

    resp = oc.parse(c.run_aws("cloudwatch", "describe-alarms", *sel, "--alarm-types", "MetricAlarm", "CompositeAlarm"))
    alarms = all_alarms(resp)

    if names:
        for n in narr:
            if not any(oc.get(a, "AlarmName") == n for a in alarms):
                c.fail("alarm.%s" % n, "not found")
    if not alarms:
        if prefix:
            c.fail("alarms.found", "no alarm with prefix %s" % prefix)
        c.finish()

    topics = []
    for a in alarms:
        nm = oc.text(oc.get(a, "AlarmName"))
        kind = a["kind"]
        en = oc.text(oc.alt(oc.get(a, "ActionsEnabled"), False))
        actions = oc.alt(oc.get(a, "AlarmActions"), [])
        nact = oc.length(actions)
        st = oc.text(oc.alt(oc.get(a, "StateValue"), "unknown"))
        reason = oc.alt(oc.get(a, "StateReason"), "")
        rsn = reason[0:120] if isinstance(reason, (str, list)) else reason
        rsn = oc.text(rsn)
        if en != "true":
            c.fail("alarm.%s.actions" % nm, "ActionsEnabled=false (%s alarm)" % kind)
        elif nact == 0:
            c.fail("alarm.%s.actions" % nm, "AlarmActions is empty (%s alarm)" % kind)
        else:
            c.pass_("alarm.%s.actions" % nm, "%s action(s) wired (%s alarm)" % (oc.num(nact), kind))
        if st == "OK":
            c.pass_("alarm.%s.state" % nm, "OK")
        elif st == "ALARM":
            c.fail("alarm.%s.state" % nm, "in ALARM: %s" % rsn)
        elif st == "INSUFFICIENT_DATA":
            if fail_insuff:
                c.fail("alarm.%s.state" % nm, "INSUFFICIENT_DATA")
            else:
                c.warn("alarm.%s.state" % nm, "INSUFFICIENT_DATA (just started, metric not available or not "
                                              "enough data): inconclusive")
        else:
            c.warn("alarm.%s.state" % nm, "unexpected StateValue %s" % st)
        for act in oc.items(actions):
            if not isinstance(act, str):
                raise oc.ParseError("AlarmActions entry is not a string")
            if act.startswith("arn:aws") and ":sns:" in act:
                topics.append(act)

    for t in sorted(set(x for x in topics if x)):
        parts = t.split(":")
        tr = parts[3] if len(parts) > 3 else ""
        tn = parts[-1]
        sub = oc.parse(c.run_aws_in(tr, "sns", "list-subscriptions-by-topic", "--topic-arn", t))
        subs = oc.items(oc.get(sub, "Subscriptions"))
        total = len(subs)
        pend = sum(1 for s in subs if oc.get(s, "SubscriptionArn") == "PendingConfirmation")
        protos = oc.jq_sorted([oc.get(s, "Protocol") for s in subs])
        groups = []
        for p in protos:
            if groups and oc.jq_cmp(groups[-1][0], p) == 0:
                groups[-1][1] += 1
            else:
                groups.append([p, 1])
        proto = ",".join("%s=%d" % (oc.text(p), n) for p, n in groups)
        if total == 0:
            c.fail("sns.%s" % tn, "topic has no subscriptions")
        elif pend > 0:
            c.fail("sns.%s" % tn, "%d of %d subscription(s) PendingConfirmation (protocols: %s)" % (pend, total, proto))
        else:
            c.pass_("sns.%s" % tn, "%d subscription(s), none pending (protocols: %s)" % (total, proto))

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__)
