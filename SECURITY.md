# Security Policy

## Reporting a Vulnerability
If you discover a security vulnerability, please report it by opening a private issue or contacting the maintainer directly via Telegram: [@sisp_t](https://t.me/sisp_t). Do **not** disclose security issues publicly until they are resolved.

## Supported Versions
| Version      | Supported          |
| ------------ | ----------------- |
| 1.0.0-dev    | ✅                |

## Security Policy
- Passwords are never stored or saved; they are used only for login and immediately discarded.
- A temporary login token is used for session security.
- All sensitive configuration is stored in environment variables.
- Security headers and best practices are enforced throughout the project. 