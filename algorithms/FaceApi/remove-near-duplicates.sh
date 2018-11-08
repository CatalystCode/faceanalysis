#!/usr/bin/env bash
#
# Near duplicate image removal script.
#
# Usage:
#   ./remove-near-duplicates.sh
#     (-t max_image_distance) (-c recheck_min_confidence)
#     [summary_tsv]
#
# The script post-processes the output of `test.sh` to remove near duplicate
# images. The output is filtered and passing rows are written unchanged to
# standard out.
#
# Options:
#
#   -h: print this help message and exit
#
#   -t max_image_distance: sets the maximum image distance for two images
#                          to be considered duplicates (default: 0.5)
#
#   -c recheck_min_confidence: sets the minimum similarity confidence for
#                              an image match pair to be rechecked for
#                              near duplication (default: 0.98)
#

set -o errexit -o pipefail

for dependency in bc puzzle-diff; do
  if ! command -v "${dependency}" >/dev/null 2>&1; then
    echo "Must install ${dependency}" >&2
    exit 1
  fi
done

max_image_distance=0.5
recheck_min_confidence=0.98

while getopts ":t:c:h" opt; do
  case "${opt}" in
    h) grep "^#" "$0" | sed "s/^# \?//" | grep -v "!/usr/bin/env bash"
       exit 0 ;;
    t) max_image_distance="${OPTARG}"
       if [[ "${max_image_distance}" =~ [^0-9.] ]]; then
         echo "Must set argument -t max_image_distance to a float" >&2
         exit 2
       fi ;;
    c) recheck_min_confidence="${OPTARG}"
       if [[ "${recheck_min_confidence}" =~ [^0-9.] ]]; then
         echo "Must set argument -c recheck_min_confidence to a float" >&2
         exit 2
       fi ;;
  esac
done
shift "$((OPTIND-1))"

summary_tsv="$1"

if [[ ! -f "${summary_tsv}" ]]; then
  echo "Must provide summary TSV path arguments" >&2
  exit 3
fi

while read line; do
  confidence="$(cut -f3 <<< "${line}")"
  if (( $(echo "${confidence} >= ${recheck_min_confidence}" | bc -l) )); then
    image_1="$(cut -f1 <<< "${line}")"
    image_2="$(cut -f2 <<< "${line}")"
    image_diff="$(puzzle-diff "${image_1}" "${image_2}")"
    if (( $(echo "${image_diff} >= ${max_image_distance}" | bc -l) )); then
      echo "${line}"
    fi
  else
    echo "${line}"
  fi
done < "${summary_tsv}"
