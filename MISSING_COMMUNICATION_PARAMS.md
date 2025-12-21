# Missing Communication Protocol Parameters

This document lists all parameters from the Boomi OpenAPI spec that are not yet exposed in the MCP server.

---

## FTP Protocol ✅ COMPLETE

### All Parameters Supported (14 total)
- `ftp_host` - FTP server hostname
- `ftp_port` - FTP server port (default: 21)
- `ftp_username` - FTP username
- `ftp_password` - FTP password
- `ftp_remote_directory` - Remote directory path
- `ftp_ssl_mode` - SSL mode: NONE, EXPLICIT, IMPLICIT
- `ftp_connection_mode` - Connection mode: ACTIVE, PASSIVE
- `ftp_transfer_type` - Transfer mode: ascii, binary *(added)*
- `ftp_get_action` - Get action: actionget, actiongetdelete, actiongetmove *(added)*
- `ftp_send_action` - Send action: actionputrename, actionputappend, actionputerror, actionputoverwrite *(added)*
- `ftp_max_file_count` - Maximum files to retrieve per poll *(added)*
- `ftp_file_to_move` - Directory to move files after get *(added)*
- `ftp_move_to_directory` - Directory to move files after send *(added)*
- `ftp_client_ssl_alias` - Client SSL certificate alias for mutual TLS *(added)*

### Missing Parameters

None - FTP protocol has complete coverage. (`use_client_authentication` is auto-set when `ftp_client_ssl_alias` is provided)

---

## SFTP Protocol ✅ COMPLETE

### All Parameters Supported (21 total)
- `sftp_host` - SFTP server hostname
- `sftp_port` - SFTP server port (default: 22)
- `sftp_username` - SFTP username
- `sftp_password` - SFTP password
- `sftp_remote_directory` - Remote directory path
- `sftp_ssh_key_auth` - Enable SSH key authentication (true/false)
- `sftp_known_host_entry` - Known hosts entry for server verification
- `sftp_ssh_key_path` - Path to SSH private key file *(added)*
- `sftp_ssh_key_password` - Password for encrypted SSH private key *(added)*
- `sftp_dh_key_max_1024` - Limit DH key size to 1024 bits for legacy servers *(added)*
- `sftp_get_action` - Get action: actionget, actiongetdelete, actiongetmove *(added)*
- `sftp_send_action` - Send action: actionputrename, actionputappend, actionputerror, actionputoverwrite *(added)*
- `sftp_max_file_count` - Maximum files to retrieve per poll *(added)*
- `sftp_file_to_move` - Directory to move files after get *(added)*
- `sftp_move_to_directory` - Directory to move files after operation *(added)*
- `sftp_move_force_override` - Force overwrite when moving files *(added)*
- `sftp_proxy_enabled` - Enable proxy connection *(added)*
- `sftp_proxy_host` - Proxy server hostname *(added)*
- `sftp_proxy_port` - Proxy server port *(added)*
- `sftp_proxy_user` - Proxy username *(added)*
- `sftp_proxy_password` - Proxy password *(added)*
- `sftp_proxy_type` - Proxy type: ATOM, HTTP, SOCKS4, SOCKS5 *(added)*

### Missing Parameters

None - SFTP protocol has complete coverage.

**Note:** `transferType` (ascii/binary) is NOT applicable to SFTP. SFTP uses SSH which is binary-only. The ASCII/binary transfer mode is an FTP-specific concept.

---

## HTTP Protocol ✅ COMPLETE

