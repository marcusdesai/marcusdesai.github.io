#!/usr/bin/env bash

BASEDIR="$(pwd)"
INPUT_DIR="${BASEDIR}/content"
OUTPUT_DIR="${BASEDIR}/output"
CONF_FILE="${BASEDIR}/pelicanconf.py"

if [[ "$1" == *"html"* ]]; then
  pelican "${INPUT_DIR}" -o "${OUTPUT_DIR}" -s "${CONF_FILE}"
fi

if [[ "$1" == *"clean"* ]]; then
  [ ! -d "${OUTPUT_DIR}" ] || rm -rf "${OUTPUT_DIR}"
fi

propagate_signal() {
    sig=$1
    kill -"$sig" -- -"$pelican_pid"
    kill -"$sig" -- -"$python_pid"
    sleep 0.1
}

if [[ "$1" == *"serve"* ]]; then
  trap 'propagate_signal SIGINT' INT
  trap 'propagate_signal SIGTERM' TERM

  set -m  # Enable job control

  pelican -lr "${INPUT_DIR}" -o "${OUTPUT_DIR}" -s "${CONF_FILE}" &
  pelican_pid=$!
  python -m tooling.wysiwyg &
  python_pid=$!
  wait $pelican_pid $python_pid
fi
