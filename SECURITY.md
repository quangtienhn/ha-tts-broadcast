# Security Policy

## Supported versions

The following versions of TTS Broadcast receive security updates:

| Version | Supported |
|---------|-----------|
| 1.2.0   | :white_check_mark: |
| < 1.2.0 | :x: |

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Send details privately to the repository owner via GitHub (the contact method
on the profile page), describing:

- The affected version of TTS Broadcast.
- The Home Assistant version.
- Steps to reproduce the issue.
- The expected and actual behavior.

## Scope

TTS Broadcast is a local, cloud-free integration:

- It never sends message text to an external service.
- It logs no message text at info level.
- It uses only public Home Assistant APIs and makes no outbound network calls
  of its own.
- Anyone who can reach an Assist pipeline using the TTS Broadcast agent can
  trigger announcements on your speakers; protect your Assist pipeline access
  accordingly.

## Disclaimer

This integration is not affiliated with or endorsed by Home Assistant, Nabu
Casa, Tapo/TP-Link, Zalo, or Google.
