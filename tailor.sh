#!/usr/bin/env bash
# tailor.sh — convenience wrapper around Claude Code
# Usage: ./tailor.sh path/to/cv.tex https://job-url.com

set -e

CV_PATH="${1}"
JD_URL="${2}"

if [[ -z "$CV_PATH" || -z "$JD_URL" ]]; then
  echo "Usage: ./tailor.sh <path/to/cv.tex> <job-url>"
  exit 1
fi

if [[ ! -f "$CV_PATH" ]]; then
  echo "Error: CV file not found at $CV_PATH"
  exit 1
fi

mkdir -p output

echo "cv2jd-tailor starting..."
echo "   CV:  $CV_PATH"
echo "   Job: $JD_URL"
echo ""

# Run Claude Code with the task — it reads CLAUDE.md automatically
claude "Tailor my CV at $CV_PATH for this job posting: $JD_URL. Follow the cv2jd-tailor pipeline in CLAUDE.md."