### All Parameters Supported (24 total)
- `http_url` - HTTP endpoint URL
- `http_username` - Username for BASIC auth
- `http_password` - Password for BASIC auth
- `http_authentication_type` - Auth type: NONE, BASIC, OAUTH2
- `http_connect_timeout` - Connection timeout in ms
- `http_read_timeout` - Read timeout in ms
- `http_client_auth` - Enable client SSL authentication
- `http_trust_server_cert` - Trust server certificate
- `http_method_type` - HTTP method: GET, POST, PUT, DELETE
- `http_data_content_type` - Content type for request
- `http_follow_redirects` - Follow redirects
- `http_return_errors` - Return errors in response
- `http_return_responses` - Return response body *(added)*
- `http_cookie_scope` - Cookie handling: IGNORED, GLOBAL, CONNECTOR_SHAPE *(added)*
- `http_client_ssl_alias` - Client SSL certificate alias *(added)*
- `http_trusted_cert_alias` - Trusted server certificate alias *(added)*
- `http_request_profile` - Request profile component ID *(added)*
- `http_request_profile_type` - Request profile type: NONE, XML, JSON *(added)*
- `http_response_profile` - Response profile component ID *(added)*
- `http_response_profile_type` - Response profile type: NONE, XML, JSON *(added)*
- `http_oauth_token_url` - OAuth2 token endpoint URL *(added)*
- `http_oauth_client_id` - OAuth2 client ID *(added)*
- `http_oauth_client_secret` - OAuth2 client secret *(added)*
- `http_oauth_scope` - OAuth2 scope *(added)*

### Missing Parameters

None - HTTP protocol has complete coverage.

---

## AS2 Protocol ✅ COMPLETE

### All Parameters Supported (34 total)
- `as2_url` - AS2 endpoint URL
- `as2_identifier` - Local AS2 identifier
- `as2_partner_identifier` - Partner AS2 identifier
- `as2_username` - Username for BASIC auth
- `as2_password` - Password for BASIC auth
- `as2_authentication_type` - Auth type: NONE, BASIC
- `as2_verify_hostname` - Verify SSL hostname
- `as2_client_ssl_alias` - Client SSL certificate alias
- `as2_encrypt_alias` - Encryption certificate alias
- `as2_sign_alias` - Signing certificate alias
- `as2_mdn_alias` - MDN certificate alias
- `as2_signed` - Sign messages
- `as2_encrypted` - Encrypt messages
- `as2_compressed` - Compress messages
- `as2_encryption_algorithm` - Encryption algorithm
- `as2_signing_digest_alg` - Signing digest algorithm
- `as2_data_content_type` - Content type
- `as2_request_mdn` - Request MDN
- `as2_mdn_signed` - Signed MDN
- `as2_mdn_digest_alg` - MDN digest algorithm
- `as2_synchronous_mdn` - Synchronous MDN
- `as2_subject` - AS2 message subject header *(added)*
- `as2_multiple_attachments` - Enable multiple attachments *(added)*
- `as2_max_document_count` - Max documents per message *(added)*
- `as2_attachment_option` - Attachment handling: BATCH, DOCUMENT_CACHE *(added)*
- `as2_attachment_cache` - Attachment cache component ID *(added)*
- `as2_mdn_external_url` - External URL for async MDN delivery *(added)*
- `as2_mdn_use_external_url` - Use external URL for MDN *(added)*
- `as2_mdn_use_ssl` - Use SSL for MDN delivery *(added)*
- `as2_mdn_client_ssl_cert` - Client SSL certificate for MDN *(added)*
- `as2_mdn_ssl_cert` - Server SSL certificate for MDN *(added)*
- `as2_reject_duplicates` - Reject duplicate messages *(added)*
- `as2_duplicate_check_count` - Number of messages to check for duplicates *(added)*
- `as2_legacy_smime` - Enable legacy S/MIME compatibility *(added)*

### Missing Parameters

None - AS2 protocol has complete coverage.

---

## MLLP Protocol ✅ COMPLETE

### All Parameters Supported (13 total)
- `mllp_host` - MLLP server hostname
- `mllp_port` - MLLP server port
- `mllp_use_ssl` - Enable SSL/TLS
- `mllp_persistent` - Use persistent connections
- `mllp_receive_timeout` - Receive timeout in ms
- `mllp_send_timeout` - Send timeout in ms
- `mllp_max_connections` - Maximum connections
- `mllp_inactivity_timeout` - Inactivity timeout in seconds *(added)*
- `mllp_max_retry` - Maximum retry attempts (1-5) *(added)*
- `mllp_halt_timeout` - Halt on timeout *(added)*
- `mllp_use_client_ssl` - Enable client SSL authentication *(added)*
- `mllp_client_ssl_alias` - Client SSL certificate alias *(added)*
- `mllp_ssl_alias` - Server SSL certificate alias *(added)*

