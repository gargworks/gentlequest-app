#!/bin/bash
# asc_status_local.sh — Read-only ASC state query, runs locally.
#
# Bypasses the GHA workflow when org billing is exhausted.
# Uses the same .p8 key the GHA workflow uses, prompts for Issuer ID once
# (or reads from $APP_STORE_CONNECT_API_ISSUER_ID env var).
#
# Usage:
#   ./scripts/asc_status_local.sh
#   APP_STORE_CONNECT_API_ISSUER_ID=<uuid> ./scripts/asc_status_local.sh
#
# Issuer ID is at https://appstoreconnect.apple.com/access/api (top of Keys section)

set -e

BUNDLE_ID="${1:-com.gentlequest.app}"
KEY_ID="L6BQY5DFKM"
KEY_FILE="$HOME/.appstoreconnect/private_keys/AuthKey_${KEY_ID}.p8"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: ASC API key not found at $KEY_FILE"
    exit 1
fi

if [ -z "$APP_STORE_CONNECT_API_ISSUER_ID" ]; then
    echo "Need ASC Issuer ID (one-time)."
    echo "Get from: https://appstoreconnect.apple.com/access/api (top of Keys section)"
    echo ""
    read -p "Issuer ID: " APP_STORE_CONNECT_API_ISSUER_ID
fi

if ! gem list -i jwt > /dev/null 2>&1; then
    echo "Installing ruby-jwt..."
    sudo gem install jwt --no-document
fi

KEY_ID="$KEY_ID" \
ISSUER_ID="$APP_STORE_CONNECT_API_ISSUER_ID" \
KEY_FILE="$KEY_FILE" \
BUNDLE_ID="$BUNDLE_ID" \
ruby <<'EOF'
require 'jwt'
require 'net/http'
require 'json'
require 'time'

key_id = ENV['KEY_ID']
issuer_id = ENV['ISSUER_ID']
private_key = File.read(ENV['KEY_FILE'])
bundle_id = ENV['BUNDLE_ID']

payload = { iss: issuer_id, exp: Time.now.to_i + 20 * 60, aud: 'appstoreconnect-v1' }
header = { kid: key_id }
token = JWT.encode(payload, OpenSSL::PKey::EC.new(private_key), 'ES256', header)

def req(path, token)
  uri = URI("https://api.appstoreconnect.apple.com/v1/#{path}")
  http = Net::HTTP.new(uri.host, uri.port); http.use_ssl = true
  request = Net::HTTP::Get.new(uri)
  request['Authorization'] = "Bearer #{token}"
  response = http.request(request)
  JSON.parse(response.body) rescue nil
end

puts "=" * 70
puts "ASC STATUS for #{bundle_id} (#{Time.now.utc.iso8601})"
puts "=" * 70

apps = req("apps?filter[bundleId]=#{bundle_id}", token)
app = apps && apps['data'] && apps['data'].first
unless app
  puts "❌ App not found"
  exit 1
end
app_id = app['id']
puts "App ID: #{app_id}"
puts ""

puts "## App Store Versions"
versions = req("apps/#{app_id}/appStoreVersions?limit=20", token)
(versions && versions['data'] || []).each do |v|
  a = v['attributes']
  puts "  #{a['versionString'].to_s.ljust(10)} #{a['platform'].to_s.ljust(5)} state=#{a['appStoreState'].to_s.ljust(28)} createdDate=#{a['createdDate']}"
end
puts ""

puts "## Active reviewSubmissions"
submissions = req("reviewSubmissions?filter[app]=#{app_id}&limit=20", token)
(submissions && submissions['data'] || []).each do |s|
  a = s['attributes']
  puts "  id=#{s['id']} state=#{a['state']} platform=#{a['platform']} submittedDate=#{a['submittedDate'] || '-'}"
  items_resp = req("reviewSubmissions/#{s['id']}/items?limit=10", token)
  (items_resp && items_resp['data'] || []).each do |item|
    ia = item['attributes']
    puts "    item id=#{item['id']} state=#{ia['state']} removed=#{ia['removed']}"
  end
end
puts ""

puts "## Latest 10 builds"
builds = req("apps/#{app_id}/builds?sort=-uploadedDate&limit=10", token)
(builds && builds['data'] || []).each do |b|
  a = b['attributes']
  puts "  build=#{a['version'].to_s.ljust(8)} state=#{a['processingState'].to_s.ljust(18)} uploaded=#{a['uploadedDate']} expired=#{a['expired']}"
end
EOF
