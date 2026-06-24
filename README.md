# Secure Password Reset Token

## Overview

This project demonstrates the difference between an insecure and a secure implementation of a password reset mechanism.

The case study focuses on common security mistakes in password reset systems and how Secure by Design principles can be applied to mitigate them.

## Insecure Version

The insecure implementation contains several vulnerabilities:

- Plaintext token storage
- Token leakage through application logs
- No token expiration
- Reusable tokens
- No user ownership validation

## Secure Version

The secure implementation introduces:

- Domain Primitive
- Secure Random Token
- SHA-256 Token Hashing
- User Binding
- Expiry Invariant
- Read-Once Token
- Misuse Prevention

## Test Results

The implementation successfully rejects:

- Token Reuse Attack
- Wrong User Binding Attack

## Technologies

- Python
- Dataclasses
- hashlib
- secrets

## Author

Michael Lim
