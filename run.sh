#!/usr/bin/env bash

BASEDIR="$(pwd)"
INPUT_DIR="${BASEDIR}/content"
OUTPUT_DIR="${BASEDIR}/output"
LOCAL_CONF="${BASEDIR}/conf/local.py"
PUBLISH_CONF="${BASEDIR}/conf/publish.py"

if [[ "$1" == *"clean"* ]]; then
  [ ! -d "${OUTPUT_DIR}" ] || rm -rf "${OUTPUT_DIR}"
fi

if [[ "$1" == *"build"* ]]; then
  pelican "${INPUT_DIR}" -o "${OUTPUT_DIR}" -s "${PUBLISH_CONF}"
fi

function propagate_signal() {
    sig=$1
    kill -"$sig" -- -"$pelican_pid"
    kill -"$sig" -- -"$python_pid"
    sleep 0.1
}

if [[ "$1" == *"serve"* ]]; then
  trap 'propagate_signal SIGINT' INT
  trap 'propagate_signal SIGTERM' TERM

  set -m  # Enable job control

  pelican -lr "${INPUT_DIR}" -o "${OUTPUT_DIR}" -s "${LOCAL_CONF}" &
  pelican_pid=$!
  sleep 2
  python -m tooling.wysiwyg "$2" &
  python_pid=$!
  wait $pelican_pid $python_pid
fi
