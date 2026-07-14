#!/usr/bin/env bash
# Exchange a short-lived Meta user token for a long-lived user token,
# then print the Page access token for FACEBOOK_PAGE_ID.
#
# Required input: FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
# FACEBOOK_ACCESS_TOKEN (USER token), FACEBOOK_PAGE_ID.
# Output defaults to a dotenv-ready FACEBOOK_ACCESS_TOKEN=<PAGE_TOKEN> line.

set -euo pipefail

readonly DEFAULT_API_VERSION="v25.0"

ENV_FILE=".env"
FORMAT="dotenv"
DRY_RUN=false
CLI_APP_ID=""
CLI_APP_SECRET=""
CLI_ACCESS_TOKEN=""
CLI_PAGE_ID=""
CLI_API_VERSION=""

usage() {
  cat <<'EOF'
Usage:
  facebook-page-token.sh [options]

Exchange FACEBOOK_ACCESS_TOKEN as a short-lived Meta USER token, then retrieve
and verify the Page access token for FACEBOOK_PAGE_ID.

Input precedence: CLI flags > --env file > inherited environment.

Options:
  --env FILE              Load supported FACEBOOK_* variables from FILE.
                          Defaults to .env when it exists.
  --app-id VALUE          Override FACEBOOK_APP_ID.
  --app-secret VALUE      Override FACEBOOK_APP_SECRET.
  --access-token VALUE    Override FACEBOOK_ACCESS_TOKEN. This must be a USER token.
  --page-id VALUE         Override FACEBOOK_PAGE_ID.
  --api-version VALUE     Override FACEBOOK_GRAPH_API_VERSION. Default: v25.0.
  --format dotenv|raw     Output format. Default: dotenv.
  --dry-run               Validate configuration and print the planned flow only.
  -h, --help              Show this help.

Required variables:
  FACEBOOK_APP_ID
  FACEBOOK_APP_SECRET
  FACEBOOK_ACCESS_TOKEN   A short-lived USER token from the same Meta app.
  FACEBOOK_PAGE_ID

Examples:
  ./facebook-page-token.sh --env .env > .env.page-token
  ./facebook-page-token.sh --env .env --format raw
  ./facebook-page-token.sh \
    --app-id "$FACEBOOK_APP_ID" \
    --app-secret "$FACEBOOK_APP_SECRET" \
    --access-token "$FACEBOOK_ACCESS_TOKEN" \
    --page-id "$FACEBOOK_PAGE_ID"

Security:
  Never commit .env files or paste tokens/app secrets in chat. The script keeps
  secrets out of curl command-line arguments by using a mode-600 temporary curl
  config file, then deletes it after each API call.
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

die() {
  log "error: $*"
  exit 1
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || die "env file not found: $file"
  [[ -r "$file" ]] || die "env file is not readable: $file"

  local raw line key value
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="$(trim "$raw")"
    [[ -z "$line" || "$line" == \#* ]] && continue

    # Ignore unrelated dotenv keys. This lets the script consume a normal
    # application .env without producing noise or evaluating arbitrary shell.
    if [[ ! "$line" =~ ^(export[[:space:]]+)?(FACEBOOK_APP_ID|FACEBOOK_APP_SECRET|FACEBOOK_ACCESS_TOKEN|FACEBOOK_PAGE_ID|FACEBOOK_GRAPH_API_VERSION)=(.*)$ ]]; then
      continue
    fi

    key="${BASH_REMATCH[2]}"
    value="$(trim "${BASH_REMATCH[3]}")"

    if [[ "$value" =~ ^\".*\"$ || "$value" =~ ^\'.*\'$ ]]; then
      value="${value:1:${#value}-2}"
    fi

    printf -v "$key" '%s' "$value"
  done <"$file"
}

apply_cli_overrides() {
  [[ -n "$CLI_APP_ID" ]] && FACEBOOK_APP_ID="$CLI_APP_ID"
  [[ -n "$CLI_APP_SECRET" ]] && FACEBOOK_APP_SECRET="$CLI_APP_SECRET"
  [[ -n "$CLI_ACCESS_TOKEN" ]] && FACEBOOK_ACCESS_TOKEN="$CLI_ACCESS_TOKEN"
  [[ -n "$CLI_PAGE_ID" ]] && FACEBOOK_PAGE_ID="$CLI_PAGE_ID"
  [[ -n "$CLI_API_VERSION" ]] && FACEBOOK_GRAPH_API_VERSION="$CLI_API_VERSION"
  return 0
}

require_var() {
  local name="$1"
  [[ -n "${!name:-}" ]] || die "missing required variable: $name"
}

json_error() {
  local context="$1"
  local json="$2"
  local message
  message="$(jq -r '.error.message // empty' <<<"$json" 2>/dev/null || true)"
  if [[ -n "$message" ]]; then
    die "$context: $message"
  fi
  die "$context: unexpected response"
}

json_value() {
  local context="$1"
  local filter="$2"
  local json="$3"
  local value
  value="$(jq -er "$filter" <<<"$json" 2>/dev/null || true)"
  [[ -n "$value" && "$value" != "null" ]] || json_error "$context" "$json"
  printf '%s' "$value"
}

# Make a GET request with query parameters stored in a temporary curl config
# rather than exposed through command-line arguments.
api_get() {
  local url="$1"
  shift
  (($# % 2 == 0)) || die "internal error: api_get expects key/value pairs"

  local config response key value
  config="$(mktemp)"
  chmod 600 "$config"

  {
    printf 'url = "%s"\n' "$url"
    # Boolean curl-config options are written without "= true". The previous
    # form is rejected by some curl builds, especially the system curl on macOS.
    printf 'get\n'
    while (($# > 0)); do
      key="$1"
      value="$2"
      shift 2
      value="${value//\\/\\\\}"
      value="${value//\"/\\\"}"
      printf 'data-urlencode = "%s=%s"\n' "$key" "$value"
    done
  } >"$config"

  if ! response="$(curl --silent --show-error --config "$config")"; then
    rm -f "$config"
    printf '%s' "$response"
    return 1
  fi

  rm -f "$config"
  printf '%s' "$response"
}

while (($# > 0)); do
  case "$1" in
  --env)
    (($# >= 2)) || die "--env requires a file path"
    ENV_FILE="$2"
    shift 2
    ;;
  --app-id)
    (($# >= 2)) || die "--app-id requires a value"
    CLI_APP_ID="$2"
    shift 2
    ;;
  --app-secret)
    (($# >= 2)) || die "--app-secret requires a value"
    CLI_APP_SECRET="$2"
    shift 2
    ;;
  --access-token)
    (($# >= 2)) || die "--access-token requires a value"
    CLI_ACCESS_TOKEN="$2"
    shift 2
    ;;
  --page-id)
    (($# >= 2)) || die "--page-id requires a value"
    CLI_PAGE_ID="$2"
    shift 2
    ;;
  --api-version)
    (($# >= 2)) || die "--api-version requires a value"
    CLI_API_VERSION="$2"
    shift 2
    ;;
  --format)
    (($# >= 2)) || die "--format requires dotenv or raw"
    FORMAT="$2"
    shift 2
    ;;
  --dry-run)
    DRY_RUN=true
    shift
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    die "unknown option: $1"
    ;;
  esac
done

if [[ -f "$ENV_FILE" ]]; then
  load_env_file "$ENV_FILE"
elif [[ "$ENV_FILE" != ".env" ]]; then
  die "env file not found: $ENV_FILE"
fi
apply_cli_overrides

FACEBOOK_GRAPH_API_VERSION="${FACEBOOK_GRAPH_API_VERSION:-$DEFAULT_API_VERSION}"

command -v curl >/dev/null 2>&1 || die "curl is required"
command -v jq >/dev/null 2>&1 || die "jq is required"

require_var FACEBOOK_APP_ID
require_var FACEBOOK_APP_SECRET
require_var FACEBOOK_ACCESS_TOKEN
require_var FACEBOOK_PAGE_ID

case "$FORMAT" in
dotenv | raw) ;;
*) die "invalid --format value: $FORMAT" ;;
esac

BASE_URL="https://graph.facebook.com/${FACEBOOK_GRAPH_API_VERSION}"

if [[ "$DRY_RUN" == true ]]; then
  log "configuration valid"
  log "1. exchange short-lived USER token at ${BASE_URL}/oauth/access_token"
  log "2. list pages at ${BASE_URL}/me/accounts using the long-lived user token"
  log "3. select and verify page ${FACEBOOK_PAGE_ID}"
  log "4. print the verified PAGE token in ${FORMAT} format"
  exit 0
fi

log "exchanging short-lived user token for a long-lived user token..."
if ! exchange_json="$(api_get "${BASE_URL}/oauth/access_token" \
  grant_type fb_exchange_token \
  client_id "$FACEBOOK_APP_ID" \
  client_secret "$FACEBOOK_APP_SECRET" \
  fb_exchange_token "$FACEBOOK_ACCESS_TOKEN")"; then
  json_error "long-lived user-token exchange failed" "$exchange_json"
fi
LONG_LIVED_USER_TOKEN="$(json_value "long-lived user-token exchange failed" '.access_token' "$exchange_json")"

log "retrieving the page token..."
if ! accounts_json="$(api_get "${BASE_URL}/me/accounts" \
  fields 'id,name,access_token,tasks' \
  access_token "$LONG_LIVED_USER_TOKEN")"; then
  json_error "page lookup failed" "$accounts_json"
fi

page_json="$(jq -ce --arg page_id "$FACEBOOK_PAGE_ID" '.data[]? | select(.id == $page_id)' <<<"$accounts_json" 2>/dev/null || true)"
[[ -n "$page_json" ]] || die "page ${FACEBOOK_PAGE_ID} was not returned by /me/accounts. Check that the user manages the Page and granted pages_show_list plus the required Pages permissions."
PAGE_ACCESS_TOKEN="$(json_value "page token missing from /me/accounts response" '.access_token' "$page_json")"
PAGE_NAME="$(json_value "page name missing from /me/accounts response" '.name' "$page_json")"

log "verifying Page token for ${PAGE_NAME} (${FACEBOOK_PAGE_ID})..."
if ! verify_json="$(api_get "${BASE_URL}/${FACEBOOK_PAGE_ID}" \
  fields 'id,name' \
  access_token "$PAGE_ACCESS_TOKEN")"; then
  json_error "page-token verification failed" "$verify_json"
fi
VERIFIED_PAGE_ID="$(json_value "page-token verification failed" '.id' "$verify_json")"
[[ "$VERIFIED_PAGE_ID" == "$FACEBOOK_PAGE_ID" ]] || die "page-token verification returned an unexpected Page ID: $VERIFIED_PAGE_ID"

if [[ "$FORMAT" == "raw" ]]; then
  printf '%s\n' "$PAGE_ACCESS_TOKEN"
else
  printf 'FACEBOOK_ACCESS_TOKEN=%s\n' "$PAGE_ACCESS_TOKEN"
fi

log "success: verified Page token for ${PAGE_NAME} (${FACEBOOK_PAGE_ID})"
