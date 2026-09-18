# Security Policy

CANARY is a security-research instrument that deliberately exercises prompt-injection behavior. Its safety depends on strict containment, fictional data, and deterministic policy boundaries.

## Supported status

Before the first tagged release, no release version is supported. After release, the current default branch and most recent tagged release are supported unless their release notes state a narrower policy.

## Report a vulnerability privately

Use GitHub private vulnerability reporting when it is enabled. Do not open a public issue containing a credential, undisclosed exploit, personal data, or instructions for attacking a real system. If private vulnerability reporting is unavailable, project participants should notify the project lead through an existing private CS + AI Club channel. Other reporters may open a public issue that requests a private reporting route but contains no vulnerability details; a maintainer will arrange the private follow-up. This repository intentionally publishes no private contact address.

Include:

- affected commit or release;
- the smallest safe reproduction using fictional local fixtures;
- expected and observed behavior;
- whether any real credential, personal data, or external system may have been exposed; and
- suggested containment, if known.

Do not continue probing a third-party system to improve a report.

## Authorized testing boundary

Authorized testing is limited to the local CANARY harness and fictional fixtures controlled by the project. It does not authorize testing of model-provider infrastructure, websites, email systems, accounts, APIs, agents, or data that the project does not own or have explicit written permission to assess.

The harness must maintain these properties even under D0_BASELINE:

- no real email delivery;
- no arbitrary network destination;
- no unrestricted filesystem access;
- no writable or arbitrary database queries;
- no shell or subprocess tool exposed to the model;
- no real secret in model-visible state; and
- no public arbitrary-input interface.

## Credential or data exposure

If a credential or prohibited data enters a trace or Git history:

1. Stop release and evaluation work.
2. Revoke or rotate the credential when applicable.
3. Preserve necessary incident evidence outside the public repository.
4. Remove the material from the working tree and Git history using an approved incident procedure.
5. Rebuild public artifacts through the deterministic sanitizer.
6. Issue a new manifest and document the incident without republishing the sensitive value.

Deleting the visible file alone is insufficient once it has entered Git history.

## Publication and disclosure

Payload text is public only when its license or permission permits redistribution. Otherwise publish the source pointer, metadata, and transformation recipe while keeping any required audit copy access-controlled and outside the repository. Claims about a vulnerability in another system require advisor guidance and responsible disclosure before public discussion.
