#!/usr/bin/env python3
"""trigger-alarm-test.py - the ONLY mutating script of this skill.

It sends cloudwatch set-alarm-state ALARM to ONE named alarm, which invokes the alarm's real
actions (an SNS message reaches real subscribers). It refuses to run unless --i-have-user-approval
is passed. An agent passes that flag only with an approval the orchestrator relayed from the user,
never on the strength of an agent's own message. Detail: ../blueprints/pillar-alarms.md
"""
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: trigger-alarm-test.py --alarm-name NAME --i-have-user-approval [options]

MUTATING. Temporarily sets ONE alarm to ALARM with cloudwatch set-alarm-state, then reads
describe-alarm-history --history-item-type Action to prove the alarm action ran. The action is real:
subscribers of the alarm's SNS topic receive a notification. Needs the cloudwatch:SetAlarmState
permission, which the read-only managed policy does not grant.

Without --i-have-user-approval the script refuses (exit 2) and makes no AWS call. Pass the flag only
when the user's explicit approval for this exact alarm was relayed by the orchestrator.

Metric alarms return to their actual state quickly, often within seconds. A composite alarm is not
guaranteed to return until a child alarm changes state, so it is refused unless --allow-composite.
An alarm that is already in ALARM is refused (the state would not change, so no action runs).
If a CLI error happens after set-alarm-state was sent, a RECOVERY line says how to check the state.

Options:
  --alarm-name NAME        the alarm to trigger (exactly one)
  --i-have-user-approval   required acknowledgement of the relayed user approval
  --allow-composite        allow a composite alarm (state may not revert by itself)
  --reason TEXT            state reason (default shown in the history), at most 1023 characters
