#!/usr/bin/env bash
#
# Evaluation script for FaceAPI's LargeFaceList+FindSimilar implementation.
#
# Usage:
#   ./evaluate.sh
#     (-o output_path) (-n max_candidates) (-m match_mode)
#     [faceApiUrl] [largeFaceListId] [inputImagePath]
#
# The script will output as tab separated values the original image path,
# the paths of all the images that match the input image, and the match
# confidence.
#
# Options:
#
#   -h: print this help message and exit
#
#   -o output_path: store a summary result HTML file (default: no file)
#
#   -n max_candidates: sets the maximum number of candidate matches to
#                      show (default: 10)
#
#   -m match_mode: sets the similarity computation mode
#                  (default: matchPerson)
#

set -o errexit -o pipefail

for dependency in jq curl basename dirname readlink base64; do
  if ! command -v "${dependency}" >/dev/null 2>&1; then
    echo "Must install ${dependency}" >&2
    exit 1
  fi
done

output_path=""
max_candidates="10"
match_mode="matchPerson"

while getopts ":o:n:m:h" opt; do
  case "${opt}" in
    h) grep "^#" "$0" | sed "s/^# \?//" | grep -v "!/usr/bin/env bash"
       exit 0 ;;
    o) output_path="${OPTARG}"
       if [[ ! -d "$(dirname "${output_path}")" ]]; then
         echo "Must set argument -o output_path to a valid path" >&2
         exit 2
       fi ;;
    n) max_candidates="${OPTARG}"
       if [[ "${max_candidates}" =~ [^0-9] ]]; then
         echo "Must set argument -n max_candidates to a number" >&2
         exit 2
       fi ;;
    m) match_mode="${OPTARG}"
       if [[ "${match_mode}" != "matchPerson" ]] && [[ "${match_mode}" != "matchFace" ]]; then
         echo "Must set argument -m match_mode to matchPerson or matchFace" >&2
         exit 2
       fi ;;
  esac
done
shift "$((OPTIND-1))"

face_api_url="$1"
model_id="$2"
image_path="$3"

if [[ -z "${face_api_url}" ]] || [[ -z "${model_id}" ]] || [[ ! -f "${image_path}" ]]; then
  echo "Must provide FaceAPI URL, largeFaceListId, and image path arguments" >&2
  exit 3
fi

get_extension() {
  local path="$(readlink -f "$1")"
  local filename="$(basename -- "${path}")"
  echo "${filename##*.}"
}

windows_to_unix_path() {
  echo "$1" | sed 's@^C:@/c/@' | tr '\\' '/'
}

format_data_uri() {
  local path="$(windows_to_unix_path "$1")"
  local content="$(base64 -w0 "${path}")"
  local extension="$(get_extension "${path}")"
  echo "data:image/${extension};base64,${content}"
}

image_extension="$(get_extension "${image_path}")"

detected_face_ids=($(curl -sf "${face_api_url}/face/v1.0/detect" -F "form=@${image_path};type=image/${image_extension}" | jq -r ".[] .faceId"))

if [[ "${#detected_face_ids[@]}" -ne 1 ]]; then
  echo "Must have exactly one face in the image" >&2
  exit 4
fi

find_similar_request="$(cat <<-EOM
{
  "faceId": "${detected_face_ids[0]}",
  "largeFaceListId": "${model_id}",
  "maxNumOfCandidatesReturned": ${max_candidates},
  "mode": "${match_mode}"
}
EOM
)"

similar_faces=($(curl -sf "${face_api_url}/face/v1.0/findsimilars" -H "Content-Type: application/json" -d "${find_similar_request}" | jq -c ".[]"))

similar_face_paths=()
similar_face_scores=()
for similar_face in "${similar_faces[@]}"; do
  similar_face_id="$(<<< "${similar_face}" jq -r ".persistedFaceId")"
  similar_face_scores+=("$(<<< "${similar_face}" jq -r ".confidence")")
  similar_face_paths+=("$(curl -sf "${face_api_url}/face/v1.0/largefacelists/${model_id}/persistedfaces/${similar_face_id}" | jq -r ".userData")")
done

for i in "${!similar_face_paths[@]}"; do
  similar_face_path="${similar_face_paths[$i]}"
  confidence="${similar_face_scores[$i]}"
  printf "%s\t%s\t%s\n" "${image_path}" "${similar_face_path}" "${confidence}"
done

if [[ -z "${output_path}" ]]; then
  exit 0
fi

cat > "${output_path}" << EOM
<html>
  <head>
    <title>Matches for ${image_path}</title>
    <style>
    .match {
      display: inline-block;
    }
    img {
      max-width: 200px;
    }
    h3 {
      width: 250px;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
    }
    </style>
  </head>
  <body>
    <div class="source">
      <h3>Source: $(basename "$(windows_to_unix_path "${image_path}")")</h3>
      <img src="$(format_data_uri "${image_path}")" />
    </div>
EOM

for i in "${!similar_face_paths[@]}"; do
  similar_face_path="${similar_face_paths[$i]}"
  confidence="${similar_face_scores[$i]}"
  cat >> "${output_path}" << EOM
    <div class="match">
      <h3>Match: $(basename "$(windows_to_unix_path "${similar_face_path}")")</h3>
      <div class="confidence">Confidence: ${confidence}</div>
      <img src="$(format_data_uri "${similar_face_path}")" />
    </div>
EOM
done

cat >> "${output_path}" << EOM
  </body>
</html>
EOM
