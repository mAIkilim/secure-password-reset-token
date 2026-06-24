import secrets
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

class InsecurePasswordResetService:
   def __init__(self):
       self.reset_tokens = {}

   def request_reset(self, email: str) -> str:
       token = secrets.token_hex(8)

       self.reset_tokens[token] = email

       print(f"[LOG] Reset token for {email}: {token}")

       return token

   def reset_password(self, token: str, new_password: str):

       email = self.reset_tokens.get(token)

       if email is None:
           raise ValueError("Invalid token")

       print(f"Password for {email} changed to: {new_password}")


def demo_insecure():
   print("\n=== DEMO INSECURE VERSION ===")

   service = InsecurePasswordResetService()

   token = service.request_reset("alice@example.com")

   service.reset_password(token, "newPassword123")

   service.reset_password(token, "hackedAgain123")


@dataclass(frozen=True)
class UserId:
   value: str

   def __post_init__(self):
       if not self.value or not self.value.strip():
           raise ValueError("UserId tidak boleh kosong")


@dataclass(frozen=True)
class EmailAddress:
   value: str

   def __post_init__(self):
       normalized = self.value.strip().lower()

       if "@" not in normalized:
           raise ValueError("Email tidak valid")

       object.__setattr__(self, "value", normalized)


class PasswordResetToken:

   EXPIRY_MINUTES = 15

   def __init__(self, user_id: UserId):
       self._plain_token = secrets.token_urlsafe(32)
       self._token_hash = self._hash(self._plain_token)
       self._user_id = user_id
       self._created_at = datetime.now(timezone.utc)
       self._expires_at = self._created_at + timedelta(minutes=self.EXPIRY_MINUTES)
       self._consumed = False

   @staticmethod
   def _hash(value: str) -> str:
       return hashlib.sha256(value.encode()).hexdigest()

   @property
   def user_id(self) -> UserId:
       return self._user_id

   @property
   def token_hash(self) -> str:
       return self._token_hash

   @property
   def expires_at(self) -> datetime:
       return self._expires_at

   def expose_once(self) -> str:

       if self._plain_token is None:
           raise RuntimeError("Token plaintext sudah pernah diekspos")

       token = self._plain_token
       self._plain_token = None
       return token

   def matches(self, raw_token: str) -> bool:
       candidate_hash = self._hash(raw_token)
       return secrets.compare_digest(candidate_hash, self._token_hash)

   def is_expired(self) -> bool:
       return datetime.now(timezone.utc) > self._expires_at

   def consume(self):
       if self._consumed:
           raise RuntimeError("Token sudah pernah digunakan")

       if self.is_expired():
           raise RuntimeError("Token sudah expired")

       self._consumed = True

   def __str__(self):
       return "[PASSWORD_RESET_TOKEN_PROTECTED]"


@dataclass(frozen=True)
class NewPassword:
   value: str

   def __post_init__(self):
       if len(self.value) < 8:
           raise ValueError("Password minimal 8 karakter")

       if self.value != self.value.strip():
           raise ValueError("Password tidak boleh diawali/diakhiri spasi")


@dataclass
class User:
   user_id: UserId
   email: EmailAddress
   password_hash: str

   def change_password(self, new_password: NewPassword):
       self.password_hash = hashlib.sha256(new_password.value.encode()).hexdigest()



class SecurePasswordResetService:
   def __init__(self):
       self.users_by_email = {}
       self.tokens_by_hash = {}

   def register_user(self, user: User):
       self.users_by_email[user.email.value] = user

   def request_reset(self, email: EmailAddress) -> str:
       user = self.users_by_email.get(email.value)

       if user is None:
           raise ValueError("Jika email terdaftar, instruksi reset akan dikirim")

       reset_token = PasswordResetToken(user.user_id)

       self.tokens_by_hash[reset_token.token_hash] = reset_token

       raw_token = reset_token.expose_once()

       print("[SECURE LOG] Password reset requested")
       print("[SECURE LOG] Token tidak dicetak ke log")

       return raw_token

   def reset_password(
       self,
       email: EmailAddress,
       raw_token: str,
       new_password: NewPassword
   ):
       user = self.users_by_email.get(email.value)

       if user is None:
           raise ValueError("User tidak ditemukan")

       token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
       reset_token = self.tokens_by_hash.get(token_hash)

       if reset_token is None:
           raise ValueError("Token tidak valid")

       if not reset_token.matches(raw_token):
           raise ValueError("Token tidak cocok")

       if reset_token.user_id != user.user_id:
           raise ValueError("Token tidak dimiliki user ini")

       reset_token.consume()

       user.change_password(new_password)

       del self.tokens_by_hash[token_hash]

       print(f"Password berhasil diubah untuk {user.email.value}")


def demo_secure():
   print("\n=== DEMO SECURE VERSION ===")

   service = SecurePasswordResetService()

   user = User(
       user_id=UserId("user-001"),
       email=EmailAddress("alice@example.com"),
       password_hash="old_hash"
   )

   service.register_user(user)

   raw_token = service.request_reset(EmailAddress("alice@example.com"))

   service.reset_password(
       email=EmailAddress("alice@example.com"),
       raw_token=raw_token,
       new_password=NewPassword("newPassword123")
   )

   print("\n=== TEST TOKEN REUSE ===")
   try:
       service.reset_password(
           email=EmailAddress("alice@example.com"),
           raw_token=raw_token,
           new_password=NewPassword("hackedAgain123")
       )
   except Exception as error:
       print("Expected rejection:", error)

   print("\n=== TEST WRONG USER BINDING ===")
   bob = User(
       user_id=UserId("user-002"),
       email=EmailAddress("bob@example.com"),
       password_hash="old_hash"
   )

   service.register_user(bob)

   bob_token = service.request_reset(EmailAddress("bob@example.com"))

   try:
       service.reset_password(
           email=EmailAddress("alice@example.com"),
           raw_token=bob_token,
           new_password=NewPassword("attackerPass123")
       )
   except Exception as error:
       print("Expected rejection:", error)


if __name__ == "__main__":
   demo_insecure()
   demo_secure()