In this script --wait-seconds defaults to 60 and --retry-seconds to 5 (history polling).
"""

# After set-alarm-state was sent, a CLI error (exit 3) leaves the alarm possibly still in ALARM:
# on_exit says how to recover. The hint never runs a command.
STATE = {"mutated": False, "alarm": "", "prev": ""}


def on_exit(rc):
    if STATE["mutated"] and rc == 3:
        sys.stdout.flush()
        a, p = STATE["alarm"], STATE["prev"]
        sys.stderr.write(
            "RECOVERY: set-alarm-state may already have been sent to '%s' (previous state %s) and the alarm may "
            "still be in ALARM. Run: python3 check-alarms.py --alarm-names '%s' to read its state; metric alarms "
            "return to their actual state by themselves. To force it back, a user-approved 'aws cloudwatch "
            "set-alarm-state --alarm-name %s --state-value %s --state-reason <reason>' is the only manual step.\n"
            % (a, p, a, a, p))
        sys.stderr.flush()


def main():
    c = oc.Ctx(__file__)
    c.wait_s = 60
    c.retry_s = 5
    alarm = ""
    approved = False
    allow_composite = False
    reason = "validating-aws-observability notification test"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--alarm-name":
            alarm = c.need_value(args, i)
            i += 2
        elif a == "--i-have-user-approval":
            approved = True
            i += 1
        elif a == "--allow-composite":
            allow_composite = True
            i += 1
        elif a == "--reason":
            reason = c.need_value(args, i)
            i += 2
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not alarm:
        c.usage_err("--alarm-name is required")
    if not approved:
        print("REFUSED trigger-alarm-test: set-alarm-state is the only mutating command of this skill and sends "
              "a real notification.")
        print("No AWS call was made. Pass --i-have-user-approval only when the orchestrator relayed the user's "
              "explicit approval for alarm '%s'." % alarm)
        sys.exit(2)
    if len(reason) > 1023:
        c.usage_err("--reason is longer than 1023 characters")

    c.init_env()

    resp = oc.parse(c.run_aws("cloudwatch", "describe-alarms", "--alarm-names", alarm,
                              "--alarm-types", "MetricAlarm", "CompositeAlarm"))
    cands = [dict(a, kind="metric") for a in oc.items(oc.get(resp, "MetricAlarms"))]
    cands += [dict(a, kind="composite") for a in oc.items(oc.get(resp, "CompositeAlarms"))]
    cands = [a for a in cands if a.get("AlarmName") == alarm]
    if not cands:
        c.fail("trigger.alarm", "alarm %s not found" % alarm)
        c.finish()
    found = cands[0]
    kind = found["kind"]
    en = oc.text(oc.alt(oc.get(found, "ActionsEnabled"), False))
    nact = oc.length(oc.alt(oc.get(found, "AlarmActions"), []))
    prev = oc.text(oc.alt(oc.get(found, "StateValue"), "unknown"))

    if kind == "composite" and not allow_composite:
        print("REFUSED trigger-alarm-test: %s is a composite alarm; it may not return to its actual state until a "
              "child alarm changes state. Use --allow-composite after telling the user." % alarm)
        sys.exit(2)
    if en != "true" or nact == 0:
        c.fail("trigger.alarm", "no action would run (ActionsEnabled=%s, AlarmActions=%s); set-alarm-state was "
                                "not sent" % (en, oc.num(nact)))
        c.finish()
    if prev == "ALARM":
        print("REFUSED trigger-alarm-test: %s is already in ALARM. set-alarm-state ALARM would not change the "
              "state, so no action would run and the test would prove nothing. Wait until it returns to OK or "
              "pick another alarm. No state was changed." % alarm)
        sys.exit(2)

    STATE["alarm"] = alarm
    STATE["prev"] = prev

    # describe-alarm-history takes --alarm-types MetricAlarm|CompositeAlarm so that a composite alarm is
    # found (register U9: the flag is (unverified); the CLI page was read only as a summary).
    # If the CLI rejects it (exit 252) the script falls back to the default, which covers metric alarms only.
    htype = "CompositeAlarm" if kind == "composite" else "MetricAlarm"
    use_types = [True]

    def history_call(t0):
        if use_types[0]:
            rc, out, err = c.run_aws_try("cloudwatch", "describe-alarm-history", "--alarm-name", alarm,
                                         "--alarm-types", htype, "--history-item-type", "Action",
                                         "--start-date", t0)
            if rc == 0:
                return oc.parse(out)
            if rc != 252:
                c.aws_fatal(rc, "cloudwatch describe-alarm-history", err)
            use_types[0] = False
            c.warn("trigger.alarm-types", "describe-alarm-history rejected --alarm-types (unverified flag); using "
                                          "the default, which returns metric alarms only (a composite alarm's "
                                          "history may be missing)")
        return oc.parse(c.run_aws("cloudwatch", "describe-alarm-history", "--alarm-name", alarm,
                                  "--history-item-type", "Action", "--start-date", t0))

    t0 = int(time.time())
    STATE["mutated"] = True
    c.run_aws("cloudwatch", "set-alarm-state", "--alarm-name", alarm, "--state-value", "ALARM",
              "--state-reason", reason)
    c.pass_("trigger.set-state", "%s set to ALARM (previous state %s, %s alarm)" % (alarm, prev, kind))

    waited = 0
    nac = 0
    while True:
        h = history_call(t0)
        nac = sum(1 for x in oc.items(oc.get(h, "AlarmHistoryItems")) if oc.get(x, "HistoryItemType") == "Action")
        if nac > 0 or waited >= c.wait_s:
            break
        time.sleep(c.retry_s)
        waited += c.retry_s
    if nac > 0:
        c.pass_("trigger.action", "%d Action history item(s) after set-alarm-state" % nac)
    else:
        c.fail("trigger.action", "no Action history item within %ds; raise --wait-seconds or check the alarm "
                                 "actions" % c.wait_s)
    if kind == "composite":
        c.warn("trigger.revert", "composite alarm: it returns to its actual state only when a child alarm changes "
                                 "state")
    else:
        c.warn("trigger.revert", "metric alarm returns to its actual state quickly; confirm with check-alarms.py")

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__, on_exit)
