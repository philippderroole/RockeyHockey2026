#!/usr/bin/env bash
set -euo pipefail

# Measures runtime timing by polling the web UI log endpoint while processing a video.
# Usage:
#   ./measure_timing.sh [video_path] [base_port] [runs]
# Example:
#   ./measure_timing.sh VirtualCamVideos/Video1.avi 8091 5

VIDEO_PATH="${1:-VirtualCamVideos/Video1.avi}"
BASE_PORT="${2:-8091}"
RUNS="${3:-1}"
TMP_PREFIX="/tmp/rockey_hockey_timing_${BASE_PORT}"

if [[ ! -f "$VIDEO_PATH" ]]; then
  echo "error: video file not found: $VIDEO_PATH" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "error: curl is required but was not found" >&2
  exit 1
fi

BIN="target/release/rockey_hockey"
if [[ ! -x "$BIN" ]]; then
  echo "Building release binary..."
  cargo build --release >/dev/null
fi

if ! [[ "$RUNS" =~ ^[0-9]+$ ]] || [[ "$RUNS" -lt 1 ]]; then
  echo "error: runs must be a positive integer" >&2
  exit 1
fi

extract_json_number_or_null() {
  local json_line="$1"
  local key="$2"
  local value
  value=$(printf '%s\n' "$json_line" | sed -nE "s/.*\"${key}\":(null|-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?).*/\1/p")
  if [[ -z "$value" ]]; then
    echo "n/a"
  else
    echo "$value"
  fi
}

calc_mean() {
  printf '%s\n' "$@" | awk '{sum+=$1; n+=1} END{if(n==0){print "n/a"} else {printf "%.12f", sum/n}}'
}

calc_median() {
  printf '%s\n' "$@" | sort -g | awk '
    {a[NR]=$1}
    END {
      if (NR == 0) {
        print "n/a";
      } else if (NR % 2 == 1) {
        printf "%.12f", a[(NR+1)/2];
      } else {
        printf "%.12f", (a[NR/2] + a[NR/2 + 1]) / 2.0;
      }
    }
  '
}

run_once() {
  local port="$1"
  local run_id="$2"
  local log_jsonl="${TMP_PREFIX}_run${run_id}.jsonl"
  local app_stdout="${TMP_PREFIX}_run${run_id}.log"

  rm -f "$log_jsonl" "$app_stdout"

  "$BIN" --video "$VIDEO_PATH" --web-ui --web-ui-port "$port" >"$app_stdout" 2>&1 &
  local app_pid=$!

  cleanup() {
    if kill -0 "$app_pid" >/dev/null 2>&1; then
      kill "$app_pid" >/dev/null 2>&1 || true
      wait "$app_pid" >/dev/null 2>&1 || true
    fi
  }

  trap cleanup EXIT INT TERM

  # Wait up to 5s for web UI to come up.
  for _ in {1..100}; do
    if curl -sf "http://127.0.0.1:${port}/api/logs/latest" >/dev/null 2>&1; then
      break
    fi
    sleep 0.05
  done

  while kill -0 "$app_pid" >/dev/null 2>&1; do
    curl -sf "http://127.0.0.1:${port}/api/logs/latest" >>"$log_jsonl" 2>/dev/null || true
    echo >>"$log_jsonl"
    sleep 0.05
  done

  if ! wait "$app_pid"; then
    local app_exit=$?
    echo "error: app exited with code $app_exit" >&2
    echo "see: $app_stdout" >&2
    trap - EXIT INT TERM
    exit "$app_exit"
  fi
  trap - EXIT INT TERM

  local last_line
  last_line=$(awk 'NF{line=$0} END{print line}' "$log_jsonl")
  if [[ -z "$last_line" ]]; then
    echo "error: no runtime logs captured" >&2
    echo "see: $app_stdout" >&2
    exit 1
  fi

  local frame avg_capture_ms avg_detect_ms avg_total_ms
  frame=$(extract_json_number_or_null "$last_line" frame)
  avg_capture_ms=$(extract_json_number_or_null "$last_line" avg_capture_ms)
  avg_detect_ms=$(extract_json_number_or_null "$last_line" avg_detect_ms)
  avg_total_ms=$(extract_json_number_or_null "$last_line" avg_total_ms)

  printf "Run %s | port=%s | frames=%s | avg_capture_ms=%s | avg_detect_ms=%s | avg_total_ms=%s\n" \
    "$run_id" "$port" "$frame" "$avg_capture_ms" "$avg_detect_ms" "$avg_total_ms" >&2

  printf "%s,%s,%s,%s\n" "$frame" "$avg_capture_ms" "$avg_detect_ms" "$avg_total_ms"
}

echo "Video: $VIDEO_PATH"
echo "Runs: $RUNS"

declare -a frames
declare -a captures
declare -a detects
declare -a totals

for ((run=1; run<=RUNS; run+=1)); do
  port=$((BASE_PORT + run - 1))
  csv=$(run_once "$port" "$run" | tail -n 1)
  IFS=',' read -r frame capture detect total <<< "$csv"
  frames+=("$frame")
  captures+=("$capture")
  detects+=("$detect")
  totals+=("$total")
done

echo "Summary:"
printf "Frames mean:      %s\n" "$(calc_mean "${frames[@]}")"
printf "Avg capture mean: %s\n" "$(calc_mean "${captures[@]}")"
printf "Avg detect mean:  %s\n" "$(calc_mean "${detects[@]}")"
printf "Avg total mean:   %s\n" "$(calc_mean "${totals[@]}")"
printf "Avg total median: %s\n" "$(calc_median "${totals[@]}")"