### Missing Parameters

None - MLLP protocol has complete coverage.

---

## OFTP Protocol

### Currently Supported
- `oftp_host` - OFTP server hostname
- `oftp_port` - OFTP server port (default: 3305)
- `oftp_tls` - Enable TLS
- `oftp_ssid_code` - ODETTE Session ID code
- `oftp_ssid_password` - ODETTE Session ID password
- `oftp_compress` - Enable compression

### Missing Parameters

| Parameter | Type | Description | SDK Field |
|-----------|------|-------------|-----------|
| `oftp_ssid_auth` | bool | Enable SSID authentication | OFTPConnectionSettings.ssidauth |
| `oftp_sfid_cipher` | int | SFID cipher strength | OFTPConnectionSettings.sfidciph |
| `oftp_use_gateway` | bool | Use OFTP gateway | OFTPConnectionSettings.useGateway |
| `oftp_use_client_ssl` | bool | Enable client SSL | OFTPConnectionSettings.useClientSSL |
| `oftp_client_ssl_alias` | string | Client SSL certificate alias | OFTPConnectionSettings.clientSSLAlias |
| `oftp_ssid_cred` | string | SSID credentials | OftpPartnerInfo.ssidcred |
| `oftp_ssid_rsyn` | bool | SSID restart synchronization | OftpPartnerInfo.ssidrsyn |
| `oftp_sfid_cmpr` | bool | SFID compression | OftpPartnerInfo.sfidcmpr |
| `oftp_sfid_desc` | string | SFID description | OftpPartnerInfo.sfiddesc |

---

## DISK Protocol

### Currently Supported
- `disk_directory` - Main directory (legacy)
- `disk_get_directory` - Get/receive directory
- `disk_send_directory` - Send directory
- `disk_file_filter` - File filter pattern (default: *)

### Missing Parameters

| Parameter | Type | Description | SDK Field |
|-----------|------|-------------|-----------|
| `disk_write_option` | enum | Write behavior: `unique`, `over`, `append`, `abort` | DiskSendOptions.writeOption |
| `disk_create_directory` | bool | Create directory if not exists | DiskSendOptions.createDirectory |
| `disk_filter_match_type` | enum | Filter type: `wildcard`, `regex` | DiskGetOptions.filterMatchType |
| `disk_delete_after_read` | bool | Delete files after reading | DiskGetOptions.deleteAfterRead |
| `disk_max_file_count` | int | Maximum files to read per poll | DiskGetOptions.maxFileCount |

---

## Summary

| Protocol | Supported | Missing | Status |
|----------|-----------|---------|--------|
| FTP | 14 | 0 | ✅ Complete |
| SFTP | 21 | 0 | ✅ Complete |
| HTTP | 24 | 0 | ✅ Complete |
| AS2 | 34 | 0 | ✅ Complete |
| MLLP | 13 | 0 | ✅ Complete |
| OFTP | 6 | 9 | Partial |
| DISK | 4 | 5 | Partial |
| **Total** | **116** | **14** | |

---

## Priority Summary

### High Priority (commonly needed)
1. ~~`sftp_ssh_key_path` - Required for SSH key authentication~~ *(done)*
2. `disk_write_option` - Critical for controlling file write behavior

### Medium Priority (useful features)
3. ~~`sftp_ssh_key_password` - Needed for encrypted SSH keys~~ *(done)*
4. `disk_create_directory` - Convenient for auto-creating paths
5. `disk_delete_after_read` - Common requirement for file processing
6. ~~`mllp_max_retry` - Important for reliability~~ *(done)*
7. ~~`mllp_inactivity_timeout` - Connection management~~ *(done)*
8. ~~`sftp_proxy_*` - Corporate proxy support~~ *(done)*
9. SSL alias parameters (all protocols) - Certificate management
10. ~~`as2_mdn_external_url` - Async MDN support~~ *(done)*

### Low Priority (advanced/rare use)
- ~~Transfer type settings~~ *(FTP done)*
- ~~File action settings (move/delete after transfer)~~ *(FTP done)*
- Profile mappings (HTTP)
- ~~Advanced AS2 attachment settings~~ *(done)*
- OFTP advanced settings
