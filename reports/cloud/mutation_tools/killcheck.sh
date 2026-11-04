#!/bin/bash
# usage: killcheck.sh "test files" < names  -> prints status<TAB>name
mkdir -p /tmp/kc && cd /home/canary/verify/mutants
while read -r name; do
  [ -z "$name" ] && continue
  MUTANT_UNDER_TEST="$name" timeout 600 /home/canary/work/CANARY/.venv/bin/python -m pytest -x -q -p no:cacheprovider --basetemp="/tmp/kc/$RANDOM$RANDOM" $1 >/dev/null 2>&1
  rc=$?
  case $rc in 0) s=survived;; 1) s=killed;; *) s="exit$rc";; esac
  printf "%s\t%s\n" "$s" "$name"
done
